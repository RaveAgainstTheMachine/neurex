import { useState, useEffect } from "react";
import { Database, Search, Cpu, Clock, ExternalLink, BrainCircuit } from "lucide-react";
import "./HiveMindPanel.css";

const API_BASE = "http://localhost:8000";

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

  useEffect(() => {
    // Initial fetch of recent memories and stats
    fetch(`${API_BASE}/api/memory/stats`)
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/api/memory/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="hive-panel">
      <div className="hive-panel__header">
        <div className="hive-panel__title-bar">
          <BrainCircuit size={24} className="text-cyan animate-pulse-slow" />
          <div>
            <h2>Collective Memory</h2>
            <p className="text-muted">Querying the Swarm's decentralized knowledge base</p>
          </div>
        </div>
        <div className="hive-stats">
          <div className="stat-pill">
            <Cpu size={14} /> <span>{stats.total_nodes} Active Nodes</span>
          </div>
          <div className="stat-pill">
            <Database size={14} /> <span>{stats.memory_count} Indexed Fragments</span>
          </div>
        </div>
      </div>

      <div className="hive-search-bar">
        <Search className="search-icon" size={18} />
        <input 
          type="text" 
          placeholder="Semantic search (e.g. 'How did we handle JWT auth in previous project?')" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <button onClick={handleSearch} disabled={searching}>
          {searching ? "Recalling..." : "Query Hive"}
        </button>
      </div>

      <div className="hive-results">
        {results.length > 0 ? (
          results.map((entry) => (
            <div key={entry.id} className="memory-card glass">
              <div className="memory-card__header">
                <div className="memory-meta">
                  <Clock size={12} />
                  <span>{new Date(entry.metadata.timestamp * 1000).toLocaleString()}</span>
                  <span className="relevance">{(1 - (entry.distance || 0)).toFixed(2)} Relevance</span>
                </div>
                <ExternalLink size={14} className="link-icon" />
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
            <p>No precedents found. Start a conversation to index new knowledge.</p>
          </div>
        )}
      </div>
    </div>
  );
}
