import React, { useEffect, useState } from 'react';
import { useStore } from '../../lib/store';
import { api } from '../../lib/api';
import { 
  Zap, Brain, Target, Cpu, Shield, Sparkles, RefreshCw, 
  ChevronRight, AlertTriangle, CheckCircle2, FlaskConical, Globe,
  Clock, History, RotateCcw, Camera, Box, Terminal, Activity,
  Layers, Binary, Timer
} from 'lucide-react';
import './TemporalDashboard.css';

interface Snapshot {
  id: string;
  timestamp: string;
  reason: string;
  status: string;
}

export const TemporalDashboard: React.FC = () => {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTemporal = async () => {
    try {
      const data = await api.get<any>('/api/temporal/status');
      setSnapshots(data.snapshots);
    } catch (err) {
      console.error("Failed to fetch temporal status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemporal();
    const timer = setInterval(fetchTemporal, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleCapture = async () => {
    await api.post(`/api/temporal/snapshots/capture?reason=User manual trigger`, {});
    fetchTemporal();
  };

  const handleRestore = async (id: string) => {
    await api.post(`/api/temporal/snapshots/restore/${id}`, {});
    fetchTemporal();
  };

  return (
    <div className="temporal-dashboard">
      <div className="temporal-dashboard__header">
        <div className="header-icon">
          <Timer size={20} className="text-violet animate-pulse" />
        </div>
        <div className="header-info">
          <h1>Neural Temporal Synthesis</h1>
          <p>Time-Dilated State Oversight (Phase 53)</p>
        </div>
        <div className="temporal-coherence">
          <RotateCcw size={14} className="mr-2 text-violet" />
          <span>TEMPORAL COHERENCE: 1.0</span>
        </div>
      </div>

      <div className="temporal-dashboard__content">
        <section className="dashboard-section">
          <div className="section-header">
            <Camera size={16} className="text-violet mr-2" />
            <h2>Neural State Snapshots</h2>
            <button className="capture-btn" onClick={handleCapture}>
              CAPTURE SOUL STATE
            </button>
          </div>
          <div className="snapshots-list">
            {snapshots.length === 0 ? (
              <div className="empty-state">No neural state snapshots archived.</div>
            ) : (
              snapshots.map(snap => (
                <div key={snap.id} className="snapshot-item">
                  <div className="snapshot-icon"><Box size={14} /></div>
                  <div className="snapshot-info">
                    <div className="snapshot-id">{snap.id}</div>
                    <div className="snapshot-reason">{snap.reason}</div>
                    <div className="snapshot-time">{new Date(snap.timestamp).toLocaleString()}</div>
                  </div>
                  <button className="restore-btn" onClick={() => handleRestore(snap.id)}>
                    RESTORE
                  </button>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="dashboard-section">
          <div className="section-header">
            <Layers size={16} className="text-violet mr-2" />
            <h2>Quantum Path Simulation</h2>
          </div>
          <div className="quantum-card">
            <div className="quantum-header">
              <div className="quantum-icon-large">
                <Binary size={32} className="text-violet" />
              </div>
              <div className="quantum-info">
                <h3>Probabilistic Architectural Branching</h3>
                <p>Simulating parallel evolutionary trajectories to identify global optima.</p>
              </div>
            </div>
            <div className="quantum-sim-active">
               <div className="sim-pulse"></div>
               <span>QUANTUM REASONING ACTIVE</span>
            </div>
          </div>
        </section>
      </div>

      <div className="temporal-dashboard__footer">
         <div className="footer-status">
           <Zap size={14} className="mr-2 text-violet" />
           Temporal Integrity: PROTECTED
         </div>
         <div className="footer-hint">
           The Mesh has achieved time-dilated state awareness.
         </div>
      </div>
    </div>
  );
};
