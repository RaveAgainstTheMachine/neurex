import { useEffect, useState } from "react";
import { Play, Square, RefreshCcw, Cpu, Zap, Database, ExternalLink, Code } from "lucide-react";
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
  const [registry, setRegistry] = useState<ModelProfile[]>([]);
  const [skills, setSkills] = useState<SkillManifest[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [sRes, rRes, skRes] = await Promise.all([
        fetch(`${API_BASE}/api/infra/status`),
        fetch(`${API_BASE}/api/infra/registry`),
        fetch(`${API_BASE}/api/infra/skills`)
      ]);
      setEngines(await sRes.json());
      setRegistry(await rRes.json());
      setSkills(await skRes.json());
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

  return (
    <div className="infra-panel">
      <div className="infra-panel__header">
        <Cpu size={16} />
        <span>Inference Infrastructure</span>
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
                  <Database size={10} /> {m.vram_required_gb}GB VRAM
                </div>
                <div className="model-card__detail">
                  <RefreshCcw size={10} /> {m.context_window / 1000}k Context
                </div>
              </div>
              <div className="model-card__tasks">
                {m.recommended_tasks.map(t => <span key={t} className="task-tag">{t}</span>)}
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
    </div>
  );
}
