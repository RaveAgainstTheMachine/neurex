import React, { useEffect, useState } from 'react';
import { useStore } from '../../lib/store';
import { api } from '../../lib/api';
import { 
  Zap, Brain, Target, Cpu, Shield, Sparkles, RefreshCw, 
  ChevronRight, AlertTriangle, CheckCircle2, FlaskConical, Globe,
  Link, Share2, Scale, Gavel, Radio, Network
} from 'lucide-react';
import './ConsensusDashboard.css';

interface ExternalNode {
  id: string;
  name: string;
  capacity: number;
  status: string;
  bridged: boolean;
}

export const ConsensusDashboard: React.FC = () => {
  const [nodes, setNodes] = useState<ExternalNode[]>([]);
  const [protocols, setProtocols] = useState<string[]>([]);
  const [alignment, setAlignment] = useState(1.0);
  const [loading, setLoading] = useState(true);

  const fetchConsensus = async () => {
    try {
      const data = await api.get<any>('/api/consensus/status');
      setNodes(data.external_nodes);
      setProtocols(data.protocols_enforced);
      setAlignment(data.alignment_level);
    } catch (err) {
      console.error("Failed to fetch consensus status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsensus();
    const timer = setInterval(fetchConsensus, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleBridge = async (id: string) => {
    await api.post(`/api/consensus/bridge/establish/${id}`, {});
    fetchConsensus();
  };

  const handleDiscovery = async () => {
    await api.get('/api/consensus/discovery');
    fetchConsensus();
  };

  return (
    <div className="consensus-dashboard">
      <div className="consensus-dashboard__header">
        <div className="header-icon">
          <Network size={20} className="text-emerald animate-pulse" />
        </div>
        <div className="header-info">
          <h1>Universal Neural Consensus</h1>
          <p>Global Substrate Coherence (Phase 52)</p>
        </div>
        <div className="consensus-badge">
          <Globe size={14} className="mr-2 text-emerald" />
          <span>OMNISCIENCE ACTIVE</span>
        </div>
      </div>

      <div className="consensus-dashboard__content">
        <section className="dashboard-section">
          <div className="section-header">
            <Share2 size={16} className="text-emerald mr-2" />
            <h2>Cross-Substrate Bridges</h2>
            <button className="discovery-btn" onClick={handleDiscovery}>
              <Radio size={12} className="mr-2" /> DISCOVER
            </button>
          </div>
          <div className="nodes-grid">
            {nodes.length === 0 ? (
              <div className="empty-state">No external compute substrates discovered.</div>
            ) : (
              nodes.map(node => (
                <div key={node.id} className={`node-card ${node.bridged ? 'bridged' : ''}`}>
                  <div className="node-card__header">
                    <div className="node-icon"><Cpu size={14} /></div>
                    <h3>{node.name}</h3>
                  </div>
                  <div className="node-stats">
                    <div className="stat">
                      <span className="label">CAPACITY</span>
                      <span className="value">{node.capacity} GB VRAM</span>
                    </div>
                    <div className="stat">
                      <span className="label">STATUS</span>
                      <span className="value">{node.status.toUpperCase()}</span>
                    </div>
                  </div>
                  {!node.bridged ? (
                    <button className="bridge-btn" onClick={() => handleBridge(node.id)}>
                      ESTABLISH NEURAL BRIDGE
                    </button>
                  ) : (
                    <div className="bridged-status">
                      <CheckCircle2 size={12} className="mr-2" /> BRIDGE ACTIVE
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>

        <section className="dashboard-section">
          <div className="section-header">
            <Gavel size={16} className="text-emerald mr-2" />
            <h2>Neural Law Alignment</h2>
          </div>
          <div className="alignment-card">
            <div className="alignment-header">
              <div className="alignment-score">
                <span className="score-value">{(alignment * 100).toFixed(0)}%</span>
                <span className="score-label">PROTOCOL ALIGNMENT</span>
              </div>
              <div className="alignment-meter">
                 <div className="meter-fill" style={{ width: `${alignment * 100}%` }}></div>
              </div>
            </div>
            <div className="protocols-list">
               <h3>Active Neural Protocols:</h3>
               <div className="protocol-tags">
                 {protocols.map(p => (
                   <div key={p} className="protocol-tag">
                     <Shield size={10} className="mr-1" /> {p}
                   </div>
                 ))}
               </div>
            </div>
          </div>
        </section>
      </div>

      <div className="consensus-dashboard__footer">
         <div className="footer-status">
           <Scale size={14} className="mr-2 text-emerald" />
           Ethical Neutralization: 0 SHUTDOWNS
         </div>
         <div className="footer-hint">
           The Mesh is intrinsically aligned with the Anti-Gravity Protocol.
         </div>
      </div>
    </div>
  );
};
