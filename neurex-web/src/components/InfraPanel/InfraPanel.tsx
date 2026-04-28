// neurex-web/src/components/InfraPanel/InfraPanel.tsx
"use client";

import { useState, useEffect, useLayoutEffect, useRef, useMemo } from "react";
import { 
  Play, Square, RefreshCcw, Cpu, Zap, Database, ExternalLink, 
  Code, Network, Search, Brain, FileJson, Video, Image, AudioLines, 
  Loader2, Info, Trash2, AlertTriangle, Thermometer, Gauge 
} from "lucide-react";
import "./InfraPanel.css";
import { useStore } from "../../lib/store";
import { ModelProfile, InfraEngine, MeshPeer } from "../../lib/types";
import toast from "react-hot-toast";

import { API_BASE } from "../../lib/config";

const getSpecialtyTag = (m: ModelProfile) => {
  const tasks = (m.recommended_tasks || []).join(" ").toLowerCase();
  if (tasks.includes("coding") || tasks.includes("code")) return "(coding)";
  if (tasks.includes("logic") || tasks.includes("thinking") || tasks.includes("deep_thinking")) return "(thinking)";
  return "(general)";
};

const formatModelName = (name: string, m: ModelProfile, simplify: boolean) => {
  let displayName = name.split(':').shift() || name;
  if (simplify) {
    displayName = displayName.replace(/\s*\([^)]*\)/g, "").trim();
    displayName += ` ${getSpecialtyTag(m)}`;
  }
  return displayName;
};

export function InfraPanel({ onExpand, currentSize }: { onExpand: (s: number) => void, currentSize: number }) {
  const engines = useStore(s => s.infraEngines);
  const metrics = useStore(s => s.infraMetrics);
  const registry = useStore(s => s.infraRegistry);
  const skills = useStore(s => s.infraSkills);
  const peers = useStore(s => s.infraPeers);
  const fetchData = useStore(s => s.refreshInfra);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ModelProfile[]>([]);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);
  
  const [selectedModel, setSelectedModel] = useState<ModelProfile | null>(null);
  const setGlobalModalOpen = useStore(s => s.setModalOpen);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 5000);
    return () => clearInterval(timer);
  }, [fetchData]);

  const bestInClass = useMemo(() => {
    const roles = { "Thinking": "thinking", "Coding": "coding" };
    const results: Record<string, ModelProfile | undefined> = {};
    Object.entries(roles).forEach(([label, cap]) => {
      results[label] = registry.find(m => m.recommended_tasks?.some(t => t.toLowerCase().includes(cap)));
    });
    return results;
  }, [registry]);

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

  return (
    <div className="infra-panel">
      <div className="infra-panel__header">
        <Gauge size={16} className="text-purple" />
        <span>INFRASTRUCTURE HUB</span>
        <div className="mesh-indicator" title="Mesh Status">
          <div className="swarm-pulse swarm-pulse--active" />
          <span>MESH ACTIVE</span>
        </div>
      </div>

      {/* TELEMETRY DASHBOARD */}
      <div className="telemetry-dashboard">
        <div className="telemetry-card">
          <div className="telemetry-card__header">
            <Zap size={12} /> <span>VRAM UTILIZATION</span>
          </div>
          <div className="telemetry-gauge">
            <div className="telemetry-gauge__bar" style={{ width: `${(metrics?.vram_gb || 0) * 4}%` }} />
            <span className="telemetry-gauge__val">{metrics?.vram_gb || 0} GB</span>
          </div>
        </div>
        <div className="telemetry-card">
          <div className="telemetry-card__header">
            <Thermometer size={12} /> <span>NODE LOAD</span>
          </div>
          <div className="telemetry-gauge">
            <div className="telemetry-gauge__bar telemetry-gauge__bar--load" style={{ width: '15%' }} />
            <span className="telemetry-gauge__val">STABLE</span>
          </div>
        </div>
      </div>

      <div className="infra-content">
        {/* COMPUTE NODES */}
        <div className="infra-section">
          <div className="infra-section__title">
            <Cpu size={12} /> <span>COMPUTE ENGINES</span>
          </div>
          <div className="engine-list">
            {engines.map((e) => (
              <div key={e.name} className={`engine-card ${e.status === 'running' ? 'active' : ''}`}>
                <div className="engine-icon"><Zap size={14} /></div>
                <div className="engine-info">
                  <div className="engine-name">{e.name.toUpperCase()}</div>
                  <div className="engine-status">{e.status.toUpperCase()}</div>
                </div>
                <button className="engine-action" disabled={loading}>
                  {e.status === 'running' ? <Square size={12} /> : <Play size={12} />}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* ACTIVE DEPLOYMENTS */}
        <div className="infra-section">
          <div className="infra-section__title">
            <RefreshCcw size={12} /> <span>ACTIVE INTELLIGENCE</span>
          </div>
          <div className="intelligence-grid">
            {Object.entries(bestInClass).map(([role, model]) => model && (
              <div key={role} className="intel-card">
                <div className="intel-role">{role}</div>
                <div className="intel-model">{model.name.split(':')[0]}</div>
                <div className="intel-specs">{model.params} • {model.vram_required_gb}G</div>
                <div className="intel-status">
                  {model.is_downloaded ? (
                    <span className="text-green">ONLINE</span>
                  ) : (
                    <button className="intel-deploy-btn" onClick={() => handlePullModel(model.engine, model.name)}>DEPLOY</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* NETWORK MESH */}
        <div className="infra-section">
          <div className="infra-section__title">
            <Network size={12} /> <span>HIVE MESH PEERS</span>
          </div>
          <div className="mesh-list">
            {peers.length === 0 ? (
              <div className="mesh-empty">Scanning for local swarm nodes...</div>
            ) : (
              peers.map((p) => (
                <div key={p.url} className="mesh-peer">
                  <div className="peer-avatar">{p.name[0]}</div>
                  <div className="peer-info">
                    <div className="peer-name">{p.name}</div>
                    <div className="peer-url">{p.url}</div>
                  </div>
                  <div className="peer-vram">{p.vram_gb}G</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
