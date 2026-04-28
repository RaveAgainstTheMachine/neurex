import { useState, useEffect } from "react";
import { 
  Shield, Network, Zap, Settings as SettingsIcon, Save, 
  Database, Bell, Palette, Cpu, HardDrive, Eye, EyeOff,
  Cloud, Lock, Sliders, Users, Trash2, LogOut, ShieldCheck
} from "lucide-react";
import toast from "react-hot-toast";
import "./SettingsPanel.css";
import { useStore } from "../../lib/store";

import { API_BASE } from "../../lib/config";

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
  accent_color: string;
  glow_color: string;
  enable_swarm_glow: boolean;
  menu_mode: "vertical" | "horizontal";
  terminal_line_height: number;
  // LLM Advanced
  llm_temperature: number;
  llm_context_length: number;
  // Workspace
  auto_save_files: boolean;
  show_hidden_files: boolean;
  // Network
  api_port: number;
  web_port: number;
  chromadb_port: number;
  ollama_port: number;
  rpc_port: number;
  firewall_enabled: boolean;
  firewall_lan_only: boolean;
  enable_insomnia: boolean;
  [key: string]: any;
}

interface UserProfile {
  id: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export function SettingsPanel() {
  const [settings, setSettings] = useState<SettingsState | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [otpData, setOtpData] = useState<{ secret: string, qr_code: string } | null>(null);
  const [otpVerifyCode, setOtpVerifyCode] = useState("");
  const logout = useStore(s => s.logout);

  const fetchData = async () => {
    const token = localStorage.getItem("token");
    try {
      const [settingsRes, userRes] = await Promise.all([
        fetch(`${API_BASE}/api/settings/`),
        fetch(`${API_BASE}/api/auth/me`, {
          headers: { "Authorization": `Bearer ${token}` }
        })
      ]);

      const settingsData = await settingsRes.json();
      const userData = await userRes.json();
      
      const finalSettings = {
        enable_glassmorphism: true,
        enable_animations: true,
        theme_preset: "obsidian",
        llm_temperature: 0.7,
        llm_context_length: 8192,
        auto_save_files: true,
        show_hidden_files: false,
        menu_mode: "horizontal",
        terminal_line_height: 1.2,
        ...settingsData
      };

      setSettings(finalSettings);
      setUser(userData);

      if (userData.role === "admin") {
        const usersRes = await fetch(`${API_BASE}/api/auth/users`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (usersRes.ok) setUsers(await usersRes.json());
      }
    } catch (err) {
      toast.error("Failed to sync with Neurex core");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const isAdmin = user?.role === "admin";
  const isViewer = user?.role === "viewer";

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

      // Sync global theme immediately
      useStore.getState().setTheme({
        accent_color: settings.accent_color,
        glow_color: settings.glow_color,
        enable_glassmorphism: settings.enable_glassmorphism,
        enable_animations: settings.enable_animations,
        menu_mode: settings.menu_mode,
        terminal_line_height: settings.terminal_line_height
      });

      toast.success("Settings saved successfully");
    } catch (err) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleSetupOtp = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/setup-otp`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      const data = await res.json();
      setOtpData(data);
    } catch (err) {
      toast.error("Failed to initiate OTP setup");
    }
  };

  const handleVerifyOtp = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/verify-otp?code=${otpVerifyCode}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      if (res.ok) {
        toast.success("2FA Enabled Successfully");
        setOtpData(null);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Invalid code");
      }
    } catch (err) {
      toast.error("Verification failed");
    }
  };

  const handleUpdateRole = async (userId: string, role: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/users/${userId}/role?role=${role}`, {
        method: "PATCH",
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      if (res.ok) {
        toast.success("Role updated");
        fetchData();
      }
    } catch (err) {
      toast.error("Failed to update role");
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm("Are you sure you want to revoke mesh access for this identity?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/auth/users/${userId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      if (res.ok) {
        toast.success("Identity purged");
        fetchData();
      }
    } catch (err) {
      toast.error("Failed to delete user");
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
        <div className="settings-panel__actions">
          <button className="btn btn--outline" onClick={logout}>
            <LogOut size={14} /> Log Out
          </button>
          <button className="btn btn--purple btn--save" onClick={handleSave} disabled={saving || isViewer}>
            <Save size={14} /> {saving ? "Saving..." : "Commit Changes"}
          </button>
        </div>
      </div>

      <div className="settings-panel__content">
        
        {/* ACCOUNT OVERVIEW */}
        <section className="settings-group">
          <div className="settings-group__header">
            <ShieldCheck size={16} /> <h3>Account Security</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Authenticated Identity</label>
                <p>You are logged in as <strong className="text-purple">{user?.username}</strong></p>
              </div>
              <div className="setting-control">
                <span className={`badge badge--${user?.role}`}>{user?.role?.toUpperCase()}</span>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Two-Factor Authentication (OTP)</label>
                <p>Add an extra layer of security to your neural connection.</p>
              </div>
              <div className="setting-control">
                {user?.is_active && !otpData && (
                  <button 
                    className={`btn ${user?.role === 'admin' ? 'btn--purple' : 'btn--outline'} btn--sm`}
                    onClick={handleSetupOtp}
                    disabled={!!(user as any).otp_enabled}
                  >
                    {(user as any).otp_enabled ? "✓ 2FA Active" : "Enable 2FA"}
                  </button>
                )}
              </div>
            </div>

            {otpData && (
              <div className="otp-setup-box glass">
                <div className="otp-setup-box__header">
                  <h4>Neural Link Synchronization</h4>
                  <p>Scan this QR code with Google Authenticator or Authy</p>
                </div>
                <div className="otp-setup-box__content">
                  <img src={otpData.qr_code} alt="OTP QR Code" className="otp-qr" />
                  <div className="otp-setup-form">
                    <p className="text-muted">Secret: <code>{otpData.secret}</code></p>
                    <input 
                      type="text" 
                      placeholder="6-digit code" 
                      className="settings-input"
                      value={otpVerifyCode}
                      onChange={e => setOtpVerifyCode(e.target.value)}
                      maxLength={6}
                    />
                    <div className="otp-setup-actions">
                      <button className="btn btn--outline btn--sm" onClick={() => setOtpData(null)}>Cancel</button>
                      <button className="btn btn--purple btn--sm" onClick={handleVerifyOtp}>Verify & Enable</button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* USER MANAGEMENT (ADMIN ONLY) */}
        {isAdmin && (
          <section className="settings-group">
            <div className="settings-group__header">
              <Users size={16} /> <h3>User Management</h3>
            </div>
            <div className="settings-group__body">
              <div className="user-management-list">
                {users.map(u => (
                  <div key={u.id} className="user-item">
                    <div className="user-item__info">
                      <strong>{u.username}</strong>
                      <span>{u.id.slice(0, 8)} • Joined {new Date(u.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="user-item__actions">
                      <select 
                        value={u.role} 
                        onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                        className="settings-select settings-select--sm"
                        disabled={u.id === user?.id}
                      >
                        <option value="admin">Admin</option>
                        <option value="developer">Developer</option>
                        <option value="viewer">Viewer</option>
                      </select>
                      <button 
                        className="btn btn--icon btn--danger" 
                        onClick={() => handleDeleteUser(u.id)}
                        disabled={u.id === user?.id}
                        title="Purge Identity"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

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

            <div className="setting-row">
              <div className="setting-info">
                <label>Status Bar Swarm Glow</label>
                <p>Enable the neural pulse animation when nodes are active.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.enable_swarm_glow} onChange={(e) => handleChange("enable_swarm_glow", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Main Menu Layout</label>
                <p>Toggle between a horizontal top bar and a vertical tree menu.</p>
              </div>
              <div className="setting-control">
                <select 
                  value={settings.menu_mode} 
                  onChange={(e) => handleChange("menu_mode", e.target.value)}
                  className="settings-select"
                  disabled={isViewer}
                >
                  <option value="horizontal">Top Horizontal (Standard)</option>
                  <option value="vertical">Side Tree (Advanced)</option>
                </select>
              </div>
            </div>
            <div className="setting-row">
              <div className="setting-info">
                <label>Terminal Line Height</label>
                <p>Adjust vertical spacing between lines in the integrated terminal.</p>
              </div>
              <div className="setting-control">
                <div className="slider-group">
                  <input 
                    type="range" min="1.0" max="2.0" step="0.25" 
                    value={settings.terminal_line_height} 
                    onChange={(e) => handleChange("terminal_line_height", parseFloat(e.target.value))}
                    disabled={isViewer}
                  />
                  <span className="slider-value">{settings.terminal_line_height.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Primary Accent Color</label>
                <p>Personalize the core visual identity of the node.</p>
              </div>
              <div className="setting-control color-picker-group">
                <input 
                  type="color" 
                  value={settings.accent_color.startsWith('hsl') ? '#9c6fff' : settings.accent_color} 
                  onChange={(e) => {
                    const hex = e.target.value;
                    handleChange("accent_color", hex);
                    // Update glow as well with alpha
                    handleChange("glow_color", hex + '66'); 
                  }} 
                  disabled={isViewer}
                />
                <input 
                  type="text" 
                  value={settings.accent_color} 
                  onChange={(e) => handleChange("accent_color", e.target.value)}
                  className="settings-input settings-input--sm"
                  placeholder="hex or hsl"
                  disabled={isViewer}
                />
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

        {/* NETWORK & PORTS */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Network size={16} /> <h3>Network Configuration</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-grid">
              <div className="setting-col">
                <label>API Port</label>
                <input type="number" value={settings.api_port} onChange={e => handleChange("api_port", parseInt(e.target.value))} className="settings-input" />
              </div>
              <div className="setting-col">
                <label>Web Port</label>
                <input type="number" value={settings.web_port} onChange={e => handleChange("web_port", parseInt(e.target.value))} className="settings-input" />
              </div>
              <div className="setting-col">
                <label>RPC Port</label>
                <input type="number" value={settings.rpc_port} onChange={e => handleChange("rpc_port", parseInt(e.target.value))} className="settings-input" />
              </div>
            </div>
            
            <div className="setting-row">
              <div className="setting-info">
                <label>Zero-Trust Firewall</label>
                <p>Enforce platform-specific firewall rules on this node.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.firewall_enabled} onChange={(e) => handleChange("firewall_enabled", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>LAN Isolation</label>
                <p>Restrict Neurex ports to the local network subnet only.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.firewall_lan_only} onChange={(e) => handleChange("firewall_lan_only", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* SYSTEM LIFECYCLE */}
        <section className="settings-group">
          <div className="settings-group__header">
            <Zap size={16} /> <h3>System Lifecycle</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Insomnia Mode</label>
                <p>Prevent system sleep while Neurex core is running.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={settings.enable_insomnia} onChange={(e) => handleChange("enable_insomnia", e.target.checked)} disabled={isViewer} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="setting-row setting-row--vertical">
              <div className="setting-info">
                <label>Neural Trash Path</label>
                <p>Base path for temporarily holding purged codebase fragments.</p>
              </div>
              <div className="setting-control full-width">
                <input 
                  type="text" 
                  value={settings.neurex_trash_path}
                  onChange={(e) => handleChange("neurex_trash_path", e.target.value)}
                  className="settings-input"
                  disabled={isViewer}
                />
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
