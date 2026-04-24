"use client";
import { useState } from "react";

const SKILLS = [
  { id: "filesystem", name: "Filesystem", icon: "📁", description: "Read/Write workspace files" },
  { id: "terminal",   name: "Terminal",   icon: "💻", description: "Execute allowed commands" },
  { id: "researcher", name: "Researcher", icon: "🔍", description: "Web search & documentation" },
  { id: "memory",     name: "Memory",     icon: "🧠", description: "RAG & long-term codebase indexing" },
];

export function SkillManager() {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100%",
    }}>
      <div style={{
        padding: "8px 12px",
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.08em",
        color: "var(--text-muted)",
        textTransform: "uppercase",
        borderBottom: "1px solid var(--border)",
      }}>
        Agent Skills (MCP)
      </div>
      
      <div style={{ padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
        {SKILLS.map((skill) => (
          <div key={skill.id} style={{
            padding: 8,
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            display: "flex",
            alignItems: "center",
            gap: 10,
            cursor: "default",
          }}>
            <div style={{ fontSize: 16 }}>{skill.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: "var(--text-primary)" }}>
                {skill.name}
              </div>
              <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
                {skill.description}
              </div>
            </div>
            <div style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "var(--accent-green)",
              boxShadow: "0 0 8px var(--accent-green)",
            }} />
          </div>
        ))}
      </div>
      
      <div style={{ 
        marginTop: "auto", 
        padding: 12, 
        borderTop: "1px solid var(--border)",
        fontSize: 10,
        color: "var(--text-muted)",
        textAlign: "center"
      }}>
        All local tools are active
      </div>
    </div>
  );
}
