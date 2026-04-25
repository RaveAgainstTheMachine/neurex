import { useState, useEffect, useCallback } from "react";
import { Download, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import "./UpdateNotifier.css";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const CHECK_INTERVAL_MS = 30 * 60 * 1000; // 30 minutes

interface UpdateStatus {
  current_version: string;
  latest_version: string | null;
  update_available: boolean;
  update_ready: boolean;
  pulling: boolean;
  error: string | null;
}

export function UpdateNotifier() {
  const [status, setStatus] = useState<UpdateStatus | null>(null);
  const [open, setOpen] = useState(false);
  const [applying, setApplying] = useState(false);

  const checkStatus = useCallback(async (fullCheck = false) => {
    try {
      const endpoint = fullCheck ? "/api/update/check" : "/api/update/status";
      const res = await fetch(`${API}${endpoint}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token") ?? ""}` },
      });
      if (res.ok) setStatus(await res.json());
    } catch {
      // silently fail — update check is non-critical
    }
  }, []);

  // Full check on load, then poll status every 30 min
  useEffect(() => {
    checkStatus(true);
    const interval = setInterval(() => checkStatus(true), CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [checkStatus]);

  // Poll status every 5s while a pull is in progress
  useEffect(() => {
    if (!status?.pulling) return;
    const interval = setInterval(() => checkStatus(false), 5000);
    return () => clearInterval(interval);
  }, [status?.pulling, checkStatus]);

  const applyUpdate = async () => {
    setApplying(true);
    try {
      await fetch(`${API}/api/update/apply`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token") ?? ""}` },
      });
      checkStatus(false);
    } finally {
      setApplying(false);
    }
  };

  if (!status?.update_available && !status?.update_ready) return null;

  const isReady   = status.update_ready;
  const isPulling = status.pulling;

  return (
    <div className="update-notifier">
      <button
        className={`update-badge ${isReady ? "update-badge--ready" : "update-badge--available"}`}
        onClick={() => setOpen(v => !v)}
        title={isReady ? "Restart to activate update" : `Update available: ${status.latest_version}`}
      >
        {isReady ? (
          <><CheckCircle size={12} /> Restart to update</>
        ) : isPulling ? (
          <><RefreshCw size={12} className="spin" /> Downloading…</>
        ) : (
          <><Download size={12} /> {status.latest_version} available</>
        )}
      </button>

      {open && (
        <div className="update-popover">
          <div className="update-popover__header">
            <span>Neurex Update</span>
            <button className="update-popover__close" onClick={() => setOpen(false)}>✕</button>
          </div>
          <div className="update-popover__body">
            <div className="update-version-row">
              <span className="update-label">Current</span>
              <span className="update-value">{status.current_version}</span>
            </div>
            <div className="update-version-row">
              <span className="update-label">Available</span>
              <span className="update-value update-value--new">{status.latest_version}</span>
            </div>

            {status.error && (
              <div className="update-error">
                <AlertCircle size={14} /> {status.error}
              </div>
            )}

            {isReady ? (
              <div className="update-ready-msg">
                ✅ New version is downloaded and ready. Reload the page to activate it.
              </div>
            ) : (
              <button
                className="update-apply-btn"
                onClick={applyUpdate}
                disabled={isPulling || applying}
              >
                {isPulling || applying ? (
                  <><RefreshCw size={14} className="spin" /> Downloading images…</>
                ) : (
                  <><Download size={14} /> Download Update</>
                )}
              </button>
            )}

            <p className="update-note">
              Neurex pulls new Docker images in the background. No service interruption until you reload.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
