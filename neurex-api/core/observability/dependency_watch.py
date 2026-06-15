"""
core/observability/dependency_watch.py
Periodic dependency health monitoring.
"""

import asyncio

import structlog

from core.agents.dependency_agent import DependencyAgent
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser

log = structlog.get_logger()


class DependencyWatch:
    def __init__(self):
        self.interval = 3600 * 24  # Once a day
        self.agent = DependencyAgent(RulesParser(), ContextManager())

    async def run_local_audit(self):
        """Perform a fast local check of outdated dependencies and record findings to FlightRecorder."""
        log.info("dependency_watch.local_audit_start")
        try:
            import sys

            # Execute sys.executable -m pip list --outdated
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pip",
                "list",
                "--outdated",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
                stdout_str = stdout.decode().strip()
                stderr_str = stderr.decode().strip()
            except TimeoutError:
                proc.kill()
                stdout_str = ""
                stderr_str = "Timeout running pip list --outdated"
                log.warning("dependency_watch.local_audit_timeout")

            if proc.returncode == 0:
                if stdout_str:
                    lines = stdout_str.split("\n")
                    # First two lines are headers
                    outdated_count = max(0, len(lines) - 2)
                    summary = f"Audit complete. Found {outdated_count} outdated packages."
                    rationale = f"Outdated packages:\n{stdout_str}"
                else:
                    summary = "Audit complete. No outdated packages found."
                    rationale = "All dependencies are up-to-date in this environment."
            else:
                summary = "Audit failed."
                rationale = f"Pip exited with code {proc.returncode}. Stderr: {stderr_str}"

            log.info("dependency_watch.local_audit_complete", summary=summary)

            # Import and record decision to FlightRecorder
            from core.observability.flight_recorder import record_decision

            await record_decision(
                conversation_id="system-watch",
                agent_type="dependency",
                decision="Dependency Audit",
                rationale=rationale,
                task_id="dependency-startup-audit",
            )
        except Exception as e:
            log.error("dependency_watch.local_audit_failed", error=str(e))
            try:
                from core.observability.flight_recorder import record_decision

                await record_decision(
                    conversation_id="system-watch",
                    agent_type="dependency",
                    decision="Dependency Audit",
                    rationale=f"Error executing local audit: {str(e)}",
                    task_id="dependency-startup-audit",
                )
            except Exception as fe:
                log.error("dependency_watch.local_audit_log_failed", error=str(fe))

    async def start_background_watch(self):
        """Periodically audit project dependencies."""
        log.info("dependency_watch.start", interval=self.interval)

        # Run fast local audit immediately on initialization
        await self.run_local_audit()

        while True:
            try:
                log.info("dependency_watch.audit_init")

                # We simulate a task for the agent
                task = {
                    "title": "Automated Dependency Audit",
                    "description": "Scan the workspace for outdated or insecure dependencies and log findings.",
                    "history": "System scheduled maintenance.",
                }

                # Run the agent (we consume the stream but don't need to yield it to a WS)
                # Note: DependencyAgent needs a conversation_id for locking, we use a system ID
                async for chunk in self.agent.execute(task, conversation_id="system-watch"):
                    if chunk["type"] == "result":
                        log.info("dependency_watch.audit_complete", result=chunk["result"][:500])

            except Exception as e:
                log.error("dependency_watch.error", error=str(e))

            await asyncio.sleep(self.interval)


dependency_watch = DependencyWatch()
