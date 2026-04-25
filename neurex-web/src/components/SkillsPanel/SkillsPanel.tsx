import { useState, useEffect } from "react";
import { Puzzle, Download, Trash2, Globe, Loader2, Plus } from "lucide-react";
import "./SkillsPanel.css";

const API_BASE = "http://localhost:8000";

interface Skill {
  id: string;
  name: string;
  description: string;
  tools_count: number;
  url: string;
}

export function SkillsPanel() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState(false);
  const [newSkillUrl, setNewSkillUrl] = useState("");

  const fetchSkills = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/skills/`);
      const data = await resp.json();
      setSkills(data);
    } catch (err) {
      console.error("Failed to fetch skills", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, []);

  const handleInstall = async () => {
    if (!newSkillUrl.trim()) return;
    setInstalling(true);
    try {
      await fetch(`${API_BASE}/api/skills/install`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: newSkillUrl })
      });
      setNewSkillUrl("");
      fetchSkills();
    } catch (err) {
      console.error("Installation failed", err);
    } finally {
      setInstalling(false);
    }
  };

  const handleUninstall = async (id: string) => {
    if (!confirm("Are you sure you want to uninstall this skill?")) return;
    try {
      await fetch(`${API_BASE}/api/skills/${id}`, { method: "DELETE" });
      fetchSkills();
    } catch (err) {
      console.error("Uninstall failed", err);
    }
  };

  return (
    <div className="skills-panel">
      <div className="skills-panel__header">
        <h2 className="skills-panel__title">Agent Skills</h2>
        <p className="skills-panel__subtitle">Extend Neurex with specialized toolsets.</p>
      </div>

      <div className="skills-panel__install">
        <div className="skills-input">
          <Globe size={14} className="skills-input__icon" />
          <input 
            type="text" 
            placeholder="Git repository URL..." 
            value={newSkillUrl}
            onChange={(e) => setNewSkillUrl(e.target.value)}
            disabled={installing}
          />
          <button 
            className="btn btn--purple" 
            onClick={handleInstall}
            disabled={installing || !newSkillUrl}
          >
            {installing ? <Loader2 className="animate-spin" size={14} /> : <Plus size={14} />}
          </button>
        </div>
      </div>

      <div className="skills-panel__list">
        {loading ? (
          <div className="skills-loading">
            <Loader2 className="animate-spin" size={24} />
          </div>
        ) : (
          <>
            {skills.length === 0 && (
              <div className="skills-empty">
                <Puzzle size={32} opacity={0.2} />
                <p>No skills installed yet.</p>
              </div>
            )}
            {skills.map((skill) => (
              <div key={skill.id} className="skill-card">
                <div className="skill-card__header">
                  <div className="skill-card__info">
                    <h3 className="skill-card__name">{skill.name}</h3>
                    <span className="skill-card__badge">{skill.tools_count} tools</span>
                  </div>
                  <button 
                    className="skill-card__delete"
                    onClick={() => handleUninstall(skill.id)}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
                <p className="skill-card__desc">{skill.description}</p>
                {skill.url && (
                  <div className="skill-card__footer">
                    <a href={skill.url} target="_blank" rel="noreferrer" className="skill-card__link">
                      View Source
                    </a>
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
