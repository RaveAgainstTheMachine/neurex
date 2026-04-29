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
}

import { AlertTriangle } from "lucide-react";

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
  const [marketSearch, setMarketSearch] = useState("");
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

  const filteredMarketplace = useMemo(() => {
    return curated.filter(item => {
      const matchesSearch = item.name.toLowerCase().includes(marketSearch.toLowerCase()) || 
                            item.description.toLowerCase().includes(marketSearch.toLowerCase());
      const matchesCategory = marketCategory === "All" || item.category === marketCategory;
      return matchesSearch && matchesCategory;
    });
  }, [curated, marketSearch, marketCategory]);

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
      setNewSkillUrl("");
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
      <div className="skills-panel__header animate-slide-up">
        <div className="skills-panel__title-bar">
          <h2 className="skills-panel__title">Agent Skills</h2>
          <div className="skills-tabs">
            <button 
              id="tab-installed"
              className={tab === "installed" ? "active" : ""} 
              onClick={() => setTab("installed")}
            >
              Installed
            </button>
            <button 
              id="tab-discover"
              className={tab === "discover" ? "active" : ""} 
              onClick={() => setTab("discover")}
            >
              Discover
            </button>
          </div>
        </div>
        <p className="skills-panel__subtitle">
          Extend Neurex via the <a href="https://skillsmp.com" target="_blank" className="text-purple hover-glow">Reasoning Marketplace</a>
        </p>
      </div>

      {tab === "installed" && (
        <div className="skills-panel__install animate-slide-up">
          <p className="skills-install-hint">
            Paste a <strong>Git repository URL</strong> or a <strong>skillsmp.com</strong> link below to synthesize new agent capabilities.
          </p>
          <div className="skills-input">
            <Globe size={14} className="skills-input__icon" />
            <input 
              id="skill-install-url"
              type="text" 
              placeholder="Git repository URL..." 
              value={newSkillUrl}
              onChange={(e) => setNewSkillUrl(e.target.value)}
              disabled={installing}
            />
            <button 
              id="btn-install-skill"
              className="btn btn--purple" 
              onClick={() => handleInstall(newSkillUrl)}
              disabled={installing || !newSkillUrl}
            >
              {installing ? <Loader2 className="animate-spin" size={14} /> : <Plus size={14} />}
            </button>
          </div>
        </div>
      )}

      <div className="skills-panel__list">
        {loading ? (
          <div className="skills-loading">
            <Loader2 className="animate-spin" size={24} />
          </div>
        ) : (
          <>
            {tab === "installed" && skills.length === 0 && (
              <div className="skills-empty animate-scale">
                <Puzzle size={32} className="text-purple opacity-20" />
                <p>No skills installed yet.</p>
              </div>
            )}
            {tab === "installed" && skills.map((skill, idx) => (
              <div 
                key={skill.id} 
                id={`skill-installed-${skill.id}`}
                className="skill-card skill-card--clickable animate-slide-up" 
                style={{ animationDelay: `${idx * 0.05}s` }}
                onClick={() => fetchSkillDetails(skill.id)}
              >
                <div className="skill-card__header">
                  <div className="skill-card__info">
                    <h3 className="skill-card__name">{skill.name}</h3>
                    <span className="skill-card__badge">{skill.tools_count} tools</span>
                  </div>
                  <button 
                    id={`btn-delete-${skill.id}`}
                    className="skill-card__delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConfirmState({ show: true, skillId: skill.id });
                    }}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
                <p className="skill-card__desc">{skill.description}</p>
                <div className="skill-card__footer">
                  <span className="skill-card__link">
                    Deep Inspection →
                  </span>
                </div>
              </div>
            ))}

            {tab === "discover" && (
              <div className="marketplace-controls animate-slide-up">
                <div className="skills-input">
                  <Search size={14} className="skills-input__icon" />
                  <input 
                    id="marketplace-search"
                    type="text" 
                    placeholder="Search marketplace..." 
                    value={marketSearch}
                    onChange={(e) => setMarketSearch(e.target.value)}
                  />
                </div>
                <div className="market-categories">
                  {["All", "Core", "Code", "Web", "Data"].map(cat => (
                    <button 
                      key={cat} 
                      id={`market-cat-${cat.toLowerCase()}`}
                      className={`market-cat-btn ${marketCategory === cat ? 'active' : ''}`}
                      onClick={() => setMarketCategory(cat)}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {tab === "discover" && filteredMarketplace.map((item, idx) => (
              <div 
                key={item.id} 
                id={`market-item-${item.id}`}
                className="skill-card skill-card--discover animate-slide-up"
                style={{ animationDelay: `${idx * 0.05}s` }}
              >
                <div className="skill-card__header">
                  <div className="skill-card__info">
                    <div className="skill-card__top">
                      <h3 className="skill-card__name">{item.name}</h3>
                      <span className="market-badge">{item.category}</span>
                    </div>
                    <div className="skill-card__subinfo">
                      <span className="skill-card__author">by {item.author}</span>
                      <span className="market-stars"><Star size={8} fill="currentColor" /> {item.stars}</span>
                    </div>
                  </div>
                  <button 
                    id={`btn-install-curated-${item.id}`}
                    className="btn btn--purple btn--small"
                    onClick={() => handleInstall(item.url)}
                    disabled={installing}
                  >
                    {installing ? <Loader2 className="animate-spin" size={12} /> : "Install"}
                  </button>
                </div>
                <p className="skill-card__desc">{item.description}</p>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
