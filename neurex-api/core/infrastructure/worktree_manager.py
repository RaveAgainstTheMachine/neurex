"""
core/infrastructure/worktree_manager.py
Manages isolated Git Worktrees for Swarm sub-agents.
Prevents overlapping file changes and race conditions during parallel refactors.
"""
from __future__ import annotations
import asyncio
import os
import shutil
import structlog

log = structlog.get_logger()

class WorktreeManager:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.worktrees_dir = os.path.join(base_path, ".neurex", "worktrees")
        os.makedirs(self.worktrees_dir, exist_ok=True)

    async def create_worktree(self, name: str, branch: str = "main") -> str:
        """Creates an isolated git worktree for a sub-agent."""
        target_path = os.path.join(self.worktrees_dir, name)
        log.info("worktree.creating", name=name, path=target_path)
        
        # git worktree add <path> <branch>
        cmd = ["git", "worktree", "add", target_path, branch]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.base_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                log.error("worktree.creation_failed", error=stderr.decode())
                return self.base_path # Fallback to main path if worktree fails
            return target_path
        except Exception as e:
            log.error("worktree.exception", error=str(e))
            return self.base_path

    async def cleanup_worktree(self, name: str):
        """Removes a git worktree after the task is done."""
        target_path = os.path.join(self.worktrees_dir, name)
        log.info("worktree.cleanup", name=name)
        
        # git worktree remove <path>
        cmd = ["git", "worktree", "remove", "--force", target_path]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.base_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if os.path.exists(target_path):
                shutil.rmtree(target_path, ignore_errors=True)
        except Exception as e:
            log.warning("worktree.cleanup_failed", error=str(e))

worktree_manager = WorktreeManager(os.getenv("WORKSPACE_PATH", os.getcwd()))
