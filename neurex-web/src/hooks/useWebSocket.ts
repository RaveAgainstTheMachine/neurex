// src/hooks/useWebSocket.ts
"use client";
import { useEffect, useRef, useCallback } from "react";
import { useStore } from "@/lib/store";
import type { WsEvent, TaskNode } from "@/lib/types";

const WS_URL   = process.env.NEXT_PUBLIC_WS_URL   ?? "ws://localhost:8000";
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN ?? "neurex-dev-token";
const RECONNECT_DELAY = 2000;

export function useWebSocket(conversationId: string) {
  const ws       = useRef<WebSocket | null>(null);
  const reconnect = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { appendToken, upsertTask, setWsStatus } = useStore();

  const handleEvent = useCallback((event: WsEvent) => {
    switch (event.event) {
      case "token":
        appendToken(event.data as string);
        break;

      case "task_created":
      case "task_updated":
        upsertTask(event.data as TaskNode);
        break;

      case "done":
        // graph complete — nothing extra needed, state already updated
        break;

      case "error":
        console.error("[neurex ws]", event.data);
        break;
    }
  }, [appendToken, upsertTask]);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const url = `${WS_URL}/ws/${conversationId}?token=${API_TOKEN}`;
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => {
      setWsStatus("connected");
    };

    socket.onmessage = (e) => {
      try {
        const event: WsEvent = JSON.parse(e.data);
        handleEvent(event);
      } catch {
        console.warn("[neurex ws] unparseable message", e.data);
      }
    };

    socket.onclose = () => {
      setWsStatus("disconnected");
      reconnect.current = setTimeout(connect, RECONNECT_DELAY);
    };

    socket.onerror = () => {
      socket.close();
    };

    setWsStatus("connecting");
  }, [conversationId, handleEvent, setWsStatus]);

  useEffect(() => {
    connect();
    return () => {
      reconnect.current && clearTimeout(reconnect.current);
      ws.current?.close();
    };
  }, [connect]);

  const send = useCallback((payload: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(payload));
    }
  }, []);

  return { send };
}
