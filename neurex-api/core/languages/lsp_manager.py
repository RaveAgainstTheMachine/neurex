# neurex-api/core/languages/lsp_manager.py
import asyncio
import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from core.logger import get_logger

logger = get_logger("lsp_manager")

# Path to workspace-local LSP binaries
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_PATH", "."))
MANAGED_LSP_DIR = WORKSPACE_ROOT / ".neurex" / "bin" / "lsp"

LSP_COMMANDS = {
    # Core & Systems
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
    "ruby": ["solargraph", "stdio"],
    "lua": ["lua-language-server"],
    "zig": ["zls"],
    "nim": ["nimlsp"],
    "d": ["serve-d"],
    "pascal": ["pascal-language-server"],
    "fortran": ["fortls"],
    "cobol": ["cobol-lsp"],
    
    # Web & Frameworks
    "html": ["vscode-html-language-server", "--stdio"],
    "css": ["vscode-css-language-server", "--stdio"],
    "json": ["vscode-json-language-server", "--stdio"],
    "yaml": ["yaml-language-server", "--stdio"],
    "xml": ["lemminx"],
    "dockerfile": ["docker-langserver", "--stdio"],
    "bash": ["bash-language-server", "start"],
    "sql": ["sql-language-server", "up", "--method", "stdio"],
    "svelte": ["svelteserver", "--stdio"],
    "vue": ["vls"],
    "astro": ["astro-ls", "--stdio"],
    "graphql": ["graphql-lsp", "server", "-m", "stream"],
    "tailwindcss": ["tailwindcss-language-server", "--stdio"],
    
    # Functional & Niche
    "elixir": ["elixir-ls"],
    "erlang": ["erlang_ls"],
    "haskell": ["haskell-language-server-wrapper", "--stdio"],
    "clojure": ["clojure-lsp"],
    "scala": ["metals"],
    "kotlin": ["kotlin-language-server"],
    "dart": ["dart", "analysis_server"],
    "ocaml": ["ocamllsp"],
    "fsharp": ["fsautocomplete"],
    "racket": ["racket", "-l", "racket-langserver"],
    
    # Data & Ops
    "terraform": ["terraform-ls", "serve"],
    "nix": ["nil"],
    "ansible": ["ansible-language-server", "--stdio"],
    "latex": ["texlab"],
    "markdown": ["marksman", "server"],
    "r": ["R", "--slave", "-e", "languageserver::run()"],
    "julia": ["julia", "--startup-file=no", "--history-file=no", "-e", "using LanguageServer; runserver()"],
    "perl": ["perl", "-MPerl::LanguageServer", "-e", "Perl::LanguageServer::run()"],
    "powershell": ["pwsh", "-NoProfile", "-NonInteractive", "-Command", "PowerShellEditorServices.Start.ps1"],
}

# Installation recipes (shell commands)
LSP_RECIPES = {
    "python": "npm install pyright",
    "javascript": "npm install typescript-language-server",
    "typescript": "npm install typescript-language-server",
    "rust": "rustup component add rust-analyzer",
    "go": "go install golang.org/x/tools/gopls@latest",
    "html": "npm install vscode-langservers-extracted",
    "css": "npm install vscode-langservers-extracted",
    "json": "npm install vscode-langservers-extracted",
    "yaml": "npm install yaml-language-server",
    "dockerfile": "npm install dockerfile-language-server-nodejs",
    "bash": "npm install bash-language-server",
    "svelte": "npm install svelte-language-server",
    "vue": "npm install vls",
    "astro": "npm install @astrojs/language-server",
    "graphql": "npm install graphql-language-service-cli",
    "tailwindcss": "npm install @tailwindcss/language-server",
    "terraform": "brew install hashicorp/tap/terraform-ls",
    "markdown": "brew install marksman",
    "lua": "brew install lua-language-server",
    "zig": "brew install zls",
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

    def _find_executable(self, cmd: str) -> Optional[str]:
        # 1. Check managed directory first
        managed_path = str(MANAGED_LSP_DIR / "node_modules" / ".bin")
        managed_exe = shutil.which(cmd, path=f"{managed_path}:{os.getenv('PATH')}")
        if managed_exe:
            return managed_exe
            
        # 2. Check system path
        return shutil.which(cmd)

    async def install_lsp(self, lang: str):
        if lang not in LSP_RECIPES:
            raise ValueError(f"No installation recipe for {lang}")
            
        recipe = LSP_RECIPES[lang]
        MANAGED_LSP_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"installing_lsp: {lang} with recipe: {recipe}")
        
        # Run installation in managed directory
        process = await asyncio.create_subprocess_shell(
            recipe,
            cwd=str(MANAGED_LSP_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info(f"lsp_installed_successfully: {lang}")
            return True
        else:
            logger.error(f"lsp_installation_failed: {lang}, error={stderr.decode()}")
            raise Exception(f"Installation failed: {stderr.decode()}")

    def get_supported_languages(self) -> List[str]:
        supported = []
        for lang, cmd in LSP_COMMANDS.items():
            if self._find_executable(cmd[0]):
                supported.append(lang)
        return supported

    async def get_session(self, lang: str, workspace_path: str) -> LSPSession:
        session_key = f"{lang}:{workspace_path}"
        if session_key not in self.sessions:
            # Check for custom override in .neurex/lsp.json
            custom_config = self._load_custom_config()
            if lang in custom_config:
                LSP_COMMANDS[lang] = custom_config[lang]
            elif lang not in LSP_COMMANDS:
                # Try to guess the command
                guessed = self._guess_lsp_command(lang)
                if guessed:
                    LSP_COMMANDS[lang] = guessed
                else:
                    raise ValueError(f"No LSP command found for {lang}")
                
            session = LSPSession(lang, workspace_path)
            await session.start()
            self.sessions[session_key] = session
        return self.sessions[session_key]

    def _guess_lsp_command(self, lang: str) -> Optional[List[str]]:
        """Try to find an LSP binary by common naming patterns."""
        patterns = [
            f"{lang}-language-server",
            f"{lang}-languageserver",
            f"{lang}-lsp",
            f"lsp-{lang}",
            f"{lang}ls"
        ]
        for p in patterns:
            exe = self._find_executable(p)
            if exe:
                logger.info(f"Guessed LSP command for {lang}: {p}")
                # Most guessed servers work with --stdio or no args
                return [p, "--stdio"]
        return None

    def _load_custom_config(self) -> Dict:
        config_path = WORKSPACE_ROOT / ".neurex" / "lsp.json"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load custom LSP config: {e}")
        return {}

    async def cleanup(self):
        for session in self.sessions.values():
            await session.stop()
        self.sessions.clear()

# Global instance
lsp_manager = LSPManager()
