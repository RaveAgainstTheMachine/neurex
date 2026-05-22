// neurex-web/src/components/TelemetryReplay/TelemetryReplayCanvas.tsx
"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { 
  Play, Pause, SkipBack, SkipForward, ArrowLeft, ArrowRight,
  Activity, Brain, Cpu, Compass, Shield, Clock,
  RefreshCw, AlertTriangle
} from "lucide-react";
import "./TelemetryReplayCanvas.css";
import { API_BASE } from "../../lib/config";

interface ScreenplayBeat {
  beat_number: number;
  timestamp: string;
  agent_type: string;
  act: string;
  narrative: string;
  context_metadata: Record<string, any>;
}

interface TelemetryReplayCanvasProps {
  conversationId: string;
}

export function TelemetryReplayCanvas({ conversationId }: TelemetryReplayCanvasProps) {
  const [beats, setBeats] = useState<ScreenplayBeat[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(-1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLive, setIsLive] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<any>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Fetch beats from the backend
  const fetchBeats = async (isInitial = false) => {
    if (!conversationId) return;
    if (isInitial) setLoading(true);
    
    try {
      const res = await fetch(`${API_BASE}/api/observability/replay/${conversationId}`, {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        }
      });
      if (!res.ok) {
        throw new Error(`Failed to fetch traces: ${res.statusText}`);
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setBeats(data);
        setError(null);
        
        // If we are in Live Sync mode, or if it's the first load, snap to the latest beat
        if (data.length > 0) {
          if (isLive || currentIndex === -1 || isInitial) {
            setCurrentIndex(data.length - 1);
          }
        } else {
          setCurrentIndex(-1);
        }
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "An error occurred while loading playback traces.");
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  // Poll for updates in the background (Live Sync)
  useEffect(() => {
    fetchBeats(true);

    const interval = setInterval(() => {
      // Avoid fetching if the browser tab is inactive or not visible to prevent lockups
      if (document.hidden) return;
      fetchBeats(false);
    }, 4000);

    return () => {
      clearInterval(interval);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [conversationId]);

  // Handle auto-playback timing
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setCurrentIndex((prev) => {
          if (prev >= beats.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 2500); // 2.5s per step
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isPlaying, beats.length]);

  // If new beats come in and we're in Live mode, keep index pinned to the end
  useEffect(() => {
    if (isLive && beats.length > 0) {
      setCurrentIndex(beats.length - 1);
    }
  }, [beats.length, isLive]);

  // Scroll active timeline node into view smoothly
  useEffect(() => {
    if (currentIndex !== -1 && scrollContainerRef.current) {
      const activeEl = scrollContainerRef.current.querySelector(
        `[data-index="${currentIndex}"]`
      );
      if (activeEl) {
        activeEl.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "center",
        });
      }
    }
  }, [currentIndex]);

  const currentBeat = useMemo(() => {
    if (currentIndex >= 0 && currentIndex < beats.length) {
      return beats[currentIndex];
    }
    return null;
  }, [beats, currentIndex]);

  // Navigation handlers
  const handleFirst = () => {
    setIsPlaying(false);
    setIsLive(false);
    if (beats.length > 0) setCurrentIndex(0);
  };

  const handleLast = () => {
    setIsPlaying(false);
    if (beats.length > 0) setCurrentIndex(beats.length - 1);
  };

  const handleBack = () => {
    setIsPlaying(false);
    setIsLive(false);
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : prev));
  };

  const handleForward = () => {
    setIsPlaying(false);
    setIsLive(false);
    setCurrentIndex((prev) => (prev < beats.length - 1 ? prev + 1 : prev));
  };

  const handleTimelineClick = (index: number) => {
    setIsPlaying(false);
    setIsLive(false);
    setCurrentIndex(index);
  };

  const togglePlay = () => {
    if (currentIndex >= beats.length - 1) {
      // Loop back to beginning if finished
      setCurrentIndex(0);
      setIsLive(false);
      setIsPlaying(true);
    } else {
      setIsLive(false);
      setIsPlaying(!isPlaying);
    }
  };

  const toggleLive = () => {
    const nextLive = !isLive;
    setIsLive(nextLive);
    if (nextLive) {
      setIsPlaying(false);
      if (beats.length > 0) {
        setCurrentIndex(beats.length - 1);
      }
    }
  };

  // Icon selector based on agent types / actions
  const getAgentIcon = (type: string) => {
    const t = (type || "").toLowerCase();
    if (t.includes("coder") || t.includes("architect")) return <Cpu className="icon-cyan animate-pulse" size={16} />;
    if (t.includes("planner")) return <Shield className="icon-purple" size={16} />;
    if (t.includes("researcher") || t.includes("explorer")) return <Compass className="icon-orange" size={16} />;
    if (t.includes("reviewer") || t.includes("verifier")) return <Brain className="icon-green" size={16} />;
    return <Activity className="icon-blue" size={16} />;
  };

  const getAgentClass = (type: string) => {
    const t = (type || "").toLowerCase();
    if (t.includes("coder")) return "agent-badge--coder";
    if (t.includes("planner")) return "agent-badge--planner";
    if (t.includes("researcher")) return "agent-badge--researcher";
    if (t.includes("reviewer")) return "agent-badge--reviewer";
    return "agent-badge--default";
  };

  return (
    <div className="teleplay-canvas">
      {/* Header Panel */}
      <div className="teleplay-header">
        <div className="teleplay-header__title">
          <Activity size={14} className="text-cyan animate-pulse" />
          <span>OBSERVABILITY PLAYBACK CANVAS</span>
        </div>
        <div className="teleplay-header__stats text-muted">
          <span>{beats.length} beats recorded</span>
          {beats.length > 0 && currentIndex !== -1 && (
            <span className="text-cyan ml-2">
              (Beat {currentIndex + 1} of {beats.length})
            </span>
          )}
        </div>
      </div>

      {loading && beats.length === 0 ? (
        <div className="teleplay-loading">
          <RefreshCw size={24} className="animate-spin text-cyan" />
          <p>Analyzing telemetry timelines...</p>
        </div>
      ) : error && beats.length === 0 ? (
        <div className="teleplay-error">
          <AlertTriangle size={32} className="text-orange mb-2" />
          <p>{error}</p>
        </div>
      ) : beats.length === 0 ? (
        <div className="teleplay-empty">
          <Brain size={32} className="text-muted opacity-40 mb-2" />
          <p>No telemetry traces available for this conversation.</p>
        </div>
      ) : (
        <div className="teleplay-body">
          {/* Timeline Bar */}
          <div className="teleplay-timeline" ref={scrollContainerRef}>
            <div className="teleplay-timeline__track">
              {beats.map((beat, idx) => {
                const isActive = idx === currentIndex;
                const isPast = idx < currentIndex;
                return (
                  <button
                    key={beat.beat_number}
                    data-index={idx}
                    className={`timeline-node ${isActive ? "active" : ""} ${isPast ? "past" : ""}`}
                    onClick={() => handleTimelineClick(idx)}
                    title={`Beat ${beat.beat_number}: [${beat.agent_type}] ${beat.act}`}
                  >
                    <div className="timeline-node__dot" />
                    <div className="timeline-node__label">
                      {beat.agent_type.substring(0, 4).toUpperCase()}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Control Bar */}
          <div className="teleplay-controls">
            <div className="control-group">
              <button
                className="control-btn"
                onClick={handleFirst}
                disabled={currentIndex <= 0}
                title="First Beat"
              >
                <SkipBack size={14} />
              </button>
              <button
                className="control-btn"
                onClick={handleBack}
                disabled={currentIndex <= 0}
                title="Step Backward"
              >
                <ArrowLeft size={14} />
              </button>
              <button
                className={`control-btn control-btn--play ${isPlaying ? "playing" : ""}`}
                onClick={togglePlay}
                title={isPlaying ? "Pause Playback" : "Auto-Play Playback"}
              >
                {isPlaying ? <Pause size={14} /> : <Play size={14} />}
              </button>
              <button
                className="control-btn"
                onClick={handleForward}
                disabled={currentIndex >= beats.length - 1}
                title="Step Forward"
              >
                <ArrowRight size={14} />
              </button>
              <button
                className="control-btn"
                onClick={handleLast}
                disabled={currentIndex >= beats.length - 1}
                title="Latest Beat"
              >
                <SkipForward size={14} />
              </button>
            </div>

            <button
              className={`live-badge-btn ${isLive ? "live" : ""}`}
              onClick={toggleLive}
              title={isLive ? "Disconnect Live Sync to explore history" : "Lock view to latest live events"}
            >
              <span className="live-dot" />
              <span>LIVE TRACKING</span>
            </button>
          </div>

          {/* Detail Display Card */}
          {currentBeat && (
            <div className="teleplay-card">
              <div className="teleplay-card__meta">
                <div className={`agent-badge ${getAgentClass(currentBeat.agent_type)}`}>
                  {getAgentIcon(currentBeat.agent_type)}
                  <span>{currentBeat.agent_type.toUpperCase()}</span>
                </div>
                <div className="timestamp-badge">
                  <Clock size={12} className="text-muted" />
                  <span>{new Date(currentBeat.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>

              <div className="teleplay-card__act">
                <h2>{currentBeat.act}</h2>
              </div>

              <div className="teleplay-card__narrative">
                <h3>REASONING TRAIL</h3>
                <div className="narrative-content">
                  {currentBeat.narrative.split("\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              </div>

              {Object.keys(currentBeat.context_metadata).length > 0 && (
                <div className="teleplay-card__context">
                  <h3>TACTICAL METADATA</h3>
                  <div className="metadata-grid">
                    {Object.entries(currentBeat.context_metadata).map(([key, val]) => (
                      <div key={key} className="metadata-item">
                        <span className="metadata-key">{key}:</span>
                        <span className="metadata-val">
                          {typeof val === "object" ? JSON.stringify(val) : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
