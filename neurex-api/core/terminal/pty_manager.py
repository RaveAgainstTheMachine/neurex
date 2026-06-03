"""
core/terminal/pty_manager.py
Manages pseudo-terminal (PTY) sessions for the interactive IDE terminal.
Uses ptyprocess for robust PTY management without forking the main process.
Provides Human-in-the-Loop command proposal and interception capabilities.
"""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Callable

import structlog
from ptyprocess import PtyProcessUnicode

log = structlog.get_logger()


class PTYManager:
    """
    PTY Manager Singleton that tracks active terminal sessions.
    Guarantees global access to terminal state across API routes and agents.
    """

    _instance = None

    def __new__(cls, *args, **kwargs) -> PTYManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "sessions"):
            self.sessions: dict[str, PTYSession] = {}

    def get_or_create_session(
        self,
        session_id: str,
        on_output: Callable[[str], None] | None = None,
        cwd: str | None = None,
    ) -> PTYSession:
        if session_id not in self.sessions:
            log.info("pty.create_session", session_id=session_id, cwd=cwd)
            session = PTYSession(session_id, cwd=cwd)
            self.sessions[session_id] = session
            session.start()

        session = self.sessions[session_id]
        if on_output:
            session.attach(on_output)
        return session

    def get_session(self, session_id: str) -> PTYSession | None:
        return self.sessions.get(session_id)

    def close_all(self) -> None:
        for s in list(self.sessions.values()):
            s.close()
        self.sessions.clear()

    def close_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            self.sessions[session_id].close()
            del self.sessions[session_id]


class PTYSession:
    def __init__(self, session_id: str, cwd: str | None = None) -> None:
        self.session_id = session_id
        self.listeners: set[Callable[[str], None]] = set()
        self.proc: PtyProcessUnicode | None = None
        self.task: asyncio.Task | None = None
        self.pending_approvals: dict[str, asyncio.Future[bool]] = {}

        requested_workspace = cwd or os.getenv("WORKSPACE_PATH")
        if requested_workspace and os.path.exists(requested_workspace):
            self.workspace = requested_workspace
        else:
            self.workspace = os.getenv("WORKSPACE_PATH", os.getcwd())
            if requested_workspace:
                log.warning(
                    "pty.invalid_cwd",
                    session=session_id,
                    requested=requested_workspace,
                    falling_back=self.workspace,
                )
        self.history = ""
        self.max_history = 50000  # Keep last 50k chars

    def attach(self, on_output: Callable[[str], None]) -> None:
        self.listeners.add(on_output)
        if self.history:
            on_output(self.history)

    def detach(self, on_output: Callable[[str], None]) -> None:
        self.listeners.discard(on_output)

    def _broadcast(self, data: str) -> None:
        self.history += data
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]
        for listener in list(self.listeners):
            try:
                listener(data)
            except Exception:
                pass

    def start(self) -> None:
        try:
            shell_candidates = [
                os.environ.get("SHELL", "/bin/bash"),
                "/bin/bash",
                "/bin/sh",
                "/usr/bin/bash",
            ]
            shell = "/bin/bash"  # Default
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
                "PS1": "neurex> ",
            }
            self.proc = PtyProcessUnicode.spawn([shell], cwd=self.workspace, env=env)
            log.info("pty.started", session=self.session_id, pid=self.proc.pid)
            self.task = asyncio.create_task(self._read_loop())
        except Exception as e:
            log.error("pty.start_failed", session=self.session_id, error=str(e))
            self._broadcast(f"\r\n❌ Failed to start terminal: {e}\r\n")

    async def _read_loop(self) -> None:
        """
        Reads from PTY and broadcasts with a small throttle to aggregate writes.
        Phase 44.5: High-Velocity Terminal Optimization.
        """
        buffer = []
        last_broadcast = asyncio.get_event_loop().time()

        try:
            while self.proc and self.proc.isalive():
                # Non-blocking read (short timeout representation via to_thread)
                data = await asyncio.to_thread(self.proc.read, 4096)
                if data:
                    buffer.append(data)

                now = asyncio.get_event_loop().time()
                # Broadcast if buffer is large or 20ms have passed
                if buffer and (now - last_broadcast > 0.02 or len(buffer) > 10):
                    aggregated = "".join(buffer)
                    self._broadcast(aggregated)
                    buffer = []
                    last_broadcast = now

                # Tiny yield to allow event loop to breathe during floods
                await asyncio.sleep(0.005)

        except EOFError:
            log.info("pty.eof", session=self.session_id)
        except Exception as e:
            if self.proc:
                log.error("pty.read_error", session=self.session_id, error=str(e))
        finally:
            self.close()

    def write(self, data: str) -> None:
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
                    except OSError:
                        pass

    def resize(self, rows: int, cols: int) -> None:
        if self.proc and self.proc.isalive():
            try:
                self.proc.setwinsize(rows, cols)
            except Exception as e:
                log.error("pty.resize_error", session=self.session_id, error=str(e))

    def clear(self) -> None:
        """Clears the session's internal history buffer."""
        self.history = ""
        log.info("pty.history_cleared", session=self.session_id)

    async def propose_and_await_approval(self, command: str, task_id: str) -> bool:
        """
        Dispatches a terminal command proposal via WebSocket and suspends
        execution until the user confirms (Enter) or declines (Esc).
        """
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self.pending_approvals[task_id] = fut

        # Broadcast command proposal to user clients via Presence WebSocket sockets
        from core.collaboration.presence import presence_manager

        log.info("pty.propose_command", session=self.session_id, command=command, task_id=task_id)
        try:
            await presence_manager.broadcast(
                self.session_id,
                {
                    "event": "terminal_command_proposal",
                    "sessionId": self.session_id,
                    "data": {
                        "command": command,
                        "taskId": task_id,
                    },
                },
            )
            # Wait for user input to resolve this command (timeout after 5 mins)
            approved = await asyncio.wait_for(fut, timeout=300.0)
            return approved
        except TimeoutError:
            log.warning("pty.proposal_timeout", session=self.session_id, task_id=task_id)
            return False
        finally:
            self.pending_approvals.pop(task_id, None)

    async def execute_command_in_pty(self, command: str, task_id: str) -> tuple[int, str]:
        """
        Pipes a command directly into the interactive shell PTY process,
        monitoring the output stream until a unique sentinel completes.
        Returns the command exit code and clean aggregated standard output.
        """
        sentinel = f"PTY_CMD_FINISHED__{task_id}__"
        output_buffer: list[str] = []
        loop = asyncio.get_running_loop()
        fut = loop.create_future()

        def listener(data: str) -> None:
            output_buffer.append(data)
            full_output = "".join(output_buffer)
            if sentinel in full_output:
                match = re.search(
                    r"PTY_CMD_FINISHED__[a-zA-Z0-9_-]+__:(?P<code>-?\d+)", full_output
                )
                if match:
                    exit_code = int(match.group("code"))
                    idx = full_output.find(sentinel)
                    # Strip echo trigger lines and return the pure stdout block
                    clean_output = full_output[:idx].strip()
                    if not fut.done():
                        fut.set_result((exit_code, clean_output))

        self.listeners.add(listener)

        try:
            log.info("pty.exec_command_in_stream", session=self.session_id, command=command)
            # Write command to PTY input
            self.write(f"{command}\n")
            await asyncio.sleep(0.1)
            # Pipe sentinel mapping the exit code
            self.write(f"echo {sentinel}:$?\n")

            # Await the listener matching the completion sentinel
            exit_code, clean_stdout = await asyncio.wait_for(fut, timeout=60.0)
            return exit_code, clean_stdout
        except TimeoutError:
            partial = "".join(output_buffer).strip()
            log.warning("pty.exec_stream_timeout", session=self.session_id, command=command)
            return -1, f"Error: Command timed out after 60.0s\nPartial Output:\n{partial}"
        finally:
            self.listeners.discard(listener)

    def close(self) -> None:
        if self.proc:
            try:
                if self.proc.isalive():
                    self.proc.terminate(force=True)
            except OSError:
                pass
            self.proc = None

        if self.task:
            self.task.cancel()
            self.task = None

        for fut in list(self.pending_approvals.values()):
            if not fut.done():
                fut.set_result(False)
        self.pending_approvals.clear()

        log.info("pty.closed", session=self.session_id)
