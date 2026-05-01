// neurex-web/src/components/InfraPanel/InfraPanel.tsx
"use client";

import { useState, useEffect, useMemo } from "react";
import { 
  Play, Square, RefreshCcw, Cpu, Zap, Search, 
  Brain, Braces, Video, AudioLines, 
  Thermometer, Gauge, Eye, X, Image as ImageIcon
} from "lucide-react";
import "./InfraPanel.css";
import { useStore } from "../../lib/store";
import { ModelProfile } from "../../lib/types";
import toast from "react-hot-toast";
import { API_BASE } from "../../lib/config";

export function InfraPanel({ onExpand, currentSize }: { onExpand: (s: number) => void, currentSize: number }) {
  const engines = useStore(s => s.infraEngines);
  const metrics = useStore(s => s.infraMetrics);
  const registry = useStore(s => s.infraRegistry);
  const skills = useStore(s => s.infraSkills);
  const peers = useStore(s => s.infraPeers);
  const fetchData = useStore(s => s.refreshInfra);

  const [searchQuery, setSearchQuery] = useState("");
  const [hfResults, setHfResults] = useState<ModelProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelProfile | null>(null);
  const [quantization, setQuantization] = useState("4-bit (Fastest)");

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 5000);
    onExpand(35);
    return () => {
      clearInterval(timer);
      onExpand(18);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounced search for Hugging Face ONLY
  useEffect(() => {
    const trimmed = searchQuery.trim();
    if (trimmed.length < 3) {
      setHfResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/infra/registry/search?query=${encodeURIComponent(trimmed)}`);
        if (!res.ok) return;
        const data = await res.json();
        setHfResults(data);
      } catch (err) {
        console.error("HF Search failed", err);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const recommendations = [
    { id: 'thinking', role: 'THINKING', model: 'deepseek-r1', specs: '32B • 20G VRAM', icon: Brain },
    { id: 'coding', role: 'CODING', model: 'qwen2.5-coder', specs: '32B • 20G VRAM', icon: Braces },
    { id: 'vision', role: 'VISION', model: 'llama3.2-vision', specs: '11B • 8.5G VRAM', icon: Eye },
    { id: 'media', role: 'MEDIA', model: 'llama3.2-vision', specs: '11B • 8.5G VRAM', icon: ImageIcon },
    { id: 'video', role: 'VIDEO', model: 'ltx-video', specs: 'Multi-Modal • 24G VRAM', icon: Video },
    { id: 'audio', role: 'AUDIO', model: 'whisper-large-v3-turbo', specs: '1.5B • 4G VRAM', icon: AudioLines },
  ];

  const handlePullModel = async (engine: string, model: string) => {
    setLoading(true);
    let targetModel = model;
    
    // Simple mapping for quantization tags for Ollama
    if (engine === 'ollama' && !model.includes(':')) {
      if (quantization.includes('4-bit')) targetModel += ':q4_K_M';
      else if (quantization.includes('8-bit')) targetModel += ':q8_0';
    }

    try {
      const res = await fetch(`${API_BASE}/api/infra/model/pull?engine=${engine}&model=${targetModel}`, { 
        method: "POST",
        headers: { "Authorization": `Bearer ${useStore.getState().token}` }
      });
      if (!res.ok) throw new Error(await res.text());
      toast.success(`Deploying ${targetModel} to node...`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEngineControl = async (action: 'start' | 'stop' | 'install', engine: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/infra/engine/${engine}/${action}`, { 
        method: "POST",
        headers: { "Authorization": `Bearer ${useStore.getState().token}` }
      });
      if (!res.ok) throw new Error(await res.text());
      toast.success(`${engine.toUpperCase()} ${action} successful`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSkill = async (skillId: string, enable: boolean) => {
    try {
      const res = await fetch(`${API_BASE}/api/infra/skills/${skillId}/toggle?enable=${enable}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${useStore.getState().token}` }
      });
      if (!res.ok) throw new Error(await res.text());
      toast.success(`Skill ${skillId} ${enable ? 'enabled' : 'disabled'}`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const filteredRegistry = useMemo(() => {
    const results: (ModelProfile & { origin: 'LOCAL' | 'HF' | 'RPC' | 'NODE', nodeName?: string })[] = [];

    // 1. Local Models (Strictly from disk)
    registry.forEach(m => {
      results.push({ ...m, origin: 'LOCAL' });
    });

    // 2. Peer Models
    peers.forEach(peer => {
      if (peer.status === 'online' && peer.models) {
        peer.models.forEach(modelName => {
          results.push({
            name: modelName,
            engine: 'ollama',
            params: '?',
            context_window: 32768,
            vram_required_gb: 0,
            recommended_tasks: [],
            origin: peer.rpc_endpoint ? 'RPC' : 'NODE',
            nodeName: peer.name
          });
        });
      }
    });

    // 3. HF Results (Discovery layer)
    if (searchQuery.trim().length >= 3) {
      hfResults.forEach(m => {
        results.push({ ...m, origin: 'HF' } as any);
      });
    }

    const query = searchQuery.toLowerCase().trim();
    if (!query) {
      // Show all real-world available models
      return results.slice(0, 20);
    }
    
    const searchWords = query.split(/\s+/);
    return results.filter(m => {
      const name = m.name.toLowerCase();
      return searchWords.every(word => name.includes(word));
    });
  }, [registry, searchQuery, hfResults, peers]);

  return (
    <div className="infra-panel">
      <div className="infra-panel__header">
        <Gauge size={16} className="text-purple" />
        <span>INFRASTRUCTURE HUB</span>
        <div className="mesh-indicator" title="Mesh Status">
          <span>{metrics?.vram_gb || 0}GB VRAM</span>
          <div className="mesh-divider" />
          <span>{metrics?.ram_used_gb || 0}G / {metrics?.ram_total_gb || 0}G RAM</span>
          <RefreshCcw size={12} className="ml-2 hover-rotate cursor-pointer" onClick={() => fetchData()} />
        </div>
      </div>

      <div className="infra-content">
        {/* AGENT RECOMMENDATIONS */}
        <div className="infra-section">
          <div className="infra-section__title">AGENT RECOMMENDATIONS</div>
          <div className="recommendation-grid">
            {recommendations.map((rec) => (
              <div 
                key={rec.id} 
                className="rec-card"
                onClick={() => {
                  const [mName] = rec.model.split(':');
                  setSelectedModel({ 
                    name: mName, 
                    engine: 'ollama', 
                    params: rec.specs.split(' ')[0], 
                    context_window: 32768, 
                    vram_required_gb: parseInt(rec.specs.match(/(\d+)G VRAM/)?.[1] || "0"),
                    recommended_tasks: [rec.role],
                    description: `Recommended model for ${rec.role} tasks on this hardware.`
                  });
                }}
              >
                <div className="rec-header">
                  <span className="rec-role">{rec.role}</span>
                  <span className="rec-specs">{rec.specs}</span>
                </div>
                <div className="rec-model">{rec.model}</div>
                <button 
                  className="rec-deploy-btn" 
                >
                  DEPLOY
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* COMPUTE ENGINES */}
        <div className="infra-section">
          <div className="infra-section__title">COMPUTE ENGINES</div>
          <div className="engine-stack">
            {engines.map((e) => (
              <div key={e.name} className={`engine-row ${e.status === 'running' ? 'active' : ''}`}>
                <div className="engine-main">
                  <div className="engine-name">{e.name}</div>
                  <div className="engine-status">{e.status.toUpperCase()} {e.version && `• ${e.version}`}</div>
                </div>
                <div className="engine-controls">
                  {e.status === 'running' ? (
                    <button className="engine-btn stop" onClick={() => handleEngineControl('stop', e.name)} title="Stop Engine">
                      <Square size={14} fill="currentColor" />
                    </button>
                  ) : e.status === 'stopped' ? (
                    <button className="engine-btn start" onClick={() => handleEngineControl('start', e.name)} title="Start Engine">
                      <Play size={14} fill="currentColor" />
                    </button>
                  ) : (
                    <button className="engine-install-btn" onClick={() => handleEngineControl('install', e.name)}>
                      INSTALL
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SKILLS */}
        {skills && skills.length > 0 && (
          <div className="infra-section">
            <div className="infra-section__title">ACTIVE SKILLS & MCP</div>
            <div className="skill-list">
              {skills.map(skill => (
                <div key={skill.id} className="skill-row">
                  <div className="skill-info">
                    <div className="skill-name">{skill.name}</div>
                    <div className="skill-meta">{skill.tools_count} Tools • {skill.author}</div>
                  </div>
                  <div className="skill-toggle">
                    <input 
                      type="checkbox" 
                      checked={skill.enabled} 
                      onChange={(e) => handleToggleSkill(skill.id, e.target.checked)}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* MODEL CATALOG */}
        <div className="infra-section">
          <div className="infra-section__title">MODEL CATALOG</div>
          <div className="catalog-search">
            <Search size={14} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search registry or Hugging Face..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="catalog-list">
            {filteredRegistry.length === 0 ? (
              <div className="catalog-empty">
                <Brain size={24} className="text-muted mb-2 opacity-20" />
                <p>No models detected in registry.</p>
                {engines.find(e => e.name === 'ollama')?.status !== 'running' && (
                  <div className="catalog-empty__hint">
                    Ollama engine is currently offline. <br/>
                    <button className="text-purple hover:underline" onClick={() => handleEngineControl('start', 'ollama')}>Start Engine</button>
                  </div>
                )}
                {searchQuery && <p className="text-muted text-xs">Try searching for something else or check your connection.</p>}
              </div>
            ) : (
              filteredRegistry.map((m) => (
                <div key={m.name} className="catalog-item" onClick={() => setSelectedModel(m)}>
                  <div className="catalog-main">
                    <div className="catalog-header">
                      <Cpu size={14} className="text-muted" />
                      <span className="catalog-name">{m.name.split(':')[0]}</span>
                      <span className="catalog-tag">{m.params}</span>
                      <span className={`catalog-badge origin-${(m as any).origin.toLowerCase()}`}>
                        {(m as any).origin === 'HF' ? 'HF' : 
                         (m as any).origin === 'RPC' ? 'MESH(RPC)' :
                         (m as any).origin === 'NODE' ? `NODE: ${(m as any).nodeName}` : 
                         'LOCAL'}
                      </span>
                    </div>
                    <div className="catalog-meta">
                      <span>{m.vram_required_gb > 0 ? `${m.vram_required_gb}GB VRAM` : 'Local Asset'}</span>
                      <RefreshCcw size={10} />
                      <span>{m.context_window / 1000}k ctx</span>
                      {((m as any).origin === 'HF' || (m as any).origin === 'NODE') && (
                        <button 
                          className="catalog-deploy-btn"
                          onClick={(e) => { e.stopPropagation(); setSelectedModel(m); }}
                        >
                          DEPLOY
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* MODEL MODAL */}
      {selectedModel && (
        <div className="infra-modal-overlay" onClick={() => setSelectedModel(null)}>
          <div className="infra-modal" onClick={e => e.stopPropagation()}>
            <div className="infra-modal__header">
              <div className="infra-modal__title-group">
                <Cpu size={18} className="text-purple" />
                <div>
                  <h3>Deploy Model</h3>
                  <p>{selectedModel.name}</p>
                </div>
              </div>
              <button className="infra-modal__close" onClick={() => setSelectedModel(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="infra-modal__content">
              <div className="infra-modal__stats">
                <div className="stat-box">
                  <span className="stat-label">VRAM REQ</span>
                  <span className="stat-value">{selectedModel.vram_required_gb > 0 ? `${selectedModel.vram_required_gb}GB` : 'AUTO'}</span>
                </div>
                <div className="stat-box">
                  <span className="stat-label">CONTEXT</span>
                  <span className="stat-value">{selectedModel.context_window / 1024}k</span>
                </div>
                <div className="stat-box">
                  <span className="stat-label">ENGINE</span>
                  <span className="stat-value">{selectedModel.engine.toUpperCase()}</span>
                </div>
              </div>

              <div className="infra-modal__section">
                <label>Configuration</label>
                <div className="config-grid">
                  <div className="config-item">
                    <span>Quantization</span>
                    <select 
                      className="settings-select" 
                      value={quantization}
                      onChange={(e) => setQuantization(e.target.value)}
                    >
                      <option>4-bit (Fastest)</option>
                      <option>8-bit (Balanced)</option>
                      <option>FP16 (High Precision)</option>
                    </select>
                  </div>
                  <div className="config-item">
                    <span>Node Affinity</span>
                    <select className="settings-select">
                      <option>Local Only</option>
                      <option>Auto-Balance Mesh</option>
                      <option>High-Compute Node</option>
                    </select>
                  </div>
                </div>
              </div>

              {selectedModel.description && (
                <div className="infra-modal__section">
                  <label>Description</label>
                  <p className="infra-modal__desc">{selectedModel.description}</p>
                </div>
              )}
            </div>

            <div className="infra-modal__footer">
              <button className="btn btn--outline" onClick={() => setSelectedModel(null)}>Cancel</button>
              <button 
                className="btn btn--purple" 
                disabled={loading}
                onClick={async () => {
                  let modelName = selectedModel.name;
                  // For Ollama models, apply quantization tags if not already present
                  if (selectedModel.engine === 'ollama' && !modelName.includes(':')) {
                    if (quantization.startsWith('4-bit')) modelName = `${modelName}:q4_K_M`;
                    else if (quantization.startsWith('8-bit')) modelName = `${modelName}:q8_0`;
                  }
                  await handlePullModel(selectedModel.engine, modelName);
                  setSelectedModel(null);
                }}
              >
                {loading ? "Initializing..." : "Start Deployment"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
