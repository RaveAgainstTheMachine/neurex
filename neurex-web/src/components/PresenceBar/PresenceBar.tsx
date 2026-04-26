import { useStore } from "../../lib/store";
import { User, Bot } from "lucide-react";
import "./PresenceBar.css";

export function PresenceBar() {
  const presence = useStore((s) => s.presence);

  return (
    <div className="presence-bar">
      {presence.length === 0 ? (
        <div className="presence-bar__empty">No other collaborators</div>
      ) : (
        <div className="presence-avatars">
          {presence.map((p, idx) => (
            <div 
              key={p.user_id || idx} 
              className="presence-avatar" 
              title={`${p.user_id || 'Unknown'} ${p.active_file ? `in ${p.active_file.split('/').pop()}` : ''}`}
            >
              {(p.user_id || "").toLowerCase().includes("agent") ? (
                <Bot size={14} className="avatar-icon avatar-icon--agent" />
              ) : (
                <User size={14} className="avatar-icon" />
              )}
              <span className="avatar-status"></span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
