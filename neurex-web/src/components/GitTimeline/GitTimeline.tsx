// neurex-web/src/components/GitTimeline/GitTimeline.tsx
import { useEffect, useState } from "react";
import { useStore } from "../../lib/store";
import { History, GitCommit, User } from "lucide-react";
import { API_BASE } from "../../lib/config";
import "./GitTimeline.css";

interface Commit {
  hash: string;
  author: string;
  time: number;
  summary: string;
}

export function GitTimeline() {
  const { activeFile, token } = useStore();
  const [history, setHistory] = useState<Commit[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeFile || !token) return;

    setLoading(true);
    fetch(`${API_BASE}/api/git/history?path=${activeFile}`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setHistory(data?.history || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, [activeFile, token]);

  if (!activeFile) {
    return (
      <div className="git-timeline-empty">
        <History size={40} className="empty-icon" />
        <p>Select a file to view history</p>
      </div>
    );
  }

  return (
    <div className="git-timeline">
      <div className="git-timeline__header">
        <History size={14} className="text-cyan" />
        <span>FILE TIMELINE</span>
      </div>

      <div className="git-timeline__content">
        {loading ? (
          <div className="loading-shimmer">Scanning repository...</div>
        ) : history.length === 0 ? (
          <div className="no-history">No local history found.</div>
        ) : (
          <div className="timeline-list">
            <div className="timeline-line" />
            {history.map((commit, i) => (
              <div key={commit.hash} className="timeline-item animate-slide-in" style={{ animationDelay: `${i * 0.05}s` }}>
                <div className="timeline-node">
                  <GitCommit size={10} />
                </div>
                <div className="timeline-card glass">
                  <div className="timeline-card__header">
                    <span className="commit-hash">{commit.hash}</span>
                    <span className="commit-date">
                      {new Date(commit.time * 1000).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="commit-summary">{commit.summary}</div>
                  <div className="commit-author">
                    <User size={10} />
                    <span>{commit.author}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
