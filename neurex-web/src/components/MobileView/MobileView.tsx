import React, { useState } from "react";
import { 
  MessageSquare, Files, Cpu, Settings,
  Terminal as TerminalIcon
} from "lucide-react";
import { useStore } from "../../lib/store";
import { AIPanel } from "../AIPanel/AIPanel";
import { FileExplorer } from "../FileExplorer/FileExplorer";
import { InfraPanel } from "../InfraPanel/InfraPanel";
import { SettingsPanel } from "../SettingsPanel/SettingsPanel";
import { Terminal } from "../Terminal/Terminal";
import { ConversationList } from "../ConversationList/ConversationList";
import "./MobileView.css";

interface MobileViewProps {
  send: (p: any) => void;
}

export function MobileView({ send }: MobileViewProps) {
  const [activeTab, setActiveTab] = useState<"chat" | "files" | "infra" | "terminal" | "settings">("chat");
  const { activeConversationId, theme } = useStore();

  const renderContent = () => {
    switch (activeTab) {
      case "chat":
        return <AIPanel send={send} conversationId={activeConversationId} isActive={true} />;
      case "files":
        return <FileExplorer />;
      case "infra":
        return <InfraPanel onExpand={() => {}} currentSize={100} />;
      case "terminal":
        return (
          <div className="mobile-terminal-wrapper">
             <Terminal 
                sessionId={activeConversationId}
                isActive={true}
                onInput={(data) => send({ type: "terminal_input", sessionId: activeConversationId, data })} 
                onResize={(rows, cols) => send({ type: "terminal_resize", sessionId: activeConversationId, rows, cols })} 
              />
          </div>
        );
      case "settings":
        return <SettingsPanel />;
      default:
        return null;
    }
  };

  return (
    <div className="mobile-view animate-scale">
      <div className="mobile-view__header">
        <div className="mobile-view__logo">
          <span className="text-purple">⬡</span> NEUREX
        </div>
        <div className="mobile-view__status">
           <div className="swarm-pulse swarm-pulse--active" />
        </div>
      </div>

      <div className="mobile-view__content">
        {renderContent()}
      </div>

      <div className="mobile-nav">
        <button 
          className={`mobile-nav__item ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <MessageSquare size={20} />
          <span>Chat</span>
        </button>
        <button 
          className={`mobile-nav__item ${activeTab === 'files' ? 'active' : ''}`}
          onClick={() => setActiveTab('files')}
        >
          <Files size={20} />
          <span>Files</span>
        </button>
        <button 
          className={`mobile-nav__item ${activeTab === 'terminal' ? 'active' : ''}`}
          onClick={() => setActiveTab('terminal')}
        >
          <TerminalIcon size={20} />
          <span>Shell</span>
        </button>
        <button 
          className={`mobile-nav__item ${activeTab === 'infra' ? 'active' : ''}`}
          onClick={() => setActiveTab('infra')}
        >
          <Cpu size={20} />
          <span>Infra</span>
        </button>
        <button 
          className={`mobile-nav__item ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          <Settings size={20} />
          <span>Config</span>
        </button>
      </div>
    </div>
  );
}
