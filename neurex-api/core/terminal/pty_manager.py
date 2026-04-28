"""
core/terminal/pty_manager.py
Manages pseudo-terminal (PTY) sessions for the interactive IDE terminal.
Uses ptyprocess for robust PTY management without forking the main process.
"""
from __future__ import annotations
import os
import asyncio
import structlog
from typing import Dict, Optional, Callable
from ptyprocess import PtyProcessUnicode

log = structlog.get_logger()

class PTYManager:
    def __init__(self):
        self.sessions: Dict[str, PTYSession] = {}

    def get_or_create_session(self, session_id: str, on_output: Optional[Callable[[str], None]] = None) -> PTYSession:
        if session_id not in self.sessions:
            log.info("pty.create_session", session_id=session_id)
            session = PTYSession(session_id)
            self.sessions[session_id] = session
            session.start()
        
        session = self.sessions[session_id]
        if on_output:
            session.attach(on_output)
        return session

    def get_session(self, session_id: str) -> Optional[PTYSession]:
        return self.sessions.get(session_id)

    def close_all(self):
        for s in list(self.sessions.values()):
            s.close()
        self.sessions.clear()

class PTYSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.listeners: set[Callable[[str], None]] = set()
        self.proc: Optional[PtyProcessUnicode] = None
        self.task: Optional[asyncio.Task] = None
        self.workspace = os.getenv("WORKSPACE_PATH", os.getcwd())
        self.history = ""
        self.max_history = 50000 # Keep last 50k chars

    def attach(self, on_output: Callable[[str], None]):
        self.listeners.add(on_output)
        if self.history:
            on_output(self.history)

    def detach(self, on_output: Callable[[str], None]):
        self.listeners.discard(on_output)

    def _broadcast(self, data: str):
        self.history += data
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        for listener in list(self.listeners):
            listener(data)

    def start(self):
        try:
            shell_candidates = [os.environ.get("SHELL", "/bin/bash"), "/bin/bash", "/bin/sh", "/usr/bin/bash"]
            shell = "/bin/bash" # Default
            for c in shell_candidates:
                if os.path.exists(c):
                    shell = c
                    break
            
            # Enhance environment for modern shells
            env = {
                **os.environ,
                "TERM": "xterm-256color",
                "COLORTERM": "truecolor",
                "LANG": "en_US.UTF-8",
                "LC_ALL": "en_US.UTF-8",
                "PS1": "neurex> "
            }
            self.proc = PtyProcessUnicode.spawn(
                [shell],
                cwd=self.workspace,
                env=env
            )
            log.info("pty.started", session=self.session_id, pid=self.proc.pid)
            self.task = asyncio.create_task(self._read_loop())
        except Exception as e:
            log.error("pty.start_failed", session=self.session_id, error=str(e))
            self._broadcast(f"\r\n❌ Failed to start terminal: {e}\r\n")

    async def _read_loop(self):
        try:
            while self.proc and self.proc.isalive():
                data = await asyncio.to_thread(self.proc.read, 4096)
                if data:
                    self._broadcast(data)
        except EOFError:
            log.info("pty.eof", session=self.session_id)
        except Exception as e:
            if self.proc:
                log.error("pty.read_error", session=self.session_id, error=str(e))
        finally:
            self.close()

    def write(self, data: str):
        if not self.proc or not self.proc.isalive():
            log.warning("pty.dead_on_write", session=self.session_id, msg="Restarting PTY session")
            self.start()
        
        if self.proc and self.proc.isalive():
            try:
                self.proc.write(data)
            except Exception as e:
                log.error("pty.write_error", session=self.session_id, error=str(e))
                self.close()
                self.start()
                if self.proc and self.proc.isalive():
                    try:
                        self.proc.write(data)
                    except:
                        pass

    def resize(self, rows: int, cols: int):
        if self.proc and self.proc.isalive():
            try:
                self.proc.setwinsize(rows, cols)
            except Exception as e:
                log.error("pty.resize_error", session=self.session_id, error=str(e))

    def close(self):
        if self.proc:
            try:
                if self.proc.isalive():
                    self.proc.terminate(force=True)
            except:
                pass
            self.proc = None
        
        if self.task:
            self.task.cancel()
            self.task = None
        
        log.info("pty.closed", session=self.session_id)
