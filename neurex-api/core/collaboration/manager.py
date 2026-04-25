"""
core/collaboration/manager.py
Zero-Trust Collaboration & Collision Prevention Engine
"""
from typing import Dict, List, Optional
import structlog
from pydantic import BaseModel
import time

log = structlog.get_logger()

class User(BaseModel):
    id: str
    username: str
    team_id: str
    role: str  # "admin", "developer", "viewer"
    api_key: str

class FileLock(BaseModel):
    path: str
    locked_by: str  # user_id or agent_id
    expires_at: float

class CollaborationManager:
    def __init__(self):
        # In memory mock for Phase 8 implementation; 
        # Production will use Redis or SQLite for distributed locks
        self.users: Dict[str, User] = {}
        self.file_locks: Dict[str, FileLock] = {}
        
        # Default Admin for initialization
        self.users["admin_01"] = User(
            id="admin_01", 
            username="neurex_admin", 
            team_id="core_team", 
            role="admin", 
            api_key="sk-dev-token"
        )

    def authenticate(self, api_key: str) -> Optional[User]:
        """Validate API key and return User object for RBAC."""
        for user in self.users.values():
            if user.api_key == api_key:
                return user
        return None

    def acquire_lock(self, path: str, requester_id: str, ttl_seconds: int = 60) -> bool:
        """
        Advanced Collision Prevention:
        Ensure only one entity (User or Agent) can mutate a file at a time.
        """
        now = time.time()
        current_lock = self.file_locks.get(path)
        
        # If lock exists and hasn't expired, and it's not the requester's
        if current_lock and current_lock.expires_at > now and current_lock.locked_by != requester_id:
            log.warn("collaboration.lock_denied", path=path, requester=requester_id, locked_by=current_lock.locked_by)
            return False
            
        # Grant or renew lock
        self.file_locks[path] = FileLock(
            path=path,
            locked_by=requester_id,
            expires_at=now + ttl_seconds
        )
        log.info("collaboration.lock_acquired", path=path, requester=requester_id)
        return True

    def release_lock(self, path: str, requester_id: str) -> bool:
        """Release a held lock, allowing others to edit."""
        current_lock = self.file_locks.get(path)
        if current_lock and current_lock.locked_by == requester_id:
            del self.file_locks[path]
            log.info("collaboration.lock_released", path=path, requester=requester_id)
            return True
        return False
