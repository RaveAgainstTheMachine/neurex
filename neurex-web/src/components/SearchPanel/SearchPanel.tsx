import { useState } from "react";
import { Search, FileText, Loader2 } from "lucide-react";
import { useStore } from "../../lib/store";
import "./SearchPanel.css";

const API_BASE = "http://127.0.0.1:8000";

interface SearchResult {
  path: string;
  line: number;
  content: string;
}

const LANG_MAP: Record<string, string> = {
  ts: "typescript", tsx: "typescriptreact", js: "javascript", jsx: "javascriptreact",
  py: "python", css: "css", json: "json", md: "markdown", sh: "shell",
  yml: "yaml", yaml: "yaml", html: "html", rs: "rust", go: "go",
};

function getLanguage(path: string) {
  return LANG_MAP[path.split(".").pop() ?? ""] ?? "plaintext";
}

export function SearchPanel() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const { openFile } = useStore();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/api/files/search?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      setResults(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setSearching(false);
    }
  };

  const handleOpenResult = async (path: string) => {
    try {
      const r = await fetch(`${API_BASE}/api/files/read?path=${encodeURIComponent(path)}`);
      if (!r.ok) throw new Error("Failed to read");
      const data = await r.json();
      openFile(path, data.content ?? "", getLanguage(path));
    } catch (err) {
      openFile(path, "// Error loading file", getLanguage(path));
    }
  };

  return (
    <div className="search-panel">
      <div className="search-panel__header">SEARCH</div>
      <form className="search-panel__form" onSubmit={handleSearch}>
        <div className="search-input-wrapper">
          <input
            type="text"
            className="search-input"
            placeholder="Search files..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="search-submit">
            {searching ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          </button>
        </div>
      </form>

      <div className="search-results">
        {results.length === 0 && !searching && query && (
          <div className="search-empty">No results found.</div>
        )}
        {results.map((res, i) => (
          <div 
            key={i} 
            className="search-item" 
            onClick={() => handleOpenResult(res.path)}
          >
            <div className="search-item__header">
              <FileText size={12} className="search-item__icon" />
              <span className="search-item__path">{res.path}</span>
              <span className="search-item__line">:{res.line}</span>
            </div>
            <div className="search-item__snippet">{res.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
