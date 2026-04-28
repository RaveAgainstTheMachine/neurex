// neurex-web/src/components/FlightRecorder/FlightRecorder.tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Brain, ChevronRight, Activity, Terminal, FileText, 
  Search, Shield, Cpu, Clock, Zap, AlertCircle
} from "lucide-react";
import "./FlightRecorder.css";

import { API_BASE } from "../../lib/config";

interface TraceEntry {
  id: string;
  agent_type: string;
  action: string;
  detail: string;
  status: "success" | "running" | "failed";
  tool_used?: string;
  timestamp: string;
}

export function FlightRecorder({ conversationId }: { conversationId: string }) {
  const [traces, setTraces] = useState<TraceEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchTraces = async () => {
    if (!conversationId) return;
    try {
      const res = await fetch(`${API_BASE}/api/observability/trace/${conversationId}`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      const data = await res.json();
      if (Array.isArray(data)) {
        setTraces(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    fetchTraces();
    const interval = setInterval(fetchTraces, 3000);
    return () => clearInterval(interval);
  }, [conversationId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [traces]);

  return (
    <div className="flight-recorder">
      <div className="flight-recorder__header">
        <Activity size={14} className="text-cyan animate-pulse" />
        <span>FLIGHT RECORDER: REASONING TRACE</span>
        <div className="live-badge">LIVE</div>
      </div>

      <div className="flight-recorder__feed" ref={scrollRef}>
        {traces.length === 0 && (
          <div className="flight-empty">
            <Zap size={32} className="text-muted" opacity={0.2} />
            <p>Awaiting agentic reasoning traces...</p>
          </div>
        )}

        {traces.map((trace) => (
          <div key={trace.id} className={`trace-item trace-item--${trace.status}`}>
            <div className="trace-item__line" />
            <div className="trace-item__icon">
              {getIcon(trace.tool_used || trace.agent_type)}
            </div>
            <div className="trace-item__content">
              <div className="trace-item__header">
                <span className="trace-agent">{trace.agent_type.toUpperCase()}</span>
                <span className="trace-time">{new Date(trace.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="trace-action">{trace.action}</div>
              <div className="trace-detail">{trace.detail}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getIcon(type: string) {
  const t = type.toLowerCase();
  if (t.includes("shell") || t.includes("terminal")) return <Terminal size={12} />;
  if (t.includes("file") || t.includes("write") || t.includes("read")) return <FileText size={12} />;
  if (t.includes("search") || t.includes("grep")) return <Search size={12} />;
  if (t.includes("planner")) return <Shield size={12} />;
  if (t.includes("researcher")) return <Cpu size={12} />;
  return <Brain size={12} />;
}
