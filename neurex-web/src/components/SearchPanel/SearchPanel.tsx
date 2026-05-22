// neurex-web/src/components/SearchPanel/SearchPanel.tsx
"use client";

import { useState, useMemo, useEffect } from "react";
import { 
  FileText, Loader2, X, ChevronDown, ChevronRight, CaseSensitive, 
  WholeWord, Regex as RegexIcon, Replace as ReplaceIcon, MoreHorizontal
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
  root?: string;
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

  // Phase 44.23: Strict State Selection (Prevent Search churn)
  const openFile = useStore(s => s.openFile);
  const setPendingJump = useStore(s => s.setPendingJump);
  const token = useStore(s => s.token);
  const workspaceFolders = useStore(s => s.workspaceFolders);

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
      const folders = workspaceFolders.length > 0 ? workspaceFolders : [""];
      
      const searchTasks = folders.map(async (folder) => {
        const params = new URLSearchParams({
          query: searchState.query,
          case_sensitive: searchState.caseSensitive.toString(),
          use_regex: searchState.useRegex.toString(),
          whole_word: searchState.wholeWord.toString(),
          include_glob: searchState.includeGlob,
          exclude_glob: searchState.excludeGlob,
          root_path: folder
        });
        
        const res = await fetch(`${API_BASE}/api/files/search?${params.toString()}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        return res.json();
      });

      const resultsArray = await Promise.all(searchTasks);
      const flattenedResults = resultsArray.flatMap((data, i) => 
        (Array.isArray(data) ? data : []).map((r: any) => ({ ...r, root: folders[i] }))
      ).filter(r => r && r.path);
      
      setSearch({ results: flattenedResults });
      
      const nextExpanded: Record<string, boolean> = {};
      flattenedResults.forEach(r => { nextExpanded[r.path] = true; });
      setExpandedFiles(nextExpanded);
    } catch (_err) {
      console.error("Search failed", err);
      toast.error("Search failed");
    } finally {
      setSearching(false);
    }
  };

  const handleReplaceAll = async () => {
    if (!searchState.query || replacing) return;
    setReplacing(true);
    try {
      const folders = workspaceFolders.length > 0 ? workspaceFolders : [""];
      
      const replaceTasks = folders.map(async (folder) => {
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
            root_path: folder
          })
        });
        return res.json();
      });

      const results = await Promise.all(replaceTasks);
      let totalReplaced = 0;
      results.forEach(data => {
        if (data.status === "ok") {
          totalReplaced += data.replaced_count || 0;
        }
      });

      if (totalReplaced > 0) {
        toast.success(`Replaced ${totalReplaced} occurrences across all folders`);
        handleSearch();
      } else {
        toast.error("No occurrences replaced");
      }
    } catch (_err) {
      console.error("Replace failed", err);
      toast.error("Replace failed");
    } finally {
      setReplacing(false);
    }
  };

  const handleOpenResult = async (path: string, line: number, root: string = "") => {
    try {
      const params = new URLSearchParams({ path, root_path: root });
      const r = await fetch(`${API_BASE}/api/files/read?${params.toString()}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!r.ok) throw new Error("Failed to read");
      const data = await r.json();
      openFile(path, data.content ?? "", getLanguage(path), true, root);
      setPendingJump(path, line, root);
    } catch (_err) {
      toast.error("Failed to open file");
    }
  };

  const groupedResults = useMemo(() => {
    const groups: Record<string, SearchResult[]> = {};
    searchState.results.forEach(res => {
      const key = res.root ? `${res.root}:${res.path}` : res.path;
      if (!groups[key]) groups[key] = [];
      groups[key].push(res);
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
    } catch (_e) {
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

        {Object.entries(groupedResults).map(([key, matches]) => {
          const first = matches[0];
          const path = first.path;
          const root = first.root;
          const displayPath = path.includes('/') ? path.substring(0, path.lastIndexOf('/')) : "";
          const rootName = root ? root.split('/').pop() : null;

          return (
            <div key={key} className="search-result-group">
              <div className="search-result-file" onClick={() => setExpandedFiles(prev => ({ ...prev, [key]: !prev[key] }))}>
                {expandedFiles[key] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <FileText size={14} className="file-icon" />
                <div className="file-info">
                  <span className="file-name">{path.split('/').pop()}</span>
                  <span className="file-path">{displayPath} {rootName && <span className="root-tag">[{rootName}]</span>}</span>
                </div>
                <span className="match-count">{matches.length}</span>
              </div>
              {expandedFiles[key] && (
                <div className="search-result-matches">
                  {matches.map((match: any, idx) => (
                    <div key={idx} className="search-match" onClick={() => handleOpenResult(path, match.line, match.root)}>
                      <span className="match-line">{match.line}</span>
                      <span className="match-content">
                        {renderContentWithHighlights(match.content, searchState.query)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
