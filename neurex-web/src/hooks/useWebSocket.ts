// src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from "react";
import { useStore } from "../lib/store";
import type { TaskNode } from "../lib/types";

import { API_BASE, WS_BASE } from "../lib/config";
export function useWebSocket(conversationId: string) {
  const ws = useRef<WebSocket | null>(null);
  const token = useStore(s => s.token);
  const user = useStore(s => s.user);
  const userId = user?.username || "anonymous";
  const refreshTimeout = useRef<any>(null);
  const workspaceFolders = useStore(s => s.workspaceFolders);
  const upsertTask = useStore(s => s.upsertTask);

  const send = useCallback((payload: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      const preferredModel = useStore.getState().preferredModel;
      ws.current.send(JSON.stringify({ ...payload, model: preferredModel }));
    }
  }, []);

  const sendPresence = useCallback((data: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "presence_update", data }));
    }
  }, []);

  useEffect(() => {
    if (!conversationId || conversationId === "undefined") return;
    
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;
    let backoff = 1000;
    const maxBackoff = 30000;

    const connect = () => {
      const state = useStore.getState();
      const rootPath = workspaceFolders && workspaceFolders.length > 0 ? workspaceFolders[0] : "";
      const url = `${WS_BASE}/ws/${conversationId}?token=${token}&user_id=${userId}&workspace_path=${encodeURIComponent(rootPath)}`;
      socket = new WebSocket(url);
      ws.current = socket;
      state.setWsStatus("connecting");
      
      // Wire up the store's send method
      useStore.setState({ send });

      socket.onopen = () => {
        state.setWsStatus("connected");
        backoff = 1000; // Reset backoff on success
        // Sync autonomy level to backend on every connect/reconnect
        const storedAutonomy = useStore.getState().autonomyLevel;
        if (storedAutonomy) {
          socket?.send(JSON.stringify({ type: "set_autonomy", level: storedAutonomy }));
        }
      };

      socket.onclose = (e) => {
        state.setWsStatus("disconnected");
        // Don't reconnect if closed normally (1000), but do reconnect on server restarts (1001)
        if (e.code !== 1000) {
          reconnectTimeout = setTimeout(() => {
            backoff = Math.min(backoff * 1.5, maxBackoff);
            connect();
          }, backoff);
        }
      };

      socket.onerror = () => {
        state.setWsStatus("disconnected");
      };

      // Phase 44.22: Token Buffering (Prevent UI thread saturation)
      let tokenBuffer = "";
      let tokenTimer: any = null;

      const flushTokens = () => {
        if (!tokenBuffer) return;
        useStore.getState().appendToken(tokenBuffer);
        tokenBuffer = "";
        tokenTimer = null;
      };

      socket.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          const { event, data } = msg;
          const s = useStore.getState();

          switch (event) {
            case "chat_reply":
              if (data && typeof data === "object" && typeof data.content === "string") {
                s.addMessage({ role: "assistant", content: data.content, graph_id: data.graph_id });
              } else {
                s.addMessage({ role: "assistant", content: typeof data === "string" ? data : "" });
              }
              break;
            case "planning_token":
              // Intercepted planning tokens: do not render raw planning JSON in main chat
              break;
            case "presence_update":
              s.setPresence(data.filter((p: any) => p.user_id !== userId));
              break;
            case "task_created":
            case "task_updated":
            case "task_status":
              s.upsertTask(data as TaskNode);
              break;
            case "plan_ready":
              s.addNotification("info", "Plan Created", "Multi-agent execution plan is ready for review.");
              (data.tasks as TaskNode[]).forEach(s.upsertTask);
              break;
            case "token":
              // Buffer tokens for O(1) store update overhead
              tokenBuffer += data as string;
              if (!tokenTimer) {
                tokenTimer = setTimeout(flushTokens, 40); // 25fps flush
              }
              break;
            case "replace_tokens":
              flushTokens();
              s.replaceTokens(data as string);
              break;
            case "done":
              flushTokens(); // Ensure buffer is empty
              s.addNotification("success", "Substrate Task Finished", "All planned operations completed cleanly.");
              (data.tasks as TaskNode[]).forEach(s.upsertTask);
              break;
            case "terminal_output":
              window.dispatchEvent(new CustomEvent("terminal_write", { 
                detail: { sessionId: msg.sessionId || conversationId, data } 
              }));
              break;
            case "terminal_command_proposal":
              window.dispatchEvent(new CustomEvent("neurex_command_proposal", {
                detail: { sessionId: msg.sessionId || conversationId, command: data.command, taskId: data.taskId }
              }));
              break;
            case "approval_required":
              s.addNotification("warning", "Governance Check", "Agent is awaiting authorization to execute a tool.");
              window.dispatchEvent(new CustomEvent("neurex_tool_approval_required", {
                detail: data
              }));
              break;
            case "lock_update":
              if (!data.path || data.path === "__proto__" || data.path === "constructor") break;
              s.setLocks({ ...s.locks, [data.path]: data });
              break;
            case "lock_release": {
              if (!data.path || data.path === "__proto__" || data.path === "constructor") break;
              const nextLocks = { ...s.locks };
              Reflect.deleteProperty(nextLocks, data.path);
              s.setLocks(nextLocks);
              break;
            }
            case "diagnostics_updated":
              if (data.path && data.diagnostics) {
                s.updateDiagnostics(data.path, data.diagnostics);
              }
              // Skip refresh if we just saved locally (likely our own change)
              if (Date.now() - s.lastLocalSave < 3000) break;

              if (refreshTimeout.current) clearTimeout(refreshTimeout.current);
              refreshTimeout.current = setTimeout(() => {
                s.refreshFileTree();
              }, 1500);
              break;
            case "file_system_changed":
              s.addNotification("success", "File System Synced", "Workspace filesystem state updated.");
              // Skip refresh if we just saved locally (likely our own change)
              if (Date.now() - s.lastLocalSave < 3000) break;

              if (refreshTimeout.current) clearTimeout(refreshTimeout.current);
              refreshTimeout.current = setTimeout(() => {
                s.refreshFileTree();
              }, 1500);
              break;
            case "inline_edit_diff":
              if (data.path && data.original !== undefined && data.modified !== undefined) {
                s.setDiff(data.path, data.original, data.modified);
              }
              break;
            case "swarm_diff":
              s.addNotification("info", "Swarm Code Proposal", "Multi-agent swarm has generated a code diff proposal.");
              if (data && Array.isArray(data.changes)) {
                 
                const diffsObj: Record<string, any> = Object.create(null);
                 
                data.changes.forEach((c: any) => {
                  if (!c.path || c.path === "__proto__" || c.path === "constructor") return;
                  Reflect.set(diffsObj, c.path, {
                    path: c.path,
                    original: c.original,
                    modified: c.modified,
                    status: "pending"
                  });
                });
                s.setSwarmDiffs(diffsObj);
                s.setSidebarTab("swarm");
              }
              break;
            case "debate_message":
              if (data) {
                s.addDebateMessage({
                  id: data.id || Math.random().toString(36).substring(7),
                  agent: data.agent,
                  role: data.role,
                  content: data.content,
                  timestamp: data.timestamp || new Date().toLocaleTimeString()
                });
                s.setSidebarTab("debate");
              }
              break;
            case "error": {
              const errorMsg = typeof data === "object" ? JSON.stringify(data) : data;
              s.addNotification("error", "Substrate Error", errorMsg);
              useStore.getState().addMessage({ role: "assistant", content: `❌ Error: ${errorMsg}` });
              break;
            }
          }
        } catch { /* intentional */ }
      };
    };

    connect();

    const heartbeat = setInterval(() => {
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "ping" }));
      }
    }, 15000);

    return () => {
      clearInterval(heartbeat);
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (socket) {
        socket.onclose = null; // Prevent reconnect on cleanup
        socket.close();
      }
      useStore.getState().clearTasks();
    };
  }, [conversationId, send, sendPresence, token, userId, workspaceFolders]);

  // Listen for frontend Monaco inline edits to forward to socket
  useEffect(() => {
    const handleInlineEdit = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { path, prompt, selection, range, taskId } = customEvent.detail;
      send({
        type: "inline_edit",
        path,
        prompt,
        selection,
        range,
        taskId
      });
    };
    window.addEventListener("neurex_inline_edit", handleInlineEdit);
    return () => window.removeEventListener("neurex_inline_edit", handleInlineEdit);
  }, [send]);

  // Load history on mount or switch
  useEffect(() => {
    if (!conversationId) return;
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    
    fetch(`${API_BASE}/api/chat/${conversationId}`, {
      headers
    })
      .then((r) => r.json())
      .then((data) => useStore.getState().setMessages(data))
      .catch(() => {});
  }, [conversationId, token]);

  // Load tasks on mount or switch
  useEffect(() => {
    if (!conversationId) return;
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    
    fetch(`${API_BASE}/api/tasks/?graph_id=${conversationId}`, {
      headers
    })
      .then((r) => r.json())
      .then((data: TaskNode[]) => {
        data.forEach(upsertTask);
      })
      .catch(() => {});
  }, [conversationId, upsertTask, token]);

  return { send, sendPresence };
}
