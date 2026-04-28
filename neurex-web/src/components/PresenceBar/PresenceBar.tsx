// neurex-web/src/components/PresenceBar/PresenceBar.tsx
"use client";

import { useStore } from "../../lib/store";
import { User, Bot, Eye, Users } from "lucide-react";
import "./PresenceBar.css";

export function PresenceBar() {
  const { presence, activeFile, setPendingJump } = useStore();

  const handleFollow = (p: any) => {
    if (p.active_file && p.cursor) {
      setPendingJump(p.active_file, p.cursor.line);
    }
  };

  return (
    <div className="presence-bar">
      <div className="presence-bar__info">
        <Users size={12} className="text-muted" />
        <span>Collaborators</span>
      </div>
      
      <div className="presence-avatars">
        {presence.length === 0 && (
          <span className="presence-solo">Solo Session</span>
        )}
        
        {presence.map((p, idx) => {
          const isAgent = (p.user_id || "").toLowerCase().includes("agent");
          const isSameFile = p.active_file === activeFile;
          
          return (
            <div 
              key={p.user_id || idx} 
              className={`presence-avatar ${isSameFile ? 'active-here' : ''}`}
              onClick={() => handleFollow(p)}
              title={`${p.user_id} is editing ${p.active_file || 'nothing'}. Click to follow.`}
            >
              <div className={`avatar-box ${isAgent ? 'avatar-box--agent' : ''}`}>
                {isAgent ? <Bot size={12} /> : <User size={12} />}
              </div>
              <div className="avatar-label">
                <span className="avatar-name">{p.user_id.split('@')[0]}</span>
                {isSameFile && (
                  <span title="Viewing this file">
                    <Eye size={10} className="text-cyan" />
                  </span>
                )}
              </div>
              <span className="avatar-pulse"></span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
