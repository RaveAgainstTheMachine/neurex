import { useState, useEffect } from "react";
import { Shield, ShieldAlert, Activity, Key } from "lucide-react";
import "./SystemLogs.css";

const API_BASE = "http://127.0.0.1:8000";

interface AuditLog {
  id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "SECURITY";
  event: string;
  user_id: string;
  ip_address: string;
  details: string;
}

interface GroupedLog extends AuditLog {
  count: number;
  timestamps: string[];
}

export function SystemLogsPanel() {
  const [logs, setLogs] = useState<GroupedLog[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const r = await fetch(`${API_BASE}/api/infra/logs`);
        const data = await r.json();
        const rawLogs = Array.isArray(data) ? data : [];
        
        // Grouping Logic
        const groups: Record<string, GroupedLog> = {};
        rawLogs.forEach((log: AuditLog) => {
          const key = `${log.event}-${log.user_id}-${log.ip_address}-${log.level}`;
          if (!groups[key]) {
            groups[key] = { ...log, count: 1, timestamps: [log.timestamp] };
          } else {
            groups[key].count++;
            groups[key].timestamps.push(log.timestamp);
          }
        });
        
        setLogs(Object.values(groups).sort((a, b) => 
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        ));
      } catch (err) {
        console.error("Failed to fetch logs", err);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const getIcon = (level: string) => {
    switch (level) {
      case "SECURITY": return <Shield size={14} color="var(--purple-light)" />;
      case "WARN": return <ShieldAlert size={14} color="var(--accent-yellow)" />;
      case "ERROR": return <ShieldAlert size={14} color="var(--accent-red)" />;
      default: return <Activity size={14} color="var(--text-muted)" />;
    }
  };

  return (
    <div className="system-logs">
      <div className="system-logs__header">
        <Key size={16} />
        Zero-Trust Audit Trail
      </div>
      <div className="system-logs__list">
        {logs.map(log => {
          const isExpanded = selectedId === log.id;
          return (
            <div 
              key={log.id} 
              className={`sys-log-item sys-log-item--${log.level.toLowerCase()} ${isExpanded ? 'sys-log-item--expanded' : ''}`}
              onClick={() => setSelectedId(isExpanded ? null : log.id)}
            >
              <div className="sys-log-item__header">
                <span className="sys-log-item__icon">{getIcon(log.level)}</span>
                <span className="sys-log-item__event">{log.event}</span>
                {log.count > 1 && <span className="sys-log-item__count">x{log.count}</span>}
                <span className="sys-log-item__time">{new Date(log.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="sys-log-item__meta">
                <span>User: {log.user_id}</span> • <span>IP: {log.ip_address}</span>
              </div>
              
              {isExpanded && (
                <div className="sys-log-item__details-expanded">
                  <div className="sys-log-detail-box">
                    <strong>Technical Details:</strong>
                    <pre>{log.details}</pre>
                  </div>
                  <div className="sys-log-timeline">
                    <strong>Occurrence Timeline:</strong>
                    <div className="timeline-list">
                      {log.timestamps.slice(0, 10).map((ts, i) => (
                        <div key={i} className="timeline-entry">{new Date(ts).toLocaleString()}</div>
                      ))}
                      {log.timestamps.length > 10 && <div className="timeline-entry">... and {log.timestamps.length - 10} more</div>}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
