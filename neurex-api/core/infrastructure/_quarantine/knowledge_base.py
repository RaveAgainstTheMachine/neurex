"""
core/infrastructure/knowledge_base.py
Phase 49: Neural Collective Intelligence (Swarm Knowledge Base)
Maintains a decentralized index of abstracted 'Neural Lessons' shared across the Mesh.
Enables workspaces to query and benefit from collective engineering patterns.
"""
import asyncio

import structlog

from core.infrastructure.distiller import NeuralLesson

log = structlog.get_logger()

class SwarmKnowledgeBase:
    def __init__(self):
        self.lessons: dict[str, list[NeuralLesson]] = {} # domain -> [lessons]
        self.kb_lock = asyncio.Lock()

    async def register_lesson(self, lesson: NeuralLesson):
        """Registers a scrubbed neural lesson in the global swarm index."""
        async with self.kb_lock:
            if lesson.domain not in self.lessons:
                self.lessons[lesson.domain] = []
            
            # Keep only the most effective lessons per domain
            self.lessons[lesson.domain].append(lesson)
            self.lessons[lesson.domain].sort(key=lambda lsn: lsn.success_delta, reverse=True)
            self.lessons[lesson.domain] = self.lessons[lesson.domain][:50]
            
        log.info("knowledge_base.lesson_indexed", domain=lesson.domain, pattern=lesson.pattern_id)

    def query_lessons(self, domain: str) -> list[NeuralLesson]:
        """Queries the index for the most effective lessons in a specific domain."""
        return self.lessons.get(domain, [])

    async def synchronize_swarm_intelligence(self):
        """
        Simulated background task that syncs the knowledge base with other Mesh projects.
        In Phase 49, this would use a decentralized gossip protocol or P2P DHT.
        """
        log.debug("knowledge_base.synchronizing_collective")
        # Simulated sync overhead
        await asyncio.sleep(0.1)

swarm_kb = SwarmKnowledgeBase()
