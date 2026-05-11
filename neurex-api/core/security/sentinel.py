"""
core/security/sentinel.py
The Security Sentinel. A specialized background agent that monitors the workspace
for architectural security violations, insecure coding patterns, and potential
injection vectors in agent-generated code.
"""

from __future__ import annotations

import asyncio
import ast
import os
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()


class SecuritySentinel:
    def __init__(self, workspace_path: str | None = None):
        self.workspace = Path(workspace_path or os.getenv("WORKSPACE_PATH", "/workspace"))

    def scan_file(self, file_path: str) -> list[dict[str, Any]]:
        """Scans a single file for security issues using AST analysis."""
        full_path = self.workspace / file_path.lstrip("/")
        if not full_path.exists() or not full_path.is_file():
            return []

        if not full_path.suffix == ".py":
            return []  # Currently only support Python AST analysis

        issues = []
        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                # 1. Check for subprocess.run(shell=True)
                if isinstance(node, ast.Call):
                    if self._is_subprocess_shell_true(node):
                        issues.append(
                            {
                                "type": "INSECURE_SUBPROCESS",
                                "severity": "CRITICAL",
                                "line": node.lineno,
                                "message": "subprocess.run with shell=True detected. Potential command injection.",
                            }
                        )

                    # 2. Check for os.system()
                    if self._is_os_system(node):
                        issues.append(
                            {
                                "type": "INSECURE_OS_SYSTEM",
                                "severity": "HIGH",
                                "line": node.lineno,
                                "message": "os.system() used. Use subprocess.run with an argument list instead.",
                            }
                        )

                    # 3. Check for eval() / exec()
                    if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                        issues.append(
                            {
                                "type": "DYNAMIC_EXECUTION",
                                "severity": "CRITICAL",
                                "line": node.lineno,
                                "message": f"{node.func.id}() used. Extremely dangerous in agentic environments.",
                            }
                        )

        except Exception as e:
            log.error("sentinel.scan_failed", file=file_path, error=str(e))

        return issues

    def _is_subprocess_shell_true(self, node: ast.Call) -> bool:
        """Helper to detect subprocess.run(..., shell=True)"""
        # Check if function name is subprocess.run or subprocess.Popen
        func = node.func
        is_subp = False
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                if func.attr in ("run", "Popen", "call", "check_call", "check_output"):
                    is_subp = True

        if not is_subp:
            return False

        # Check for shell=True keyword argument
        for kw in node.keywords:
            if kw.arg == "shell":
                if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
        return False

    def _is_os_system(self, node: ast.Call) -> bool:
        """Helper to detect os.system(...)"""
        func = node.func
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id == "os":
                if func.attr == "system":
                    return True
        return False

    async def audit_workspace(self) -> dict[str, Any]:
        """Performs a full workspace audit."""
        log.info("sentinel.audit_started", workspace=str(self.workspace))
        all_issues = {}

        # Walk workspace (limited to python files for now)
        for root, _, files in os.walk(self.workspace):
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.workspace)
                    if any(
                        part.startswith(".") or part == "venv" or part == "node_modules"
                        for part in rel_path.split(os.sep)
                    ):
                        continue

                    file_issues = self.scan_file(rel_path)
                    if file_issues:
                        all_issues[rel_path] = file_issues

        log.info("sentinel.audit_complete", issues_found=len(all_issues))
        return {
            "status": "success",
            "issues": all_issues,
            "summary": {
                "files_scanned": sum(
                    1 for _, _, files in os.walk(self.workspace) for f in files if f.endswith(".py")
                ),
                "vulnerable_files": len(all_issues),
            },
        }


    async def start_background_scan(self, interval_seconds: int = 300):
        """Periodically scans the workspace for security violations."""
        log.info("sentinel.background_task_started", interval=interval_seconds)
        while True:
            try:
                report = await self.audit_workspace()
                if report["issues"]:
                    log.warning("sentinel.security_audit_findings", 
                                issues_found=len(report["issues"]),
                                vulnerable_files=list(report["issues"].keys()))
                    
                    # Phase 2.2: Future - Generate Task Graph nodes for auto-patching
            except Exception as e:
                log.error("sentinel.background_scan_error", error=str(e))
            
            await asyncio.sleep(interval_seconds)


# Global singleton
security_sentinel = SecuritySentinel()
