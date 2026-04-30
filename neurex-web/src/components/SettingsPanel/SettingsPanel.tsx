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
  vllm_port: number;
  llama_cpp_port: number;
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
  const store = useStore();
  const [localSettings, setLocalSettings] = useState<SettingsState | null>(store.settings);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(!store.settings);
  const [saving, setSaving] = useState(false);
  const [otpData, setOtpData] = useState<{ secret: string, qr_code: string } | null>(null);
  const [otpVerifyCode, setOtpVerifyCode] = useState("");

  const fetchData = async () => {
    if (!store.token) return;
    try {
      // 1. Refresh global settings in background
      await store.refreshSettings();
      
      // 2. Sync local state with refreshed store
      if (useStore.getState().settings) {
        setLocalSettings(useStore.getState().settings);
      }

      // 3. Admin specific: fetch users
      if (store.user?.role === "admin") {
        const res = await fetch(`${API_BASE}/api/auth/users`, {
          headers: { "Authorization": `Bearer ${store.token}` }
        });
        if (res.ok) setUsers(await res.json());
      }
    } catch (err) {
      console.error("SettingsPanel sync error:", err);
      if (!localSettings) toast.error("Failed to sync with Neurex core");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [store.token]);

  const isAdmin = store.user?.role === "admin";
  const isViewer = store.user?.role === "viewer";

  const ADMIN_ONLY_SETTINGS = [
    "api_port", "web_port", "chromadb_port", "ollama_port", "vllm_port", "llama_cpp_port", "rpc_port",
    "firewall_enabled", "firewall_lan_only", "enable_mesh_routing",
    "enable_distributed_pooling", "ollama_base_url"
  ];

  const isRestricted = (key: string) => {
    if (isAdmin) return false;
    return ADMIN_ONLY_SETTINGS.includes(key);
  };

  const handleChange = (key: string, value: any) => {
    if (!localSettings || isViewer || isRestricted(key)) return;
    
    setLocalSettings(prev => {
      if (!prev) return null;
      return { ...prev, [key]: value };
    });

    // Immediate preview for visual settings
    if (["accent_color", "glow_color", "enable_glassmorphism", "enable_animations", "menu_mode", "terminal_line_height", "terminal_font_size", "terminal_font_family", "terminal_cursor_style"].includes(key)) {
      store.setTheme({ [key]: value });
    }
  };

  const handleBatchChange = (updates: Record<string, any>) => {
    if (!localSettings || isViewer) return;
    
    setLocalSettings(prev => {
      if (!prev) return null;
      let next = { ...prev };
      for (const [k, v] of Object.entries(updates)) {
        if (!isRestricted(k)) {
          next[k] = v;
        }
      }
      return next;
    });

    // Immediate preview for visual settings
    const visualUpdates: any = {};
    for (const [k, v] of Object.entries(updates)) {
      if (["accent_color", "glow_color", "enable_glassmorphism", "enable_animations", "menu_mode", "terminal_line_height", "terminal_font_size", "terminal_font_family", "terminal_cursor_style"].includes(k)) {
        visualUpdates[k] = v;
      }
    }
    if (Object.keys(visualUpdates).length > 0) {
      store.setTheme(visualUpdates);
    }
  };

  const handleSave = async () => {
    if (!localSettings || isViewer) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/settings/`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${store.token}`
        },
        body: JSON.stringify({ settings: localSettings })
      });

      if (res.status === 403) {
        toast.error("Operation denied: Admin privileges required.");
        return;
      }

      if (res.ok) {
        // Sync global theme immediately
        store.setTheme({
          accent_color: localSettings.accent_color,
          glow_color: localSettings.glow_color,
          enable_glassmorphism: localSettings.enable_glassmorphism,
          enable_animations: localSettings.enable_animations,
          menu_mode: localSettings.menu_mode,
          terminal_line_height: localSettings.terminal_line_height,
          terminal_font_size: localSettings.terminal_font_size,
          terminal_font_family: localSettings.terminal_font_family,
          terminal_cursor_style: localSettings.terminal_cursor_style
        });
        toast.success("Settings saved successfully");
        // Re-fetch to ensure sync
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Failed to save settings");
      }
    } catch (err) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
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

  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("Commonly Used");

  if (loading || !localSettings) {
    return (
      <div className="settings-panel loading">
        <div className="settings-loader">
          <SettingsIcon className="animate-spin text-purple" size={32} />
          <span>Syncing Core...</span>
        </div>
      </div>
    );
  }

  const categories = [
    { id: "Commonly Used", icon: Zap },
    { id: "Text Editor", icon: Sliders },
    { id: "AI Runtime", icon: Cpu },
    { id: "Network & Mesh", icon: Network },
    { id: "Account & Security", icon: ShieldCheck },
  ];

  return (
    <div className="settings-panel">
      <div className="settings-panel__header">
        <div className="settings-search">
          <input 
            type="text" 
            placeholder="Search settings" 
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="settings-panel__actions">
          <button className="btn btn--purple btn--save" onClick={handleSave} disabled={saving || isViewer}>
            <Save size={14} /> {saving ? "Saving..." : "Commit Changes"}
          </button>
        </div>
      </div>

      <div className="settings-body">
        <aside className="settings-sidebar">
          {categories.map(cat => (
            <div 
              key={cat.id} 
              className={`settings-sidebar-item ${activeCategory === cat.id ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat.id)}
            >
              <cat.icon size={14} />
              <span>{cat.id}</span>
            </div>
          ))}
        </aside>
        
        <div className="settings-main">
          {/* Main settings content will be filtered by category or search */}
          <div className="settings-view-header">
            <h2>{activeCategory}</h2>
          </div>
        
        {/* ACCOUNT OVERVIEW */}
        <section className="settings-group">
          <div className="settings-group__header">
            <ShieldCheck size={16} /> <h3>Account Security</h3>
          </div>
          <div className="settings-group__body">
            <div className="setting-row">
              <div className="setting-info">
                <label>Authenticated Identity</label>
                <p>You are logged in as <strong className="text-purple">{store.user?.username}</strong></p>
              </div>
              <div className="setting-control">
                <span className={`badge badge--${store.user?.role}`}>{store.user?.role?.toUpperCase()}</span>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Two-Factor Authentication (OTP)</label>
                <p>Add an extra layer of security to your neural connection.</p>
              </div>
              <div className="setting-control">
                {store.user?.is_active && !otpData && (
                  <button 
                    className={`btn ${store.user?.role === 'admin' ? 'btn--purple' : 'btn--outline'} btn--sm`}
                    onClick={handleSetupOtp}
                    disabled={!!(store.user as any).otp_enabled}
                  >
                    {(store.user as any).otp_enabled ? "✓ 2FA Active" : "Enable 2FA"}
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
                        disabled={u.id === store.user?.id}
                      >
                        <option value="admin">Admin</option>
                        <option value="developer">Developer</option>
                        <option value="viewer">Viewer</option>
                      </select>
                      <button 
                        className="btn btn--icon btn--danger" 
                        onClick={() => handleDeleteUser(u.id)}
                        disabled={u.id === store.user?.id}
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
                  value={localSettings.ollama_base_url} 
                  onChange={(e) => handleChange("ollama_base_url", e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="settings-input"
                  placeholder="http://127.0.0.1:11434"
                  disabled={isViewer || isRestricted("ollama_base_url")}
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
                  value={localSettings.llm_context_length} 
                  onChange={(e) => handleChange("llm_context_length", parseInt(e.target.value))}
                  className="settings-select"
                  disabled={isViewer || isRestricted("llm_context_length")}
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
                  <input type="checkbox" checked={localSettings.enable_glassmorphism} onChange={(e) => handleChange("enable_glassmorphism", e.target.checked)} disabled={isViewer || isRestricted("enable_glassmorphism")} />
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
                  <input type="checkbox" checked={localSettings.enable_animations} onChange={(e) => handleChange("enable_animations", e.target.checked)} disabled={isViewer || isRestricted("enable_animations")} />
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
                  <input type="checkbox" checked={localSettings.enable_swarm_glow} onChange={(e) => handleChange("enable_swarm_glow", e.target.checked)} disabled={isViewer || isRestricted("enable_swarm_glow")} />
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
                  value={localSettings.menu_mode} 
                  onChange={(e) => handleChange("menu_mode", e.target.value)}
                  className="settings-select"
                  disabled={isViewer || isRestricted("menu_mode")}
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
                    value={localSettings.terminal_line_height} 
                    onChange={(e) => handleChange("terminal_line_height", parseFloat(e.target.value))}
                    disabled={isViewer || isRestricted("terminal_line_height")}
                  />
                  <span className="slider-value">{localSettings.terminal_line_height.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Terminal Font Size</label>
                <p>Set the base pixel size for terminal text.</p>
              </div>
              <div className="setting-control">
                <div className="slider-group">
                  <input 
                    type="range" min="10" max="20" step="1" 
                    value={localSettings.terminal_font_size} 
                    onChange={(e) => handleChange("terminal_font_size", parseInt(e.target.value))}
                    disabled={isViewer || isRestricted("terminal_font_size")}
                  />
                  <span className="slider-value">{localSettings.terminal_font_size}px</span>
                </div>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Terminal Font Family</label>
                <p>Select your preferred monospace typeface.</p>
              </div>
              <div className="setting-control">
                <select 
                  value={localSettings.terminal_font_family} 
                  onChange={(e) => handleChange("terminal_font_family", e.target.value)}
                  className="settings-select"
                  disabled={isViewer || isRestricted("terminal_font_family")}
                >
                  <option value="'JetBrains Mono', 'Fira Code', monospace">JetBrains Mono (Modern)</option>
                  <option value="'Fira Code', monospace">Fira Code (Ligatures)</option>
                  <option value="'Source Code Pro', monospace">Source Code Pro (Classic)</option>
                  <option value="'Roboto Mono', monospace">Roboto Mono (Clean)</option>
                  <option value="'Courier New', Courier, monospace">Courier New (Legacy)</option>
                </select>
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <label>Terminal Cursor Style</label>
                <p>Customize the appearance of the shell cursor.</p>
              </div>
              <div className="setting-control">
                <select 
                  value={localSettings.terminal_cursor_style} 
                  onChange={(e) => handleChange("terminal_cursor_style", e.target.value)}
                  className="settings-select"
                  disabled={isViewer || isRestricted("terminal_cursor_style")}
                >
                  <option value="block">Block (Retro)</option>
                  <option value="bar">Bar (Standard)</option>
                  <option value="underline">Underline (Minimal)</option>
                </select>
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
                  value={localSettings.accent_color.startsWith('#') ? localSettings.accent_color : '#9c6fff'} 
                  onChange={(e) => {
                    const hex = e.target.value;
                    handleBatchChange({
                      "accent_color": hex,
                      "glow_color": hex + '66'
                    });
                  }} 
                  disabled={isViewer || isRestricted("accent_color")}
                />
                <input 
                  type="text" 
                  value={localSettings.accent_color} 
                  onChange={(e) => handleChange("accent_color", e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="settings-input settings-input--sm"
                  placeholder="hex or hsl"
                  disabled={isViewer || isRestricted("accent_color")}
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
                  value={localSettings.autonomy_level} 
                  onChange={(e) => handleChange("autonomy_level", e.target.value)}
                  className="settings-select"
                  disabled={isViewer || isRestricted("autonomy_level")}
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
                    value={localSettings.llm_temperature} 
                    onChange={(e) => handleChange("llm_temperature", parseFloat(e.target.value))}
                    disabled={isViewer || isRestricted("llm_temperature")}
                  />
                  <span className="slider-value">{localSettings.llm_temperature}</span>
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
                  value={localSettings.system_prompt_addition}
                  onChange={(e) => handleChange("system_prompt_addition", e.target.value)}
                  placeholder="e.g. Always write comments in French..."
                  className="settings-textarea"
                  disabled={isViewer || isRestricted("system_prompt_addition")}
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
                  <input type="checkbox" checked={localSettings.auto_save_files} onChange={(e) => handleChange("auto_save_files", e.target.checked)} disabled={isViewer || isRestricted("auto_save_files")} />
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
                  <input type="checkbox" checked={localSettings.show_hidden_files} onChange={(e) => handleChange("show_hidden_files", e.target.checked)} disabled={isViewer || isRestricted("show_hidden_files")} />
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
                  <input type="checkbox" checked={localSettings.enable_agent_internet} onChange={(e) => handleChange("enable_agent_internet", e.target.checked)} disabled={isViewer || isRestricted("enable_agent_internet")} />
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
                  <input type="checkbox" checked={localSettings.enable_mesh_routing} onChange={(e) => handleChange("enable_mesh_routing", e.target.checked)} disabled={isViewer || isRestricted("enable_mesh_routing")} />
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
                  <input type="checkbox" checked={localSettings.enable_distributed_pooling} onChange={(e) => handleChange("enable_distributed_pooling", e.target.checked)} disabled={isViewer || isRestricted("enable_distributed_pooling")} />
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
                  <input type="checkbox" checked={localSettings.enable_push_notifications} onChange={(e) => handleChange("enable_push_notifications", e.target.checked)} disabled={isViewer || isRestricted("enable_push_notifications")} />
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
                <input type="number" value={localSettings.api_port} onChange={e => handleChange("api_port", parseInt(e.target.value))} className="settings-input" disabled={isViewer || isRestricted("api_port")} />
              </div>
              <div className="setting-col">
                <label>Web Port</label>
                <input type="number" value={localSettings.web_port} onChange={e => handleChange("web_port", parseInt(e.target.value))} className="settings-input" disabled={isViewer || isRestricted("web_port")} />
              </div>
              <div className="setting-col">
                <label>RPC Port</label>
                <input type="number" value={localSettings.rpc_port} onChange={e => handleChange("rpc_port", parseInt(e.target.value))} className="settings-input" disabled={isViewer || isRestricted("rpc_port")} />
              </div>
            </div>

            <div className="setting-grid mt-4">
              <div className="setting-col">
                <label>Ollama Port</label>
                <input type="number" value={localSettings.ollama_port} onChange={e => handleChange("ollama_port", parseInt(e.target.value))} className="settings-input" disabled={isViewer || isRestricted("ollama_port")} />
              </div>
              <div className="setting-col">
                <label>vLLM Port</label>
                <input type="number" value={localSettings.vllm_port} onChange={e => handleChange("vllm_port", parseInt(e.target.value))} className="settings-input" disabled={isViewer || isRestricted("vllm_port")} />
              </div>
              <div className="setting-col">
                <label>llama.cpp Port</label>
                <input type="number" value={localSettings.llama_cpp_port} onChange={e => handleChange("llama_cpp_port", parseInt(e.target.value))} className="settings-input" disabled={isViewer || isRestricted("llama_cpp_port")} />
              </div>
            </div>
            
            <div className="setting-row">
              <div className="setting-info">
                <label>Zero-Trust Firewall</label>
                <p>Enforce platform-specific firewall rules on this node.</p>
              </div>
              <div className="setting-control">
                <label className={`toggle-switch ${isViewer ? 'disabled' : ''}`}>
                  <input type="checkbox" checked={localSettings.firewall_enabled} onChange={(e) => handleChange("firewall_enabled", e.target.checked)} disabled={isViewer || isRestricted("firewall_enabled")} />
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
                  <input type="checkbox" checked={localSettings.firewall_lan_only} onChange={(e) => handleChange("firewall_lan_only", e.target.checked)} disabled={isViewer || isRestricted("firewall_lan_only")} />
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
                  <input type="checkbox" checked={localSettings.enable_insomnia} onChange={(e) => handleChange("enable_insomnia", e.target.checked)} disabled={isViewer || isRestricted("enable_insomnia")} />
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
                  value={localSettings.neurex_trash_path}
                  onChange={(e) => handleChange("neurex_trash_path", e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="settings-input"
                  disabled={isViewer || isRestricted("neurex_trash_path")}
                />
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
