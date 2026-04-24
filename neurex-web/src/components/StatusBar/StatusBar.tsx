"use client";
// src/components/StatusBar/StatusBar.tsx
// Thin bottom bar showing WS connection, active model, and task progress.
import { useStore } from "@/lib/store";

export function StatusBar() {
  const wsStatus = useStore((s) => s.wsStatus);
  const tasks    = useStore((s) => s.tasks);

  const nodes     = Object.values(tasks);
  const active    = nodes.filter((t) => ["thinking", "writing", "testing"].includes(t.status));
  const done      = nodes.filter((t) => t.status === "done").length;
  const failed    = nodes.filter((t) => t.status === "failed").length;

  const wsColor =
    wsStatus === "connected"    ? "var(--accent-green)"  :
    wsStatus === "connecting"   ? "var(--accent-amber)"  :
                                  "var(--accent-red)";

  return (
    <div style={{
      gridArea: "statusbar",
      height: 22,
      display: "flex",
      alignItems: "center",
      padding: "0 12px",
      gap: 16,
      background: "var(--bg-surface)",
      borderTop: "1px solid var(--border)",
      fontSize: 11,
      color: "var(--text-muted)",
      userSelect: "none",
    }}>
      {/* WS status */}
      <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: wsColor }} />
        {wsStatus}
      </span>

      {/* Active agent */}
      {active.length > 0 && (
        <span style={{ color: "var(--accent-blue)" }}>
          ⚡ {active.map((t) => t.title).join(", ")}
        </span>
      )}

      {/* Task counts */}
      {nodes.length > 0 && (
        <span style={{ marginLeft: "auto" }}>
          {done}/{nodes.length} tasks
          {failed > 0 && (
            <span style={{ color: "var(--accent-red)", marginLeft: 8 }}>
              {failed} failed
            </span>
          )}
        </span>
      )}
    </div>
  );
}
