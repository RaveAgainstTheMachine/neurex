// neurex-web/src/components/Benchmark/BenchmarkDashboard.tsx
"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Play, CheckCircle2, XCircle, AlertCircle, Clock, Trophy, 
  RotateCw, ChevronDown, ChevronUp, Terminal, Percent, Code
} from "lucide-react";
import "./BenchmarkDashboard.css";
import { API_BASE } from "../../lib/config";
import toast from "react-hot-toast";

interface BenchmarkCase {
  id: string;
  passed: boolean;
  duration_s: number;
  details: string;
}

interface BenchmarkState {
  status: "idle" | "running" | "completed" | "failed";
  current_case: string | null;
  log: string[];
  results: BenchmarkCase[];
  score: string;
  percentage: number;
  duration_s: number;
  start_time: number;
  error_details: string | null;
}

export function BenchmarkDashboard() {
  const [state, setState] = useState<BenchmarkState>({
    status: "idle",
    current_case: null,
    log: [],
    results: [],
    score: "0/0",
    percentage: 0,
    duration_s: 0.0,
    start_time: 0.0,
    error_details: null
  });
  
  const [selectedTag, setSelectedTag] = useState<string>("smoke");
  const [expandedCaseId, setExpandedCaseId] = useState<string | null>(null);
  const [showRawLogs, setShowRawLogs] = useState<boolean>(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Poll status from the backend
  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/benchmarks/status`, {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setState(data);
      }
    } catch (err) {
      console.error("Failed to fetch benchmark status:", err);
    }
  };

  // Run benchmark trigger
  const runBenchmark = async () => {
    try {
      const url = `${API_BASE}/api/benchmarks/run${selectedTag ? `?tag=${selectedTag}` : ""}`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        }
      });
      if (res.ok) {
        toast.success("Simulation benchmark execution triggered!");
        fetchStatus();
      } else {
        const errData = await res.json();
        toast.error(errData.detail || "Failed to start benchmark.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error triggering simulation benchmark.");
    }
  };

  // Initial fetch and polling logic
  useEffect(() => {
    fetchStatus();
    
    // Fast polling when running, slow polling when idle
    const intervalTime = state.status === "running" ? 1500 : 5000;
    const interval = setInterval(() => {
      // Avoid fetching when tab is backgrounded
      if (document.hidden) return;
      fetchStatus();
    }, intervalTime);

    return () => clearInterval(interval);
  }, [state.status]);

  // Scroll to bottom of raw logs when they update
  useEffect(() => {
    if (logEndRef.current && showRawLogs) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [state.log, showRawLogs]);

  const toggleExpandCase = (id: string) => {
    setExpandedCaseId(expandedCaseId === id ? null : id);
  };

  return (
    <div className="benchmark-dashboard">
      {/* Banner / Controller */}
      <div className="benchmark-banner">
        <div className="banner-info">
          <Trophy size={18} className="text-cyan animate-pulse" />
          <div className="banner-text">
            <h2>Visual Benchmark Arena</h2>
            <p className="text-muted">Validate core code reliability, execution correctness, and regression safety.</p>
          </div>
        </div>

        <div className="banner-controls">
          <div className="select-wrapper">
            <Code size={12} className="text-muted mr-1" />
            <select 
              value={selectedTag} 
              onChange={(e) => setSelectedTag(e.target.value)}
              disabled={state.status === "running"}
            >
              <option value="smoke">Smoke Suite (Fast)</option>
              <option value="python">Python Suite</option>
              <option value="typescript">TypeScript Suite</option>
              <option value="multi">Multi-file Suite</option>
              <option value="">Full Engine Suite</option>
            </select>
          </div>

          <button 
            className={`btn-run ${state.status === "running" ? "running" : ""}`}
            onClick={runBenchmark}
            disabled={state.status === "running"}
          >
            {state.status === "running" ? (
              <>
                <RotateCw size={14} className="animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Play size={14} />
                <span>Run Simulation</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* High-Level Stats Dashboard */}
      <div className="benchmark-stats">
        <div className="stat-card">
          <div className="stat-card__meta">
            <Trophy size={16} className="text-cyan" />
            <span>Success Metric</span>
          </div>
          <div className="stat-card__value">
            {state.score}
          </div>
          <div className="stat-card__desc text-muted">
            Test cases passed
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card__meta">
            <Percent size={16} className="text-purple" />
            <span>Pass Percentage</span>
          </div>
          <div className="stat-card__value">
            {state.percentage}%
          </div>
          <div className="stat-card__desc">
            <div className="progress-bar-bg">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${state.percentage}%` }}
              />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card__meta">
            <Clock size={16} className="text-orange" />
            <span>Arena Duration</span>
          </div>
          <div className="stat-card__value">
            {state.duration_s}s
          </div>
          <div className="stat-card__desc text-muted">
            Status: <span className={`status-badge status-badge--${state.status}`}>{state.status.toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* Running / Current Status Banner */}
      {state.status === "running" && state.current_case && (
        <div className="running-banner animate-pulse">
          <RotateCw size={14} className="animate-spin text-cyan" />
          <span>Currently processing: <strong>{state.current_case}</strong></span>
        </div>
      )}

      {state.error_details && (
        <div className="benchmark-error-details">
          <AlertCircle size={16} />
          <span>Execution failed: {state.error_details}</span>
        </div>
      )}

      {/* Results Grid / Log Toggle */}
      <div className="benchmark-views-toggle">
        <button 
          className={`toggle-tab ${!showRawLogs ? "active" : ""}`}
          onClick={() => setShowRawLogs(false)}
        >
          SIMULATION CASES ({state.results.length})
        </button>
        <button 
          className={`toggle-tab ${showRawLogs ? "active" : ""}`}
          onClick={() => setShowRawLogs(true)}
        >
          CONSOLE OUTPUT ({state.log.length} lines)
        </button>
      </div>

      <div className="benchmark-content-panel">
        {!showRawLogs ? (
          state.results.length === 0 ? (
            <div className="empty-results">
              <Code size={32} className="text-muted opacity-30 mb-2" />
              <p>Awaiting simulation benchmarks execution results...</p>
            </div>
          ) : (
            <div className="results-grid">
              {state.results.map((c) => {
                const isExpanded = expandedCaseId === c.id;
                return (
                  <div 
                    key={c.id} 
                    className={`case-card ${c.passed ? "passed" : "failed"} ${isExpanded ? "expanded" : ""}`}
                    onClick={() => toggleExpandCase(c.id)}
                  >
                    <div className="case-card__header">
                      <div className="case-title">
                        {c.passed ? (
                          <CheckCircle2 size={16} className="text-green" />
                        ) : (
                          <XCircle size={16} className="text-red" />
                        )}
                        <span className="case-name">{c.id}</span>
                      </div>
                      <div className="case-meta text-muted">
                        <span>{c.duration_s}s</span>
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="case-card__details" onClick={(e) => e.stopPropagation()}>
                        {c.passed ? (
                          <p className="text-green font-mono text-xs">Simulated evaluation case completed successfully with all target code verification matches passed.</p>
                        ) : (
                          <div className="failure-details">
                            <h4 className="text-red text-xs font-bold uppercase mb-1">Failure Report</h4>
                            <pre className="failure-log">{c.details || "No error details available"}</pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )
        ) : (
          <div className="console-panel">
            <div className="console-header">
              <Terminal size={12} className="text-muted" />
              <span>LIVE LOG CONSOLE</span>
            </div>
            <div className="console-feed">
              {state.log.length === 0 && (
                <div className="text-muted text-center p-8">No terminal stdout logged yet.</div>
              )}
              {state.log.map((line, idx) => (
                <div key={idx} className="console-line">{line}</div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
