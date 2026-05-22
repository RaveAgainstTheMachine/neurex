import React, { useRef, useEffect, useState } from "react";
import { useStore } from "../../lib/store";
import { Globe, Send, Gavel, Shield, Bot, AlertTriangle, Eye, Sparkles, Loader2, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../../lib/api";
import type { DebateMessage } from "../../lib/types";
import "./DebateArena.css";

export function DebateArena() {
  const debateMessages = useStore((s) => s.debateMessages);
  const wsStatus = useStore((s) => s.wsStatus);
  const send = useStore((s) => s.send);
  const clearDebateMessages = useStore((s) => s.clearDebateMessages);
  const activeConversationId = useStore((s) => s.activeConversationId);
  
  const [input, setInput] = useState("");
  const [proposalQuery, setProposalQuery] = useState("");
  const [initiating, setInitiating] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [debateMessages]);

  useEffect(() => {
    let active = true;
    const fetchHistory = async () => {
      if (!activeConversationId) return;
      setLoadingHistory(true);
      try {
        const data = await api.get<DebateMessage[]>(`/api/debate/status?conversation_id=${activeConversationId}`);
        if (active) {
          clearDebateMessages();
          data.forEach((msg) => {
            useStore.getState().addDebateMessage(msg);
          });
        }
      } catch (err) {
        console.error("Failed to load debate history:", err);
      } finally {
        if (active) setLoadingHistory(false);
      }
    };
    fetchHistory();
    return () => {
      active = false;
    };
  }, [activeConversationId, clearDebateMessages]);

  const handleSend = () => {
    const content = input.trim();
    if (!content || wsStatus !== "connected") return;
    
    // Optimistically inject Judge's verdict
    const judgeMsg: DebateMessage = {
      id: Math.random().toString(36).substring(7),
      agent: "Architect Judge",
      role: "judge",
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

  const handleInitiateDebate = async () => {
    const query = proposalQuery.trim();
    if (!query) {
      toast.error("Please enter a technical proposal query first.");
      return;
    }
    setInitiating(true);
    try {
      await api.post("/api/debate/start", {
        conversation_id: activeConversationId,
        query
      });
      clearDebateMessages();
      toast.success("Swarm technical debate session initiated!");
      setProposalQuery("");
    } catch (err) {
      toast.error("Failed to initiate debate session");
      console.error(err);
    } finally {
      setInitiating(false);
    }
  };

  const handleReachVerdict = () => {
    if (!input.trim()) {
      setInput("Architect Verdict: Proceed with the proposed technical plan. Tradeoffs have been evaluated and the risks are acceptable.");
      toast("Drafted a default verdict. Click again to dispatch!", { icon: "📝" });
      return;
    }
    handleSend();
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

  const templates = [
    {
      label: "SQL Engine Migration",
      text: "Should we migrate the high-throughput task queues from SQLite to a dedicated PostgreSQL instance?"
    },
    {
      label: "Parallel Orchestrator",
      text: "Should we refactor the orchestrator to process independent task nodes in parallel or enforce strict sequential chains?"
    },
    {
      label: "Zero-Trust MCP Sandbox",
      text: "Should we enforce local sandbox restriction on third-party MCP tool permissions or trust standard shell defaults?"
    }
  ];

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
        {loadingHistory ? (
          <div className="debate-arena__loading">
            <RefreshCw size={24} className="animate-spin text-cyan" />
            <span>Reading technical courtroom archives...</span>
          </div>
        ) : debateMessages.length > 0 ? (
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
            <div className="empty-title-section">
              <Gavel size={40} className="text-muted text-gavel-empty animate-pulse" />
              <h3>Assemble the Consensus Swarm</h3>
              <p>Propose an architectural dilemma or code-level decision to the multi-agent consensus swarm. The Planner, Coder, and Reviewer will debate tradeoffs, while you exercise supreme veto authority as the Architect Judge.</p>
            </div>

            <div className="courtroom-proposal-card">
              <div className="card-header">
                <Sparkles size={14} className="text-cyan text-sparkles" />
                <span>Consensus Proposal Engine</span>
              </div>

              <textarea
                className="proposal-textarea"
                value={proposalQuery}
                onChange={(e) => setProposalQuery(e.target.value)}
                placeholder="Type or click a template below to describe your architectural dilemma..."
                rows={4}
              />

              <div className="template-chips">
                {templates.map((tpl, i) => (
                  <button
                    key={i}
                    className="template-chip"
                    onClick={() => setProposalQuery(tpl.text)}
                  >
                    {tpl.label}
                  </button>
                ))}
              </div>

              <button
                className="initiate-debate-btn"
                onClick={handleInitiateDebate}
                disabled={initiating || !proposalQuery.trim() || wsStatus !== "connected"}
              >
                {initiating ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Assembling Swarm...</span>
                  </>
                ) : (
                  <>
                    <Gavel size={16} />
                    <span>Initiate Technical Debate</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="debate-arena__input-area">
        <textarea
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
          <button 
            className="reach-verdict-btn" 
            onClick={handleReachVerdict}
            disabled={wsStatus !== "connected"}
          >
            Reach Verdict
          </button>
          <button className="clear-debate-btn" onClick={clearDebateMessages}>
            Reset Court logs
          </button>
        </div>
      )}
    </div>
  );
}
