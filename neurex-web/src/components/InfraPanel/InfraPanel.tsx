// neurex-web/src/components/InfraPanel/InfraPanel.tsx
"use client";

import { useState, useEffect, useMemo } from "react";
import { 
  Play, Square, RefreshCcw, Cpu, Zap, Search, 
  Brain, Braces, Video, AudioLines, 
  Thermometer, Gauge, Eye, X
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
  const peers = useStore(s => s.infraPeers);
  const fetchData = useStore(s => s.refreshInfra);

  const [searchQuery, setSearchQuery] = useState("");
  const [hfResults, setHfResults] = useState<ModelProfile[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 5000);
    onExpand(35);
    return () => {
      clearInterval(timer);
      onExpand(18);
    };
  }, [fetchData, onExpand]);

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
    { id: 'thinking', role: 'THINKING', model: 'deepseek-r1 (thinking)', specs: '32B • 20G VRAM', icon: Brain },
    { id: 'coding', role: 'CODING', model: 'qwen2.5-coder (coding)', specs: '32B • 20G VRAM', icon: Braces },
    { id: 'vision', role: 'VISION', model: 'llama3.2-vision (vision)', specs: '11B • 8.5G VRAM', icon: Eye },
    { id: 'media', role: 'MEDIA', model: 'llama3.2-vision (vision)', specs: '11B • 8.5G VRAM', icon: Image },
    { id: 'video', role: 'VIDEO', model: 'ltx-video (video)', specs: 'Multi-Modal • 24G VRAM', icon: Video },
    { id: 'audio', role: 'AUDIO', model: 'whisper-large-v3-turbo (transcribe)', specs: '1.5B • 4G VRAM', icon: AudioLines },
  ];

  const handlePullModel = async (engine: string, model: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/infra/model/pull?engine=${engine}&model=${model}`, { 
        method: "POST",
        headers: { "Authorization": `Bearer ${useStore.getState().token}` }
      });
      if (!res.ok) throw new Error(await res.text());
      toast.success(`Deploying ${model} to node...`);
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
          <span>24GB</span>
          <div className="mesh-divider" />
          <span>47.7G FREE</span>
          <RefreshCcw size={12} className="ml-2 hover-rotate cursor-pointer" onClick={() => fetchData()} />
        </div>
      </div>

      <div className="infra-content">
        {/* AGENT RECOMMENDATIONS */}
        <div className="infra-section">
          <div className="infra-section__title">AGENT RECOMMENDATIONS</div>
          <div className="recommendation-grid">
            {recommendations.map((rec) => (
              <div key={rec.id} className="rec-card">
                <div className="rec-header">
                  <span className="rec-role">{rec.role}</span>
                  <span className="rec-specs">{rec.specs}</span>
                </div>
                <div className="rec-model">{rec.model}</div>
                <button className="rec-deploy-btn" onClick={() => handlePullModel('ollama', rec.model.split(' ')[0])}>
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
                  <div className="engine-status">{e.status.toUpperCase()}</div>
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
            {filteredRegistry.map((m) => (
              <div key={m.name} className="catalog-item">
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
                        onClick={() => handlePullModel(m.engine, m.name)}
                      >
                        DEPLOY
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
