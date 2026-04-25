import { useState, useEffect } from "react";
import { Shield, Network, Zap, Settings as SettingsIcon, Save, Database, Bell } from "lucide-react";
import toast from "react-hot-toast";
import "./SettingsPanel.css";

const API_BASE = "http://localhost:8000";

interface SettingsState {
  autonomy_level: string;
  enable_agent_internet: boolean;
  system_prompt_addition: string;
  enable_mesh_routing: boolean;
  enable_distributed_pooling: boolean;
  ollama_base_url: string;
  neurex_trash_path: string;
  enable_push_notifications: boolean;
  [key: string]: any;
}

export function SettingsPanel() {
  const [settings, setSettings] = useState<SettingsState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/settings/`)
      .then(res => res.json())
      .then(data => {
        setSettings(data);
        setLoading(false);
      });
  }, []);

  const handleChange = (key: string, value: any) => {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  };

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await fetch(`${API_BASE}/api/settings/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ settings })
      });
      toast.success("Settings saved successfully");
    } catch (err) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !settings) {
    return <div className="settings-panel loading"><SettingsIcon className="animate-spin" /></div>;
  }

  return (
    <div className="settings-panel">
      <div className="settings-panel__header">
        <div className="settings-panel__title-bar">
          <SettingsIcon size={20} className="text-purple" />
          <h2>Neurex Control Center</h2>
        </div>
        <button className="btn btn--purple btn--save" onClick={handleSave} disabled={saving}>
          <Save size={14} /> {saving ? "Saving..." : "Save Changes"}
        </button>
      </div>

      <div className="settings-panel__content">
        
        {/* AGENT BEHAVIOR */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Zap size={16} /> <h3>Agent Behavior & Autonomy</h3>
          </div>
          <div className="settings-group__body">
            
            <div className="setting-row">
              <div className="setting-info">
                <label>Autonomy Level</label>
                <p>Dictates how frequently the agent requires human approval for execution.</p>
              </div>
              <div className="setting-control">
                <select 
                  value={settings.autonomy_level} 
                  onChange={(e) => handleChange("autonomy_level", e.target.value)}
                  className="settings-select"
                >
                  <option value="restricted">Restricted (High Touch)</option>
                  <option value="limited">Limited (Balanced)</option>
                  <option value="full">Full (Autonomous)</option>
                </select>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Custom System Prompt</label>
                <p>Inject permanent behavioral rules into the agent's core memory.</p>
              </div>
              <div className="setting-control full-width">
                <textarea 
                  value={settings.system_prompt_addition}
                  onChange={(e) => handleChange("system_prompt_addition", e.target.value)}
                  placeholder="e.g. Always write comments in French..."
                  className="settings-textarea"
                />
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
                <p>Allows the terminal sandbox to curl, wget, or npm install from public registries. Disable for air-gapped security.</p>
              </div>
              <div className="setting-control">
                <label className="toggle-switch">
                  <input type="checkbox" checked={settings.enable_agent_internet} onChange={(e) => handleChange("enable_agent_internet", e.target.checked)} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Hardened Trash Path</label>
                <p>The protected directory where agent-deleted files are moved. Agents cannot read or write to this directory.</p>
              </div>
              <div className="setting-control">
                <input type="text" value={settings.neurex_trash_path} onChange={(e) => handleChange("neurex_trash_path", e.target.value)} className="settings-input" />
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
                <p>Automatically offload heavy LLM inference to the most powerful connected peer node.</p>
              </div>
              <div className="setting-control">
                <label className="toggle-switch">
                  <input type="checkbox" checked={settings.enable_mesh_routing} onChange={(e) => handleChange("enable_mesh_routing", e.target.checked)} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Enable Distributed MPI Pooling (Phase 10.5)</label>
                <p>Act as a worker node for Llama.cpp RPC, pooling your CPU/RAM with other nodes to run massive models.</p>
                <span className="badge badge--experimental">Experimental</span>
              </div>
              <div className="setting-control">
                <label className="toggle-switch toggle-switch--purple">
                  <input type="checkbox" checked={settings.enable_distributed_pooling} onChange={(e) => handleChange("enable_distributed_pooling", e.target.checked)} />
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
                <p>Wake up your mobile device when an agent requires manual approval to proceed.</p>
              </div>
              <div className="setting-control">
                <label className="toggle-switch">
                  <input type="checkbox" checked={settings.enable_push_notifications} onChange={(e) => handleChange("enable_push_notifications", e.target.checked)} />
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
