"""
core/skills/manager.py
Manages external skill sets (MCP tool collections).
Supports downloading, validating, and dynamic registration.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()


class SkillSet:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict[str, Any]:
        manifest_path = self.path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)
        return {}

    @property
    def tools(self) -> list[dict[str, Any]]:
        return self.manifest.get("tools", [])


class SkillManager:
    def __init__(self):
        self.SKILLS_DIR = Path(os.getenv("NEUREX_SKILLS_PATH", "./skills")).absolute()
        self.SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    def install_from_git(self, url: str) -> str:
        """Clone a skill repository into the local skills store, supporting subdirectories."""
        # SECURITY: Use urlparse to validate domain to prevent SSRF
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if parsed.netloc == "skillsmp.com":
            try:
                import httpx

                # Reconstruct URL from validated parts to satisfy CodeQL (breaks taint flow)
                safe_url = f"https://skillsmp.com{parsed.path}"
                if parsed.query:
                    safe_url += f"?{parsed.query}"

                log.info("skill.resolve_marketplace", url=safe_url)
                resp = httpx.get(safe_url, timeout=10, follow_redirects=False)
                if resp.status_code == 200:
                    import re

                    match = re.search(r"githubUrl=([^&\"' >]+)", resp.text)
                    if match:
                        from urllib.parse import unquote

                        url = unquote(match.group(1))
                        log.info("skill.resolved_from_marketplace", git_url=url)
                    else:
                        match = re.search(r"(https://github\.com/[^\"' >]+)", resp.text)
                        if match:
                            url = match.group(1)
                            log.info("skill.fallback_resolved_from_marketplace", git_url=url)
            except Exception as e:
                log.error("skill.marketplace_resolve_failed", url=url, error=str(e))

        # Handle GitHub tree/blob URLs (subdirectories)
        sub_path = None
        if "github.com" in url and "/tree/" in url:
            import re

            # Extract Repo URL and Path: https://github.com/USER/REPO/tree/BRANCH/PATH
            match = re.match(r"(https://github\.com/[^/]+/[^/]+)/tree/([^/]+)/(.*)", url)
            if match:
                base_repo = match.group(1)
                branch = match.group(2)
                sub_path = match.group(3)

                # SECURITY: Sanitize sub_path to prevent path traversal
                # Ensure it's not absolute and doesn't contain parent directory references
                if os.path.isabs(sub_path) or ".." in sub_path:
                    log.error("security.path_traversal_attempt", path=sub_path)
                    raise Exception(
                        f"Invalid sub-path in URL: {sub_path}. Absolute paths and '..' are forbidden."
                    )

                url = base_repo
                log.info("skill.detected_github_tree", repo=base_repo, branch=branch, path=sub_path)

        name = url.split("/")[-1].replace(".git", "")
        if sub_path:
            name = sub_path.split("/")[-1]

        target_path = self.SKILLS_DIR / name

        if target_path.exists():
            log.info("skill.update", name=name)
            if not sub_path:
                subprocess.run(["git", "pull"], cwd=target_path, check=True)
            else:
                # Update logic for subpath skills would involve re-cloning or tracking origin
                # For now, let's just allow re-install by deletion or skipping
                pass
        else:
            if sub_path:
                import tempfile

                with tempfile.TemporaryDirectory() as tmpdir:
                    log.info("skill.install_subpath", repo=url, path=sub_path)
                    # SECURITY: Use '--' to prevent parameter injection
                    subprocess.run(["git", "clone", "--depth", "1", "--", url, tmpdir], check=True)
                    source = Path(tmpdir) / sub_path
                    if source.exists():
                        shutil.copytree(source, target_path)
                    else:
                        raise Exception(f"Sub-path {sub_path} not found in repository")
            else:
                log.info("skill.install", name=name, url=url)
                # SECURITY: Use '--' to prevent parameter injection
                subprocess.run(["git", "clone", "--", url, str(target_path)], check=True)

        return name

    def _load_metadata(self, skill_path: Path) -> dict[str, Any]:
        """Load metadata from manifest.json or markdown frontmatter."""
        m = {}

        # 1. Try manifest.json (Primary)
        manifest_path = skill_path / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    m = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # 2. Try Markdown Frontmatter (Fallback & Instructions)
        for fname in ["SKILL.md", "README.md", "readme.md"]:
            fpath = skill_path / fname
            if fpath.exists():
                try:
                    content = fpath.read_text()
                    if content.startswith("---"):
                        import yaml

                        parts = content.split("---")
                        if len(parts) >= 3:
                            front = yaml.safe_load(parts[1])
                            if front:
                                # Merge into m if missing
                                m["name"] = m.get("name") or front.get("name")
                                m["description"] = m.get("description") or front.get("description")
                                # Handle nested metadata object
                                meta = front.get("metadata", {})
                                m["author"] = (
                                    m.get("author") or meta.get("author") or front.get("author")
                                )
                                m["version"] = (
                                    m.get("version") or meta.get("version") or front.get("version")
                                )

                    # Always extract instructions from markdown body if not already in m
                    if not m.get("instructions"):
                        body = content.split("---")[-1].strip()
                        m["instructions"] = body

                    # Use body for description only if still missing
                    if not m.get("description"):
                        m["description"] = "\n".join(m.get("instructions", "").split("\n")[:5])
                    break
                except (Exception, yaml.YAMLError):
                    pass
        return m

    def list_available(self) -> list[dict[str, Any]]:
        """Scan skills directory and return metadata for all installed skills."""
        skills = []
        if not self.SKILLS_DIR.exists():
            return []
        for d in self.SKILLS_DIR.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                m = self._load_metadata(d)

                skills.append(
                    {
                        "id": d.name,
                        "name": m.get("name", d.name),
                        "description": m.get("description", "No description available."),
                        "version": m.get("version", "0.1.0"),
                        "author": m.get("author") or "local",
                        "tools_count": len(m.get("tools", [])),
                        "type": "functional" if m.get("tools") else "instructional",
                        "enabled": True,
                        "source_repo": m.get("repository", ""),
                    }
                )
        return skills

    def get_skill_details(self, name: str) -> dict[str, Any]:
        """Return full manifest and tools for a specific skill, with fallbacks."""
        skill_path = self.SKILLS_DIR / name
        if not skill_path.exists() or not skill_path.is_dir():
            return {}

        m = self._load_metadata(skill_path)
        author = m.get("author", "")
        repo_url = m.get("repository", "")

        # GitHub Author Extraction fallback
        if not author and "github.com" in repo_url:
            import re

            match = re.search(r"github\.com/([^/]+)/", repo_url)
            if match:
                author = match.group(1)

        return {
            "id": name,
            "name": m.get("name", name),
            "description": m.get("description", "No description available."),
            "instructions": m.get("instructions", ""),
            "version": m.get("version", "0.1.0"),
            "author": author or "local",
            "repository": repo_url,
            "tools": m.get("tools", []),
            "type": "functional" if m.get("tools") else "instructional",
            "installed_at": os.path.getctime(skill_path) if os.path.exists(skill_path) else 0,
        }

    def get_enabled_tools(self) -> list[dict[str, Any]]:
        """Scan skills directory and return all tool definitions."""
        all_tools = []
        self._tool_to_skill = {}  # Map tool_name -> skill_name for dispatch

        if not self.SKILLS_DIR.exists():
            return []

        for skill_dir in self.SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                try:
                    skill = SkillSet(skill_dir.name, skill_dir)
                    for tool in skill.tools:
                        tool_name = tool.get("function", {}).get("name")
                        if tool_name:
                            self._tool_to_skill[tool_name] = skill_dir.name
                    all_tools.extend(skill.tools)
                except Exception as e:
                    log.warning("skill.load_failed", name=skill_dir.name, error=str(e))
        return all_tools

    def get_skill_for_tool(self, tool_name: str) -> str | None:
        """Return the skill name that provides the given tool."""
        # Ensure we've scanned
        if not hasattr(self, "_tool_to_skill"):
            self.get_enabled_tools()

        # Hot-rescan if tool is missing (allows immediate use of newly published skills)
        if tool_name not in self._tool_to_skill:
            log.info("skill.hot_rescan", tool=tool_name)
            self.get_enabled_tools()

        return self._tool_to_skill.get(tool_name)

    def fetch_curated_list(self) -> list[dict[str, Any]]:
        """Fetch the curated list from the Neurex Skills Marketplace."""
        # Fallback curated skills (Elite/Official MCP-style servers)
        fallback = [
            {
                "id": "web-search",
                "name": "Web Research",
                "category": "Web",
                "description": "Exploratory search via Google/Brave API. Essential for real-time fact checking.",
                "url": "https://github.com/neurex-swarm/skill-web-search",
                "author": "Neurex Authors",
                "version": "1.0.0",
                "stars": 1240,
                "enabled": True,
            },
            {
                "id": "code-reviewer",
                "name": "Code Reviewer",
                "category": "Code",
                "description": "Expert-level PR analysis and security auditing. Uses best-in-class coding standards.",
                "url": "https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/awesome_agent_skills/self-improving-agent-skills/example_skills/code-reviewer",
                "author": "Shubham Saboo",
                "version": "1.1.0",
                "stars": 850,
                "enabled": True,
            },
            {
                "id": "fs-elite",
                "name": "FS Elite",
                "category": "Core",
                "description": "High-integrity filesystem manipulation with deep file-tree understanding.",
                "url": "https://github.com/neurex-swarm/skill-fs-elite",
                "author": "Neurex Authors",
                "version": "1.2.0",
                "stars": 500,
                "enabled": True,
            },
            {
                "id": "python-exec",
                "name": "Python Sandbox",
                "category": "Code",
                "description": "Secure, isolated Python execution environment for data science and automation.",
                "url": "https://github.com/neurex-swarm/skill-python-exec",
                "author": "Neurex Authors",
                "version": "1.0.5",
                "stars": 2100,
                "enabled": True,
            },
            {
                "id": "sqlite-master",
                "name": "SQLite Master",
                "category": "Data",
                "description": "Direct database interaction and query optimization for local datasets.",
                "url": "https://github.com/neurex-swarm/skill-sqlite-master",
                "author": "Neurex Authors",
                "version": "1.0.0",
                "stars": 320,
                "enabled": True,
            },
            {
                "id": "browser-automation",
                "name": "Playwright Agent",
                "category": "Web",
                "description": "Full browser automation for testing and complex web interaction tasks.",
                "url": "https://github.com/neurex-swarm/skill-playwright",
                "author": "Neurex Authors",
                "version": "0.8.5",
                "stars": 1500,
                "enabled": True,
            },
            {
                "id": "caveman",
                "name": "Caveman Ultra",
                "category": "Core",
                "description": "Ultra-compressed communication mode. Cuts token usage ~75% while keeping full technical accuracy.",
                "url": "https://github.com/JuliusBrussee/caveman",
                "author": "Julius Brussee",
                "version": "1.1.0",
                "stars": 95,
                "enabled": False,
            },
        ]

        import httpx

        try:
            url = "https://skills.mp/api/v1/registry.json"
            resp = httpx.get(url, timeout=5)
            if resp.status_code == 200:
                remote = resp.json().get("skills", [])
                return remote if remote else fallback
        except Exception as e:
            log.warning("skill.fetch_curated_failed", error=str(e))
        return fallback

    def delete_skill(self, name: str) -> bool:
        """Remove a skill from the local store."""
        target_path = self.SKILLS_DIR / name
        if target_path.exists() and target_path.is_dir():
            try:
                log.info("skill.delete_attempt", name=name, path=str(target_path))
                shutil.rmtree(target_path)
                log.info("skill.delete_success", name=name)
                return True
            except Exception as e:
                log.error("skill.delete_error", name=name, error=str(e))
                return False
        log.warning("skill.delete_not_found", name=name, path=str(target_path))
        return False

    async def execute_skill_tool(
        self, skill_name: str, tool_name: str, args: dict[str, Any]
    ) -> str:
        skill_path = self.SKILLS_DIR / skill_name
        handler_path = skill_path / "handler.py"
        if not handler_path.exists():
            return f"Error: Skill '{skill_name}' does not have a handler.py"
        import importlib.util
        import sys

        try:
            module_name = f"neurex_skill_{skill_name}"
            spec = importlib.util.spec_from_file_location(module_name, str(handler_path))
            if not spec or not spec.loader:
                return f"Error: Could not load handler for skill '{skill_name}'"
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            if not hasattr(module, "handle"):
                return f"Error: Skill '{skill_name}' handler has no 'handle' function"
            result = await module.handle(tool_name, args)
            return str(result)
        except Exception as e:
            log.error("skill.execution_failed", skill=skill_name, tool=tool_name, error=str(e))
            return f"Skill execution error: {str(e)}"


skill_manager = SkillManager()
