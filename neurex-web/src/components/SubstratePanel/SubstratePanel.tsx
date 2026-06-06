import React, { useState, useEffect } from "react";
import { 
  Database, Network, Search, Trash2, RefreshCw, 
  HelpCircle, ChevronDown, ChevronUp, Layers, Cpu
} from "lucide-react";
import { useStore } from "../../lib/store";
import { api } from "../../lib/api";
import "./SubstratePanel.css";

interface MemoryResult {
  id: string;
  content: string;
  metadata: Record<string, any>;
  distance: number;
}

export function SubstratePanel() {
  const hiveStats = useStore((s) => s.hiveStats);
  const refreshHiveStats = useStore((s) => s.refreshHiveStats);
  
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [memories, setMemories] = useState<MemoryResult[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // Initial stats fetch
  useEffect(() => {
    refreshHiveStats();
  }, [refreshHiveStats]);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setMessage(null);
    try {
      const res = await api.get<{ results: MemoryResult[] }>(
        `/api/memory/search?q=${encodeURIComponent(searchQuery)}`
      );
      setMemories(res.results || []);
    } catch (err) {
      console.error("Semantic recall failed", err);
      setMessage({ text: "Recall search failed. Ensure API is online.", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleClearMemory = async () => {
    if (!window.confirm("CAUTION: Are you sure you want to purge the collective cognitive substrate? This will erase all indexed conventions.")) {
      return;
    }

    setClearing(true);
    setMessage(null);
    try {
      // Clear endpoint in memory.py requires ADMIN
      const token = localStorage.getItem("token");
      await fetch("/api/memory/clear", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      setMessage({ text: "Cognitive substrate successfully purged.", type: "success" });
      setMemories([]);
      refreshHiveStats();
    } catch (err) {
      console.error("Purge failed", err);
      setMessage({ text: "Purge failed. Verify admin authorization.", type: "error" });
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="substrate-panel glassmorphic">
      <div className="substrate-panel__header">
        <Database size={14} className="icon-glow" />
        <span>Cognitive Substrate</span>
        <button 
          className="substrate-panel__refresh-btn" 
          onClick={refreshHiveStats}
          title="Refresh Stats"
        >
          <RefreshCw size={12} />
        </button>
      </div>

      <div className="substrate-panel__stats">
        <div className="substrate-stat-card">
          <div className="substrate-stat-value text-glow-purple">{hiveStats.memory_count}</div>
          <div className="substrate-stat-label">
            <Layers size={10} />
            <span>Memories Indexed</span>
          </div>
        </div>
        <div className="substrate-stat-card">
          <div className="substrate-stat-value text-glow-green">{hiveStats.total_nodes}</div>
          <div className="substrate-stat-label">
            <Network size={10} />
            <span>Mesh Nodes</span>
          </div>
        </div>
      </div>

      <form className="substrate-panel__search-box" onSubmit={handleSearch}>
        <div className="substrate-search-input-wrapper">
          <Search size={14} className="search-icon" />
          <input
            type="text"
            placeholder="Query semantic memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {loading && <RefreshCw size={12} className="spinner search-spinner" />}
        </div>
        <button type="submit" className="substrate-search-submit btn--purple">
          Recall
        </button>
      </form>

      {message && (
        <div className={`substrate-panel__message message--${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="substrate-panel__body">
        {loading ? (
          <div className="substrate-loader">
            <Cpu size={24} className="spinner text-purple" />
            <span>Traversing Vector Space...</span>
          </div>
        ) : memories.length > 0 ? (
          <div className="substrate-memories-list">
            {memories.map((mem) => {
              const isExpanded = expandedId === mem.id;
              const formattedDistance = (1 - mem.distance).toFixed(3);
              return (
                <div 
                  key={mem.id}
                  className={`substrate-memory-item ${isExpanded ? "substrate-memory-item--expanded" : ""}`}
                  onClick={() => setExpandedId(isExpanded ? null : mem.id)}
                >
                  <div className="substrate-memory-item__header">
                    <div className="substrate-memory-badge" title="Vector Similarity Match Score">
                      Match: {formattedDistance}
                    </div>
                    <span className="substrate-memory-item__id">ID: {mem.id.substring(0, 8)}...</span>
                    {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  </div>

                  <div className="substrate-memory-item__snippet">
                    {mem.content}
                  </div>

                  {isExpanded && (
                    <div className="substrate-memory-item__details">
                      <div className="details-section">
                        <strong>Full Context Document:</strong>
                        <pre className="details-doc">{mem.content}</pre>
                      </div>
                      {mem.metadata && Object.keys(mem.metadata).length > 0 && (
                        <div className="details-section">
                          <strong>Swarm Metadata:</strong>
                          <div className="details-metadata">
                            {Object.entries(mem.metadata).map(([key, val]) => (
                              <div key={key} className="meta-tag">
                                <span className="meta-key">{key}:</span>
                                <span className="meta-val">{String(val)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="substrate-empty">
            <HelpCircle size={24} className="text-muted" />
            <span>No active recall query executed. Type a semantic query to search through the collective memory pool.</span>
          </div>
        )}
      </div>

      <div className="substrate-panel__actions">
        <button 
          className="substrate-purge-btn" 
          onClick={handleClearMemory}
          disabled={clearing}
        >
          <Trash2 size={12} />
          <span>{clearing ? "Purging..." : "Purge Cognitive Core"}</span>
        </button>
      </div>
    </div>
  );
}
