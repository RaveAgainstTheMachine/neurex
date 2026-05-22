import React, { useRef, useEffect, useState } from "react";
import { useStore } from "../../lib/store";
import { Globe, Send, Gavel, Shield, Bot, AlertTriangle, Eye } from "lucide-react";
import toast from "react-hot-toast";
import "./DebateArena.css";

export function DebateArena() {
  const debateMessages = useStore((s) => s.debateMessages);
  const wsStatus = useStore((s) => s.wsStatus);
  const send = useStore((s) => s.send);
  const clearDebateMessages = useStore((s) => s.clearDebateMessages);
  
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [debateMessages]);

  const handleSend = () => {
    const content = input.trim();
    if (!content || wsStatus !== "connected") return;
    
    // Optimistically inject Judge's verdict
    const judgeMsg = {
      id: Math.random().toString(36).substring(7),
      agent: "Architect Judge",
      role: "judge" as const,
      content,
      timestamp: new Date().toLocaleTimeString()
    };
    useStore.getState().addDebateMessage(judgeMsg);

    // Send steer command via WebSocket
    send({
      type: "debate_steer",
      verdict: content
    });

    setInput("");
    toast.success("Architect verdict dispatched to swarm!");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getAgentRoleBadge = (role: string) => {
    switch (role) {
      case "planner":
        return { label: "PLANNER", bg: "rgba(33,150,243,0.15)", color: "#2196f3", icon: Shield };
      case "coder":
        return { label: "CODER", bg: "rgba(0,230,118,0.15)", color: "#00e676", icon: Bot };
      case "reviewer":
        return { label: "REVIEWER", bg: "rgba(255,109,0,0.15)", color: "#ff6d00", icon: Eye };
      case "judge":
        return { label: "ARCHITECT JUDGE", bg: "rgba(0,184,212,0.25)", color: "#00b8d4", icon: Gavel };
      default:
        return { label: "AGENT", bg: "rgba(255,255,255,0.08)", color: "#aaa", icon: Bot };
    }
  };

  return (
    <div className="debate-arena">
      <div className="debate-arena__header">
        <div className="title-wrapper">
          <Globe size={16} className="text-cyan animate-spin-slow" />
          <span>Swarm Debate Arena</span>
        </div>
        <Gavel size={16} className="courtroom-gavel-icon" />
      </div>

      <div className="debate-arena__instructions">
        <AlertTriangle size={14} className="text-orange" />
        <span>Specialized agents are debating technical tradeoffs. You have supreme veto power as the Architect Judge.</span>
      </div>

      <div className="debate-arena__chat" ref={scrollRef}>
        {debateMessages.length > 0 ? (
          debateMessages.map((msg) => {
            const badge = getAgentRoleBadge(msg.role);
            const Icon = badge.icon;
            return (
              <div key={msg.id} className={`debate-bubble-wrapper ${msg.role}`}>
                <div className="debate-bubble-header">
                  <div className="agent-identity">
                    <span className="agent-badge" style={{ backgroundColor: badge.bg, color: badge.color }}>
                      <Icon size={10} style={{ marginRight: "4px" }} />
                      {badge.label}
                    </span>
                    <span className="agent-name">{msg.agent}</span>
                  </div>
                  <span className="debate-timestamp">{msg.timestamp}</span>
                </div>
                <div className="debate-bubble-content">
                  <p>{msg.content}</p>
                </div>
              </div>
            );
          })
        ) : (
          <div className="debate-arena__empty">
            <Gavel size={32} className="text-muted text-gavel-empty" />
            <p>Courtroom is quiet.</p>
            <span>Multi-agent debates will stream here automatically when agents evaluate architectural design paths.</span>
          </div>
        )}
      </div>

      <div className="debate-arena__input-area">
        <textarea
          ref={null}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Type steering feedback to guide the swarm..."
          rows={2}
          disabled={wsStatus !== "connected"}
        />
        <button 
          className="debate-send-btn" 
          onClick={handleSend}
          disabled={!input.trim() || wsStatus !== "connected"}
          title="Send steering command"
        >
          <Send size={14} />
        </button>
      </div>

      {debateMessages.length > 0 && (
        <div className="debate-arena__footer">
          <button className="clear-debate-btn" onClick={clearDebateMessages}>
            Reset Court logs
          </button>
        </div>
      )}
    </div>
  );
}
