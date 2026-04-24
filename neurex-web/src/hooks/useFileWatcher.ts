"use client";
// src/hooks/useFileWatcher.ts
// Listens for file-change events from the WS and refreshes the editor
// and file tree automatically when an agent writes a file.

import { useEffect, useCallback } from "react";
import { useStore } from "@/lib/store";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Call this once at the app root (page.tsx).
 * It watches the Zustand task store for DONE coder tasks, then
 * re-fetches the open file content so the editor stays in sync
 * with what the agent wrote — without losing cursor position unless
 * the file was overwritten.
 */
export function useFileWatcher() {
  const tasks          = useStore((s) => s.tasks);
  const openFile       = useStore((s) => s.openFile);
  const setFileContent = useStore((s) => s.setFileContent);

  const refreshOpenFile = useCallback(async () => {
    if (!openFile) return;
    try {
      const r = await fetch(
        `${API}/api/files/read?path=${encodeURIComponent(openFile)}`
      );
      if (!r.ok) return;
      const data = await r.json();
      setFileContent(openFile, data.content);
    } catch {
      // Network errors during agent operation are normal — ignore silently
    }
  }, [openFile, setFileContent]);

  useEffect(() => {
    const doneCoder = Object.values(tasks).find(
      (t) => t.agent_type === "coder" && t.status === "done"
    );
    if (doneCoder) {
      // Small delay so the file is fully flushed to disk before we fetch
      const timer = setTimeout(refreshOpenFile, 300);
      return () => clearTimeout(timer);
    }
  }, [tasks, refreshOpenFile]);
}
