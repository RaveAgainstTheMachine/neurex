import { useState, useEffect, useLayoutEffect, useRef, useMemo } from "react";
import { 
  Play, Square, RefreshCcw, Cpu, Zap, Database, ExternalLink, 
  Code, Network, Search, Brain, FileJson, Video, Image, AudioLines, 
  Loader2, Info, Trash2, AlertTriangle
} from "lucide-react";
import "./InfraPanel.css";
import { useStore } from "../../lib/store";
import { ModelProfile, InfraEngine, MeshPeer } from "../../lib/types";
import toast from "react-hot-toast";

const API_BASE = "http://127.0.0.1:8000";

function ModelDetailsModal({ 
  show, 
  model, 
  onClose,
  onDeploy,
  loading
}: { 
  show: boolean; 
  model: ModelProfile | null; 
  onClose: () => void;
  onDeploy: (e: string, m: string) => void;
  loading: boolean;
}) {
  if (!show || !model) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-content--large" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <Brain size={20} className="text-purple" />
          <h3 style={{ fontSize: 20 }}>{model.name}</h3>
          <button className="icon-btn" style={{ marginLeft: 'auto' }} onClick={onClose}>
            <Square size={14} />
          </button>
        </div>
        <div className="modal-body">
          <div style={{ display: 'flex', gap: 20, marginBottom: 20 }}>
            <div className="spec-tile">
              <span className="spec-label">PARAMS</span>
              <span className="spec-value">{model.params}</span>
            </div>
            <div className="spec-tile">
              <span className="spec-label">VRAM</span>
              <span className="spec-value">{model.vram_required_gb}GB</span>
            </div>
            <div className="spec-tile">
              <span className="spec-label">CONTEXT</span>
              <span className="spec-value">{model.context_window.toLocaleString()}</span>
            </div>
          </div>

          <div className="detail-section">
            <h4>Description</h4>
            <p>{model.description || "Elite model profile with high-consistency performance across specialized tasks."}</p>
          </div>

          {model.benchmarks && Object.keys(model.benchmarks).length > 0 && (
            <div className="detail-section">
              <h4>Benchmarks</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {Object.entries(model.benchmarks).map(([k, v]) => (
                  <div key={k} className="benchmark-row">
                    <span className="benchmark-key">{k}</span>
                    <div className="benchmark-bar-bg">
                      <div className="benchmark-bar-fill" style={{ width: `${Math.min(100, parseFloat(v) || 50)}%` }} />
                    </div>
                    <span className="benchmark-val">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn--muted" onClick={onClose}>Close</button>
          {model.repo_url && (
            <a 
              href={model.repo_url} 
              target="_blank" 
              rel="noreferrer" 
              className="btn btn--muted"
              style={{ display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}
            >
              <ExternalLink size={14} /> HF HUB
            </a>
          )}
          <button 
            className={`btn ${model.is_downloaded ? 'btn--disabled' : 'btn--purple'}`}
            disabled={loading || model.is_downloaded}
            onClick={() => onDeploy(model.engine, model.name)}
          >
            {model.is_downloaded ? "ALREADY INSTALLED" : "DEPLOY TO NODE"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfirmModal({ 
  show, 
  title, 
  message, 
  onConfirm, 
  onCancel 
}: { 
  show: boolean; 
  title: string; 
  message: string; 
  onConfirm: () => void; 
  onCancel: () => void;
}) {
  if (!show) return null;
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <AlertTriangle size={18} className="text-amber" />
          <h3>{title}</h3>
        </div>
        <div className="modal-body">
          <p>{message}</p>
        </div>
        <div className="modal-footer">
          <button className="btn btn--muted" onClick={onCancel}>Cancel</button>
          <button className="btn btn--red" onClick={onConfirm}>Confirm Deletion</button>
        </div>
      </div>
    </div>
  );
}

export function InfraPanel({ onExpand, currentSize }: { onExpand: (s: number) => void, currentSize: number }) {
  const engines = useStore(s => s.infraEngines);
  const metrics = useStore(s => s.infraMetrics);
  const registry = useStore(s => s.infraRegistry);
  const skills = useStore(s => s.infraSkills);
  const peers = useStore(s => s.infraPeers);
  const fetchData = useStore(s => s.refreshInfra);

  const [searchResults, setSearchResults] = useState<ModelProfile[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [animating, setAnimating] = useState(true);
  
  // Custom Modal State
  const [confirmState, setConfirmState] = useState<{ show: boolean; skillId: string | null }>({ show: false, skillId: null });
  const [selectedModel, setSelectedModel] = useState<ModelProfile | null>(null);

  const hubRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (hubRef.current) {
      const originalSize = currentSize;
      const requiredPx = 440;
      const totalWidth = window.innerWidth;
      const percentage = Math.min(45, Math.max(20, (requiredPx / totalWidth) * 100));
      
      onExpand(percentage);
      const t = setTimeout(() => setAnimating(false), 200);
      return () => {
        onExpand(originalSize);
        clearTimeout(t);
      };
    }
  }, []);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 10000);
    return () => clearInterval(timer);
  }, [fetchData]);

  const bestInClass = useMemo(() => {
    const roles = {
      "Thinking": "thinking",
      "Coding": "coding",
      "Vision": "vision",
      "Media": "image",
      "Video": "video",
      "Audio": "audio"
    };
    const results: Record<string, ModelProfile | undefined> = {};
    Object.entries(roles).forEach(([label, cap]) => {
      results[label] = registry.find(m => m.recommended_tasks?.some(t => t.toLowerCase().includes(cap)) || m.name.toLowerCase().includes(cap));
    });
    return results;
  }, [registry]);

  const handleControl = async (name: string, action: "start" | "stop") => {
    setLoading(true);
    try {
      await fetch(`${API_BASE}/api/infra/engine/${name}/${action}`, { method: "POST" });
      await fetchData();
    } finally {
      setLoading(false);
    }
  };

  const handlePullModel = async (engine: string, model: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/infra/model/pull?engine=${engine}&model=${model}`, { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      fetchData();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/api/infra/registry/search?query=${encodeURIComponent(query)}`);
      if (res.ok) {
        setSearchResults(await res.json());
      }
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setSearching(false);
    }
  };

  const handleDeleteSkill = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/infra/skills/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to delete skill");
      }
      toast.success("Skill purged");
      fetchData();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setConfirmState({ show: false, skillId: null });
    }
  };

  const getCapabilityIcon = (tasks: string[] | undefined) => {
    if (!tasks) return <Brain size={14} className="capability-icon--active" />;
    const t = tasks.join(" ").toLowerCase();
    if (t.includes("vision") || t.includes("image")) return <Image size={14} className="capability-icon--active" />;
    if (t.includes("code")) return <FileJson size={14} className="capability-icon--active" />;
    if (t.includes("audio")) return <AudioLines size={14} className="capability-icon--active" />;
    if (t.includes("video")) return <Video size={14} className="capability-icon--active" />;
    return <Brain size={14} className="capability-icon--active" />;
  };

  const renderModelCard = (m: ModelProfile) => {
    const isDownloaded = m.is_downloaded || false;
    return (
      <div key={m.name} className={`model-card ${isDownloaded ? 'model-card--downloaded' : ''}`} onClick={() => setSelectedModel(m)} style={{ cursor: 'pointer' }}>
        <div className="model-card__header">
          {getCapabilityIcon(m.recommended_tasks)}
          <span className="model-card__name">{m.name}</span>
          <span className="model-card__tag">{m.params}</span>
        </div>
        <div className="model-card__details">
          <div className="model-card__detail">
            <Database size={10} /> {(m.vram_required_gb || 0)}GB VRAM
          </div>
          <div className="model-card__detail">
            <RefreshCcw size={10} /> {((m.context_window || 0) / 1000).toFixed(0)}k ctx
          </div>
        </div>
      </div>
    );
  };

  return (
    <div ref={hubRef} className={`infra-panel ${expanded ? 'infra-panel--expanded' : ''}`}>
      <ConfirmModal 
        show={confirmState.show}
        title="Purge Skill"
        message="Are you sure you want to delete this community skill? Permanent removal."
        onConfirm={() => confirmState.skillId && handleDeleteSkill(confirmState.skillId)}
        onCancel={() => setConfirmState({ show: false, skillId: null })}
      />
      <ModelDetailsModal
        show={!!selectedModel}
        model={selectedModel}
        onClose={() => setSelectedModel(null)}
        onDeploy={(e, m) => { handlePullModel(e, m); setSelectedModel(null); }}
        loading={loading}
      />
      
      <div className="infra-panel__header">
        <Cpu size={16} />
        <span>Infrastructure Hub</span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
          {metrics && (
            <div style={{ fontSize: 10, color: "var(--text-muted)", display: "flex", gap: 12 }}>
              <span title="GPU VRAM"><Zap size={10} style={{marginRight: 4, color: metrics.vram_gb > 0 ? 'var(--status-done)' : 'var(--text-muted)'}}/>{metrics.vram_gb}GB</span>
              <span title="System RAM"><Database size={10} style={{marginRight: 4}}/>{metrics.ram_used_gb}G</span>
            </div>
          )}
          <button className="icon-btn" onClick={() => setExpanded(!expanded)}>
            <RefreshCcw size={12} className={expanded ? "rotate-180" : ""} />
          </button>
        </div>
      </div>

      {/* RECOMMENDATIONS */}
      <div className="infra-section">
        <div className="infra-section__title">Agent Recommendations</div>
        <div className="infra-list" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
          {Object.entries(bestInClass).map(([role, model]: [string, ModelProfile | undefined]) => model && (
            <div key={role} className="model-card" style={{ padding: 10, borderStyle: 'dashed', cursor: 'pointer' }} onClick={() => setSelectedModel(model)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ fontSize: 10.5, textTransform: 'uppercase', color: 'var(--purple-light)', fontWeight: 700 }}>{role}</div>
                <div style={{ fontSize: 9.5, color: 'var(--text-muted)' }}>{model.params} • {model.vram_required_gb}G VRAM</div>
              </div>
              <div style={{ fontSize: 12.5, fontWeight: 600, margin: '4px 0' }}>{model.name.split(':').shift()}</div>
              <button 
                className={`btn ${model.is_downloaded ? 'btn--disabled' : 'btn--purple'}`}
                style={{ width: '100%', marginTop: 'auto', fontSize: 10.5, padding: '4px' }}
                onClick={(e) => { e.stopPropagation(); handlePullModel(model.engine, model.name); }}
                disabled={loading || model.is_downloaded}
              >
                {model.is_downloaded ? "ACTIVE" : "DEPLOY"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ENGINES */}
      <div className="infra-section">
        <div className="infra-section__title">Compute Engines</div>
        <div className="infra-list">
          {engines.length === 0 ? <div className="loading-text">Scanning local core...</div> : engines.map((e: InfraEngine) => (
            <div key={e.name} className={`infra-card ${e.status === "running" ? "infra-card--active" : ""}`}>
              <div className="infra-card__info">
                <div className="infra-card__name">{e.name}</div>
                <div className="infra-card__version">{e.status.toUpperCase()}</div>
              </div>
              <div className="infra-card__actions">
                <button className={`icon-btn ${e.status === "running" ? 'icon-btn--red' : 'icon-btn--green'}`} onClick={() => handleControl(e.name, e.status === "running" ? "stop" : "start")} disabled={loading}>
                  {e.status === "running" ? <Square size={14} /> : <Play size={14} />}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CATALOG + SEARCH */}
      <div className="infra-section">
        <div className="infra-section__title">Model Catalog</div>
        <div className="infra-search" style={{ marginBottom: 12 }}>
          <div className="skills-input">
            <Search size={14} className="skills-input__icon" />
            <input 
              type="text" 
              placeholder="Search registry or Hugging Face..." 
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
            />
            {searching && <Loader2 size={14} className="animate-spin" />}
          </div>
        </div>
        <div className="infra-list">
          {(searchQuery ? searchResults : registry).map((m: ModelProfile) => renderModelCard(m))}
        </div>
      </div>

      {/* MESH */}
      <div className="infra-section">
        <div className="infra-section__title">Infrastructure Mesh</div>
        <div className="infra-list">
          {peers.length === 0 ? (
            <div style={{ fontSize: 10, color: "var(--text-muted)", padding: 8 }}>No peers detected. Enable Mesh to split loads.</div>
          ) : (
            peers.map((p: MeshPeer) => (
              <div key={p.url} className={`infra-card ${p.status === "online" ? "infra-card--active" : ""}`}>
                <div className="infra-card__info">
                  <div className="infra-card__name">{p.name}</div>
                  <div className="infra-card__version"><Network size={10} /> {p.url} • {p.vram_gb}GB</div>
                </div>
                <div className="infra-card__actions">
                  <span className="task-tag">{p.status.toUpperCase()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* SKILLS */}
      <div className="infra-section">
        <div className="infra-section__title">Community Skills</div>
        <div className="infra-list">
          {skills.map((s: any) => (
            <div key={s.id} className={`model-card ${s.enabled ? "model-card--active" : ""}`}>
              <div className="model-card__header">
                <Code size={12} className="model-card__icon" />
                <span className="model-card__name">{s.name}</span>
                <button className="icon-btn text-red" style={{ marginLeft: 'auto', opacity: 0.4 }} onClick={() => setConfirmState({ show: true, skillId: s.id })}>
                  <Trash2 size={12} />
                </button>
                <span className="model-card__tag">v{s.version}</span>
              </div>
              <p style={{ fontSize: 10, color: "var(--text-muted)", margin: "4px 0" }}>{s.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
