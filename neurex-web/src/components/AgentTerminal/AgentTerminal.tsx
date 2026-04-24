"use client";
// src/components/AgentTerminal/AgentTerminal.tsx
import { useEffect, useRef, useState } from "react";
import { Send, Loader2 } from "lucide-react";
import { useStore } from "@/lib/store";
import type { ChatMessage } from "@/lib/types";

interface Props {
  send: (payload: object) => void;
  conversationId: string;
}

export function AgentTerminal({ send, conversationId }: Props) {
  const { messages, addMessage, setMessages, wsStatus, tasks } = useStore();

  useEffect(() => {
    fetch(`http://localhost:8000/api/chat/${conversationId}`)
      .then(r => r.json())
      .then(data => {
        setMessages(data);
      })
      .catch(console.error);
  }, [conversationId, setMessages]);


  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLTextAreaElement>(null);

  const isWorking = Object.values(tasks).some(
    (t) => ["thinking", "writing", "testing"].includes(t.status)
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const handleSend = () => {
    const content = input.trim();
    if (!content || wsStatus !== "connected" || isWorking) return;

    addMessage({ role: "user", content });
    send({ type: "message", content });
    setInput("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100%",
      background: "var(--bg-base)",
    }}>
      {/* Panel header */}
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
        gap: 8,
      }}>
        <span>Agent Chat</span>
        {isWorking && (
          <Loader2 size={10} style={{ animation: "spin 1s linear infinite", color: "var(--accent-blue)" }} />
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{
        flex: 1,
        overflow: "auto",
        padding: "12px 0",
      }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>

      {/* Input */}
      <div style={{
        borderTop: "1px solid var(--border)",
        padding: "8px 12px",
        display: "flex",
        gap: 8,
        alignItems: "flex-end",
      }}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            wsStatus !== "connected"
              ? "Connecting…"
              : isWorking
              ? "Agent is working…"
              : "Ask the agent team anything…"
          }
          disabled={wsStatus !== "connected" || isWorking}
          rows={1}
          style={{
            flex: 1,
            background: "var(--bg-elevated)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            color: "var(--text-primary)",
            fontFamily: "Inter, sans-serif",
            fontSize: 13,
            padding: "8px 12px",
            resize: "none",
            outline: "none",
            maxHeight: 80,
            lineHeight: 1.5,
            transition: "border-color 0.15s",
          }}
          onFocus={e => (e.target.style.borderColor = "var(--accent-blue)")}
          onBlur={e  => (e.target.style.borderColor = "var(--border)")}
        />
        <button
          onClick={handleSend}
          disabled={wsStatus !== "connected" || isWorking || !input.trim()}
          style={{
            padding: "8px 12px",
            background: "var(--accent-blue)",
            border: "none",
            borderRadius: 6,
            color: "#fff",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: 4,
            fontSize: 12,
            opacity: (wsStatus !== "connected" || isWorking || !input.trim()) ? 0.5 : 1,
            transition: "opacity 0.15s",
          }}
        >
          <Send size={13} />
        </button>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div style={{
      padding: "6px 16px",
      display: "flex",
      flexDirection: "column",
      gap: 2,
      animation: "slide-in-right 0.15s ease",
    }}>
      <span style={{
        fontSize: 10,
        fontWeight: 600,
        color: isUser ? "var(--accent-blue)" : "var(--accent-purple)",
        textTransform: "uppercase",
        letterSpacing: "0.06em",
      }}>
        {isUser ? "You" : "Neurex"}
      </span>
      <div style={{
        fontSize: 13,
        color: "var(--text-primary)",
        lineHeight: 1.6,
        whiteSpace: "pre-wrap",
        fontFamily: message.content.includes("```")
          ? "JetBrains Mono, monospace"
          : "inherit",
      }}>
        {message.content}
      </div>
    </div>
  );
}
