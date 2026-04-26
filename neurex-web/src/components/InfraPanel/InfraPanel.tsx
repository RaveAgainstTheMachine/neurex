import { useEffect, useState } from "react";
import { Play, Square, RefreshCcw, Cpu, Zap, Database, ExternalLink, Code, Network } from "lucide-react";
import "./InfraPanel.css";

const API_BASE = "http://localhost:8000";

interface EngineStatus {
  name: string;
  status: "running" | "stopped";
  version: string;
  installed: boolean;
}

interface ModelProfile {
  name: string;
  engine: string;
  params: string;
  context_window: number;
  vram_required_gb: number;
  recommended_tasks: string[];
}

interface SkillManifest {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  source_repo: string;
}

export function InfraPanel() {
  const [engines, setEngines] = useState<EngineStatus[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [registry, setRegistry] = useState<ModelProfile[]>([]);
  const [skills, setSkills] = useState<SkillManifest[]>([]);
  const [peers, setPeers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [sRes, rRes, skRes, pRes] = await Promise.all([
        fetch(`${API_BASE}/api/infra/status`),
        fetch(`${API_BASE}/api/infra/registry`),
        fetch(`${API_BASE}/api/infra/skills`),
        fetch(`${API_BASE}/api/infra/mesh/peers`)
      ]);
      const sData = await sRes.json();
      setEngines(sData.engines || []);
      setMetrics(sData.metrics || null);
      
      setRegistry(await rRes.json());
      setSkills(await skRes.json());
      setPeers(await pRes.json());
    } catch (err) {
      console.error("Failed to fetch infra data:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 5000);
    return () => clearInterval(timer);
  }, []);

  const handleControl = async (name: string, action: "start" | "stop") => {
    setLoading(true);
    try {
      await fetch(`${API_BASE}/api/infra/engine/${name}/${action}`, { method: "POST" });
      await fetchData();
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSkill = async (id: string, enable: boolean) => {
    try {
      await fetch(`${API_BASE}/api/infra/skills/${id}/toggle?enable=${enable}`, { method: "POST" });
      await fetchData();
    } catch (err) {
      console.error("Failed to toggle skill:", err);
    }
  };

  const handlePullModel = async (engine: string, model: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/infra/model/pull?engine=${engine}&model=${model}`, { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      fetchData();
    } catch (err) {
      console.error("Failed to pull model:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="infra-panel">
      <div className="infra-panel__header">
        <Cpu size={16} />
        <span>Inference Infrastructure</span>
        {metrics && (
          <div style={{ marginLeft: "auto", fontSize: 10, color: "var(--text-muted)", display: "flex", gap: 12 }}>
            <span><Cpu size={10} style={{marginRight: 4}}/>{(metrics.cpu_percent || 0).toFixed(1)}%</span>
            <span><Database size={10} style={{marginRight: 4}}/>{(metrics.ram_used_gb || 0).toFixed(1)} / {(metrics.ram_total_gb || 0).toFixed(1)} GB</span>
          </div>
        )}
      </div>

      <div className="infra-section">
        <div className="infra-section__title">Engines</div>
        <div className="infra-list">
          {engines.map((e) => (
            <div key={e.name} className={`infra-card ${e.status === "running" ? "infra-card--active" : ""}`}>
              <div className="infra-card__info">
                <div className="infra-card__name">{e.name}</div>
                <div className="infra-card__version">{e.version}</div>
              </div>
              <div className="infra-card__actions">
                {e.status === "running" ? (
                  <button className="icon-btn icon-btn--red" onClick={() => handleControl(e.name, "stop")} disabled={loading}>
                    <Square size={14} />
                  </button>
                ) : (
                  <button className="icon-btn icon-btn--green" onClick={() => handleControl(e.name, "start")} disabled={loading || !e.installed}>
                    <Play size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="infra-section">
        <div className="infra-section__title">Model Registry</div>
        <div className="infra-list">
          {registry.map((m) => (
            <div key={m.name} className="model-card">
              <div className="model-card__header">
                <Zap size={12} className="model-card__icon" />
                <span className="model-card__name">{m.name}</span>
                <span className="model-card__tag">{m.params}</span>
              </div>
              <div className="model-card__details">
                <div className="model-card__detail">
                  <Database size={10} /> {(m.vram_required_gb || 0)}GB VRAM
                </div>
                <div className="model-card__detail">
                  <RefreshCcw size={10} /> {((m.context_window || 0) / 1000).toFixed(0)}k Context
                </div>
              </div>
              <div className="model-card__footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="model-card__tasks">
                  {(m.recommended_tasks || []).map(t => <span key={t} className="task-tag">{t}</span>)}
                </div>
                <button 
                  className="btn btn--purple" 
                  style={{ padding: '4px 10px', fontSize: 10 }}
                  onClick={() => handlePullModel(m.engine, m.name)}
                  disabled={loading}
                >
                  {loading ? "Pulling..." : "Pull Model"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="infra-section">
        <div className="infra-section__title">Community Skills</div>
        <div className="infra-list">
          {skills.map((s) => (
            <div key={s.id} className={`model-card ${s.enabled ? "model-card--active" : ""}`}>
              <div className="model-card__header">
                <Code size={12} className="model-card__icon" />
                <span className="model-card__name">{s.name}</span>
                <span className="model-card__tag">v{s.version}</span>
              </div>
              <div className="model-card__details" style={{ marginBottom: 6 }}>
                <span style={{ fontSize: 10, color: "var(--text-muted)", lineHeight: 1.4 }}>{s.description}</span>
              </div>
              <div className="model-card__tasks" style={{ justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                <a href={s.source_repo} target="_blank" rel="noreferrer" className="task-tag" style={{ display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none' }}>
                  <ExternalLink size={8} /> {s.author}
                </a>
                <button 
                  className={`btn ${s.enabled ? "btn--red" : "btn--green"}`}
                  style={{ padding: '2px 8px', fontSize: 9 }}
                  onClick={() => handleToggleSkill(s.id, !s.enabled)}
                >
                  {s.enabled ? "Disable" : "Enable"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="infra-section">
        <div className="infra-section__title">Mesh Federation</div>
        <div className="infra-list">
          {peers.length === 0 ? (
            <div className="model-card" style={{ textAlign: "center", color: "var(--text-muted)" }}>
              No remote nodes connected.
            </div>
          ) : (
            peers.map((p) => (
              <div key={p.url} className={`infra-card ${p.status === "online" ? "infra-card--active" : ""}`}>
                <div className="infra-card__info">
                  <div className="infra-card__name">{p.name}</div>
                  <div className="infra-card__version" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Network size={10} /> {p.url}
                  </div>
                </div>
                <div className="infra-card__actions" style={{ flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                  <span className="task-tag" style={{ background: p.status === 'online' ? 'rgba(46, 204, 113, 0.1)' : 'rgba(255, 69, 58, 0.1)', color: p.status === 'online' ? 'var(--status-done)' : 'var(--status-failed)' }}>
                    {p.status.toUpperCase()}
                  </span>
                  {p.status === 'online' && (
                    <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>
                      {p.vram_gb}GB VRAM • {p.ram_total_gb}GB RAM • {p.cpu_percent}% CPU • {p.latency_ms}ms
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
