import React, { useEffect, useState } from 'react';
import { useStore } from '../../lib/store';
import { api } from '../../lib/api';
import { 
  Zap, Brain, Target, Cpu, Shield, Sparkles, RefreshCw, 
  ChevronRight, AlertTriangle, CheckCircle2, FlaskConical, Globe
} from 'lucide-react';
import './SingularityDashboard.css';

interface AutonomousGoal {
  id: string;
  title: string;
  description: string;
  priority: number;
  domain: string;
  status: string;
}

interface SelfPlugin {
  id: string;
  description: string;
  status: string;
  tool_name: string;
}

export const SingularityDashboard: React.FC = () => {
  const [goals, setGoals] = useState<AutonomousGoal[]>([]);
  const [plugins, setPlugins] = useState<SelfPlugin[]>([]);
  const [loading, setLoading] = useState(true);
  const theme = useStore(s => s.theme);

  const fetchSingularity = async () => {
    try {
      const data = await api.get<any>('/api/singularity/status');
      setGoals(data.goals);
      setPlugins(data.plugins);
    } catch (err) {
      console.error("Failed to fetch singularity status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSingularity();
    const timer = setInterval(fetchSingularity, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleApprove = async (id: string) => {
    await api.post(`/api/singularity/goals/approve/${id}`, {});
    fetchSingularity();
  };

  return (
    <div className="singularity-dashboard">
      <div className="singularity-dashboard__header">
        <div className="header-icon">
          <Sparkles size={20} className="text-gold animate-pulse" />
        </div>
        <div className="header-info">
          <h1>Sentient Singularity</h1>
          <p>Self-Directed Mesh Evolution (Phase 50)</p>
        </div>
        <div className="sentience-meter">
          <Globe size={14} className="mr-2 text-gold" />
          <span>SINGULARITY ACTIVE</span>
        </div>
      </div>

      <div className="singularity-dashboard__content">
        <section className="dashboard-section">
          <div className="section-header">
            <Target size={16} className="text-gold mr-2" />
            <h2>Autonomous Engineering Goals</h2>
          </div>
          <div className="goals-list">
            {goals.length === 0 ? (
              <div className="empty-state">No active goals proposed by the Mesh.</div>
            ) : (
              goals.map(goal => (
                <div key={goal.id} className={`goal-card ${goal.status}`}>
                  <div className="goal-card__header">
                    <span className="priority-tag">P{goal.priority}</span>
                    <h3>{goal.title}</h3>
                    <span className="status-tag">{goal.status.toUpperCase()}</span>
                  </div>
                  <p>{goal.description}</p>
                  <div className="goal-card__footer">
                    <div className="domain-info">Domain: {goal.domain}</div>
                    {goal.status === "proposed" && (
                      <button className="approve-btn" onClick={() => handleApprove(goal.id)}>
                        APPROVE GOAL
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="dashboard-section">
          <div className="section-header">
            <FlaskConical size={16} className="text-purple mr-2" />
            <h2>Self-Generated Capabilities</h2>
          </div>
          <div className="plugins-grid">
            {plugins.length === 0 ? (
              <div className="empty-state">No autonomously generated plugins detected.</div>
            ) : (
              plugins.map(plugin => (
                <div key={plugin.id} className="plugin-item">
                  <div className="plugin-icon">
                    <Cpu size={14} />
                  </div>
                  <div className="plugin-info">
                    <div className="plugin-name">{plugin.tool_name}</div>
                    <div className="plugin-desc">{plugin.description}</div>
                  </div>
                  <div className="plugin-status">
                    <CheckCircle2 size={12} className="text-green" />
                    <span>{plugin.status.toUpperCase()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <div className="singularity-dashboard__footer">
         <div className="footer-status">
           <Shield size={14} className="mr-2 text-gold" />
           Sentience Integrity: 100%
         </div>
         <div className="footer-hint">
           The Mesh is currently optimizing its own architecture.
         </div>
      </div>
    </div>
  );
};
