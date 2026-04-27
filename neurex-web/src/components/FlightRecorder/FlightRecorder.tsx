import { useState, useEffect } from "react";
import { Brain, ChevronRight, Activity } from "lucide-react";
import "./FlightRecorder.css";

const API = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

interface Decision {
  id: string;
  agent_type: string;
  decision: string;
  rationale: string;
  created_at: string;
}

export function FlightRecorder({ conversationId, isActive = true }: { conversationId: string; isActive?: boolean }) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLog = async () => {
    if (!conversationId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/observability/flight-log/${conversationId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token") ?? ""}` },
      });
      if (res.ok) {
        setDecisions(await res.json());
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isActive) return;
    fetchLog();
    const interval = setInterval(fetchLog, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, [conversationId, isActive]);

  return (
    <div className="flight-recorder">
      <div className="flight-header">
        <Activity size={14} className="pulse-icon" />
        <span>Flight Recorder: Reasoning Trace</span>
        <button className="btn-refresh" onClick={fetchLog} disabled={loading}>
          {loading ? "..." : "Refresh"}
        </button>
      </div>

      <div className="flight-feed">
        {decisions.length === 0 ? (
          <div className="flight-empty">No reasoning traces captured for this session.</div>
        ) : (
          decisions.map((d) => (
            <div key={d.id} className="decision-card">
              <div className="decision-meta">
                <span className={`agent-tag agent-tag--${d.agent_type}`}>
                  <Brain size={10} /> {d.agent_type}
                </span>
                <span className="decision-time">
                  {new Date(d.created_at).toLocaleTimeString()}
                </span>
              </div>
              <div className="decision-title">
                <ChevronRight size={12} /> {d.decision}
              </div>
              <div className="decision-rationale">{d.rationale}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
