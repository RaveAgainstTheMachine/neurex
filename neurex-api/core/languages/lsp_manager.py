# neurex-api/core/languages/lsp_manager.py
import asyncio
import json
import os
import shutil
from pathlib import Path

from core.logger import log as logger

# Path to workspace-local LSP binaries
API_ROOT = Path(__file__).parent.parent.parent
MANAGED_LSP_DIR = API_ROOT / ".neurex" / "bin" / "lsp"
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_PATH", "."))


class DiagnosticTracker:
    def __init__(self):
        # path -> list of diagnostics
        self.diagnostics: dict[str, list[dict]] = {}

    def update(self, uri: str, items: list[dict]):
        # Convert URI to relative path
        from urllib.parse import unquote

        path = unquote(uri.replace("file://", ""))

        try:
            from api.routes.files import get_workspace

            WORKSPACE = get_workspace()
            abs_path = Path(path).resolve()
            if str(abs_path).startswith(str(WORKSPACE)):
                rel_path = str(abs_path.relative_to(WORKSPACE))
                if rel_path == ".":
                    rel_path = ""
                path = rel_path
        except Exception:
            pass

        if not items:
            self.diagnostics.pop(path, None)
        else:
            self.diagnostics[path] = items

        # Trigger global broadcast for UI refresh
        from core.collaboration.presence import presence_manager

        asyncio.create_task(
            presence_manager.broadcast_global(
                {"event": "diagnostics_updated", "data": {"path": path, "diagnostics": items}}
            )
        )

    def get_for_path(self, path: str) -> list[dict]:
        return self.diagnostics.get(path, [])

    def get_count_for_prefix(self, prefix: str) -> int:
        """Returns the total number of diagnostics for all paths starting with prefix."""
        count = 0
        # Ensure prefix ends with / unless empty
        if prefix and not prefix.endswith("/"):
            match_prefix = prefix + "/"
        else:
            match_prefix = prefix

        for path, items in self.diagnostics.items():
            if path == prefix or path.startswith(match_prefix):
                count += len(items)
        return count

    def get_all(self) -> dict[str, list[dict]]:
        return self.diagnostics


diagnostic_tracker = DiagnosticTracker()

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
    "julia": [
        "julia",
        "--startup-file=no",
        "--history-file=no",
        "-e",
        "using LanguageServer; runserver()",
    ],
    "perl": ["perl", "-MPerl::LanguageServer", "-e", "Perl::LanguageServer::run()"],
    "powershell": [
        "pwsh",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "PowerShellEditorServices.Start.ps1",
    ],
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
    "terraform": "curl -L https://github.com/hashicorp/terraform-ls/releases/latest/download/terraform-ls_linux_amd64.zip -o terraform-ls.zip && unzip terraform-ls.zip",
    "markdown": "curl -L https://github.com/artempyanykh/marksman/releases/latest/download/marksman-linux-x64 -o marksman && chmod +x marksman",
    "lua": "npm install lua-language-server",
    "zig": "curl -L https://github.com/zigtools/zls/releases/latest/download/zls-x86_64-linux.tar.xz | tar -xJ",
}


class LSPSession:
    def __init__(self, lang: str, workspace_path: str):
        self.lang = lang
        self.workspace_path = workspace_path
        self.process: asyncio.subprocess.Process | None = None
        self.cmd = LSP_COMMANDS.get(lang)
        self._running = False
        self._output_queue = asyncio.Queue()
        self._reader_task: asyncio.Task | None = None
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._request_id_counter = 0

    async def _read_loop(self):
        """Persistent background reader for LSP stdout with proper protocol parsing."""
        if not self.process or not self.process.stdout:
            return

        buffer = b""
        try:
            while self._running:
                chunk = await self.process.stdout.read(65536)
                if not chunk:
                    break

                buffer += chunk

                # Push raw chunk to queue for any active websocket listeners
                await self._output_queue.put(chunk)

                # Process buffer for diagnostics
                while b"Content-Length:" in buffer and b"\r\n\r\n" in buffer:
                    try:
                        header_start = buffer.find(b"Content-Length:")
                        header_end = buffer.find(b"\r\n\r\n", header_start)
                        if header_end == -1:
                            break

                        length_line = buffer[header_start:header_end].split(b"\r\n")[0]
                        content_length = int(length_line.split(b":")[1].strip())

                        body_start = header_end + 4
                        if len(buffer) < body_start + content_length:
                            break  # Wait for more data

                        body_raw = buffer[body_start : body_start + content_length]
                        buffer = buffer[body_start + content_length :]

                        self.handle_json(body_raw)
                    except Exception as e:
                        logger.error(f"LSP header parse error: {e}")
                        # Move past current header to avoid stuck loop
                        buffer = (
                            buffer[buffer.find(b"Content-Length:", 1) :]
                            if b"Content-Length:" in buffer[1:]
                            else b""
                        )
                        break

        except Exception as e:
            logger.error(f"LSP reader loop error for {self.lang}: {e}")
        finally:
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
                cwd=self.workspace_path,
            )
            self._running = True
            logger.info(f"Started LSP for {self.lang} (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"Failed to start LSP for {self.lang}: {e}")
            raise

        self._reader_task = asyncio.create_task(self._read_loop())

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
        """Read from the pre-populated output queue (consumable by WebSocket)."""
        try:
            # We don't use chunk_size here as we return what's in the queue
            return await self._output_queue.get()
        except Exception:
            return b""

    async def send_request(self, method: str, params: dict) -> dict:
        if not self.process or not self._running:
            raise RuntimeError(f"LSP server for {self.lang} is not running")

        self._request_id_counter += 1
        req_id = self._request_id_counter
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        body = json.dumps(payload).encode('utf-8')
        header = f"Content-Length: {len(body)}\r\n\r\n".encode('ascii')
        
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_requests[req_id] = fut
        
        await self.write(header + body)
        
        try:
            response = await asyncio.wait_for(fut, timeout=10.0)
            return response
        except TimeoutError:
            self._pending_requests.pop(req_id, None)
            raise TimeoutError(f"LSP request '{method}' (id: {req_id}) timed out after 10.0 seconds")

    def handle_json(self, body_raw: bytes):
        """Parse LSP JSON messages for diagnostic tracking and request resolution."""
        try:
            body = json.loads(body_raw.decode('utf-8', errors='ignore'))
            
            # Resolve pending requests if it's a response
            if "id" in body:
                req_id = body["id"]
                fut = self._pending_requests.pop(req_id, None)
                if fut and not fut.done():
                    fut.set_result(body)
                    
            if body.get("method") == "textDocument/publishDiagnostics":
                params = body.get("params", {})
                uri = params.get("uri")
                diagnostics = params.get("diagnostics", [])
                if uri:
                    diagnostic_tracker.update(uri, diagnostics)
        except Exception as e:
            logger.error(f"Failed to parse LSP JSON: {e}")


class LSPManager:
    def __init__(self):
        self.sessions: dict[str, LSPSession] = {}
        self.failed_installs: set[str] = set()
        self.installing_langs: set[str] = set()

    def _find_executable(self, name: str) -> str | None:
        # Check managed dir first (both root and node_modules/.bin)
        managed_root = str(MANAGED_LSP_DIR)
        managed_bin = str(MANAGED_LSP_DIR / "node_modules" / ".bin")

        search_path = f"{managed_root}:{managed_bin}:{os.environ.get('PATH', '')}"
        return shutil.which(name, path=search_path)

    async def initialize_workspace(self, workspace_path: str):
        """Scans workspace for extensions and starts LSPs for found languages."""
        logger.info("lsp.initialize_workspace", workspace_path=workspace_path)
        try:
            from api.routes.files import get_workspace
            workspace = get_workspace()
        except Exception:
            workspace = None

        safe_root = os.path.realpath(str(workspace or "."))
        target = os.path.realpath(workspace_path)
        safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
        if not target.startswith(safe_prefix) and target != safe_root:
            raise PermissionError("Path traversal attempt blocked in initialize_workspace")
        workspace_path = target

        root = Path(workspace_path)
        if not root.exists():
            logger.warning("lsp.workspace_missing", workspace_path=workspace_path)
            return

        found_langs = set()
        ext_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".rs": "rust",
            ".go": "go",
            ".c": "c",
            ".cpp": "cpp",
        }

        # Efficient scan with depth limit
        IGNORED = {".git", "node_modules", "__pycache__", ".neurex_trash", "venv", ".venv"}
        try:

            def scan_dir(path: Path, depth: int):
                if depth <= 0:
                    return
                try:
                    for item in path.iterdir():
                        if item.is_dir():
                            if item.name not in IGNORED:
                                scan_dir(item, depth - 1)
                        elif item.suffix in ext_map:
                            found_langs.add(ext_map[item.suffix])
                        if len(found_langs) > 5:
                            break
                except Exception:
                    pass

            scan_dir(root, 3)
            supported = self.get_supported_languages()
            logger.info("lsp.scan_results", found=list(found_langs), supported=supported)
        except Exception as e:
            logger.error(f"workspace_init_scan_error: {e}")
            pass

        for lang in found_langs:
            if lang in self.failed_installs:
                continue
            if lang in self.get_supported_languages():
                logger.info(f"auto_starting_lsp: {lang} for workspace {workspace_path}")
                try:
                    await self.get_session(lang, workspace_path)
                except Exception:
                    pass
            elif lang in LSP_RECIPES:
                # Autopilot: Auto-install if recipe exists but binary not found
                logger.info(f"autopilot_installing_lsp: {lang} for workspace {workspace_path}")
                try:
                    await self.install_lsp(lang)
                    # Try starting after install
                    if lang in self.get_supported_languages():
                        await self.get_session(lang, workspace_path)
                except Exception as e:
                    logger.error(f"autopilot_install_failed: {lang}, {e}")

    async def install_lsp(self, lang: str):
        if lang in self.get_supported_languages():
            logger.info(f"lsp_already_supported: {lang}")
            if lang in self.failed_installs:
                self.failed_installs.remove(lang)
            return True

        if lang in self.installing_langs:
            logger.info(f"lsp_install_already_in_progress: {lang}")
            return

        if lang not in LSP_RECIPES:
            raise ValueError(f"No installation recipe for {lang}")

        self.installing_langs.add(lang)
        recipe = LSP_RECIPES[lang]
        MANAGED_LSP_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"installing_lsp: {lang} with recipe: {recipe}")

        try:
            # Run installation in managed directory
            process = await asyncio.create_subprocess_shell(
                recipe,
                cwd=str(MANAGED_LSP_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"lsp_installed_successfully: {lang}")
                if lang in self.failed_installs:
                    self.failed_installs.remove(lang)
                return True
            else:
                self.failed_installs.add(lang)
                logger.error(f"lsp_installation_failed: {lang}, error={stderr.decode()}")
                raise Exception(f"Installation failed: {stderr.decode()}")
        finally:
            self.installing_langs.discard(lang)

    def get_supported_languages(self) -> list[str]:
        supported = []
        for lang, cmd in LSP_COMMANDS.items():
            if self._find_executable(cmd[0]):
                supported.append(lang)
        return supported

    def _find_project_root(self, start_path: Path) -> Path:
        """Find the nearest directory containing a .git folder or common project markers."""
        try:
            from api.routes.files import get_workspace
            workspace = get_workspace()
        except Exception:
            workspace = None

        safe_root = os.path.realpath(str(workspace or "."))
        target = os.path.realpath(str(start_path))
        safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
        if not target.startswith(safe_prefix) and target != safe_root:
            raise PermissionError("Path traversal attempt blocked in _find_project_root")
        start_path = Path(target)

        curr = start_path.resolve()
        while curr != curr.parent:
            # Check for git or common project markers
            if (
                (curr / ".git").is_dir()
                or (curr / "pyproject.toml").exists()
                or (curr / "package.json").exists()
            ):
                return curr
            curr = curr.parent

        # If not found in parent, check if there is a project root in a direct subdirectory
        for item in start_path.iterdir():
            if item.is_dir() and ((item / ".git").is_dir() or (item / "pyproject.toml").exists()):
                return item

        return start_path

    async def get_session(self, lang: str, workspace_path: str) -> LSPSession:
        # Adjust workspace_path to the nearest project root
        try:
            from api.routes.files import get_workspace
            workspace = get_workspace()
        except Exception:
            workspace = None

        safe_root = os.path.realpath(str(workspace or "."))
        target = os.path.realpath(workspace_path)
        safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
        if not target.startswith(safe_prefix) and target != safe_root:
            raise PermissionError("Path traversal attempt blocked in get_session")
        workspace_path = target

        actual_root = self._find_project_root(Path(workspace_path))
        root_str = str(actual_root)

        session_key = f"{lang}:{root_str}"
        if session_key not in self.sessions:
            # Check for custom override in .neurex/lsp.json
            custom_config = self._load_custom_config(actual_root)
            if lang in custom_config:
                LSP_COMMANDS[lang] = custom_config[lang]
            elif lang not in LSP_COMMANDS:
                guessed = self._guess_lsp_command(lang)
                if guessed:
                    LSP_COMMANDS[lang] = guessed
                else:
                    raise ValueError(f"No LSP command found for {lang}")

            # Resolve full path for the command
            cmd = LSP_COMMANDS[lang]
            exe_path = self._find_executable(cmd[0])
            if exe_path:
                cmd[0] = exe_path

            session = LSPSession(lang, root_str)
            await session.start()
            self.sessions[session_key] = session
        return self.sessions[session_key]

    def _guess_lsp_command(self, lang: str) -> list[str] | None:
        """Try to find an LSP binary by common naming patterns."""
        patterns = [
            f"{lang}-language-server",
            f"{lang}-languageserver",
            f"{lang}-lsp",
            f"lsp-{lang}",
            f"{lang}ls",
        ]
        for p in patterns:
            exe = self._find_executable(p)
            if exe:
                logger.info(f"Guessed LSP command for {lang}: {p}")
                # Most guessed servers work with --stdio or no args
                return [p, "--stdio"]
        return None

    def _load_custom_config(self, root: Path) -> dict:
        try:
            from api.routes.files import get_workspace
            workspace = get_workspace()
        except Exception:
            workspace = None

        safe_root = os.path.realpath(str(workspace or "."))
        target = os.path.realpath(str(root / ".neurex" / "lsp.json"))
        safe_prefix = safe_root if safe_root.endswith(os.sep) else safe_root + os.sep
        if not target.startswith(safe_prefix) and target != safe_root:
            return {}
        
        config_path = Path(target)

        if config_path.exists():
            try:
                with open(config_path) as f:
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
