// neurex-web/src/components/SearchPanel/SearchPanel.tsx
"use client";

import { useState, useMemo } from "react";
import { 
  Search, FileText, Loader2, X, ChevronDown, ChevronRight, CaseSensitive, 
  WholeWord, Regex as RegexIcon, Replace as ReplaceIcon, Check, MoreHorizontal
} from "lucide-react";
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

interface SearchResult {
  path: string;
  line: number;
  content: string;
}

export function SearchPanel() {
  const searchState = useStore((s) => s.search);
  const setSearch = useStore((s) => s.setSearch);
  const clearSearch = useStore((s) => s.clearSearch);
  
  const [searching, setSearching] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [showReplace, setShowReplace] = useState(false);
  const [replaceQuery, setReplaceQuery] = useState("");
  const [replacing, setReplacing] = useState(false);
  const [expandedFiles, setExpandedFiles] = useState<Record<string, boolean>>({});

  const { openFile, setPendingJump, token } = useStore();

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
      
      const res = await fetch(`${API_BASE}/api/files/search?${params.toString()}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setSearch({ results: Array.isArray(data) ? data : [] });
      
      // Auto-expand all files on new search
      const nextExpanded: Record<string, boolean> = {};
      (Array.isArray(data) ? data : []).forEach(r => { nextExpanded[r.path] = true; });
      setExpandedFiles(nextExpanded);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setSearching(false);
    }
  };

  const handleReplaceAll = async () => {
    if (!searchState.query || replacing) return;
    setReplacing(true);
    try {
      const res = await fetch(`${API_BASE}/api/files/replace-all`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          query: searchState.query,
          replacement: replaceQuery,
          case_sensitive: searchState.caseSensitive,
          use_regex: searchState.useRegex,
          whole_word: searchState.wholeWord,
          include_glob: searchState.includeGlob,
          exclude_glob: searchState.excludeGlob,
        })
      });
      if (res.ok) {
        // Refresh search results after replace
        handleSearch();
      }
    } catch (err) {
      console.error("Replace failed", err);
    } finally {
      setReplacing(false);
    }
  };

  const handleOpenResult = async (path: string, line: number) => {
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

  const groupedResults = useMemo(() => {
    const groups: Record<string, SearchResult[]> = {};
    searchState.results.forEach(res => {
      if (!groups[res.path]) groups[res.path] = [];
      groups[res.path].push(res);
    });
    return groups;
  }, [searchState.results]);

  const toggleFile = (path: string) => {
    setExpandedFiles(prev => ({ ...prev, [path]: !prev[path] }));
  };

  return (
    <div className="search-panel">
      <div className="search-panel__header" onClick={() => setExpanded(!expanded)}>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span>SEARCH</span>
      </div>
      
      {expanded && (
        <div className="search-panel__controls">
          <div className="search-panel__inputs-group">
            <div className="search-panel__row">
              <button 
                className={`search-expand-btn ${showReplace ? "active" : ""}`} 
                onClick={() => setShowReplace(!showReplace)}
                title="Toggle Replace"
              >
                {showReplace ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>
              <div className="search-input-wrapper">
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search"
                  value={searchState.query}
                  onChange={(e) => setSearch({ query: e.target.value })}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
                <div className="search-options">
                  <button 
                    type="button" title="Match Case"
                    className={`search-opt-btn ${searchState.caseSensitive ? "active" : ""}`}
                    onClick={() => setSearch({ caseSensitive: !searchState.caseSensitive })}
                  >
                    <CaseSensitive size={16} />
                  </button>
                  <button 
                    type="button" title="Match Whole Word"
                    className={`search-opt-btn ${searchState.wholeWord ? "active" : ""}`}
                    onClick={() => setSearch({ wholeWord: !searchState.wholeWord })}
                  >
                    <WholeWord size={16} />
                  </button>
                  <button 
                    type="button" title="Use Regular Expression"
                    className={`search-opt-btn ${searchState.useRegex ? "active" : ""}`}
                    onClick={() => setSearch({ useRegex: !searchState.useRegex })}
                  >
                    <RegexIcon size={16} />
                  </button>
                </div>
              </div>
            </div>

            {showReplace && (
              <div className="search-panel__row animate-slide-down">
                <div className="search-expand-spacer" />
                <div className="search-input-wrapper">
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Replace"
                    value={replaceQuery}
                    onChange={(e) => setReplaceQuery(e.target.value)}
                  />
                  <div className="search-options">
                    <button 
                      type="button" 
                      title="Replace All"
                      className="search-opt-btn replace-all-btn"
                      onClick={handleReplaceAll}
                      disabled={replacing || !searchState.query}
                    >
                      {replacing ? <Loader2 size={16} className="animate-spin" /> : <ReplaceIcon size={16} />}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="search-extra-inputs">
            <input 
              type="text" placeholder="files to include" className="search-extra-input"
              value={searchState.includeGlob} onChange={(e) => setSearch({ includeGlob: e.target.value })}
            />
            <input 
              type="text" placeholder="files to exclude" className="search-extra-input"
              value={searchState.excludeGlob} onChange={(e) => setSearch({ excludeGlob: e.target.value })}
            />
          </div>
        </div>
      )}

      <div className="search-results">
        {searchState.results.length > 0 && (
          <div className="search-results-count">
            <span>{Object.keys(groupedResults).length} files, {searchState.results.length} results</span>
            <button className="search-clear-btn" onClick={clearSearch} title="Clear Results"><X size={12} /></button>
          </div>
        )}
        
        {searchState.results.length === 0 && !searching && searchState.query && (
          <div className="search-empty">No results found.</div>
        )}
        
        {searching && (
          <div className="search-loading">
            <Loader2 size={24} className="animate-spin" />
            <span>Searching throughout codebase...</span>
          </div>
        )}

        {Object.entries(groupedResults).map(([path, matches]) => (
          <div key={path} className={`search-file-group ${expandedFiles[path] ? "expanded" : ""}`}>
            <div className="search-file-header" onClick={() => toggleFile(path)}>
              {expandedFiles[path] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <FileText size={14} className="search-file-icon" />
              <span className="search-file-name">{path.split('/').pop()}</span>
              <span className="search-file-path">{path.substring(0, path.lastIndexOf('/'))}</span>
              <span className="search-file-count">{matches.length}</span>
            </div>
            {expandedFiles[path] && (
              <div className="search-file-matches">
                {matches.map((match, idx) => (
                  <div key={idx} className="search-match" onClick={() => handleOpenResult(path, match.line)}>
                    <span className="search-match__line">{match.line}</span>
                    <span className="search-match__content">{match.content}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
