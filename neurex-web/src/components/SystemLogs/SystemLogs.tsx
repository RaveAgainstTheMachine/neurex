import { useState, useEffect } from "react";
import { Shield, ShieldAlert, Activity, Key } from "lucide-react";
import "./SystemLogs.css";

const API_BASE = "http://localhost:8000";

interface AuditLog {
  id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "SECURITY";
  event: string;
  user_id: string;
  ip_address: string;
  details: string;
}

export function SystemLogsPanel() {
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    // Fetch mock logs for now, representing the Phase 8 requirements
    setLogs([
      {
        id: "1",
        timestamp: new Date().toISOString(),
        level: "INFO",
        event: "mTLS Handshake Success",
        user_id: "admin_01",
        ip_address: "192.168.1.105",
        details: "Secure remote desktop access established."
      },
      {
        id: "2",
        timestamp: new Date(Date.now() - 5000).toISOString(),
        level: "SECURITY",
        event: "File Lock Acquired",
        user_id: "agent_coder",
        ip_address: "internal",
        details: "Collision prevention engaged on main.py"
      },
      {
        id: "3",
        timestamp: new Date(Date.now() - 15000).toISOString(),
        level: "WARN",
        event: "Unauthorized Access Attempt",
        user_id: "unknown",
        ip_address: "10.0.0.50",
        details: "Failed API Key validation on /api/files/read"
      }
    ]);
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
        {logs.map(log => (
          <div key={log.id} className={`sys-log-item sys-log-item--${log.level.toLowerCase()}`}>
            <div className="sys-log-item__header">
              <span className="sys-log-item__icon">{getIcon(log.level)}</span>
              <span className="sys-log-item__event">{log.event}</span>
              <span className="sys-log-item__time">{new Date(log.timestamp).toLocaleTimeString()}</span>
            </div>
            <div className="sys-log-item__meta">
              <span>User: {log.user_id}</span> • <span>IP: {log.ip_address}</span>
            </div>
            <div className="sys-log-item__details">{log.details}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
