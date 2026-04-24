"use client";
// src/app/page.tsx — Root IDE workspace layout
import { useEffect, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useFileWatcher } from "@/hooks/useFileWatcher";
import { FileTree } from "@/components/FileTree/FileTree";
import { CodeEditor } from "@/components/Editor/CodeEditor";
import { AgentTerminal } from "@/components/AgentTerminal/AgentTerminal";
import { AgentDashboard } from "@/components/AgentDashboard/AgentDashboard";
import { SkillManager } from "@/components/SkillManager/SkillManager";
import { Scratchpad } from "@/components/Scratchpad/Scratchpad";

import { StatusBar } from "@/components/StatusBar/StatusBar";
import { useStore } from "@/lib/store";

const CONVERSATION_ID = "default"; // TODO: multi-conversation support

export default function Home() {
  const { send }    = useWebSocket(CONVERSATION_ID);
  const wsStatus    = useStore((s) => s.wsStatus);
  const [showScratch, setShowScratch] = useState(true);

  useFileWatcher();

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "220px 1fr 360px",
      gridTemplateRows: "36px 1fr 280px 22px",
      gridTemplateAreas: `
        "header    header     header"
        "sidebar   editor     panel"
        "sidebar   terminal   panel"
        "statusbar statusbar  statusbar"
      `,
      height: "100vh",
      width: "100vw",
      background: "var(--bg-base)",
      overflow: "hidden",
    }}>
      {/* ── Header ────────────────────────────────────────────────── */}
      <header style={{
        gridArea: "header",
        display: "flex",
        alignItems: "center",
        padding: "0 16px",
        gap: 12,
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
      }}>
        <span style={{
          fontFamily: "JetBrains Mono, monospace",
          fontWeight: 700,
          fontSize: 14,
          letterSpacing: "0.05em",
          color: "var(--accent-blue)",
        }}>NEUREX</span>

        <span style={{
          marginLeft: "auto",
          display: "flex",
          alignItems: "center",
          gap: 6,
          color: "var(--text-secondary)",
          fontSize: 11,
        }}>
          <span style={{
            width: 7, height: 7, borderRadius: "50%",
            background: wsStatus === "connected"
              ? "var(--accent-green)"
              : wsStatus === "connecting"
              ? "var(--accent-amber)"
              : "var(--accent-red)",
          }} />
          {wsStatus}
        </span>

        <button
          onClick={() => setShowScratch((v) => !v)}
          style={{
            marginLeft: 8,
            padding: "2px 10px",
            background: showScratch ? "var(--bg-elevated)" : "transparent",
            border: "1px solid var(--border)",
            borderRadius: 4,
            color: "var(--text-secondary)",
            cursor: "pointer",
            fontSize: 11,
          }}>
          Scratchpad
        </button>
      </header>

      {/* ── File Sidebar ──────────────────────────────────────────── */}
      <aside style={{
        gridArea: "sidebar",
        background: "var(--bg-surface)",
        borderRight: "1px solid var(--border)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}>
        <div style={{ flex: 1, overflow: "auto" }}>
          <FileTree />
        </div>
        <div style={{ borderTop: "1px solid var(--border)", height: 280 }}>
          <SkillManager />
        </div>
      </aside>


      {/* ── Code Editor ───────────────────────────────────────────── */}
      <main style={{ gridArea: "editor", overflow: "hidden", position: "relative" }}>
        <CodeEditor />
      </main>

      {/* ── Agent Terminal / Chat ─────────────────────────────────── */}
      <section style={{
        gridArea: "terminal",
        borderTop: "1px solid var(--border)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}>
        <AgentTerminal send={send} conversationId={CONVERSATION_ID} />
      </section>

      {/* ── Right Panel: Dashboard + Scratchpad ───────────────────── */}
      <aside style={{
        gridArea: "panel",
        borderLeft: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        background: "var(--bg-surface)",
      }}>
        <AgentDashboard />
        {showScratch && (
          <div style={{ borderTop: "1px solid var(--border)", flex: "0 0 220px" }}>
            <Scratchpad />
          </div>
        )}
      </aside>

      {/* ── Status Bar ────────────────────────────────────────────── */}
      <StatusBar />
    </div>
  );
}
