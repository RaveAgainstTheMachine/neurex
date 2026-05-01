import React, { useEffect, useState } from 'react';
import { useStore } from '../../lib/store';
import { api } from '../../lib/api';
import { 
  Zap, Brain, GitMerge, Activity, RefreshCw, Layers, Shield, Cpu, 
  ChevronRight, TrendingUp, Sparkles, Database
} from 'lucide-react';
import './EvolutionPanel.css';

interface NeuralAdapter {
  domain: string;
  adapter_id: string;
  version: number;
  fitness: number;
  rank: number;
  alpha: number;
  modules: string[];
}

export const EvolutionPanel: React.FC = () => {
  const [adapters, setAdapters] = useState<NeuralAdapter[]>([]);
  const [loading, setLoading] = useState(true);
  const theme = useStore(s => s.theme);

  const fetchEvolution = async () => {
    try {
      const data = await api.get<any>('/api/evolution/status');
      setAdapters(data.adapters);
    } catch (err) {
      console.error("Failed to fetch evolution status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvolution();
    const timer = setInterval(fetchEvolution, 5000);
    return () => clearInterval(timer);
  }, []);

  const handleReset = async (domain: string) => {
    if (window.confirm(`Reset neural adapter for ${domain}?`)) {
      await api.post(`/api/evolution/reset/${domain}`, {});
      fetchEvolution();
    }
  };

  return (
    <div className="evolution-panel">
      <div className="evolution-panel__header">
        <div className="header-icon">
          <Brain size={20} className="text-purple animate-pulse" />
        </div>
        <div className="header-info">
          <h1>Neural Evolution</h1>
          <p>Autonomous Adapter Specialization (Phase 48)</p>
        </div>
        <button onClick={fetchEvolution} className="refresh-btn">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="evolution-panel__content">
        {adapters.length === 0 ? (
          <div className="empty-state">
            <Activity size={48} className="text-white/10 mb-4" />
            <p>No active neural evolutions detected.</p>
            <span className="text-xs text-white/40">Complete missions to trigger adapter specialization.</span>
          </div>
        ) : (
          <div className="adapter-grid">
            {adapters.map(adapter => (
              <div key={adapter.domain} className="adapter-card">
                <div className="adapter-card__top">
                  <div className="domain-pill">
                    <Database size={12} className="mr-1" />
                    {adapter.domain}
                  </div>
                  <div className="version-pill">v{adapter.version}</div>
                </div>

                <div className="adapter-card__body">
                  <div className="stat-group">
                    <div className="stat-label">Fitness Score</div>
                    <div className="fitness-bar">
                      <div 
                        className="fitness-fill" 
                        style={{ width: `${Math.min(100, adapter.fitness)}%` }}
                      />
                      <span className="fitness-val">{adapter.fitness} / 100</span>
                    </div>
                  </div>

                  <div className="spec-grid">
                    <div className="spec-item">
                      <Layers size={14} className="text-purple/60" />
                      <div className="spec-info">
                        <span className="label">Rank</span>
                        <span className="value">{adapter.rank}</span>
                      </div>
                    </div>
                    <div className="spec-item">
                      <Zap size={14} className="text-purple/60" />
                      <div className="spec-info">
                        <span className="label">Alpha</span>
                        <span className="value">{adapter.alpha}</span>
                      </div>
                    </div>
                  </div>

                  <div className="modules-list">
                    <div className="modules-label">Target Modules:</div>
                    <div className="modules-chips">
                      {adapter.modules.map(m => (
                        <span key={m} className="module-chip">{m}</span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="adapter-card__footer">
                   <button className="action-btn" onClick={() => handleReset(adapter.domain)}>
                     RESET EVOLUTION
                   </button>
                   <div className="status-indicator">
                     <span className="dot animate-ping" />
                     LIVE MUTATION
                   </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="evolution-panel__footer">
        <div className="footer-metric">
          <TrendingUp size={14} className="mr-2 text-green" />
          <span>Collective Mesh Intelligence: +14.2%</span>
        </div>
        <div className="footer-hint">
          <Shield size={12} className="mr-1" />
          Quorum Aggregation Active
        </div>
      </div>
    </div>
  );
};
