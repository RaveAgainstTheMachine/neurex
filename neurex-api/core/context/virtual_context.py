"""
core/context/virtual_context.py
Unified context assembler implementing the Virtual Context Paging System.
"""

from __future__ import annotations

import asyncio
import os
import re

import structlog

from core.context.compression import ContextCompressor
from core.context.manager import ContextManager
from core.settings.manager import settings_manager

log = structlog.get_logger()


class VirtualContextAssembler:
    def __init__(self, context_manager: ContextManager):
        self.ctx = context_manager
        self.compressor = ContextCompressor(context_manager)

    def _compute_hardware_budget(self) -> int:
        """Convert pooled VRAM to usable token budget, respecting manual overrides."""
        hw_override = settings_manager.get("llm_hardware_context")
        if hw_override and hw_override > 0:
            return hw_override

        from core.infrastructure.vram_pool import vram_pool
        return vram_pool.get_effective_context_tokens()

    def _gather_hot(self, query: str, conversation_id: str | None, task_history: list[dict] | None, budget: int) -> list[dict]:
        """
        Gathers Tier 1 (HOT) context:
        - The last 3 chat turns (either from task_history or db query)
        - Content of active file(s) mentioned in the query or task description
        """
        hot_messages = []
        history_messages = []

        # 1. Gather chat history (prioritize task_history parameter, fallback to DB query)
        if task_history:
            history_messages = task_history.copy()
        elif conversation_id:
            try:
                from sqlmodel import select

                from api.routes.chat import ChatMessage
                from core.task_graph import AsyncSession, engine
                
                clean_request = query.split("User request:")[-1].strip() if "User request:" in query else query
                
                # Fetch history synchronously since we are wrapped in run_in_executor/to_thread
                async def fetch_history():
                    async with AsyncSession(engine) as db_session:
                        stmt = (
                            select(ChatMessage)
                            .where(ChatMessage.conversation_id == conversation_id)
                            .order_by(ChatMessage.created_at.desc())
                            .limit(10)
                        )
                        res = await db_session.exec(stmt)
                        return res.all()
                
                # Run the async fetch in a loop block since this runs in a separate thread
                loop = asyncio.new_event_loop()
                try:
                    db_messages = loop.run_until_complete(fetch_history())
                finally:
                    loop.close()

                for msg in reversed(db_messages):
                    if msg.role == "user" and (msg.content.strip() == clean_request or clean_request.endswith(msg.content.strip())):
                        continue
                    history_messages.append({"role": msg.role, "content": msg.content})
            except Exception as e:
                log.warning("virtual_context.db_history_load_failed", error=str(e))

        # Keep last 3 turns
        recent_turns = history_messages[-3:] if history_messages else []
        for msg in recent_turns:
            hot_messages.append(msg.copy())

        # 2. Extract and load active files mentioned in query or history
        file_paths = set()
        texts_to_scan = [query]
        for m in history_messages:
            content = m.get("content") or ""
            if isinstance(content, str):
                texts_to_scan.append(content)

        for text in texts_to_scan:
            matches = re.findall(r"(?:file:///|/|[a-zA-Z]:\\|[.\w\-_]+/)([\w\-_./]+)", text)
            for m in matches:
                cleaned = m.strip("`'\"()[]{},.")
                if cleaned and ("." in cleaned or "/" in cleaned or "\\" in cleaned):
                    if os.path.isfile(cleaned):
                        file_paths.add(os.path.abspath(cleaned))
                    else:
                        cand = os.path.join(os.getcwd(), cleaned)
                        if os.path.isfile(cand):
                            file_paths.add(os.path.abspath(cand))

        # Load file contents up to budget limit
        current_tokens = self.ctx._count_tokens(hot_messages)
        for fp in sorted(file_paths):
            try:
                with open(fp, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                file_tokens = self.ctx.count_tokens(content)
                if current_tokens + file_tokens + 200 > budget:
                    # Fit what we can
                    fit_chars = (budget - current_tokens - 200) * 4
                    if fit_chars > 100:
                        content_truncated = content[:fit_chars] + "\n... [truncated to fit hot context budget]"
                        hot_messages.append({
                            "role": "system",
                            "content": f"### [ACTIVE FILE: {os.path.basename(fp)}]\nPath: {fp}\n\n{content_truncated}"
                        })
                        current_tokens += self.ctx.count_tokens(content_truncated)
                    break
                else:
                    hot_messages.append({
                        "role": "system",
                        "content": f"### [ACTIVE FILE: {os.path.basename(fp)}]\nPath: {fp}\n\n{content}"
                    })
                    current_tokens += file_tokens
            except Exception:
                pass

        return hot_messages

    async def _gather_warm(self, query: str, budget: int) -> list[dict]:
        """
        Gathers Tier 2 (WARM) context:
        - FederatedRAG global search, AST-compacted to signatures and docstrings.
        """
        try:
            from core.context.federated_rag import FederatedRAG
            frag = FederatedRAG(self.ctx)
            raw_rag = await frag.global_search(query, limit=10)
            
            compacted = self.compressor.compress_to_signatures(raw_rag)
            
            # Truncate warm context if it exceeds budget
            if self.ctx.count_tokens(compacted) > budget:
                fit_chars = budget * 4
                compacted = compacted[:fit_chars] + "\n... [truncated warm context]"
                
            return [{"role": "system", "content": f"### [WARM CONTEXT: AST SIGNATURES]\n{compacted}"}]
        except Exception as e:
            log.warning("virtual_context.warm_gather_failed", error=str(e))
            return []

    async def _gather_cold(self, query: str, conversation_id: str | None, budget: int) -> list[dict]:
        """
        Gathers Tier 3 (COLD) context:
        - Vectorized memories from HiveMind
        - Dynamic summaries of older chat interactions
        """
        cold_messages = []
        
        # 1. Hive Mind recall
        try:
            from core.memory.hive import hive_mind
            memories = hive_mind.recall(query, limit=5)
            if memories:
                memory_str = "\n".join([f"- {m['content']}" for m in memories])
                cold_messages.append({
                    "role": "system",
                    "content": f"### [COLD CONTEXT: VECTORIZED MEMORIES]\n{memory_str}"
                })
        except Exception as e:
            log.warning("virtual_context.hive_mind_failed", error=str(e))

        return cold_messages

    def _enforce_budget(
        self,
        system_prompt: str,
        hot: list[dict],
        warm: list[dict],
        cold: list[dict],
        hardware_budget: int
    ) -> list[dict]:
        """
        Prune and cap slot components to fit within the computed hardware budget.
        System prompt has the highest priority.
        """
        budgets = self.ctx.get_budgets(hardware_context=hardware_budget)

        # 1. System Prompt Cap
        sys_msg = {"role": "system", "content": system_prompt}
        sys_tokens = self.ctx._count_tokens([sys_msg])
        if sys_tokens > budgets["SYSTEM_BUDGET"]:
            sys_msg["content"] = sys_msg["content"][:budgets["SYSTEM_BUDGET"] * 4] + "\n... [truncated system prompt]"
            sys_tokens = self.ctx._count_tokens([sys_msg])

        # 2. Trim Cold Budget (15%)
        cold_budget = int(budgets["CONTEXT_WINDOW"] * 0.15)
        while cold and self.ctx._count_tokens(cold) > cold_budget:
            cold.pop()

        # 3. Trim Warm Budget (25%)
        warm_budget = int(budgets["CONTEXT_WINDOW"] * 0.25)
        while warm and self.ctx._count_tokens(warm) > warm_budget:
            msg = warm[0]
            fit_chars = int(warm_budget * 4)
            msg["content"] = msg["content"][:fit_chars] + "\n... [truncated warm context]"
            break

        # 4. Trim Hot Budget (35%)
        hot_budget = int(budgets["CONTEXT_WINDOW"] * 0.35)
        while hot and self.ctx._count_tokens(hot) > hot_budget:
            if len(hot) > 1:
                hot.pop(0)
            else:
                msg = hot[0]
                fit_chars = int(hot_budget * 4)
                msg["content"] = msg["content"][:fit_chars] + "\n... [truncated hot context]"
                break

        # Combine: System prompt -> Cold -> Warm -> Hot
        final_messages = [sys_msg] + cold + warm + hot

        # Safety Margin check (force-trim if still exceeding the total hardware limit)
        total_tokens = self.ctx._count_tokens(final_messages)
        if total_tokens > hardware_budget:
            # 1. Trim cold entirely
            if total_tokens > hardware_budget and cold:
                final_messages = [sys_msg] + warm + hot
                total_tokens = self.ctx._count_tokens(final_messages)
            # 2. Trim warm entirely
            if total_tokens > hardware_budget and warm:
                final_messages = [sys_msg] + hot
                total_tokens = self.ctx._count_tokens(final_messages)
            # 3. Truncate hot to fit the remaining space
            if total_tokens > hardware_budget and hot:
                allowed_hot_tokens = max(0, hardware_budget - sys_tokens - 100)
                # Keep only last turn, truncated
                last_msg = hot[-1].copy()
                last_msg["content"] = last_msg["content"][:allowed_hot_tokens * 4] + "\n... [truncated hot context]"
                final_messages = [sys_msg, last_msg]

        return final_messages

    async def assemble(
        self,
        query: str,
        conversation_id: str | None,
        agent_type: str,
        task_history: list[dict] | None,
        system_prompt: str
    ) -> tuple[list[dict], int]:
        """
        Assemble dynamic multi-tier context to fit local/mesh VRAM constraints.
        Returns:
            Tuple: (final_messages_list, computed_hardware_budget)
        """
        hardware_budget = self._compute_hardware_budget()
        log.info("virtual_context.assembly_started", agent_type=agent_type, hardware_budget=hardware_budget)

        budgets = self.ctx.get_budgets(hardware_context=hardware_budget)

        # Run I/O intensive Hot gathering in executor
        hot_task = asyncio.to_thread(self._gather_hot, query, conversation_id, task_history, budgets["CONTEXT_WINDOW"])
        warm_task = self._gather_warm(query, budgets["CONTEXT_WINDOW"])
        cold_task = self._gather_cold(query, conversation_id, budgets["CONTEXT_WINDOW"])

        hot, warm, cold = await asyncio.gather(hot_task, warm_task, cold_task)

        final_messages = self._enforce_budget(
            system_prompt=system_prompt,
            hot=hot,
            warm=warm,
            cold=cold,
            hardware_budget=hardware_budget
        )

        total_tokens = self.ctx._count_tokens(final_messages)
        log.info(
            "virtual_context.assembly_completed",
            total_tokens=total_tokens,
            hardware_budget=hardware_budget,
            messages_count=len(final_messages)
        )
        return final_messages, hardware_budget
