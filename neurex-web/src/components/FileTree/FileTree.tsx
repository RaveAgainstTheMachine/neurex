"use client";
// src/components/FileTree/FileTree.tsx
import { useEffect, useState, useCallback } from "react";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from "lucide-react";
import { useStore } from "@/lib/store";
import type { FileNode } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function FileTree() {
  const [tree, setTree]       = useState<FileNode | null>(null);
  const [error, setError]     = useState<string | null>(null);
  const setOpenFile           = useStore((s) => s.setOpenFile);
  const setFileContent        = useStore((s) => s.setFileContent);
  const openFile              = useStore((s) => s.openFile);

  const fetchTree = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/files/tree`);
      if (!r.ok) throw new Error(await r.text());
      setTree(await r.json());
      setError(null);
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    fetchTree();
    const interval = setInterval(fetchTree, 5000); // poll until WS push
    return () => clearInterval(interval);
  }, [fetchTree]);

  const openFileFn = async (path: string) => {
    setOpenFile(path);
    try {
      const r = await fetch(`${API}/api/files/read?path=${encodeURIComponent(path)}`);
      const data = await r.json();
      setFileContent(path, data.content);
    } catch {}
  };

  return (
    <div style={{ overflow: "auto", flex: 1 }}>
      <div style={{
        padding: "8px 12px",
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.08em",
        color: "var(--text-muted)",
        textTransform: "uppercase",
        borderBottom: "1px solid var(--border)",
      }}>
        Explorer
      </div>
      {error && <div style={{ color: "var(--accent-red)", padding: 8, fontSize: 11 }}>{error}</div>}
      {tree && <TreeNode node={tree} depth={0} onOpen={openFileFn} activeFile={openFile} />}
    </div>
  );
}

function TreeNode({
  node, depth, onOpen, activeFile
}: {
  node: FileNode;
  depth: number;
  onOpen: (path: string) => void;
  activeFile: string | null;
}) {
  const [expanded, setExpanded] = useState(depth === 0);
  const isDir   = node.type === "dir";
  const isActive = node.path === activeFile;

  if (isDir) {
    return (
      <div>
        <div
          onClick={() => setExpanded((v) => !v)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            padding: `3px 12px 3px ${12 + depth * 12}px`,
            cursor: "pointer",
            color: "var(--text-secondary)",
            userSelect: "none",
          }}
          onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-hover)")}
          onMouseLeave={e => (e.currentTarget.style.background = "")}
        >
          {expanded
            ? <ChevronDown size={12} />
            : <ChevronRight size={12} />
          }
          {expanded
            ? <FolderOpen size={13} color="var(--accent-amber)" />
            : <Folder size={13} color="var(--accent-amber)" />
          }
          <span style={{ fontSize: 12 }}>{node.name}</span>
        </div>
        {expanded && node.children?.map((child) => (
          <TreeNode
            key={child.name}
            node={child}
            depth={depth + 1}
            onOpen={onOpen}
            activeFile={activeFile}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      onClick={() => node.path && onOpen(node.path)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        padding: `3px 12px 3px ${24 + depth * 12}px`,
        cursor: "pointer",
        background: isActive ? "var(--bg-elevated)" : "",
        borderLeft: isActive ? "2px solid var(--accent-blue)" : "2px solid transparent",
        color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
        fontSize: 12,
      }}
      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = "var(--bg-hover)"; }}
      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = ""; }}
    >
      <File size={12} />
      {node.name}
    </div>
  );
}
