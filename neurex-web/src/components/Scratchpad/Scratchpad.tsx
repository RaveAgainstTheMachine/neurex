"use client";
// src/components/Scratchpad/Scratchpad.tsx
import { useStore } from "@/lib/store";
import { useEffect, useRef } from "react";

export function Scratchpad() {
  const { scratchpad, setScratchpad, tasks } = useStore();
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-populate scratchpad with current plan when tasks arrive
  useEffect(() => {
    const nodes = Object.values(tasks);
    if (nodes.length === 0) return;

    const lines = nodes.map((t) => {
      const check = t.status === "done" ? "✅" : t.status === "failed" ? "❌" : "○";
      return `${check} [${t.agent_type}] ${t.title}`;
    });

    setScratchpad(lines.join("\n"));
  }, [tasks, setScratchpad]);

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100%",
      background: "var(--bg-surface)",
    }}>
      <div style={{
        padding: "6px 12px",
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.08em",
        color: "var(--text-muted)",
        textTransform: "uppercase",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <span>Scratchpad</span>
        <button
          onClick={() => setScratchpad("")}
          style={{
            background: "none",
            border: "none",
            color: "var(--text-muted)",
            cursor: "pointer",
            fontSize: 10,
          }}
        >
          Clear
        </button>
      </div>

      <textarea
        ref={ref}
        value={scratchpad}
        onChange={(e) => setScratchpad(e.target.value)}
        placeholder={"Agent plan and notes appear here…\nYou can also edit freely."}
        style={{
          flex: 1,
          background: "transparent",
          border: "none",
          resize: "none",
          color: "var(--text-secondary)",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: 11,
          lineHeight: 1.7,
          padding: "10px 12px",
          outline: "none",
        }}
      />
    </div>
  );
}
