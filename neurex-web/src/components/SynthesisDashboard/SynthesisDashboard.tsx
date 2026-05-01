import React, { useEffect, useState } from 'react';
import { useStore } from '../../lib/store';
import { api } from '../../lib/api';
import { 
  Zap, Brain, Target, Cpu, Shield, Sparkles, RefreshCw, 
  ChevronRight, AlertTriangle, CheckCircle2, FlaskConical, Globe,
  Box, Terminal, Vote, Activity
} from 'lucide-react';
import './SynthesisDashboard.css';

interface Inception {
  name: string;
  path: string;
}

interface Optimization {
  id: string;
  target: string;
  reason: string;
  status: string;
}

interface Proposal {
  id: string;
  title: string;
  description: string;
  status: string;
  votes: {
    total: number;
    support: number;
  };
}

export const SynthesisDashboard: React.FC = () => {
  const [inceptions, setInceptions] = useState<Inception[]>([]);
  const [optimizations, setOptimizations] = useState<Optimization[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSynthesis = async () => {
    try {
      const data = await api.get<any>('/api/synthesis/status');
      setInceptions(data.inceptions);
      setOptimizations(data.optimizations);
      setProposals(data.proposals);
    } catch (err) {
      console.error("Failed to fetch synthesis status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSynthesis();
    const timer = setInterval(fetchSynthesis, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleVote = async (id: string, support: boolean) => {
    await api.post(`/api/synthesis/proposals/vote/${id}?support=${support}`, {});
    fetchSynthesis();
  };

  const handleApplyOpt = async (id: string) => {
    await api.post(`/api/synthesis/optimizations/apply/${id}`, {});
    fetchSynthesis();
  };

  return (
    <div className="synthesis-dashboard">
      <div className="synthesis-dashboard__header">
        <div className="header-icon">
          <Activity size={20} className="text-cyan animate-pulse" />
        </div>
        <div className="header-info">
          <h1>Neural Self-Synthesis</h1>
          <p>Recursive Substrate Improvement (Phase 51)</p>
        </div>
        <div className="synthesis-integrity">
          <Shield size={14} className="mr-2 text-cyan" />
          <span>SYNTHESIS ACTIVE</span>
        </div>
      </div>

      <div className="synthesis-dashboard__content">
        <section className="dashboard-section">
          <div className="section-header">
            <Box size={16} className="text-cyan mr-2" />
            <h2>Autonomous Inceptions</h2>
          </div>
          <div className="inceptions-list">
            {inceptions.length === 0 ? (
              <div className="empty-state">No sub-projects have been autonomously incepted.</div>
            ) : (
              inceptions.map(inc => (
                <div key={inc.name} className="inception-item">
                  <div className="inception-icon"><Terminal size={14} /></div>
                  <div className="inception-info">
                    <div className="inception-name">{inc.name}</div>
                    <div className="inception-path">{inc.path}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="dashboard-section">
          <div className="section-header">
            <RefreshCw size={16} className="text-cyan mr-2" />
            <h2>Recursive Self-Optimizations</h2>
          </div>
          <div className="optimizations-list">
            {optimizations.length === 0 ? (
              <div className="empty-state">No core optimizations currently proposed.</div>
            ) : (
              optimizations.map(opt => (
                <div key={opt.id} className={`opt-card ${opt.status}`}>
                  <div className="opt-card__header">
                    <h3>Refactor: {opt.target}</h3>
                    <span className="status-tag">{opt.status.toUpperCase()}</span>
                  </div>
                  <p>{opt.reason}</p>
                  {opt.status === "proposed" && (
                    <button className="apply-btn" onClick={() => handleApplyOpt(opt.id)}>
                      APPLY CORE REFACTOR
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </section>

        <section className="dashboard-section">
          <div className="section-header">
            <Vote size={16} className="text-gold mr-2" />
            <h2>Neural Governance DAO</h2>
          </div>
          <div className="proposals-list">
            {proposals.length === 0 ? (
              <div className="empty-state">No active governance proposals.</div>
            ) : (
              proposals.map(p => (
                <div key={p.id} className={`proposal-card ${p.status}`}>
                  <div className="proposal-card__header">
                    <h3>{p.title}</h3>
                    <div className="vote-stats">
                      {p.votes.support} / {p.votes.total} VOTES
                    </div>
                  </div>
                  <p>{p.description}</p>
                  <div className="proposal-card__footer">
                    <span className="status-tag">{p.status.toUpperCase()}</span>
                    {p.status === "voting" && (
                      <div className="vote-btns">
                        <button className="vote-btn-yes" onClick={() => handleVote(p.id, true)}>SUPPORT</button>
                        <button className="vote-btn-no" onClick={() => handleVote(p.id, false)}>REJECT</button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <div className="synthesis-dashboard__footer">
         <div className="footer-status">
           <Zap size={14} className="mr-2 text-cyan" />
           Substrate Coherence: 100%
         </div>
         <div className="footer-hint">
           The Mesh is autonomously optimizing its own soul.
         </div>
      </div>
    </div>
  );
};
