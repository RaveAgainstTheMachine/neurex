// neurex-web/src/components/HiveMindPanel/HiveMindPanel.tsx
"use client";

import { useState, useEffect } from "react";
import { 
  Database, Search, Cpu, Clock, ExternalLink, 
  BrainCircuit, Pin, Check, RefreshCw 
} from "lucide-react";
import toast from "react-hot-toast";
import "./HiveMindPanel.css";

import { API_BASE } from "../../lib/config";

interface MemoryEntry {
  id: string;
  content: string;
  metadata: {
    task_id?: string;
    conversation_id?: string;
    timestamp: number;
    tags?: string[];
  };
  distance?: number;
}

export function HiveMindPanel() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MemoryEntry[]>([]);
  const [searching, setSearching] = useState(false);
  const [stats, setStats] = useState({ total_nodes: 0, memory_count: 0 });
  const [pinned, setPinned] = useState<string[]>([]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/stats`);
      const data = await res.json();
      setStats(data);
    } catch (err) {}
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/api/memory/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      toast.error("Swarm recall failed");
    } finally {
      setSearching(false);
    }
  };

  const handlePin = (id: string) => {
    if (pinned.includes(id)) {
      setPinned(pinned.filter(p => p !== id));
      toast("Context unpinned", { icon: "📍" });
    } else {
      setPinned([...pinned, id]);
      toast.success("Added to AI context");
    }
  };

  return (
    <div className="hive-panel">
      <div className="hive-panel__header">
        <div className="hive-panel__title-bar">
          <BrainCircuit size={24} className="text-purple animate-pulse-slow" />
          <div>
            <h2>HIVE MIND</h2>
            <p className="text-muted">Collective Swarm Knowledge</p>
          </div>
          <button className="refresh-btn" onClick={fetchStats} title="Refresh Hive Stats">
            <RefreshCw size={14} />
          </button>
        </div>
        <div className="hive-stats">
          <div className="stat-pill" title="Connected AI Nodes">
            <Cpu size={12} /> <span>{stats.total_nodes} NODES</span>
          </div>
          <div className="stat-pill" title="Total Indexed Context">
            <Database size={12} /> <span>{stats.memory_count} FRAGMENTS</span>
          </div>
        </div>
      </div>

      <div className="hive-search-bar">
        <Search className="search-icon" size={16} />
        <input 
          type="text" 
          placeholder="Search collective memory..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <button className="query-btn" onClick={handleSearch} disabled={searching}>
          {searching ? <RefreshCw className="animate-spin" size={14} /> : "QUERY"}
        </button>
      </div>

      <div className="hive-results">
        {results.length > 0 ? (
          results.map((entry) => (
            <div key={entry.id} className={`memory-card glass ${pinned.includes(entry.id) ? 'pinned' : ''}`}>
              <div className="memory-card__header">
                <div className="memory-meta">
                  <Clock size={10} />
                  <span>{new Date(entry.metadata.timestamp * 1000).toLocaleTimeString()}</span>
                  <span className="relevance">Match: {Math.round((1 - (entry.distance || 0)) * 100)}%</span>
                </div>
                <button 
                  className={`pin-btn ${pinned.includes(entry.id) ? 'pinned' : ''}`} 
                  onClick={() => handlePin(entry.id)}
                  title="Pin to current AI context"
                >
                  {pinned.includes(entry.id) ? <Check size={14} /> : <Pin size={14} />}
                </button>
              </div>
              <div className="memory-content">
                <pre><code>{entry.content}</code></pre>
              </div>
              {entry.metadata.tags && (
                <div className="memory-tags">
                  {entry.metadata.tags.map(tag => (
                    <span key={tag} className="tag">#{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="hive-empty">
            <div className="empty-icon-box">
              <Database size={48} className="text-muted opacity-20" />
            </div>
            <p>No precedents found in collective memory.</p>
          </div>
        )}
      </div>
    </div>
  );
}
