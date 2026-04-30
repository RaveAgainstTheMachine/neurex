# neurex-api/core/languages/lsp_manager.py
import asyncio
import os
import json
import logging
from typing import Dict, List, Optional
from core.logger import get_logger

logger = get_logger("lsp_manager")

LSP_COMMANDS = {
    "python": ["pyright-langserver", "--stdio"],
    "javascript": ["typescript-language-server", "--stdio"],
    "typescript": ["typescript-language-server", "--stdio"],
    "rust": ["rust-analyzer"],
    "go": ["gopls"],
    "cpp": ["clangd"],
    "c": ["clangd"],
    "csharp": ["csharp-ls"],
    "java": ["jdtls"],
    "swift": ["sourcekit-lsp"],
    "php": ["php-language-server"],
    "html": ["vscode-html-language-server", "--stdio"],
    "css": ["vscode-css-language-server", "--stdio"],
    "json": ["vscode-json-language-server", "--stdio"],
    "yaml": ["yaml-language-server", "--stdio"],
    "dockerfile": ["docker-langserver", "--stdio"],
    "bash": ["bash-language-server", "start"],
    "sql": ["sql-language-server", "up", "--method", "stdio"],
}

class LSPSession:
    def __init__(self, lang: str, workspace_path: str):
        self.lang = lang
        self.workspace_path = workspace_path
        self.process: Optional[asyncio.subprocess.Process] = None
        self.cmd = LSP_COMMANDS.get(lang)
        self._running = False

    async def start(self):
        if not self.cmd:
            raise ValueError(f"No LSP command configured for {self.lang}")

        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path
            )
            self._running = True
            logger.info(f"Started LSP for {self.lang} (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"Failed to start LSP for {self.lang}: {e}")
            raise

    async def stop(self):
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self._running = False
            logger.info(f"Stopped LSP for {self.lang}")

    async def write(self, data: bytes):
        if self.process and self.process.stdin:
            self.process.stdin.write(data)
            await self.process.stdin.drain()

    async def read_stdout(self, chunk_size: int = 4096) -> bytes:
        if self.process and self.process.stdout:
            return await self.process.stdout.read(chunk_size)
        return b""

import shutil

class LSPManager:
    def __init__(self):
        self.sessions: Dict[str, LSPSession] = {}

    def get_supported_languages(self) -> List[str]:
        supported = []
        for lang, cmd in LSP_COMMANDS.items():
            if shutil.which(cmd[0]):
                supported.append(lang)
        return supported

    async def get_session(self, lang: str, workspace_path: str) -> LSPSession:
        session_key = f"{lang}:{workspace_path}"
        if session_key not in self.sessions:
            session = LSPSession(lang, workspace_path)
            await session.start()
            self.sessions[session_key] = session
        return self.sessions[session_key]

    async def cleanup(self):
        for session in self.sessions.values():
            await session.stop()
        self.sessions.clear()

# Global instance
lsp_manager = LSPManager()
