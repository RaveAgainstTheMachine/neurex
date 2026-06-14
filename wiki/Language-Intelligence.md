# Language Intelligence Hub

The **Language Intelligence Hub** is the core subsystem responsible for providing IDE-grade code intelligence (completions, diagnostics, navigation) natively within Neurex, without the need for external VS Code plugins.

## 1. Universal LSP Architecture
Neurex implements a native, high-performance bridge to the **Language Server Protocol (LSP)**.

### Mega-Registry Expansion
The system includes a pre-configured registry for the **Top 100+** most popular languages, including:
- **Core**: Python, TypeScript/JS, Rust, Go, C++, C#, Java.
- **Web**: Svelte, Vue, Astro, HTML/CSS, GraphQL, TailwindCSS.
- **Systems**: Zig, Nim, Fortran, Cobol, Pascal.
- **Functional**: Elixir, Haskell, Clojure, Scala.

### Dynamic Fallback Engine
If a language is not in the hardcoded registry, Neurex employs a heuristic discovery engine. It interrogates the host system for standard LSP naming patterns (e.g., `lang-lsp`, `lang-language-server`) to provide zero-config support for niche languages.

### Workspace Customization (`lsp.json`)
For proprietary or highly specialized environments, you can define custom LSP commands in your workspace root at `.neurex/lsp.json`.
```json
{
  "custom-lang": ["/path/to/lsp", "--stdio"]
}
```

## 2. LSP Autopilot (Self-Healing)
Neurex can autonomously provision its own intelligence tools using **Autopilot**.
- **Localized Installation**: Missing LSPs are installed into the workspace-private directory `.neurex/bin/lsp/` to avoid polluting the host system.
- **One-Click Provisioning**: The IDE detects missing support and offers an "ENABLE AUTOPILOT" action directly in the editor.

## 3. Neural Lens Suite
The visual layer atop the LSP data, designed for high situational awareness.

### Neural Error Lens
- **Inline Diagnostics**: Groups multiple errors/warnings and renders them as ghost-text directly following the affected line.
- **Neon Theming**: Uses high-contrast, glowing accents to ensure critical issues are visually prominent in the dark workspace.

### Neural GitLens
- **Ghost-Text Blame**: Renders commit authorship metadata (author, date, summary) for the active line.
- **File Timeline**: A dedicated sidebar view providing a visual, glassmorphic audit trail of the file's history.

## 4. Intelligent Automation
- **Format on Save**: Automatically triggers the LSP's formatting engine (e.g., Black, Prettier, Gofmt) on every save.
- **Telemetry-Aware**: LSP traffic is multiplexed via dedicated WebSockets to ensure zero-latency intelligence even during heavy agentic execution.
