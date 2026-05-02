import { useState, useEffect, useMemo } from "react";
import { Puzzle, Download, Trash2, Globe, Loader2, Plus, Search, Star, X, Zap } from "lucide-react";
import "./SkillsPanel.css";
import toast from "react-hot-toast";

import { API_BASE } from "../../lib/config";

interface Skill {
  id: string;
  name: string;
  description: string;
  tools_count: number;
  url: string;
  author?: string;
  version?: string;
}

import { AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";

function ConfirmModal({ 
  show, 
  title, 
  message, 
  onConfirm, 
  onCancel 
}: { 
  show: boolean; 
  title: string; 
  message: string; 
  onConfirm: () => void; 
  onCancel: () => void;
}) {
  if (!show) return null;
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <AlertTriangle size={18} className="text-amber" />
          <h3>{title}</h3>
        </div>
        <div className="modal-body">
          <p>{message}</p>
        </div>
        <div className="modal-footer">
          <button className="btn btn--muted" onClick={onCancel}>Cancel</button>
          <button className="btn btn--red" onClick={onConfirm}>Confirm Uninstallation</button>
        </div>
      </div>
    </div>
  );
}

function SkillDetailModal({
  skill,
  onClose
}: {
  skill: any;
  onClose: () => void;
}) {
  if (!skill) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-content--large" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="skill-modal-title">
            <Puzzle size={20} className="text-purple" />
            <h2>{skill.name}</h2>
            <span className="skill-modal-version">v{skill.version}</span>
          </div>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>
        <div className="modal-body">
          <div className="skill-modal-meta">
            <div className="meta-item">
              <span className="meta-label">Author</span>
              <span className="meta-value">{skill.author}</span>
            </div>
            {skill.repository && (
              <div className="meta-item">
                <span className="meta-label">Repository</span>
                <a href={skill.repository} target="_blank" className="meta-value text-purple">{skill.repository}</a>
              </div>
            )}
          </div>
          <p className="skill-modal-desc">{skill.description}</p>
          
          {skill.instructions && (
            <div className="skill-modal-instructions">
              <h3 className="section-title">Behavioral Guidelines</h3>
              <pre className="instructions-box">{skill.instructions}</pre>
            </div>
          )}

          <div className="skill-modal-tools">
            <h3 className="section-title">
              {skill.type === 'functional' ? `Capabilities (${skill.tools?.length || 0})` : 'Logic Extension'}
            </h3>
            <div className="tools-list">
              {skill.type === 'functional' && skill.tools?.length > 0 ? (
                skill.tools.map((t: any, idx: number) => (
                  <div key={idx} className="tool-entry">
                    <div className="tool-name">
                      <Zap size={10} />
                      {t.function?.name}
                    </div>
                    <p className="tool-desc">{t.function?.description}</p>
                  </div>
                ))
              ) : (
                <div className="tools-empty">
                  <p>This skill provides high-level instructions and reasoning logic to refine agent behavior rather than exposing discrete tools.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SkillsPanel() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [curated, setCurated] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState(false);
  const [newSkillUrl, setNewSkillUrl] = useState("");
  const [tab, setTab] = useState<"installed" | "discover">("installed");
  const [confirmState, setConfirmState] = useState<{ show: boolean; skillId: string | null }>({ show: false, skillId: null });
  const [selectedSkill, setSelectedSkill] = useState<any>(null);
  
  // Marketplace states
  const [searchQuery, setSearchQuery] = useState("");
  
  const [marketCategory, setMarketCategory] = useState("All");

  const fetchSkills = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/skills/`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      const data = await resp.json();
      if (Array.isArray(data)) setSkills(data);
    } catch (err) {
      console.error("Failed to fetch skills", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSkillDetails = async (id: string) => {
    try {
      const resp = await fetch(`${API_BASE}/api/skills/${id}`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        setSelectedSkill(data);
      }
    } catch (err) {
      toast.error("Failed to load skill details");
    }
  };

  const fetchCurated = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/skills/curated`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
      });
      const data = await resp.json();
      if (Array.isArray(data)) setCurated(data);
    } catch (err) {
      console.error("Failed to fetch curated list", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tab === "installed") fetchSkills();
    else fetchCurated();
  }, [tab]);

  const filteredInstalled = useMemo(() => {
    return skills.filter(s => 
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      s.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [skills, searchQuery]);

  const filteredMarketplace = useMemo(() => {
    return curated.filter(item => {
      const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                            item.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = marketCategory === "All" || item.category === marketCategory;
      return matchesSearch && matchesCategory;
    });
  }, [curated, searchQuery, marketCategory]);

  const handleInstall = async (url: string) => {
    setInstalling(true);
    try {
      const res = await fetch(`${API_BASE}/api/skills/install`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({ url })
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Installation failed");
      }
      toast.success("Skill installed successfully");
      setSearchQuery("");
      setTab("installed");
      fetchSkills();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setInstalling(false);
    }
  };

  const handleUninstall = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/skills/${id}`, { 
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        }
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to delete");
      }
      toast.success("Skill uninstalled");
      fetchSkills();
    } catch (err: any) {
      toast.error(err.message);
      console.error("Uninstall failed", err);
    } finally {
      setConfirmState({ show: false, skillId: null });
    }
  };

  return (
    <div className="skills-panel">
      <ConfirmModal 
        show={confirmState.show}
        title="Uninstall Skill"
        message="Are you sure you want to uninstall this agent skill? This will remove all associated tools and capabilities permanently."
        onConfirm={() => confirmState.skillId && handleUninstall(confirmState.skillId)}
        onCancel={() => setConfirmState({ show: false, skillId: null })}
      />
      <SkillDetailModal 
        skill={selectedSkill}
        onClose={() => setSelectedSkill(null)}
      />
      
      <div className="extensions-header">
        <div className="extensions-search-container">
          <input 
            type="text" 
            placeholder="Search Skills & Extensions" 
            className="extensions-search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <div className="extensions-search-icon"><Search size={14} /></div>
        </div>
      </div>

      <div className="extensions-content">
        <div className="extensions-section">
          <div className="extensions-section-header">
            <ChevronDown size={14} />
            <span>INSTALLED</span>
          </div>
          <div className="extensions-list">
            {filteredInstalled.length > 0 ? (
              filteredInstalled.map(skill => (
                <div key={skill.id} className="extension-item" onClick={() => fetchSkillDetails(skill.id)}>
                  <div className="extension-icon">
                    <Puzzle size={24} className="text-purple" />
                  </div>
                  <div className="extension-details">
                    <div className="extension-name-row">
                      <span className="extension-name">{skill.name}</span>
                      <button 
                        className="extension-manage"
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmState({ show: true, skillId: skill.id });
                        }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                    <span className="extension-description">{skill.description}</span>
                    <div className="extension-footer">
                      <span className="extension-author">{skill.author || 'Local Agent'}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <Puzzle size={32} className="text-muted" />
                <p>No skills or extensions installed.</p>
                <button className="btn btn--purple btn--xs" onClick={() => setTab("discover")}>
                  Discover in Marketplace
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="extensions-section">
          <div className="extensions-section-header">
            <ChevronDown size={14} />
            <span>DISCOVER</span>
          </div>
          <div className="extensions-list">
            {filteredMarketplace.map(item => (
              <div key={item.id} className="extension-item extension-item--discover">
                <div className="extension-icon">
                  <Globe size={24} className="text-cyan" />
                </div>
                <div className="extension-details">
                  <div className="extension-name-row">
                    <span className="extension-name">{item.name}</span>
                    <button 
                      className="btn btn--purple btn--xs"
                      onClick={() => handleInstall(item.url)}
                      disabled={installing}
                    >
                      Install
                    </button>
                  </div>
                  <span className="extension-description">{item.description}</span>
                  <div className="extension-footer">
                    <span className="extension-author">{item.author}</span>
                    <span className="extension-rating"><Star size={8} fill="currentColor" /> {item.stars}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
