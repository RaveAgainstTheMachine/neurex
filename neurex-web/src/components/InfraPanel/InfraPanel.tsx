import { useEffect, useState } from "react";
import { 
  Play, Square, RefreshCcw, Cpu, Zap, Database, ExternalLink, 
  Code, Network, Search, Brain, FileJson, Video, Image, AudioLines, 
  Loader2, Info
} from "lucide-react";
import "./InfraPanel.css";

const API_BASE = "http://127.0.0.1:8000";

interface ModelProfile {
  name: string;
  engine: string;
  params: string;
  context_window: number;
  vram_required_gb: number;
  recommended_tasks: string[];
  is_downloaded?: boolean;
  is_community?: boolean;
  downloads?: number;
}

export function InfraPanel({ onExpand, currentSize }: { onExpand: (s: number) => void, currentSize: number }) {
  const [engines, setEngines] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [registry, setRegistry] = useState<ModelProfile[]>([]);
  const [searchResults, setSearchResults] = useState<ModelProfile[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [skills, setSkills] = useState<any[]>([]);
  const [peers, setPeers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    const originalSize = currentSize;
    onExpand(35); // Grow simultaneously
    return () => onExpand(originalSize); // Back to user size
  }, []);

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

  const getCapabilityIcon = (tasks: string[] | undefined) => {
    if (!tasks) return <Brain size={14} className="capability-icon--active" />;
    const t = tasks.join(" ").toLowerCase();
    if (t.includes("vision") || t.includes("image")) return <span title="Vision Capable"><Image size={14} className="capability-icon--active" /></span>;
    if (t.includes("code")) return <span title="Coding Specialized"><FileJson size={14} className="capability-icon--active" /></span>;
    if (t.includes("audio") || t.includes("voice")) return <span title="Audio/STT Capable"><AudioLines size={14} className="capability-icon--active" /></span>;
    if (t.includes("video")) return <span title="Video Generation"><Video size={14} className="capability-icon--active" /></span>;
    return <span title="General Reasoning"><Brain size={14} className="capability-icon--active" /></span>;
  };

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 10000); // 10s refresh
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

  const renderModelCard = (m: any) => {
    const nodesWithModel = peers.filter(p => p.models?.some((rm: string) => rm.includes(m.name)));
    const isDownloaded = m.is_downloaded || false;

    return (
      <div key={m.name} className={`model-card ${isDownloaded ? 'model-card--downloaded' : ''}`}>
        <div className="model-card__header">
          {getCapabilityIcon(m.recommended_tasks)}
          <span className="model-card__name" title={m.name}>{m.name.split('/').pop()}</span>
          <span className="model-card__tag">{m.params}</span>
          {isDownloaded && <span className="badge badge--done" style={{marginLeft: 'auto', fontSize: 8}}>LOCAL</span>}
          {m.is_community && <span className="badge badge--warn" style={{marginLeft: 4, fontSize: 8}}>HF</span>}
        </div>
        <div className="model-card__details">
          <div className="model-card__detail">
            <Database size={10} /> {(m.vram_required_gb || 0)}GB VRAM
          </div>
          <div className="model-card__detail">
            <RefreshCcw size={10} /> {((m.context_window || 0) / 1000).toFixed(0)}k
          </div>
          {m.downloads !== undefined && (
            <div className="model-card__detail">
              <Search size={10} /> {m.downloads.toLocaleString()}
            </div>
          )}
        </div>
        
        {nodesWithModel.length > 0 && (
          <div className="model-card__nodes">
            <div className="node-availability">
              <Network size={10} style={{marginRight: 4}}/> Available on: {nodesWithModel.map(n => n.name).join(", ")}
            </div>
          </div>
        )}

        <div className="model-card__footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
          <div className="model-card__tasks">
            {(m.recommended_tasks || []).map((t: string) => <span key={t} className="task-tag">{t}</span>)}
          </div>
          <button 
            className={`btn ${isDownloaded ? 'btn--disabled' : 'btn--purple'}`} 
            style={{ padding: '4px 10px', fontSize: 10 }}
            onClick={() => handlePullModel(m.engine, m.name)}
            disabled={loading || isDownloaded}
          >
            {isDownloaded ? "READY" : loading ? "..." : "PULL"}
          </button>
        </div>
      </div>
    );
  };

  const bestInClass = {
    thinking: registry.find(m => m.name.toLowerCase().includes("r1")),
    coding: registry.find(m => m.name.toLowerCase().includes("coder")),
    vision: registry.find(m => m.name.toLowerCase().includes("vision")),
    audio: registry.find(m => m.name.toLowerCase().includes("whisper")),
    video: registry.find(m => m.name.toLowerCase().includes("video")),
    images: registry.find(m => m.name.toLowerCase().includes("stable-diffusion"))
  };

  return (
    <div 
      className={`infra-panel ${expanded ? 'infra-panel--expanded' : ''}`}
    >
      <div className="infra-panel__header">
        <Cpu size={16} />
        <span>Infrastructure Hub</span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
          {metrics && (
            <div style={{ fontSize: 10, color: "var(--text-muted)", display: "flex", gap: 12 }}>
              <span title="GPU Detection"><Zap size={10} style={{marginRight: 4, color: metrics.vram_gb > 0 ? 'var(--status-done)' : 'var(--text-muted)'}}/>{metrics.vram_gb || 0}GB</span>
              <span title="RAM Usage"><Database size={10} style={{marginRight: 4}}/>{metrics.ram_used_gb}G</span>
            </div>
          )}
          <button 
            className="icon-btn" 
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            title={expanded ? "Minimize" : "Expand Focus"}
          >
            <RefreshCcw size={12} className={expanded ? "rotate-180" : ""} />
          </button>
        </div>
      </div>

      {/* AGENT RECOMMENDATIONS */}
      <div className="infra-section">
        <div className="infra-section__title">Agent Recommendations</div>
        <div className="infra-list" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {Object.entries(bestInClass).map(([role, model]) => model && (
            <div key={role} className="model-card" style={{ padding: 8, borderStyle: 'dashed' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ fontSize: 9, textTransform: 'uppercase', color: 'var(--purple-light)', fontWeight: 700 }}>{role}</div>
                <div style={{ fontSize: 8, color: 'var(--text-muted)' }}>{model.params} • {model.vram_required_gb}G</div>
              </div>
              <div style={{ fontSize: 11, fontWeight: 600, margin: '4px 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {model.name.split(':').shift()}
              </div>
              <div className="model-card__tasks" style={{ margin: '4px 0 8px' }}>
                {(model.recommended_tasks || []).map(t => <span key={t} className="task-tag" style={{ fontSize: 7, padding: '1px 4px' }}>{t}</span>)}
              </div>
              <button 
                className={`btn ${model.is_downloaded ? 'btn--disabled' : 'btn--purple'}`}
                style={{ width: '100%', marginTop: 'auto', fontSize: 8, padding: '2px' }}
                onClick={() => handlePullModel(model.engine, model.name)}
                disabled={loading || model.is_downloaded}
              >
                {model.is_downloaded ? "ACTIVE" : "DEPLOY"}
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="infra-section">
        <div className="infra-section__title">Compute Engines</div>
        <div className="infra-list">
          {engines.length === 0 ? (
            <div className="model-card" style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>
              <Loader2 size={20} className="loading-spinner" style={{ margin: '0 auto 8px' }} />
              Connecting to local core...
            </div>
          ) : (
            engines.map((e) => (
              <div key={e.name} className={`infra-card ${e.status === "running" ? "infra-card--active" : ""}`}>
                <div className="infra-card__info">
                  <div className="infra-card__name" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {e.name}
                    {e.status === "missing" && <span title={e.details}><Info size={12} className="text-warn" /></span>}
                  </div>
                  <div className="infra-card__version">{e.version?.split(' ').pop()} • {e.status.toUpperCase()}</div>
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
            ))
          )}
        </div>
      </div>

      <div className="infra-section">
        <div className="infra-section__title">Model Discovery</div>
        <div className="infra-search">
          <Search size={14} />
          <input 
            type="text" 
            placeholder="Search Hugging Face (e.g. llama-3, mistral)..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch(searchQuery)}
          />
          {searching && <Loader2 size={14} className="loading-spinner" style={{ position: 'absolute', right: 10, top: 10 }} />}
        </div>

        <div className="infra-list">
          {searchResults.length > 0 && (
            <div className="search-results-label">
              <Search size={10} /> SEARCH RESULTS (HUGGINGFACE)
            </div>
          )}
          {searchResults.map(m => renderModelCard(m))}
          
          {searchResults.length === 0 && (
            <>
              <div className="search-results-label">
                <Brain size={10} /> MODEL REGISTRY
              </div>
              {registry.map(m => renderModelCard(m))}
            </>
          )}
        </div>
      </div>

      <div className="infra-section">
        <div className="infra-section__title">Mesh Federation</div>
        <div className="infra-list">
          {peers.length === 0 ? (
            <div className="model-card" style={{ textAlign: "center", color: "var(--text-muted)", fontSize: 10, padding: 10 }}>
              No peers detected. Enable Mesh to split loads.
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
                      {p.vram_gb}GB VRAM • {p.latency_ms}ms
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
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
        <div className="infra-section__title">Storage & Environment</div>
        <div className="model-card" style={{ padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
            <Database size={14} className="text-purple" />
            <span>Local Model Path: <code>~/.models</code></span>
          </div>
          <p style={{ margin: '8px 0 0', fontSize: 10, color: 'var(--text-muted)' }}>
            All downloaded assets are stored in the persistent volume mounted to LLM_MODELS_PATH.
          </p>
        </div>
      </div>
    </div>
  );
}
