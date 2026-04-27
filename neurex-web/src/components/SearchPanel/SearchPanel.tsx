// neurex-web/src/components/SearchPanel/SearchPanel.tsx
"use client";

import { useState } from "react";
import { Search, FileText, Loader2, X, ChevronDown, ChevronRight, CaseSensitive, WholeWord, Regex as RegexIcon } from "lucide-react";
import { useStore } from "../../lib/store";
import "./SearchPanel.css";

import { API_BASE } from "../../lib/config";

const LANG_MAP: Record<string, string> = {
  ts: "typescript", tsx: "typescriptreact", js: "javascript", jsx: "javascriptreact",
  py: "python", css: "css", json: "json", md: "markdown", sh: "shell",
  yml: "yaml", yaml: "yaml", html: "html", rs: "rust", go: "go",
};

function getLanguage(path: string) {
  return LANG_MAP[path.split(".").pop() ?? ""] ?? "plaintext";
}

export function SearchPanel() {
  const searchState = useStore((s) => s.search);
  const setSearch = useStore((s) => s.setSearch);
  const clearSearch = useStore((s) => s.clearSearch);
  
  const [searching, setSearching] = useState(false);
  const [expanded, setExpanded] = useState(true);
  
  const { openFile } = useStore();

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!searchState.query.trim()) return;

    setSearching(true);
    try {
      const params = new URLSearchParams({
        query: searchState.query,
        case_sensitive: searchState.caseSensitive.toString(),
        use_regex: searchState.useRegex.toString(),
        whole_word: searchState.wholeWord.toString(),
        include_glob: searchState.includeGlob,
        exclude_glob: searchState.excludeGlob,
      });
      
      const res = await fetch(`${API_BASE}/api/files/search?${params.toString()}`);
      const data = await res.json();
      setSearch({ results: Array.isArray(data) ? data : [] });
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setSearching(false);
    }
  };

  const handleOpenResult = async (path: string, line: number) => {
    const { openFile, setPendingJump, token } = useStore.getState();
    try {
      const r = await fetch(`${API_BASE}/api/files/read?path=${encodeURIComponent(path)}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!r.ok) throw new Error("Failed to read");
      const data = await r.json();
      openFile(path, data.content ?? "", getLanguage(path));
      setPendingJump(path, line);
    } catch (err) {
      openFile(path, "// Error loading file", getLanguage(path));
    }
  };

  return (
    <div className="search-panel">
      <div className="search-panel__header" onClick={() => setExpanded(!expanded)}>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span>SEARCH</span>
      </div>
      
      {expanded && (
        <div className="search-panel__controls">
          <form className="search-panel__form" onSubmit={handleSearch}>
            <div className="search-input-wrapper">
              <input
                type="text"
                className="search-input"
                placeholder="Search"
                value={searchState.query}
                onChange={(e) => setSearch({ query: e.target.value })}
              />
              <div className="search-options">
                <button 
                  type="button"
                  title="Match Case"
                  className={`search-opt-btn ${searchState.caseSensitive ? "active" : ""}`}
                  onClick={() => setSearch({ caseSensitive: !searchState.caseSensitive })}
                >
                  <CaseSensitive size={16} />
                </button>
                <button 
                  type="button"
                  title="Match Whole Word"
                  className={`search-opt-btn ${searchState.wholeWord ? "active" : ""}`}
                  onClick={() => setSearch({ wholeWord: !searchState.wholeWord })}
                >
                  <WholeWord size={16} />
                </button>
                <button 
                  type="button"
                  title="Use Regular Expression"
                  className={`search-opt-btn ${searchState.useRegex ? "active" : ""}`}
                  onClick={() => setSearch({ useRegex: !searchState.useRegex })}
                >
                  <RegexIcon size={16} />
                </button>
              </div>
              <button type="submit" className="search-submit">
                {searching ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
              </button>
            </div>
            
            <div className="search-extra-inputs">
              <input 
                type="text" 
                placeholder="files to include (e.g. *.ts, src/)" 
                className="search-extra-input"
                value={searchState.includeGlob}
                onChange={(e) => setSearch({ includeGlob: e.target.value })}
              />
              <input 
                type="text" 
                placeholder="files to exclude (e.g. *.test.ts)" 
                className="search-extra-input"
                value={searchState.excludeGlob}
                onChange={(e) => setSearch({ excludeGlob: e.target.value })}
              />
            </div>
          </form>
        </div>
      )}

      <div className="search-results">
        {searchState.results.length > 0 && (
          <div className="search-results-count">
            {searchState.results.length} results found
            <button className="search-clear-btn" onClick={clearSearch}><X size={12} /></button>
          </div>
        )}
        
        {searchState.results.length === 0 && !searching && searchState.query && (
          <div className="search-empty">No results found.</div>
        )}
        
        {searchState.results.map((res, i) => (
          <div 
            key={i} 
            className="search-item" 
            onClick={() => handleOpenResult(res.path, res.line)}
          >
            <div className="search-item__header">
              <FileText size={12} className="search-item__icon" />
              <span className="search-item__path">{res.path}</span>
              <span className="search-item__line">{res.line}</span>
            </div>
            <div className="search-item__snippet">
              {res.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
