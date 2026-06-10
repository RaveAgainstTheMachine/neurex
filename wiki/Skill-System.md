# Skill System

Neurex utilizes a modular **MCP (Model Context Protocol)** compatible skill architecture. Skills extend the base capabilities of agents with specialized tools.

## 1. Skill Discovery
Skills can be discovered via the **SkillsMP Marketplace** integrated directly into the `SkillsPanel`.
- **Curated List**: A set of verified, high-performance skills (Web Search, Git Manager, Terminal).
- **Marketplace**: Third-party skills shared via GitHub repositories.

## 2. Unified Search & Discovery
The `SkillsPanel` features a global, real-time search substrate:
- **Global Filter**: Simultaneously searches both the local **Installed** registry and the remote **Marketplace**.
- **Proactive Empty States**: If no local skills are detected, the system provides a contextual call-to-action (CTA) directing the user to the discovery marketplace.
- **Nomenclature**: Unified as "Skills & Extensions" to align with industry-standard extensibility models.

## 2. Installation (Git-Based)
Skills are installed by cloning a Git repository into the `neurex-api/skills/` directory.
- **Support for Subdirectories**: Neurex can extract specific sub-paths from a repository (e.g., `git+https://github.com/user/repo.git#path/to/skill`).
- **Security**: Sub-paths are normalized and sanitized to prevent system-level file access.

## 3. Skill Manifest
Every skill must include a `manifest.json`:
```json
{
  "name": "My Skill",
  "version": "1.0.0",
  "tools": ["tool_a", "tool_b"],
  "entrypoint": "main.py"
}
```

## 4. Dynamic Loading
Neurex dynamically hot-reloads the agent registry when a new skill is installed, making new tools immediately available to the Orchestrator without a service restart.
