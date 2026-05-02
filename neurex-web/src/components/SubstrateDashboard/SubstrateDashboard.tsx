import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Database, 
  Cpu, 
  ShieldCheck, 
  Zap, 
  AlertCircle, 
  RefreshCw, 
  CheckCircle2, 
  Settings2,
  HardDrive
} from 'lucide-react';
import { API_BASE } from '../../lib/config';

interface SubstrateStatus {
  docker: {
    active: boolean;
    version: string | null;
    gpu_acceleration: boolean;
  };
  wasm: {
    active: boolean;
    coreutils_present: boolean;
  };
  hardware: {
    os: string;
    arch: string;
    cpu: string;
    ram_gb: number;
  };
}

export const SubstrateDashboard: React.FC = () => {
  const [status, setStatus] = useState<SubstrateStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/substrate/status`);
      if (!res.ok) throw new Error("Substrate API unreachable");
      const data = await res.json();
      setStatus(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-full text-white/40">
        <RefreshCw className="animate-spin mb-4" size={32} />
        <p className="text-sm font-medium">Synchronizing Substrate...</p>
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto custom-scrollbar bg-void/50 backdrop-blur-xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
            <ShieldCheck className="text-purple-400" />
            Hermetic Substrate
          </h2>
          <p className="text-xs text-white/40 uppercase tracking-widest font-mono">Phase 54: Universal Execution Plane</p>
        </div>
        <button 
          onClick={fetchStatus}
          className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/60 hover:text-white"
        >
          <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="grid gap-6">
        {/* Hardware Status */}
        <StatusCard 
          title="Hardware Environment"
          icon={<Cpu className="text-blue-400" />}
          active={true}
        >
          <div className="grid gap-3">
            <Metric label="Architecture" value={`${status?.hardware.os} / ${status?.hardware.arch}`} />
            <Metric label="CPU" value={status?.hardware.cpu || "Unknown"} />
            <Metric label="Memory" value={`${status?.hardware.ram_gb} MB Total`} />
          </div>
        </StatusCard>

        {/* Tier 1: Docker */}
        <StatusCard 
          title="Tier 1: Performance (Docker)"
          icon={<Zap className={status?.docker.active ? "text-yellow-400" : "text-white/20"} />}
          active={status?.docker.active || false}
          subtitle={status?.docker.version || "Service Not Detected"}
        >
          <div className="grid gap-3">
            <StatusToggle 
              label="GPU Acceleration" 
              active={status?.docker.gpu_acceleration || false} 
              warning={!status?.docker.gpu_acceleration && status?.docker.active ? "Toolkit Missing" : undefined}
            />
            <StatusToggle 
              label="Container Runtime" 
              active={status?.docker.active || false} 
            />
          </div>
        </StatusCard>

        {/* Tier 2: WASM */}
        <StatusCard 
          title="Tier 2: Portability (WASM)"
          icon={<Database className="text-cyan-400" />}
          active={status?.wasm.active || false}
          subtitle="Wasmtime 29.0 Engine"
        >
          <div className="grid gap-3">
            <StatusToggle 
              label="WASM Execution Bridge" 
              active={status?.wasm.active || false} 
            />
            <StatusToggle 
              label="Coreutils Payload" 
              active={status?.wasm.coreutils_present || false} 
              warning={!status?.wasm.coreutils_present ? "Bootstrap Required" : undefined}
            />
          </div>
        </StatusCard>

        {/* Tier 3: Native */}
        <StatusCard 
          title="Tier 3: Reliability (Native)"
          icon={<HardDrive className="text-green-400" />}
          active={true}
          subtitle="Jailed Filesystem Host"
        >
          <div className="grid gap-3">
            <StatusToggle label="Substrate Fallback" active={true} />
            <StatusToggle label="Workspace Jailing" active={true} />
          </div>
        </StatusCard>
      </div>

      {error && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400"
        >
          <AlertCircle size={20} />
          <p className="text-sm">{error}</p>
        </motion.div>
      )}
    </div>
  );
};

const StatusCard: React.FC<{ 
  title: string; 
  icon: React.ReactNode; 
  active: boolean; 
  subtitle?: string;
  children: React.ReactNode 
}> = ({ title, icon, active, subtitle, children }) => (
  <div className={`p-5 rounded-2xl border transition-all ${active ? 'bg-white/5 border-white/10' : 'bg-white/2 border-white/5 opacity-60'}`}>
    <div className="flex items-start justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${active ? 'bg-white/5' : 'bg-white/2'}`}>
          {icon}
        </div>
        <div>
          <h3 className="font-semibold text-white">{title}</h3>
          {subtitle && <p className="text-[10px] text-white/40 font-mono uppercase tracking-tighter">{subtitle}</p>}
        </div>
      </div>
      {active ? (
        <CheckCircle2 className="text-green-500" size={16} />
      ) : (
        <AlertCircle className="text-red-500" size={16} />
      )}
    </div>
    {children}
  </div>
);

const Metric: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="flex items-center justify-between text-[11px]">
    <span className="text-white/40 uppercase tracking-wider">{label}</span>
    <span className="text-white font-mono">{value}</span>
  </div>
);

const StatusToggle: React.FC<{ label: string; active: boolean; warning?: string }> = ({ label, active, warning }) => (
  <div className="flex items-center justify-between text-[11px]">
    <span className="text-white/60">{label}</span>
    <div className="flex items-center gap-2">
      {warning && <span className="text-[9px] px-1.5 py-0.5 bg-yellow-500/10 text-yellow-500 rounded border border-yellow-500/20 uppercase font-bold">{warning}</span>}
      <div className={`w-2 h-2 rounded-full ${active ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-red-500'}`} />
    </div>
  </div>
);
