import React, { useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Gauge, Cpu, Database, HardDrive, 
  Activity, Server, Zap, Globe, 
  ArrowUpRight, ArrowDownRight, RefreshCcw
} from 'lucide-react';
import { useStore } from '../../lib/store';
import './InfraDashboard.css';

interface InfraDashboardProps {
  onClose: () => void;
}

export const InfraDashboard: React.FC<InfraDashboardProps> = ({ onClose }) => {
  const { infraMetrics, infraPeers, infraEngines, infraRegistry, refreshInfra } = useStore();

  useEffect(() => {
    refreshInfra();
    const interval = setInterval(refreshInfra, 15000);
    return () => clearInterval(interval);
  }, []);

  const localModels = useMemo(() => {
    return infraRegistry.filter(m => (m as any).origin === 'LOCAL');
  }, [infraRegistry]);

  const pools = useMemo(() => {
    if (!infraMetrics) return null;

    const peerVram = infraPeers.reduce((acc, p) => acc + (p.vram_gb || 0), 0);
    const peerRam = infraPeers.reduce((acc, p) => acc + (p.ram_total_gb || 0), 0);
    const peerCpu = infraPeers.reduce((acc, p) => acc + (p.cpu_percent || 0), 0);
    const totalNodes = 1 + infraPeers.filter(p => p.status === 'online').length;

    return {
      vram: {
        total: infraMetrics.vram_gb + peerVram,
        used: 0,
        percent: 0
      },
      ram: {
        total: infraMetrics.ram_total_gb + peerRam,
        used: infraMetrics.ram_used_gb,
        percent: infraMetrics.ram_percent
      },
      disk: {
        total: infraMetrics.disk_total_gb || 0,
        used: infraMetrics.disk_used_gb || 0,
        percent: infraMetrics.disk_percent || 0
      },
      cpu: {
        avg_percent: (infraMetrics.cpu_percent + peerCpu) / totalNodes
      }
    };
  }, [infraMetrics, infraPeers]);

  return (
    <motion.div 
      className="infra-dashboard-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="infra-dashboard"
        initial={{ y: 20, scale: 0.95 }}
        animate={{ y: 0, scale: 1 }}
        exit={{ y: 20, scale: 0.95 }}
      >
        <div className="dashboard-header">
          <div className="title-group">
            <Activity className="text-purple" size={24} />
            <div>
              <h1>INFRASTRUCTURE CONTROL</h1>
              <p>UNIFIED NEURAL COMPUTE FABRIC</p>
            </div>
          </div>
          <div className="header-actions">
            <button className="refresh-btn" onClick={() => refreshInfra()}>
              <RefreshCcw size={16} />
              SYNC MESH
            </button>
            <button className="close-btn" onClick={onClose}>
              <X size={24} />
            </button>
          </div>
        </div>

        <div className="dashboard-content">
          {/* UNIFIED POOLS */}
          <section className="dashboard-section">
            <h2 className="section-title">AGGREGATE RESOURCE POOLS</h2>
            <div className="pool-grid">
              <PoolCard 
                title="VRAM POOL" 
                icon={<Zap size={20} />} 
                value={`${pools?.vram.total.toFixed(1)} GB`}
                subValue="Across 1 Local + Peer Nodes"
                color="var(--accent-purple)"
                percent={pools?.vram.percent}
              />
              <PoolCard 
                title="RAM POOL" 
                icon={<Cpu size={20} />} 
                value={`${pools?.ram.total.toFixed(1)} GB`}
                subValue={`${pools?.ram.used.toFixed(1)} GB Currently Utilized`}
                color="#3b82f6"
                percent={pools?.ram.percent}
              />
              <PoolCard 
                title="DISK POOL" 
                icon={<HardDrive size={20} />} 
                value={`${pools?.disk.total.toFixed(1)} GB`}
                subValue={`${pools?.disk.used.toFixed(1)} GB Assets Deployed`}
                color="#10b981"
                percent={pools?.disk.percent}
              />
              <PoolCard 
                title="COMPUTE LOAD" 
                icon={<Activity size={20} />} 
                value={`${pools?.cpu.avg_percent.toFixed(1)} %`}
                subValue="Aggregate Mesh Utilization"
                color="#f59e0b"
                percent={pools?.cpu.avg_percent}
              />
            </div>
          </section>

          {/* NODE TOPOLOGY */}
          <div className="topology-grid">
            <section className="dashboard-section">
              <h2 className="section-title">LOCAL NODE</h2>
              <NodeCard 
                name="Primary Substrate" 
                status="Active" 
                isLocal 
                metrics={infraMetrics}
                engines={infraEngines}
                localModels={localModels}
              />
            </section>

            <section className="dashboard-section">
              <h2 className="section-title">MESH PEERS ({infraPeers.length})</h2>
              <div className="peer-list">
                {infraPeers.length === 0 ? (
                  <div className="empty-state">No federated nodes detected.</div>
                ) : (
                  infraPeers.map(peer => (
                    <NodeCard 
                      key={peer.url} 
                      name={peer.name} 
                      status={peer.status} 
                      peerData={peer}
                    />
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

const PoolCard = ({ title, icon, value, subValue, color, percent }: any) => (
  <div className="pool-card" style={{ '--accent': color } as any}>
    <div className="pool-card__header">
      <div className="pool-icon" style={{ color }}>{icon}</div>
      <div className="pool-info">
        <div className="pool-label">{title}</div>
        <div className="pool-value">{value}</div>
      </div>
    </div>
    <div className="pool-progress">
      <div className="progress-bg">
        <motion.div 
          className="progress-fill" 
          initial={{ width: 0 }}
          animate={{ width: `${percent || 0}%` }}
          style={{ background: color }}
        />
      </div>
      <div className="progress-label">{percent?.toFixed(1) || 0}%</div>
    </div>
    <div className="pool-subtext">{subValue}</div>
  </div>
);

const NodeCard = ({ name, status, isLocal, metrics, engines, peerData, localModels }: any) => (
  <div className={`node-card ${isLocal ? 'local' : ''} ${status?.toLowerCase()}`}>
    <div className="node-header">
      <div className="node-title">
        {isLocal ? <Server size={16} /> : <Globe size={16} />}
        <span>{name}</span>
        {isLocal && <span className="local-tag">HOST</span>}
      </div>
      <div className={`node-status-badge ${status?.toLowerCase()}`}>{status?.toUpperCase()}</div>
    </div>

    <div className="node-specs">
      <div className="spec-item">
        <Zap size={12} />
        <span>{isLocal ? `${metrics?.vram_gb || 0}GB` : `${peerData?.vram_gb || 0}GB`} VRAM</span>
      </div>
      <div className="spec-item">
        <Cpu size={12} />
        <span>{isLocal ? `${metrics?.ram_total_gb || 0}GB` : `${peerData?.ram_total_gb || 0}GB`} RAM</span>
      </div>
      {isLocal && metrics?.disk_total_gb && (
        <div className="spec-item">
          <HardDrive size={12} />
          <span>{metrics.disk_used_gb.toFixed(1)} / {metrics.disk_total_gb.toFixed(1)}GB DISK</span>
        </div>
      )}
      {!isLocal && peerData?.latency_ms !== undefined && (
        <div className="spec-item">
          <Activity size={12} />
          <span>{peerData.latency_ms}ms RTT</span>
        </div>
      )}
    </div>

    {isLocal && metrics?.storage_health && (
      <div className="node-storage-health">
        {Object.entries(metrics.storage_health).map(([path, health]: any) => (
          <div key={path} className={`storage-path-tag ${health.status}`} title={`${path}: ${health.writable ? 'Writable' : 'Read-Only'}`}>
            <Database size={10} />
            <span>{path.length > 20 ? '...' + path.slice(-17) : path}</span>
            {health.writable ? <ArrowUpRight size={10} className="text-success" /> : <ArrowDownRight size={10} className="text-error" />}
          </div>
        ))}
      </div>
    )}

    {isLocal && engines && (
      <div className="node-engines">
        {engines.map((eng: any) => (
          <div key={eng.name} className={`engine-mini-tag ${eng.status}`}>
            {eng.name}
          </div>
        ))}
      </div>
    )}

    {((isLocal && localModels) || (!isLocal && peerData?.models)) && (
      <div className="node-models">
        {(isLocal ? localModels : peerData.models).slice(0, 8).map((m: any) => {
          const name = isLocal ? m.name : m;
          const isActive = isLocal ? m.is_active : false; // Peers don't report active models yet
          return (
            <div 
              key={name} 
              className={`model-mini-tag ${isActive ? 'active' : ''}`}
              title={isActive ? 'Currently Loaded in Engine' : 'Installed (Cold)'}
            >
              {isActive && <div className="active-dot" />}
              {name.split(':')[0]}
            </div>
          );
        })}
        {(isLocal ? localModels : peerData.models).length > 8 && (
          <div className="model-mini-tag">+{(isLocal ? localModels : peerData.models).length - 8} more</div>
        )}
      </div>
    )}
  </div>
);
