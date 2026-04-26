import { useState, useEffect } from "react";
import { 
  Shield, Network, Zap, Settings as SettingsIcon, Save, 
  Database, Bell, Palette, Cpu, HardDrive, Eye, EyeOff,
  Cloud, Lock, Sliders
} from "lucide-react";
import toast from "react-hot-toast";
import "./SettingsPanel.css";

const API_BASE = "http://127.0.0.1:8000";

interface SettingsState {
  autonomy_level: string;
  enable_agent_internet: boolean;
  system_prompt_addition: string;
  enable_mesh_routing: boolean;
  enable_distributed_pooling: boolean;
  ollama_base_url: string;
  neurex_trash_path: string;
  enable_push_notifications: boolean;
  // Appearance
  enable_glassmorphism: boolean;
  enable_animations: boolean;
  theme_preset: string;
  // LLM Advanced
  llm_temperature: number;
  llm_context_length: number;
  // Workspace
  auto_save_files: boolean;
  show_hidden_files: boolean;
  [key: string]: any;
}

export function SettingsPanel() {
  const [settings, setSettings] = useState<SettingsState | null>(null);
  const [user, setUser] = useState<{ id: string, role: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [settingsRes, userRes] = await Promise.all([
          fetch(`${API_BASE}/api/settings/`),
          fetch(`${API_BASE}/api/auth/me`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
          })
        ]);

        if (settingsRes.status === 403 || userRes.status === 401) {
          toast.error("Unauthorized access. Admin privileges required.");
        }

        const settingsData = await settingsRes.json();
        const userData = await userRes.json();
        
        // Merge defaults if keys missing
        const finalSettings = {
          enable_glassmorphism: true,
          enable_animations: true,
          theme_preset: "obsidian",
          llm_temperature: 0.7,
          llm_context_length: 8192,
          auto_save_files: true,
          show_hidden_files: false,
          ...settingsData
        };

        setSettings(finalSettings);
        setUser(userData);
      } catch (err) {
        toast.error("Failed to sync with Neurex core");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const isAdmin = user?.role === "ADMIN";
  const isViewer = user?.role === "VIEWER";

  const handleChange = (key: string, value: any) => {
    if (!settings || isViewer) return;
    setSettings({ ...settings, [key]: value });
  };

  const handleSave = async () => {
    if (!settings || isViewer) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/settings/`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({ settings })
      });

      if (res.status === 403) {
        toast.error("Operation denied: Admin privileges required.");
        return;
      }

      toast.success("Settings saved successfully");
    } catch (err) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !settings) {
    return (
      <div className="settings-panel loading">
        <div className="settings-loader">
          <SettingsIcon className="animate-spin text-purple" size={32} />
          <span>Syncing Core...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-panel">
      <div className="settings-panel__header">
        <div className="settings-panel__title-bar">
          <div className="settings-icon-wrapper">
            <SettingsIcon size={20} className="text-purple" />
          </div>
          <div>
            <h2>Control Center</h2>
            <p className="settings-panel__subtitle">Node ID: {user?.id?.slice(0,8) || "Local"}</p>
          </div>
        </div>
        <button className="btn btn--purple btn--save" onClick={handleSave} disabled={saving || isViewer}>
          <Save size={14} /> {saving ? "Saving..." : "Commit Changes"}
        </button>
      </div>

      <div className="settings-panel__content">
        
        {/* AI INFRASTRUCTURE */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Cpu size={16} /> <h3>AI Infrastructure</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Ollama API Endpoint</label>
                <p>The base URL for your local Ollama service.</p>
              </div>
              <div className="setting-control">
                <input 
                  type="text" 
                  value={settings.ollama_base_url} 
                  onChange={(e) => handleChange("ollama_base_url", e.target.value)}
                  className="settings-input"
                  placeholder="http://127.0.0.1:11434"
                  disabled={isViewer}
                />
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Global Context Window</label>
                <p>Override the default context length for all models.</p>
              </div>
              <div className="setting-control">
                <select 
                  value={settings.llm_context_length} 
                  onChange={(e) => handleChange("llm_context_length", parseInt(e.target.value))}
                  className="settings-select"
                  disabled={isViewer}
                >
                  <option value={4096}>4k (Fast)</option>
                  <option value={8192}>8k (Balanced)</option>
                  <option value={16384}>16k (Deep)</option>
                  <option value={32768}>32k (Ultra)</option>
                  <option value={131072}>128k (Full)</option>
                </select>
              </div>
            </div>
          </div>
        </section>

        {/* APPEARANCE */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Palette size={16} /> <h3>Interface & Visuals</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Glassmorphism Effects</label>
                <p>Enable high-fidelity backdrop blurs and translucency. (Requires GPU)</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.enable_glassmorphism} onChange={(e) => handleChange("enable_glassmorphism", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Motion & Transitions</label>
                <p>Enable smooth kinetic transitions and micro-interactions.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.enable_animations} onChange={(e) => handleChange("enable_animations", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* AGENT BEHAVIOR */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Zap size={16} /> <h3>Agent Runtime & Autonomy</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Autonomy Level</label>
                <p>Control the frequency of required human approvals.</p>
              </div>
              <div className="setting-control">
                <select 
                  value={settings.autonomy_level} 
                  onChange={(e) => handleChange("autonomy_level", e.target.value)}
                  className="settings-select"
                  disabled={isViewer}
                >
                  <option value="restricted">Restricted (High Touch)</option>
                  <option value="limited">Limited (Balanced)</option>
                  <option value="full">Full (Autonomous)</option>
                </select>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Inference Temperature</label>
                <p>Adjust creativity vs. determinism in agent output.</p>
              </div>
              <div className="setting-control">
                <div className="slider-group">
                  <input 
                    type="range" min="0" max="2" step="0.1" 
                    value={settings.llm_temperature} 
                    onChange={(e) => handleChange("llm_temperature", parseFloat(e.target.value))}
                    disabled={isViewer}
                  />
                  <span className="slider-value">{settings.llm_temperature}</span>
                </div>
              </div>
            </div>

            <div className="setting-row setting-row--vertical">
              <div className="setting-info">
                <label>Custom System Prompt</label>
                <p>Inject permanent behavioral logic into the core agent memory.</p>
              </div>
              <div className="setting-control full-width">
                <textarea 
                  value={settings.system_prompt_addition}
                  onChange={(e) => handleChange("system_prompt_addition", e.target.value)}
                  placeholder="e.g. Always write comments in French..."
                  className="settings-textarea"
                  disabled={isViewer}
                />
              </div>
            </div>
          </div>
        </section>

        {/* WORKSPACE */}
        <section className="settings-group">
          <div className="settings-group__header">
            <HardDrive size={16} /> <h3>Workspace & Filesystem</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Auto-Save Documents</label>
                <p>Automatically save file changes after 500ms of inactivity.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.auto_save_files} onChange={(e) => handleChange("auto_save_files", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Show Hidden Files</label>
                <p>Display dotfiles (e.g. .env, .git) in the file explorer.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.show_hidden_files} onChange={(e) => handleChange("show_hidden_files", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* SECURITY & ISOLATION */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Shield size={16} /> <h3>Security & Isolation</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Enable Agent Internet Access</label>
                <p>Allows the terminal sandbox to access public registries.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.enable_agent_internet} onChange={(e) => handleChange("enable_agent_internet", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* MESH & DISTRIBUTED COMPUTE */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Network size={16} /> <h3>Mesh & Distributed Compute</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Enable Mesh Inference Routing</label>
                <p>Automatically offload heavy inference to connected peer nodes.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.enable_mesh_routing} onChange={(e) => handleChange("enable_mesh_routing", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Enable Distributed MPI Pooling</label>
                <p>Act as a worker node for Llama.cpp RPC pooling.</p>
                <span className="badge badge--experimental">Experimental</span>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch toggle-switch--purple ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.enable_distributed_pooling} onChange={(e) => handleChange("enable_distributed_pooling", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* NOTIFICATIONS */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Bell size={16} /> <h3>Alerts & Telemetry</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Push Notifications (VAPID)</label>
                <p>Wake up your mobile device when approval is required.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.enable_push_notifications} onChange={(e) => handleChange("enable_push_notifications", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
