// neurex-web/src/components/InfraPanel/InfraPanel.tsx
"use client";

import { useState, useEffect, useMemo } from "react";
import { 
  Play, Square, RefreshCcw, Cpu, Zap, Search, 
  Brain, Braces, Video, AudioLines, 
  Thermometer, Gauge, Eye, X, Image as ImageIcon,
  Monitor, HardDrive, Activity, Info, MessageSquare, Plus, Trash2
} from "lucide-react";
import "./InfraPanel.css";
import { useStore } from "../../lib/store";
import { ModelProfile } from "../../lib/types";
import toast from "react-hot-toast";
import { API_BASE } from "../../lib/config";
import { InfraDashboard } from "../InfraDashboard/InfraDashboard";
import { AnimatePresence } from "framer-motion";

export function InfraPanel({ onExpand, currentSize }: { onExpand: (s: number) => void, currentSize: number }) {
  const engines = useStore(s => s.infraEngines);
  const metrics = useStore(s => s.infraMetrics);
  const registry = useStore(s => s.infraRegistry);
  const skills = useStore(s => s.infraSkills);
  const peers = useStore(s => s.infraPeers);
  const settings = useStore(s => s.settings);
  const fetchData = useStore(s => s.refreshInfra);
  const refreshSettings = useStore(s => s.refreshSettings);

  const [searchQuery, setSearchQuery] = useState("");
  const [hfResults, setHfResults] = useState<ModelProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelProfile | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<string>("");
  const [quantization, setQuantization] = useState("4-bit (Fastest)");
  const [showDashboard, setShowDashboard] = useState(false);

  useEffect(() => {
    fetchData();
    refreshSettings();
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

  const routeIcons: Record<string, any> = {
    "Planning":    Brain,
    "Coding":      Braces,
    "Testing":     Zap,
    "Researching": Search,
    "Reviewing":   Eye,
    "Vision":      Eye,
    "Media":       ImageIcon,
    "Audio":       AudioLines,
    "Chat":        MessageSquare
  };

  const handleUpdateRoute = async (role: string, model: string) => {
    if (!settings) return;
    const newRoutes = { ...settings.model_routes };
    newRoutes[role] = model;
    
    try {
      const res = await fetch(`${API_BASE}/api/settings/`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${useStore.getState().token}` 
        },
        body: JSON.stringify({ settings: { model_routes: newRoutes } })
      });
      if (!res.ok) throw new Error(await res.text());
      refreshSettings();
      toast.success(`Route ${role} updated`);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleAddRoute = async () => {
    const role = prompt("Enter new cognitive role name (e.g. Documentation):");
    if (!role) return;
    handleUpdateRoute(role, modelOptions[0] || "qwen2.5-coder:14b");
  };

  const handleDeleteRoute = async (role: string) => {
    if (!settings) return;
    const newRoutes = { ...settings.model_routes };
    delete newRoutes[role];
    try {
      const res = await fetch(`${API_BASE}/api/settings/`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${useStore.getState().token}` 
        },
        body: JSON.stringify({ settings: { model_routes: newRoutes } })
      });
      if (!res.ok) throw new Error(await res.text());
      refreshSettings();
      toast.success(`Route ${role} removed`);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const modelOptions = useMemo(() => {
    const local = registry.map(m => m.name.split(':')[0]);
    const peerModels = peers.flatMap(p => p.models || []).map(m => m.split(':')[0]);
    return Array.from(new Set([...local, ...peerModels])).sort();
  }, [registry, peers]);

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
    const resultsMap: Map<string, any> = new Map();

    // 1. Local Models
    registry.forEach(m => {
      resultsMap.set(m.name, { ...m, origin: 'LOCAL', is_downloaded: true });
    });

    // 2. Peer Models
    peers.forEach(peer => {
      if (peer.status === 'online' && peer.models) {
        peer.models.forEach(modelName => {
          if (!resultsMap.has(modelName)) {
            resultsMap.set(modelName, {
              name: modelName,
              engine: 'ollama',
              params: 'Mesh',
              context_window: 32768,
              vram_required_gb: 0,
              recommended_tasks: [],
              origin: peer.rpc_endpoint ? 'RPC' : 'NODE',
              nodeName: peer.name,
              is_downloaded: true
            });
          }
        });
      }
    });

    // 3. HF Results
    if (searchQuery.trim().length >= 3) {
      hfResults.forEach(m => {
        if (!resultsMap.has(m.name)) {
          resultsMap.set(m.name, { ...m, origin: 'HF', is_downloaded: false });
        }
      });
    }

    let results = Array.from(resultsMap.values());

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      results = results.filter(m => 
        m.name.toLowerCase().includes(q) || 
        (m.description || '').toLowerCase().includes(q)
      );
    }

    return results;
  }, [registry, peers, hfResults, searchQuery]);

  return (
    <>
      <AnimatePresence>
        {showDashboard && (
          <InfraDashboard onClose={() => setShowDashboard(false)} />
        )}
      </AnimatePresence>

      <div className="infra-panel">
        <div className="infra-panel__header">
          <Gauge size={16} className="text-purple" />
          <span>INFRASTRUCTURE HUB</span>
          <div className="mesh-indicator" title="Mesh Status">
            <span>{metrics?.vram_gb || 0}GB VRAM</span>
            <div className="mesh-divider" />
            <span>{metrics?.ram_used_gb || 0}G / {metrics?.ram_total_gb || 0}G RAM</span>
            <div className="mesh-divider" />
            <span>{metrics?.disk_used_gb?.toFixed(1) || 0}G / {metrics?.disk_total_gb?.toFixed(1) || 0}G DISK</span>
            <RefreshCcw size={12} className="ml-2 hover-rotate cursor-pointer" onClick={() => fetchData()} />
            <button 
              className="dashboard-launch-btn" 
              onClick={() => setShowDashboard(true)}
              title="Open Infrastructure Dashboard"
            >
              <Monitor size={12} />
            </button>
          </div>
        </div>

      <div className="infra-content">
        {/* MODEL ROUTING GRID */}
        <div className="infra-section">
          <div className="infra-section__title">MODEL ROUTING</div>
          <div className="routing-grid">
            {settings?.model_routes && Object.entries(settings.model_routes).map(([role, routeValue]) => {
              const Icon = routeIcons[role] || Info;
              const isDefault = ["Planning", "Coding", "Testing", "Researching", "Reviewing", "Vision", "Media", "Audio", "Chat"].includes(role);
              
              const modelStr = typeof routeValue === 'string' ? routeValue : routeValue.model;
              const isActive = engines.some(e => e.status === 'running' && modelStr.includes(e.name));

              return (
                <div key={role} className="routing-card">
                  {!isDefault && (
                    <div className="routing-card__delete" onClick={() => handleDeleteRoute(role)}>
                      <Trash2 size={12} />
                    </div>
                  )}
                  <div className="routing-card__header">
                    <div className="routing-card__icon">
                      <Icon size={14} />
                    </div>
                    <span className="routing-card__role">{role}</span>
                  </div>
                  
                  <div className="routing-card__controls">
                    <select 
                      className="routing-card__selector"
                      value={modelStr.split(':')[0]}
                      onChange={(e) => handleUpdateRoute(role, e.target.value)}
                    >
                      <option value="" disabled>Select model...</option>
                      {modelOptions.map(opt => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>

                    {/* Derived params display (non-editable) */}
                    {(() => {
                      if (!modelStr) return null;
                      const baseName = modelStr.split(':')[0];
                      
                      // Find best matching group in registry
                      const group = registry.find(m => m.name === baseName) || 
                                    registry.find(m => m.name.split(':')[0] === baseName);
                      
                      if (!group) return null;

                      // Find specific variant or fallback to group defaults
                      const variant = group.variants?.find(v => v.name === modelStr) || 
                                      group.variants?.find(v => v.name.split(':')[0] === baseName) ||
                                      group.variants?.[0];
                      
                      const derived = variant?.params || group.params || "";
                      
                      if (derived && derived !== "Unknown") {
                        return (
                          <div className="routing-card__params-badge">
                            {derived}
                          </div>
                        );
                      }
                      return null;
                    })()}
                  </div>

                  <div className={`routing-card__status ${isActive ? 'active' : ''}`}>
                    <div className="routing-card__status-dot" />
                    <span>{isActive ? 'SUBSTRATE ACTIVE' : 'STANDBY'}</span>
                  </div>
                </div>
              );
            })}
            
            <div className="routing-card routing-card__add" onClick={handleAddRoute}>
              <Plus size={24} className="opacity-20" />
              <span className="text-[10px] font-black opacity-40">ADD ROLE</span>
            </div>
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
                <div key={m.name} className="catalog-item" onClick={() => {
                  setSelectedModel(m);
                  if (m.variants && m.variants.length > 0) {
                    setSelectedVariant(m.variants[0].name);
                  } else {
                    setSelectedVariant("");
                  }
                }}>
                  <div className="catalog-main">
                    <div className="catalog-header">
                      <Cpu size={14} className="text-muted" />
                      <span className="catalog-name">{m.name.replace('registry.ollama.ai/library/', '').replace('library/', '').split(':')[0]}</span>
                      {m.params && m.params !== "Unknown" && <span className="catalog-tag">{m.params}</span>}
                      <span className={`catalog-badge origin-${(m as any).origin.toLowerCase()}`}>
                        {(m as any).origin === 'HF' ? 'HF' : 
                         (m as any).origin === 'RPC' ? 'MESH(RPC)' :
                         (m as any).origin === 'NODE' ? `NODE: ${(m as any).nodeName}` : 
                         'LOCAL'}
                      </span>
                      {(m as any).is_active && (
                        <span className="catalog-badge status-active">
                          <Activity size={8} /> ACTIVE
                        </span>
                      )}
                    </div>
                    <div className="catalog-meta">
                      <span>{m.size_gb ? `${m.size_gb.toFixed(1)}GB` : (m.vram_required_gb > 0 ? `${m.vram_required_gb}GB VRAM` : '0.0GB')}</span>
                      <RefreshCcw size={10} />
                      <span>{m.context_window / 1000}k ctx</span>
                      {!m.is_downloaded && ((m as any).origin === 'HF' || (m as any).origin === 'NODE') && (
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
                  <h3>{selectedModel.is_downloaded ? 'Model Diagnostics' : 'Deploy Model'}</h3>
                  <p className="infra-modal__subtitle">{selectedModel.name.replace('registry.ollama.ai/library/', '').replace('library/', '')}</p>
                </div>
              </div>
              <button className="infra-modal__close" onClick={() => setSelectedModel(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="infra-modal__content">
              {/* TECHNICAL SPECS */}
              <div className="infra-modal__stats">
                <div className="stat-box">
                  <span className="stat-label">VRAM REQ</span>
                  <span className="stat-value">
                    {(() => {
                      const v = selectedModel.variants?.find(v => v.name === selectedVariant);
                      const size = v?.size_gb || selectedModel.size_gb || 0;
                      return size > 0 ? `${Math.ceil(size * 1.2)}GB` : (selectedModel.vram_required_gb > 0 ? `${selectedModel.vram_required_gb}GB` : 'AUTO');
                    })()}
                  </span>
                </div>
                <div className="stat-box">
                  <span className="stat-label">CONTEXT</span>
                  <span className="stat-value">{selectedModel.context_window / 1024}k</span>
                </div>
                <div className="stat-box">
                  <span className="stat-label">DISK SIZE</span>
                  <span className="stat-value">
                    {(() => {
                      const v = selectedModel.variants?.find(v => v.name === selectedVariant);
                      return (v?.size_gb || selectedModel.size_gb || 0).toFixed(1) + 'GB';
                    })()}
                  </span>
                </div>
              </div>

              {/* SELECTION GRID */}
              <div className="infra-modal__section">
                <label>Configuration & Variants</label>
                <div className="config-grid">
                  {selectedModel.variants && selectedModel.variants.length > 0 ? (
                    <div className="config-item full-width">
                      <span>Available Versions (Quantization)</span>
                      <select 
                        className="settings-select" 
                        value={selectedVariant}
                        onChange={(e) => setSelectedVariant(e.target.value)}
                      >
                        {selectedModel.variants.map(v => (
                          <option key={v.name} value={v.name}>
                            {v.name} ({v.size_gb.toFixed(1)} GB)
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : (
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
                  )}
                  
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
                  <label>Architectural Context</label>
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
                  // If it's a community model from HF, we need 'repo:file'
                  if ((selectedModel as any).origin === 'HF' && selectedVariant) {
                    modelName = `${selectedModel.name}:${selectedVariant}`;
                  } else if (selectedModel.engine === 'ollama' && !modelName.includes(':')) {
                    // For Ollama library models, apply quantization tags
                    if (quantization.startsWith('4-bit')) modelName = `${modelName}:q4_K_M`;
                    else if (quantization.startsWith('8-bit')) modelName = `${modelName}:q8_0`;
                  }
                  await handlePullModel(selectedModel.engine, modelName);
                  setSelectedModel(null);
                }}
              >
                {loading ? "Initializing..." : (selectedModel.is_downloaded ? "Redeploy (Update)" : "Start Deployment")}
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
}
