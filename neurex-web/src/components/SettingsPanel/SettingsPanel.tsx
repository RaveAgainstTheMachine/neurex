// src/components/SettingsPanel/SettingsPanel.tsx
import React, { useState, useEffect } from "react";
import { 
  Zap, Settings as SettingsIcon, Save, Palette, Cpu, HardDrive, 
  ShieldCheck, Network, Sliders, ChevronRight, Search
} from "lucide-react";
import toast from "react-hot-toast";
import "./SettingsPanel.css";
import { useStore } from "../../lib/store";
import { API_BASE } from "../../lib/config";

import { Settings } from "../../lib/types";

interface SettingsState extends Settings {
  autonomy_level: string;
  enable_agent_internet: boolean;
  system_prompt_addition: string;
  enable_mesh_routing: boolean;
  enable_distributed_pooling: boolean;
  ollama_base_url: string;
  neurex_trash_path: string;
  enable_push_notifications: boolean;
  enable_glassmorphism: boolean;
  enable_animations: boolean;
  theme_preset: string;
  accent_color: string;
  glow_color: string;
  enable_swarm_glow: boolean;
  menu_mode: "vertical" | "horizontal";
  terminal_line_height: number;
  terminal_font_size: number;
  terminal_font_family: string;
  terminal_cursor_style: string;
  llm_temperature: number;
  llm_context_length: number;
  auto_save_files: boolean;
  show_hidden_files: boolean;
  api_port: number;
  web_port: number;
  rpc_port: number;
  firewall_enabled: boolean;
  firewall_lan_only: boolean;
  enable_insomnia: boolean;
  neurex_install_dir: string;
  models_dir: string;
  storage_paths: string | string[];
}

interface UserProfile {
  id: string;
  username: string;
  role: string;
  created_at: string;
}

export function SettingsPanel() {
  const store = useStore();
  const [localSettings, setLocalSettings] = useState<SettingsState | null>(store.settings as SettingsState);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(!store.settings);
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("commonly_used");

  const fetchData = async () => {
    if (!store.token) return;
    try {
      await store.refreshSettings();
      if (useStore.getState().settings) setLocalSettings(useStore.getState().settings as SettingsState);
      if (store.user?.role === "admin") {
        const res = await fetch(`${API_BASE}/api/auth/users`, {
          headers: { "Authorization": `Bearer ${store.token}` }
        });
        if (res.ok) setUsers(await res.json());
      }
    } catch (_err) {
      if (!localSettings) toast.error("Failed to sync with Neurex core");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [store.token]);

  const isAdmin = store.user?.role === "admin";
  const isViewer = store.user?.role === "viewer";

  const handleChange = (key: string, value: any) => {
    if (!localSettings || isViewer) return;
    setLocalSettings(prev => prev ? { ...prev, [key]: value } : null);
    
    if (["accent_color", "glow_color", "enable_glassmorphism", "enable_animations", "menu_mode", "terminal_line_height", "terminal_font_size", "terminal_font_family", "terminal_cursor_style"].includes(key)) {
      store.setTheme({ [key]: value });
    }
  };

  const handleSave = async () => {
    if (!localSettings || isViewer) return;
    setSaving(true);
    try {
      const settingsToSave = { ...localSettings };
      if (typeof settingsToSave.storage_paths === 'string') {
        settingsToSave.storage_paths = settingsToSave.storage_paths.split(',').map(p => p.trim()).filter(p => p);
      }

      const res = await fetch(`${API_BASE}/api/settings/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${store.token}` },
        body: JSON.stringify({ settings: settingsToSave })
      });
      if (res.ok) {
        toast.success("Settings committed");
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || "Save failed");
      }
    } catch (_err) {
      toast.error("Network error");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !localSettings) {
    return (
      <div className="settings-panel loading">
        <div className="settings-loader">
          <SettingsIcon className="animate-spin" size={32} />
          <span>Synchronizing...</span>
        </div>
      </div>
    );
  }

  const renderSetting = (key: string, label: string, description: string, type: 'toggle' | 'select' | 'input' | 'range' | 'color' | 'textarea', options?: any) => {
    const value = localSettings[key];
    const restricted = isViewer;

    return (
      <div className={`setting-item setting-item--${type}`}>
        <div className="setting-item__info">
          <label className="setting-item__label">{label}</label>
          <p className="setting-item__description">{description}</p>
        </div>
        <div className="setting-item__control">
          {type === 'toggle' && (
            <label className="toggle-switch">
              <input type="checkbox" checked={!!value} onChange={e => handleChange(key, e.target.checked)} disabled={restricted} />
              <span className="toggle-slider"></span>
            </label>
          )}
          {type === 'select' && (
            <select value={value} onChange={e => handleChange(key, e.target.value)} className="settings-select" disabled={restricted}>
              {options.map((opt: any) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          )}
          {type === 'input' && (
            <input 
              type="text" 
              value={Array.isArray(value) ? value.join(", ") : (value || "")} 
              onChange={e => handleChange(key, e.target.value)} 
              className="settings-input" 
              disabled={restricted} 
            />
          )}
          {type === 'range' && (
            <div className="slider-group">
              <input type="range" min={options.min} max={options.max} step={options.step} value={value} onChange={e => handleChange(key, parseFloat(e.target.value))} disabled={restricted} />
              <span className="slider-value">{value}{options.unit || ""}</span>
            </div>
          )}
          {type === 'color' && (
            <div className="color-picker-group">
              <input type="color" value={value.startsWith('#') ? value : '#9c6fff'} onChange={e => handleChange(key, e.target.value)} disabled={restricted} />
              <input type="text" value={value} onChange={e => handleChange(key, e.target.value)} className="settings-input settings-input--sm" disabled={restricted} />
            </div>
          )}
          {type === 'textarea' && (
            <textarea value={value} onChange={e => handleChange(key, e.target.value)} className="settings-textarea" disabled={restricted} />
          )}
        </div>
      </div>
    );
  };

  const categories = [
    { id: "commonly_used", label: "Commonly Used", icon: Zap },
    { id: "appearance", label: "Appearance", icon: Palette },
    { id: "text_editor", label: "Text Editor", icon: Sliders },
    { id: "ai_runtime", label: "AI Runtime", icon: Cpu },
    { id: "network", label: "Network & Mesh", icon: Network },
    { id: "security", label: "Security", icon: ShieldCheck },
    { id: "workspace", label: "Workspace", icon: HardDrive },
  ];

  return (
    <div className="settings-panel">
      <div className="settings-panel__header">
        <div className="settings-search">
          <Search size={14} />
          <input type="text" placeholder="Search settings" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        </div>
        <button className="btn btn--purple" onClick={handleSave} disabled={saving || isViewer}>
          <Save size={14} /> {saving ? "Saving..." : "Commit Changes"}
        </button>
      </div>

      <div className="settings-body">
        <aside className="settings-sidebar">
          {categories.map(cat => (
            <div key={cat.id} className={`settings-sidebar-item ${activeCategory === cat.id ? 'active' : ''}`} onClick={() => setActiveCategory(cat.id)}>
              <cat.icon size={16} />
              <span>{cat.label}</span>
            </div>
          ))}
          <div className="settings-sidebar-user">
            <div className="user-avatar">{store.user?.username?.[0].toUpperCase()}</div>
            <div className="user-info">
              <span className="username">{store.user?.username}</span>
              <span className="role-badge">{store.user?.role}</span>
            </div>
          </div>
        </aside>
        
        <main className="settings-content">
          <div className="settings-content-header">
            <div className="breadcrumb">
              <span>Settings</span> <ChevronRight size={12} />
              <span className="current">{categories.find(c => c.id === activeCategory)?.label}</span>
            </div>
            <h2>{categories.find(c => c.id === activeCategory)?.label}</h2>
          </div>

          <div className="settings-list">
            {activeCategory === "commonly_used" && (
              <>
                {renderSetting("auto_save_files", "Auto Save", "Automatically save changes after a delay of inactivity.", "toggle")}
                {renderSetting("theme_preset", "Theme Preset", "Select a pre-configured neural theme.", "select", [
                  { value: "neurex-dark", label: "Neurex Dark" }, { value: "neurex-light", label: "Neurex Light" }
                ])}
                {renderSetting("accent_color", "Primary Accent", "Personalize the core visual identity.", "color")}
                {renderSetting("autonomy_level", "Agent Autonomy", "Control the frequency of required approvals.", "select", [
                  { value: "restricted", label: "Restricted" }, { value: "limited", label: "Limited" }, { value: "full", label: "Full" }
                ])}
              </>
            )}

            {activeCategory === "appearance" && (
              <>
                <div className="settings-section-title">Visual Effects</div>
                {renderSetting("enable_glassmorphism", "Glassmorphism", "Enable backdrop blurs and translucency.", "toggle")}
                {renderSetting("enable_animations", "Animations", "Enable smooth kinetic transitions.", "toggle")}
                {renderSetting("enable_swarm_glow", "Swarm Glow", "Enable neural pulse animation.", "toggle")}
                <div className="settings-section-title">Layout</div>
                {renderSetting("menu_mode", "Menu Layout", "Toggle between horizontal and vertical menus.", "select", [
                  { value: "horizontal", label: "Horizontal" }, { value: "vertical", label: "Vertical" }
                ])}
              </>
            )}

            {activeCategory === "text_editor" && (
              <>
                <div className="settings-section-title">Terminal</div>
                {renderSetting("terminal_font_size", "Font Size", "Set base pixel size for terminal text.", "range", { min: 10, max: 24, step: 1, unit: "px" })}
                {renderSetting("terminal_line_height", "Line Height", "Adjust vertical spacing.", "range", { min: 1, max: 2, step: 0.1 })}
                {renderSetting("terminal_font_family", "Font Family", "Select monospace typeface.", "select", [
                  { value: "'JetBrains Mono', monospace", label: "JetBrains Mono" },
                  { value: "'Fira Code', monospace", label: "Fira Code" }
                ])}
              </>
            )}

            {activeCategory === "ai_runtime" && (
              <>
                {renderSetting("ollama_base_url", "Ollama API", "Base URL for local Ollama service.", "input")}
                {renderSetting("llm_temperature", "Temperature", "Adjust creativity vs determinism.", "range", { min: 0, max: 2, step: 0.1 })}
                {renderSetting("system_prompt_addition", "System Prompt", "Inject permanent behavioral logic.", "textarea")}
              </>
            )}

            {activeCategory === "network" && (
              <>
                {renderSetting("enable_mesh_routing", "Mesh Routing", "Offload inference to peers.", "toggle")}
                {renderSetting("enable_distributed_pooling", "MPI Pooling", "Act as a worker for RPC pooling.", "toggle")}
                <div className="settings-section-title">Ports</div>
                <div className="setting-grid">
                  {renderSetting("api_port", "API Port", "", "input")}
                  {renderSetting("web_port", "Web Port", "", "input")}
                </div>
              </>
            )}

            {activeCategory === "security" && (
              <>
                {renderSetting("firewall_enabled", "Neural Firewall", "Enforce node-specific rules.", "toggle")}
                {renderSetting("firewall_lan_only", "LAN Isolation", "Restrict to local subnet.", "toggle")}
                {isAdmin && (
                  <div className="user-management-list">
                    <div className="settings-section-title">Users</div>
                    {users.map(u => (
                      <div key={u.id} className="user-item">
                        <span>{u.username} ({u.role})</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {activeCategory === "workspace" && (
              <>
                {renderSetting("show_hidden_files", "Hidden Files", "Display dotfiles in explorer.", "toggle")}
                {renderSetting("enable_insomnia", "Insomnia Mode", "Prevent system sleep.", "toggle")}
                
                <div className="settings-section-title">Storage & Paths</div>
                {renderSetting("neurex_install_dir", "Install Path", "Root directory for Neurex substrate.", "input")}
                {renderSetting("models_dir", "Models Path", "Default directory for LLM weights.", "input")}
                {renderSetting("storage_paths", "Telemetry Paths", "Comma-separated list of directories to monitor for disk telemetry.", "input")}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
