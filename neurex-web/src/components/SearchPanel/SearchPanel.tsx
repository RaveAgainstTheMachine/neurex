// neurex-web/src/components/SearchPanel/SearchPanel.tsx
"use client";

import { useState, useMemo, useEffect } from "react";
import { 
  Search, FileText, Loader2, X, ChevronDown, ChevronRight, CaseSensitive, 
  WholeWord, Regex as RegexIcon, Replace as ReplaceIcon, Check, MoreHorizontal
} from "lucide-react";
import { useStore } from "../../lib/store";
import { toast } from "react-hot-toast";
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

export function SearchPanel({ onExpand }: { onExpand?: (s: number) => void }) {
  const searchState = useStore((s) => s.search);
  const setSearch = useStore((s) => s.setSearch);
  const clearSearch = useStore((s) => s.clearSearch);
  
  const [searching, setSearching] = useState(false);
  const [showReplace, setShowReplace] = useState(false);
  const [replaceQuery, setReplaceQuery] = useState("");
  const [replacing, setReplacing] = useState(false);
  const [expandedFiles, setExpandedFiles] = useState<Record<string, boolean>>({});
  const [showDetails, setShowDetails] = useState(false);

  const { openFile, setPendingJump, token } = useStore();

  useEffect(() => {
    if (searchState.results.length > 0 && onExpand) {
      onExpand(35);
    }
  }, [searchState.results.length, onExpand]);

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
        toast.success("Replaced all occurrences");
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
      openFile(path, data.content ?? "", getLanguage(path), true);
      setPendingJump(path, line);
    } catch (err) {
      toast.error("Failed to open file");
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

  const renderContentWithHighlights = (content: string, query: string) => {
    if (!query) return content;
    try {
      const flags = searchState.caseSensitive ? "g" : "gi";
      const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const regex = new RegExp(`(${escapedQuery})`, flags);
      const parts = content.split(regex);
      return parts.map((part, i) => 
        regex.test(part) ? <span key={i} className="search-highlight">{part}</span> : part
      );
    } catch (e) {
      return content;
    }
  };

  return (
    <div className="search-panel">
      <div className="search-panel__inputs">
        <div className="search-panel__row">
          <button 
            className={`replace-toggle ${showReplace ? "active" : ""}`}
            onClick={() => setShowReplace(!showReplace)}
            title="Toggle Replace"
          >
            {showReplace ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
          <div className="search-input-container">
            <input
              type="text"
              className="search-input"
              placeholder="Search"
              value={searchState.query}
              onChange={(e) => setSearch({ query: e.target.value })}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <div className="search-input-actions">
              <button 
                className={`input-action ${searchState.caseSensitive ? "active" : ""}`}
                onClick={() => setSearch({ caseSensitive: !searchState.caseSensitive })}
                title="Match Case"
              >
                <CaseSensitive size={14} />
              </button>
              <button 
                className={`input-action ${searchState.wholeWord ? "active" : ""}`}
                onClick={() => setSearch({ wholeWord: !searchState.wholeWord })}
                title="Match Whole Word"
              >
                <WholeWord size={14} />
              </button>
              <button 
                className={`input-action ${searchState.useRegex ? "active" : ""}`}
                onClick={() => setSearch({ useRegex: !searchState.useRegex })}
                title="Use Regular Expression"
              >
                <RegexIcon size={14} />
              </button>
            </div>
          </div>
        </div>

        {showReplace && (
          <div className="search-panel__row replace-row">
            <div className="replace-spacer" />
            <div className="search-input-container">
              <input
                type="text"
                className="search-input"
                placeholder="Replace"
                value={replaceQuery}
                onChange={(e) => setReplaceQuery(e.target.value)}
              />
              <div className="search-input-actions">
                <button 
                  className="input-action"
                  onClick={handleReplaceAll}
                  title="Replace All"
                  disabled={replacing || !searchState.query}
                >
                  {replacing ? <Loader2 size={14} className="animate-spin" /> : <ReplaceIcon size={14} />}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="search-details-toggle" onClick={() => setShowDetails(!showDetails)}>
          <MoreHorizontal size={14} />
          <span>{showDetails ? "Hide" : "Show"} Advanced Search Options</span>
        </div>

        {showDetails && (
          <div className="search-advanced">
            <div className="advanced-row">
              <label>files to include</label>
              <input 
                type="text" placeholder="e.g. *.ts, src/**"
                value={searchState.includeGlob}
                onChange={(e) => setSearch({ includeGlob: e.target.value })}
              />
            </div>
            <div className="advanced-row">
              <label>files to exclude</label>
              <input 
                type="text" placeholder="e.g. node_modules/**, dist/**"
                value={searchState.excludeGlob}
                onChange={(e) => setSearch({ excludeGlob: e.target.value })}
              />
            </div>
          </div>
        )}
      </div>

      <div className="search-panel__results">
        {searchState.results.length > 0 && (
          <div className="results-header">
            <span>{searchState.results.length} results in {Object.keys(groupedResults).length} files</span>
            <button className="clear-btn" onClick={clearSearch} title="Clear Search Results">
              <X size={12} />
            </button>
          </div>
        )}

        {searching && (
          <div className="search-status">
            <Loader2 size={16} className="animate-spin" />
            <span>Searching...</span>
          </div>
        )}

        {Object.entries(groupedResults).map(([path, matches]) => (
          <div key={path} className="search-result-group">
            <div className="search-result-file" onClick={() => setExpandedFiles(prev => ({ ...prev, [path]: !prev[path] }))}>
              {expandedFiles[path] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <FileText size={14} className="file-icon" />
              <span className="file-name">{path.split('/').pop()}</span>
              <span className="file-path">{path.substring(0, path.lastIndexOf('/'))}</span>
              <span className="match-count">{matches.length}</span>
            </div>
            {expandedFiles[path] && (
              <div className="search-result-matches">
                {matches.map((match, idx) => (
                  <div key={idx} className="search-match" onClick={() => handleOpenResult(path, match.line)}>
                    <span className="match-line">{match.line}</span>
                    <span className="match-content">
                      {renderContentWithHighlights(match.content, searchState.query)}
                    </span>
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
