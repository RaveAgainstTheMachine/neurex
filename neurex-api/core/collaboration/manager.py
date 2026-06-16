"""
core/collaboration/manager.py
Federated Governance & Zero-Trust Collision Prevention Engine
"""

import time
from datetime import UTC, datetime, timedelta

import structlog
from sqlmodel import select

from core.collaboration.presence import presence_manager
from core.task_graph import FileLock, async_session

log = structlog.get_logger()


class CollaborationManager:
    def __init__(self):
        # We use a unique node ID to identify which mesh instance holds a lock
        self.node_id = f"node-{int(time.time())}"

    async def acquire_lock(
        self,
        path: str,
        requester_id: str,
        ttl_seconds: int = 300,
        conversation_id: str | None = None,
    ) -> bool:
        """
        Federated Collision Prevention:
        Ensure only one entity (User or Agent) can mutate a file across the entire mesh.
        """
        session = async_session()
        try:
            now = datetime.now(UTC)

            # Check for existing lock
            current_lock = await session.get(FileLock, path)

            # If lock exists and hasn't expired, and it's not the requester's
            if current_lock:
                expires_at = current_lock.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=UTC)

                if expires_at > now and current_lock.locked_by != requester_id:
                    log.warn(
                        "collaboration.lock_denied",
                        path=path,
                        requester=requester_id,
                        locked_by=current_lock.locked_by,
                        node=current_lock.owner_node,
                    )
                    return False

                # If it's expired or owned by the same requester, we can overwrite/renew
                await session.delete(current_lock)
                await session.commit()

            # Grant or renew lock
            new_lock = FileLock(
                path=path,
                locked_by=requester_id,
                owner_node=self.node_id,
                expires_at=now + timedelta(seconds=ttl_seconds),
            )
            session.add(new_lock)
            await session.commit()

            # Broadcast to the conversation
            if conversation_id:
                await presence_manager.broadcast(
                    conversation_id,
                    {
                        "event": "lock_update",
                        "data": {
                            "path": path,
                            "locked_by": requester_id,
                            "expires_at": new_lock.expires_at.isoformat(),
                        },
                    },
                )

            log.info(
                "collaboration.lock_acquired", path=path, requester=requester_id, node=self.node_id
            )
            return True
        finally:
            await session.close()

    async def release_lock(
        self, path: str, requester_id: str, conversation_id: str | None = None
    ) -> bool:
        """Release a held lock, allowing others to edit."""
        session = async_session()
        try:
            current_lock = await session.get(FileLock, path)

            if current_lock and current_lock.locked_by == requester_id:
                await session.delete(current_lock)
                await session.commit()

                if conversation_id:
                    await presence_manager.broadcast(
                        conversation_id, {"event": "lock_release", "data": {"path": path}}
                    )

                log.info("collaboration.lock_released", path=path, requester=requester_id)
                return True

            return False
        finally:
            await session.close()

    async def get_active_locks(self) -> list[FileLock]:
        """Fetch all active locks across the mesh."""
        session = async_session()
        try:
            now = datetime.now(UTC)
            statement = select(FileLock).where(FileLock.expires_at > now)
            results = await session.exec(statement)
            return results.all()
        finally:
            await session.close()


collaboration_manager = CollaborationManager()
