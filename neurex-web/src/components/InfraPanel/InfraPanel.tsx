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
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 5000);
    return () => clearInterval(timer);
  }, [fetchData]);

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
      const res = await fetch(`${API_BASE}/api/infra/model/pull?engine=${engine}&model=${model}`, { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      toast.success(`Deploying ${model} to node...`);
      fetchData();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredRegistry = useMemo(() => {
    if (!searchQuery) return registry.slice(0, 10);
    return registry.filter(m => m.name.toLowerCase().includes(searchQuery.toLowerCase()));
  }, [registry, searchQuery]);

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
                  <button className="engine-btn"><X size={14} /></button>
                </div>
              </div>
            ))}
            <div className="engine-row missing">
              <div className="engine-main">
                <div className="engine-name">vLLM</div>
                <div className="engine-status">MISSING</div>
              </div>
              <button className="engine-install-btn">INSTALL</button>
            </div>
            <div className="engine-row missing">
              <div className="engine-main">
                <div className="engine-name">llama.cpp</div>
                <div className="engine-status">MISSING</div>
              </div>
              <button className="engine-install-btn">INSTALL</button>
            </div>
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
                  </div>
                  <div className="catalog-meta">
                    <span>{m.vram_required_gb}GB VRAM</span>
                    <RefreshCcw size={10} />
                    <span>128k ctx</span>
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
