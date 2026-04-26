// src/components/ConversationList/ConversationList.tsx
import { useEffect } from "react";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { useStore } from "../../lib/store";
import "./ConversationList.css";

const API_BASE = "http://127.0.0.1:8000";

export function ConversationList() {
  const { 
    conversations, setConversations, 
    activeConversationId, setActiveConversation, 
    newConversation 
  } = useStore();

  const fetchConversations = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/chat/conversations`);
      const data = await r.json();
      setConversations(data);
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [activeConversationId]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this conversation?")) return;
    
    try {
      await fetch(`${API_BASE}/api/chat/${id}`, { method: "DELETE" });
      if (id === activeConversationId) {
        newConversation();
      } else {
        fetchConversations();
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  return (
    <div className="conv-list">
      <div className="conv-list__header">
        <span className="conv-list__title">Conversations</span>
        <button className="icon-btn" onClick={newConversation} title="New Chat">
          <Plus size={14} />
        </button>
      </div>
      <div className="conv-list__items">
        {conversations.length === 0 && (
          <div className="conv-list__empty">No active chats</div>
        )}
        {conversations.map((c) => (
          <div
            key={c.conversation_id}
            className={`conv-item ${c.conversation_id === activeConversationId ? "conv-item--active" : ""}`}
            onClick={() => setActiveConversation(c.conversation_id)}
          >
            <MessageSquare size={14} className="conv-item__icon" />
            <div className="conv-item__content">
              <div className="conv-item__id">{(c.conversation_id || "").slice(0, 8) || "unknown"}</div>
              <div className="conv-item__date">
                {c.last_message ? new Date(c.last_message).toLocaleDateString() : "No date"}
              </div>
            </div>
            <button 
              className="conv-item__delete" 
              onClick={(e) => handleDelete(e, c.conversation_id)}
            >
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
