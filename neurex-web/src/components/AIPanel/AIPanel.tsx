import React, { useRef, useEffect, useState, useMemo } from "react";
import { 
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent
} from '@dnd-kit/core';
import {
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { CustomSelect } from '../CustomSelect/CustomSelect';
import { VoiceLangSelect } from '../CustomSelect/VoiceLangSelect';
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import { Loader2, Trash2, CheckCircle2, XCircle, ArrowUp, Mic, Volume2, Paperclip, Shield, Plus, Brain } from "lucide-react";
import { useStore } from "../../lib/store";
import type { TaskNode } from "../../lib/types";
import toast from "react-hot-toast";
import "./AIPanel.css";

import { API_BASE } from "../../lib/config";

const STATUS_COLOR = new Map<string, string>([
  ["PENDING",          "var(--status-pending)"],
  ["THINKING",         "var(--status-thinking)"],
  ["WRITING",          "var(--status-writing)"],
  ["TESTING",          "var(--status-writing)"],
  ["DONE",             "var(--status-done)"],
  ["FAILED",           "var(--status-failed)"],
  ["CANCELLED",        "var(--status-failed)"],
  ["AWAITING_APPROVAL","var(--status-approval)"]
]);

const STATUS_LABEL = new Map<string, string>([
  ["PENDING", "Pending"],
  ["THINKING", "Thinking…"],
  ["WRITING", "Writing…"],
  ["TESTING", "Testing…"],
  ["DONE", "Done"],
  ["FAILED", "Failed"],
  ["CANCELLED", "Cancelled"],
  ["AWAITING_APPROVAL", "Awaiting Approval"]
]);


const AUTONOMY_OPTIONS = [
  { value: "restricted", label: "Restricted" },
  { value: "limited", label: "Limited" },
  { value: "staging", label: "Staging" },
  { value: "full", label: "Full Auto" }
];

const VOICE_OPTIONS = [
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "narrator", label: "Narrator" },
  { value: "explorer", label: "Explorer" },
  { value: "scientist", label: "Scientist" },
  { value: "system", label: "System" },
  { value: "core", label: "Core" },
  { value: "companion", label: "Companion" }
];

const LANG_OPTIONS = [
  { value: "en-US", label: "EN" },
  { value: "fr-FR", label: "FR" },
  { value: "ar-SA", label: "AR" },
  { value: "es-ES", label: "ES" },
  { value: "de-DE", label: "DE" },
  { value: "it-IT", label: "IT" },
  { value: "ja-JP", label: "JA" },
  { value: "zh-CN", label: "ZH" },
];

const TRANSLATIONS = {
  chat: "Chat",
  tasks: "Tasks",
  history: "History",
  noChats: "No previous chats.",
  askAnything: "Ask Neurex anything",
  poweredBy: "Powered by Open Source Intelligence.",
  authWaiting: "Neurex is waiting for your authorization to execute this plan.",
  noTasksYet: "No tasks yet. Ask Neurex to build something.",
  step: "Step ",
  awaitingGov: "Awaiting Governance Approval",
};



interface AIPanelProps {
  send: (payload: object) => void;
  conversationId: string;
  isActive?: boolean;
}

export function AIPanel({ send, conversationId, isActive = true }: AIPanelProps) {
  const [tab, setTab] = useState<"chat" | "tasks" | "history">("chat");
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Phase 44.18: Strict State Selection (Prevent Chat churn)
  const messages = useStore(s => s.messages);
  const tasks = useStore(s => s.tasks);
  const workspaceFolders = useStore(s => s.workspaceFolders);
  const wsStatus = useStore(s => s.wsStatus);
  const clearTasks = useStore(s => s.clearTasks);
  const conversations = useStore(s => s.conversations);
  const setConversations = useStore(s => s.setConversations);
  const setActiveConversation = useStore(s => s.setActiveConversation);
  const newConversation = useStore(s => s.newConversation);
  const preferredModel = useStore(s => s.preferredModel);
  const setPreferredModel = useStore(s => s.setPreferredModel);
  const speechLang = useStore(s => s.speechLang);
  const setSpeechLang = useStore(s => s.setSpeechLang);
  const activeFile = useStore(s => s.activeFile);
  const fileTree = useStore(s => s.fileTree);
  const infraRegistry = useStore(s => s.infraRegistry);
  const autonomyLevel = useStore(s => s.autonomyLevel);
  const setAutonomyLevel = useStore(s => s.setAutonomyLevel);

  const [isListening, setIsListening] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [approvalTrayOpen, setApprovalTrayOpen] = useState(false);
  const [historySearch, setHistorySearch] = useState("");
  const [voicePreset, setVoicePreset] = useState(() => {
    const saved = localStorage.getItem("neurex_voice_preset");
    const migrationMap: Record<string, string> = {
      freeman: "narrator",
      attenborough: "explorer",
      rick: "scientist",
      glados: "system",
      hal: "core",
      samantha: "companion"
    };
    return (saved && migrationMap[saved]) || saved || "male";
  });
  const [autoSpeak, setAutoSpeak] = useState(() => localStorage.getItem("neurex_auto_speak") === "true");
  const [mentionQuery, setMentionQuery] = useState("");
  const [showMentions, setShowMentions] = useState(false);
  const [mentionIndex, setMentionIndex] = useState(0);
  const lastSpokenRef = useRef<string>("");
  const recognitionRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Initialize Web Speech API for voice dictation
    const handleVoicesChanged = () => {
      window.speechSynthesis.getVoices();
    };
    window.speechSynthesis.onvoiceschanged = handleVoicesChanged;

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      // Use browser language or fallback
      recognition.lang = navigator.language || 'en-US';
      recognition.onresult = (event: any) => {
        let finalTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const result = event.results.item(i);
          if (result && result.isFinal) {
            const alternative = result.item(0);
            if (alternative) {
              finalTranscript += alternative.transcript;
            }
          }
        }
        if (finalTranscript) {
          setInput(prev => {
            const newVal = prev + (prev ? " " : "") + finalTranscript;
            // Auto-send if it sounds like a command (optional heuristic)
            return newVal;
          });
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        // We could auto-send here if we wanted
      };
      recognition.onerror = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
  }, []);
  const nodes = Object.values(tasks || {}).sort(
    (a, b) => new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime()
  );

  const isWorking = nodes.some((t) =>
    ["THINKING", "WRITING", "TESTING"].includes(t.status)
  );


  useEffect(() => {
    if (!autoSpeak || messages.length === 0) return;
    const lastMsg = messages.slice(-1)[0];
    
    // Only speak if it's the assistant and it's a new message
    if (lastMsg && lastMsg.role === "assistant" && lastMsg.content !== lastSpokenRef.current) {
      // Small delay to ensure streaming is truly done
      const timer = setTimeout(() => {
        speakContent(lastMsg.content);
        lastSpokenRef.current = lastMsg.content;
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [messages, isWorking, autoSpeak]);

  const speakContent = async (content: string) => {
    if (!content) return;
    
    // Stop any existing audio
    const existingAudio = (window as any)._neurex_audio;
    if (existingAudio) {
      existingAudio.pause();
      existingAudio.src = "";
    }

    fallbackBrowserSpeak(content);
  };

  const fallbackBrowserSpeak = (content: string) => {
    window.speechSynthesis.resume();
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(content);
    utterance.lang = speechLang;
    const voices = window.speechSynthesis.getVoices();
    
    if (voices.length > 0) {
      // Find closest browser voice
      const v = voices.find(v => v.lang.startsWith("en")) || voices[0];
      utterance.voice = v;
      // Apply rough pitch/rate mods
      if (voicePreset === "narrator") { utterance.pitch = 0.75; utterance.rate = 0.85; }
      else if (voicePreset === "explorer") { utterance.pitch = 0.95; utterance.rate = 0.82; }
      else if (voicePreset === "scientist") { utterance.pitch = 1.35; utterance.rate = 1.25; }
    }

    window.speechSynthesis.speak(utterance);
  };

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.lang = speechLang;
        recognitionRef.current.start();
        setIsListening(true);
      }
    }
  };


  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, tab]);

  // Fetch conversation list when history tab is opened
  useEffect(() => {
    if (tab === "history" && isActive) {
      const rootPath = workspaceFolders.length > 0 ? workspaceFolders[0] : "";
      const url = rootPath 
        ? `${API_BASE}/api/chat/conversations?workspace_path=${encodeURIComponent(rootPath)}`
        : `${API_BASE}/api/chat/conversations`;
      fetch(url)
        .then(r => r.json())
        .then(data => {
          if (Array.isArray(data)) setConversations(data);
        })
        .catch(() => {});
    }
  }, [tab, setConversations, isActive, workspaceFolders]);

  // Fetch tasks for the current conversation
  useEffect(() => {
    if (tab === "tasks" && isActive) {
      fetch(`${API_BASE}/api/tasks/?graph_id=${conversationId}`)
        .then(r => r.json())
        .then(ts => {
          if (Array.isArray(ts)) {
            ts.forEach((t: TaskNode) => useStore.getState().upsertTask(t));
          }
        })
        .catch(() => {});
    }
  }, [tab, conversationId, isActive]);

  const insertMention = (forceValue?: string) => {
    const idx = mentionIndex % filteredMentions.length;
    const val = forceValue || filteredMentions.slice(idx, idx + 1)[0];
    if (!val) return;
    const cursor = inputRef.current?.selectionStart || 0;
    const textBefore = input.slice(0, cursor).replace(/@\w*$/, "@" + val + " ");
    const textAfter = input.slice(cursor);
    setInput(textBefore + textAfter);
    setShowMentions(false);
    setTimeout(() => inputRef.current?.focus(), 10);
  };

  const allFiles = useMemo(() => {
    const files: string[] = [];
    const walk = (nodes: any[]) => {
      nodes.forEach(n => {
        if (n.type === "file") files.push(n.name);
        if (n.children) walk(n.children);
      });
    };
    walk(fileTree || []);
    return files;
  }, [fileTree]);

  const filteredMentions = useMemo(() => {
    return ["codebase", "workspace", "terminal", "web", ...allFiles]
      .filter(m => m.toLowerCase().includes(mentionQuery.toLowerCase()))
      .slice(0, 10);
  }, [allFiles, mentionQuery]);

  const handleSend = () => {
    const content = input.trim();
    if (!content || wsStatus !== "connected" || isWorking) return;
    useStore.getState().addMessage({ role: "user", content });
    send({ type: "message", content });
    setInput("");
    inputRef.current?.focus();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/files/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.status === "uploaded") {
        const msg = `I have uploaded a file named ${data.filename} to ${data.path}. Please review it.`;
        useStore.getState().addMessage({ role: "user", content: msg });
        send({ type: "message", content: msg });
      }
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleClear = async () => {
    try {
      await fetch(`${API_BASE}/api/tasks/`, { method: "DELETE" });
      clearTasks();
    } catch { /* intentional */ }
  };

  const handleApprovePlan = (graphId: string) => {
    send({ type: "approve_plan", graph_id: graphId });
    setApprovalTrayOpen(false);
  };

  const handleDenyPlan = async (graphId: string) => {
    try {
      await fetch(`${API_BASE}/api/tasks/${graphId}/cancel`, { method: "POST" });
    } catch { /* intentional */ }
    setApprovalTrayOpen(false);
  };

  const handleApproveShell = (taskId: string, approved: boolean) => {
    send({ type: "approve_shell", task_id: taskId, approved });
    setApprovalTrayOpen(false);
  };

  const doneCount = nodes.filter((n) => n.status?.toUpperCase() === "DONE").length;

  const [_headerOrder, setHeaderOrder] = useState<string[]>(() => {
    const saved = localStorage.getItem("neurex_header_order");
    return saved ? JSON.parse(saved) : ["tabs", "model", "autonomy", "voice", "actions"];
  });

  const _sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const _handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setHeaderOrder((items) => {
        const oldIndex = items.indexOf(active.id as string);
        const newIndex = items.indexOf(over.id as string);
        const next = arrayMove(items, oldIndex, newIndex);
        localStorage.setItem("neurex_header_order", JSON.stringify(next));
        return next;
      });
    }
  };

  const MODEL_OPTIONS = useMemo(() => {
    if (infraRegistry.length === 0) {
      // Fallback to currently preferred model if registry is not yet loaded
      return [{ value: preferredModel, label: preferredModel, group: "Active" }];
    }
    return infraRegistry.map(m => ({
      value: m.name,
      label: `${m.name} (${m.params || 'Local'})`,
      group: m.is_community ? "Community" : "Open Source"
    }));
  }, [infraRegistry, preferredModel]);

  const headerElements: Record<string, React.ReactNode> = {
    tabs: (
      <div className="ai-panel__tabs">
        <button className={`ai-tab ${tab === "chat" ? "ai-tab--active" : ""}`} onClick={() => setTab("chat")}>{TRANSLATIONS.chat}</button>
        <button className={`ai-tab ${tab === "tasks" ? "ai-tab--active" : ""}`} onClick={() => setTab("tasks")}>
          {TRANSLATIONS.tasks} {nodes.length > 0 && <span className="ai-tab__badge">{doneCount}/{nodes.length}</span>}
        </button>
        <button className={`ai-tab ${tab === "history" ? "ai-tab--active" : ""}`} onClick={() => setTab("history")}>{TRANSLATIONS.history}</button>
      </div>
    ),
    model: (
      <CustomSelect 
        className="model-selector"
        value={preferredModel}
        onChange={(val) => setPreferredModel(val)}
        options={MODEL_OPTIONS}
        title="Select Active LLM"
      />
    ),
    autonomy: (
      <CustomSelect 
        className="autonomy-selector"
        value={autonomyLevel}
        onChange={(val) => setAutonomyLevel(val)}
        options={AUTONOMY_OPTIONS}
        title="Set Autonomy Level"
      />
    ),
    voice: (
      <CustomSelect 
        className="voice-selector" 
        value={voicePreset} 
        onChange={(val) => setVoicePreset(val)} 
        options={VOICE_OPTIONS}
        title="TTS Voice Personality"
      />
    ),
    actions: (
      <button className="icon-btn" onClick={newConversation} title="New Chat">
        <Trash2 size={14} style={{ transform: "rotate(45deg)" }} />
      </button>
    )
  };

  return (
    <div className="ai-panel">
      {/* Header */}
      <div className="ai-panel__header">
        {headerElements.tabs}
        <div className="ai-panel__header-actions">
          <button className="icon-btn" onClick={newConversation} title="New Chat">
            <Plus size={14} />
          </button>
        </div>
      </div>

      {/* History tab */}
      {tab === "history" && (
        <div className="ai-history">
          <div className="ai-history__search">
            <input
              type="text"
              placeholder="Search chats…"
              value={historySearch}
              onChange={e => setHistorySearch(e.target.value)}
              className="ai-history__search-input"
            />
          </div>
          <div className="ai-history__list">
            {conversations.length === 0 && <div className="ai-history__empty">{TRANSLATIONS.noChats}</div>}
            {conversations
              .filter(c => {
                const q = historySearch.toLowerCase();
                return !q || (c.title || c.conversation_id).toLowerCase().includes(q);
              })
              .map((c) => {
                const isActive = c.conversation_id === conversationId;
                const relTime = c.last_message ? (() => {
                  const diff = Date.now() - new Date(c.last_message).getTime();
                  if (diff < 60000) return "just now";
                  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
                  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
                  return `${Math.floor(diff / 86400000)}d ago`;
                })() : "—";
                return (
                  <button
                    key={c.conversation_id}
                    className={`history-item ${isActive ? "history-item--active" : ""}`}
                    onClick={() => { setHistorySearch(""); setActiveConversation(c.conversation_id); setTab("chat"); }}
                    title={c.conversation_id}
                  >
                    <div className="history-item__row">
                      {isActive && <span className="history-item__dot" />}
                      <span className="history-item__title">
                        {c.title || c.conversation_id.slice(0, 8) + "…"}
                      </span>
                    </div>
                    <div className="history-item__date">{relTime}</div>
                  </button>
                );
              })}
          </div>
        </div>
      )}

      {/* Chat tab */}
      {tab === "chat" && (
        <>
          <div ref={scrollRef} className="ai-messages">
            {showMentions && filteredMentions.length > 0 && (
              <div className="ai-mentions">
                {filteredMentions.map((m, i) => (
                  <div 
                    key={m} 
                    className={`mention-item ${i === (mentionIndex % filteredMentions.length) ? "mention-item--active" : ""}`}
                    onClick={() => insertMention(m)}
                  >
                    {m}
                  </div>
                ))}
              </div>
            )}
            {messages.length === 0 && (
              <div className="ai-messages__empty">
                <div className="ai-messages__empty-icon">⬡</div>
                <div>{TRANSLATIONS.askAnything}</div>
                <div className="ai-messages__attribution">
                  {TRANSLATIONS.poweredBy}
                </div>
              </div>
            )}
            {messages.filter(m => m.content && typeof m.content === 'string' && m.content.trim() !== "").map((msg, msgIdx) => (
              <div key={msg.id} id={msg.id ? `msg-${msg.id}` : `msg-idx-${msgIdx}`} className={`message message--${msg.role}`}>
                <div className="message__content">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                    urlTransform={(value: string) => value}
                    components={{
                      code({ node, inline, className, children }: any) {
                        const match = /language-(\w+)/.exec(className || "");
                        const codeContent = String(children).replace(/\n$/, "");
                        
                        if (!inline && match) {
                          if (match[1] === "thinking") {
                            return (
                              <div className="ai-thinking-block">
                                <div className="ai-thinking-header">
                                  <Brain size={12} /> Intermediate Thinking
                                </div>
                                <div className="ai-thinking-content">{children}</div>
                              </div>
                            );
                          }
                          
                          if (match[1] === "json") {
                            try {
                              const parsed = JSON.parse(codeContent);
                              if (parsed && typeof parsed === "object") {
                                if (parsed.name && parsed.arguments) {
                                  // This is a tool call raw json, hide it from the chat UI
                                  return null;
                                }
                              }
                            } catch (e) {
                              // If it's a streaming partial JSON, we might want to hide it too
                              // by checking if it starts with a tool call signature.
                              if (codeContent.trim().startsWith('{\n  "name":') || codeContent.trim().startsWith('{"name":')) {
                                return null;
                              }
                            }
                          }

                          return (
                            <div className="code-block-container">
                              <div className="code-block-header">
                                <span className="code-block-lang">{match[1]}</span>
                                <button 
                                  className="code-block-apply" 
                                  onClick={() => {
                                    if (activeFile) {
                                      useStore.getState().setFileContent(activeFile, codeContent);
                                      toast.success("Code applied to editor");
                                    }
                                  }}
                                  title="Apply to active file"
                                >
                                  <ArrowUp size={12} /> Apply
                                </button>
                              </div>
                              <pre className={className}>
                                <code>{children}</code>
                              </pre>
                            </div>
                          );
                        }
                        return <code className={className}>{children}</code>;
                      },
                      table({ node, children, className }: any) {
                        const thead = React.Children.toArray(children).find((c: any) => c.type === "thead") as any;
                        const headers: string[] = [];
                        if (thead && thead.props && thead.props.children) {
                          const tr = thead.props.children;
                          React.Children.forEach(tr.props.children, (th: any) => {
                            headers.push(extractText(th).trim().toLowerCase());
                          });
                        }
                        const isPlanTable = headers.includes("step") && headers.includes("agent");
                        if (isPlanTable) {
                          return <PlanTimeline>{children}</PlanTimeline>;
                        }
                        return <table className={className}>{children}</table>;
                      },
                      a({ node, children, href, ...props }: any) {
                        const { className, title } = props || {};
                        if (href && href.startsWith("file://")) {
                          return (
                            <a 
                              href="#" 
                              onClick={async (e) => {
                                e.preventDefault();
                                const path = href.replace("file://", "");
                                const state = useStore.getState();
                                const root = state.workspaceFolders?.[0] || "";
                                try {
                                  const { api } = await import("../../lib/api");
                                  const data = await api.get<any>(`/api/files/read?path=${encodeURIComponent(path)}&root_path=${encodeURIComponent(root)}`);
                                  state.openFile(path, data.content || "", "markdown", true, root);
                                } catch (err) {
                                  console.error("Failed to fetch markdown file content", err);
                                  state.openFile(path, "", "markdown", true, root);
                                }
                              }}
                              className={className}
                              title={title}
                            >
                              {children}
                            </a>
                          );
                        }
                        return <a href={href} target="_blank" rel="noreferrer" className={className} title={title}>{children}</a>;
                      }
                    }}
                  >
                    {msg.content.replace(/<think>/g, "```thinking\n").replace(/<\/think>/g, "\n```\n")}
                  </ReactMarkdown>
                </div>
                {msg.role === "assistant" && msg.graph_id && nodes.some(n => n.graph_id === msg.graph_id && n.status?.toUpperCase() === "AWAITING_APPROVAL") && (
                  <div className="message__inline-approval">
                    <div className="inline-approval-card">
                      <div className="inline-approval-card__title">
                        <Shield size={14} style={{ flexShrink: 0 }} /> {TRANSLATIONS.awaitingGov}
                      </div>
                      <p>{TRANSLATIONS.authWaiting}</p>
                      <div className="inline-approval-card__actions">
                        <button 
                          className="btn btn--purple" 
                          onClick={() => handleApprovePlan(msg.graph_id!)}
                        >
                          <CheckCircle2 size={13} /> Approve & Execute Plan
                        </button>
                        <button
                          className="btn btn--red"
                          onClick={() => handleDenyPlan(msg.graph_id!)}
                        >
                          <XCircle size={13} /> Deny
                        </button>
                      </div>
                    </div>
                  </div>
                )}
                {msg.role === "assistant" && (
                  <button 
                    className="icon-btn message__tts" 
                    onClick={() => speakContent(msg.content)}
                    title="Read Aloud"
                  >
                    <Volume2 size={12} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <div className="ai-input">
            <div className={`ai-input__wrapper ${isWorking ? 'ai-input__wrapper--working' : ''}`}>
              <div className="ai-input__textarea-container">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => {
                    const val = e.target.value;
                    setInput(val);
                    
                    // Mention detection
                    const cursor = e.target.selectionStart;
                    const textBefore = val.slice(0, cursor);
                    const match = textBefore.match(/@(\w*)$/);
                    
                    if (match) {
                      setMentionQuery(match[1]);
                      setShowMentions(true);
                      setMentionIndex(0);
                    } else {
                      setShowMentions(false);
                    }

                    // Auto-expand logic
                    const el = inputRef.current;
                    if (el) {
                      el.style.height = "auto";
                      el.style.height = Math.min(el.scrollHeight, window.innerHeight * 0.4) + "px";
                    }
                  }}
                  onKeyDown={(e) => {
                    if (showMentions) {
                      if (e.key === "ArrowDown") { e.preventDefault(); setMentionIndex(i => i + 1); }
                      if (e.key === "ArrowUp") { e.preventDefault(); setMentionIndex(i => i - 1); }
                      if (e.key === "Enter" || e.key === "Tab") {
                        e.preventDefault();
                        insertMention();
                      }
                      if (e.key === "Escape") setShowMentions(false);
                      return;
                    }
                    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
                  }}
                  placeholder={wsStatus !== "connected" ? "Connecting…" : isWorking ? "Agent is working…" : isListening ? "Listening..." : "Ask Neurex anything…"}
                  disabled={wsStatus !== "connected" || isWorking}
                  rows={1}
                  className="ai-input__textarea"
                />
                <button 
                  className="ai-input__send-embedded"
                  onClick={handleSend}
                  disabled={!input.trim() || wsStatus !== "connected" || isWorking}
                  title="Send Message (Enter)"
                >
                  <ArrowUp size={18} strokeWidth={2.5} />
                </button>
              </div>
              <div className="ai-input__footer">
                <div className="ai-input__footer-left">
                  <CustomSelect 
                    className="mini model-selector-footer"
                    value={preferredModel}
                    onChange={(val) => setPreferredModel(val)}
                    options={MODEL_OPTIONS}
                    title="Preferred Model"
                  />
                  <CustomSelect 
                    className="mini autonomy-selector-footer"
                    value={autonomyLevel}
                    onChange={(val) => setAutonomyLevel(val)}
                    options={AUTONOMY_OPTIONS}
                    title="Set Autonomy Level"
                  />
                </div>
                <div className="ai-input__footer-right">
                  <VoiceLangSelect 
                    voiceValue={voicePreset}
                    voiceOnChange={(val) => {
                      setVoicePreset(val);
                      localStorage.setItem("neurex_voice_preset", val);
                    }}
                    voiceOptions={VOICE_OPTIONS}
                    autoSpeak={autoSpeak}
                    onAutoSpeakToggle={() => {
                      const next = !autoSpeak;
                      setAutoSpeak(next);
                      localStorage.setItem("neurex_auto_speak", String(next));
                    }}
                    langValue={speechLang}
                    langOnChange={setSpeechLang}
                    langOptions={LANG_OPTIONS}
                  />

                  <button 
                    className={`icon-btn ai-input__mic ${isListening ? "ai-input__mic--active" : ""}`} 
                    onClick={toggleListen}
                    title="Dictate"
                    disabled={!recognitionRef.current}
                  >
                    {isListening ? <Mic className="animate-pulse text-red-500" size={14} color="var(--status-failed)" /> : <Mic size={14} />}
                  </button>
                  <button 
                    className="icon-btn ai-input__attach"
                    onClick={() => fileInputRef.current?.click()}
                    title="Upload File"
                    disabled={isUploading}
                  >
                    {isUploading ? <Loader2 className="animate-spin" size={14} /> : <Paperclip size={14} />}
                  </button>
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    style={{ display: 'none' }} 
                    onChange={handleFileUpload}
                  />
                </div>
              </div>
            </div>
          </div>
          {/* Approval Banner */}
          {(() => {
            const pendingPlanTasks = nodes.filter(n => n.status?.toUpperCase() === "AWAITING_APPROVAL");
            const pendingShellTasks = nodes.filter(n => n.result?.includes("APPROVAL_REQUIRED"));
            const hasPending = pendingPlanTasks.length > 0 || pendingShellTasks.length > 0;
            if (!hasPending) return null;
            const total = pendingPlanTasks.length + pendingShellTasks.length;

            const scrollToApproval = () => {
              // Try to find the message for the first pending task
              const firstTask = pendingPlanTasks[0] || pendingShellTasks[0];
              const targetMsg = messages.find(m => m.graph_id && m.graph_id === firstTask?.graph_id && m.role === "assistant");
              if (targetMsg) {
                const el = document.getElementById(targetMsg.id ? `msg-${targetMsg.id}` : undefined!);
                if (el) {
                  el.scrollIntoView({ behavior: "smooth", block: "center" });
                }
              }
              setApprovalTrayOpen(o => !o);
            };

            return (
              <div className="ai-approval-banner">
                <button
                  className="ai-approval-banner__trigger"
                  onClick={scrollToApproval}
                  aria-expanded={approvalTrayOpen}
                >
                  <Shield size={14} />
                  <span>{total} task{total !== 1 ? "s" : ""} awaiting approval</span>
                  <span className="ai-approval-banner__chevron">{approvalTrayOpen ? "▾" : "▴"}</span>
                </button>
                {approvalTrayOpen && (
                  <div className="ai-approval-tray">
                    {pendingPlanTasks.map(task => (
                      <div key={task.id} className="ai-approval-tray__item">
                        <div className="ai-approval-tray__label">
                          <span className="ai-approval-tray__agent">{task.agent_type}</span>
                          <span className="ai-approval-tray__title">{task.title}</span>
                          {task.approval_reason && (
                            <span className="ai-approval-tray__reason">{task.approval_reason}</span>
                          )}
                        </div>
                        <div className="ai-approval-tray__actions">
                          <button className="btn btn--purple btn--sm" onClick={() => handleApprovePlan(task.graph_id)}>
                            <CheckCircle2 size={12} /> Approve
                          </button>
                          <button className="btn btn--red btn--sm" onClick={() => handleDenyPlan(task.graph_id)}>
                            <XCircle size={12} /> Deny
                          </button>
                        </div>
                      </div>
                    ))}
                    {pendingShellTasks.map(task => (
                      <div key={task.id} className="ai-approval-tray__item">
                        <div className="ai-approval-tray__label">
                          <span className="ai-approval-tray__agent">{task.agent_type}</span>
                          <span className="ai-approval-tray__title">{task.title}</span>
                        </div>
                        <div className="ai-approval-tray__actions">
                          <button className="btn btn--green btn--sm" onClick={() => handleApproveShell(task.id, true)}>
                            <CheckCircle2 size={12} /> Approve
                          </button>
                          <button className="btn btn--red btn--sm" onClick={() => handleApproveShell(task.id, false)}>
                            <XCircle size={12} /> Deny
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })()}
        </>
      )}

      {/* Tasks tab */}
      {tab === "tasks" && (
        <div className="ai-tasks">
          <div className="ai-tasks__toolbar">
            <span className="ai-tasks__count">{doneCount}/{nodes.length} done</span>
            {nodes.some(n => n.status?.toUpperCase() === "AWAITING_APPROVAL" || n.result?.includes("APPROVAL_REQUIRED")) && (
              <button 
                className="btn btn--purple btn--sm tasks-bulk-approve"
                onClick={() => {
                  const graph_id = nodes[0]?.graph_id;
                  if (!graph_id) return;
                  handleApprovePlan(graph_id);
                }}
              >
                <CheckCircle2 size={12} /> Approve All
              </button>
            )}
            <button className="icon-btn" onClick={handleClear} title="Clear all tasks">
              <Trash2 size={12} />
            </button>
          </div>
          <div className="ai-tasks__list">
            {nodes.length === 0 && (
              <div className="ai-tasks__empty">{TRANSLATIONS.noTasksYet}</div>
            )}
            {nodes.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onApprove={() => handleApprovePlan(task.graph_id)}
                onApproveShell={(approved) => handleApproveShell(task.id, approved)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const TaskCard = React.memo(function TaskCard({
  task,
  onApprove,
  onApproveShell,
}: {
  task: TaskNode;
  onApprove: () => void;
  onApproveShell: (approved: boolean) => void;
}) {
  const color = STATUS_COLOR.get(task.status) ?? "var(--text-muted)";
  const isActive = ["THINKING", "WRITING", "TESTING"].includes(task.status);

  return (
    <div className={`task-card ${isActive ? "task-card--active" : ""}`}>
      <div className="task-card__header">
        <span className="task-card__agent">{task.agent_type}</span>
        <span className="task-card__status" style={{ color }}>
          <span className={`task-dot ${isActive ? "animate-pulse" : ""}`} style={{ background: color }} />
          {STATUS_LABEL.get(task.status) ?? task.status}
        </span>
      </div>
      <div className="task-card__title">{task.title}</div>
      {task.description && <div className="task-card__desc">{task.description}</div>}
      {task.approval_reason && (
        <div className="task-card__approval-reason">
          <Shield size={12} /> {task.approval_reason}
        </div>
      )}
      {task.error && <div className="task-card__error">{task.error}</div>}
      {isActive && <div className="task-card__progress"><div className="task-card__progress-bar" style={{ background: color }} /></div>}

      {task.status?.toUpperCase() === "AWAITING_APPROVAL" && task.agent_type === "planner" && (
        <button className="btn btn--purple btn--full" onClick={onApprove}>
          ▶ Approve & Execute Plan
        </button>
      )}

      {task.status?.toUpperCase() === "AWAITING_APPROVAL" && task.agent_type !== "planner" && (
        <div className="task-card__shell-approval">
          <button className="btn btn--green" onClick={() => onApproveShell(true)}>
            <CheckCircle2 size={12} /> Approve Tool
          </button>
          <button className="btn btn--red" onClick={() => onApproveShell(false)}>
            <XCircle size={12} /> Deny Tool
          </button>
        </div>
      )}

      {task.result?.includes("APPROVAL_REQUIRED") && (
        <div className="task-card__shell-approval">
          <button className="btn btn--green" onClick={() => onApproveShell(true)}>
            <CheckCircle2 size={12} /> Approve
          </button>
          <button className="btn btn--red" onClick={() => onApproveShell(false)}>
            <XCircle size={12} /> Deny
          </button>
        </div>
      )}
    </div>
  );
});

const extractText = (node: any): string => {
  if (!node) return "";
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (node.props && node.props.children) return extractText(node.props.children);
  return "";
};

const PlanTimeline = React.memo(function PlanTimeline({ children }: { children: React.ReactNode }) {
  const thead = React.Children.toArray(children).find((c: any) => c.type === "thead") as any;
  const tbody = React.Children.toArray(children).find((c: any) => c.type === "tbody") as any;

  const headers: string[] = [];
  if (thead && thead.props && thead.props.children) {
    const tr = thead.props.children;
    React.Children.forEach(tr.props.children, (th: any) => {
      headers.push(extractText(th).trim().toLowerCase());
    });
  }

  const rows: string[][] = [];
  if (tbody && tbody.props && tbody.props.children) {
    React.Children.forEach(tbody.props.children, (tr: any) => {
      if (tr && tr.props && tr.props.children) {
        const rowCells: string[] = [];
        React.Children.forEach(tr.props.children, (td: any) => {
          rowCells.push(extractText(td).trim());
        });
        rows.push(rowCells);
      }
    });
  }

  const stepIdx = headers.findIndex(h => h.includes("step"));
  const agentIdx = headers.findIndex(h => h.includes("agent"));
  const titleIdx = headers.findIndex(h => h.includes("title") || h.includes("task"));
  const descIdx = headers.findIndex(h => h.includes("desc"));
  const statusIdx = headers.findIndex(h => h.includes("status"));

  // Strip emoji characters and leading/trailing whitespace from a cell value
  const stripEmoji = (s: string) =>
    s.replace(/\p{Emoji}/gu, "").trim();

  // Filter rows where the step cell looks like a JSON fragment (malformed LLM output)
  const validRows = rows.filter((row) => {
    const stepCell = row[stepIdx] ?? "";
    return !stepCell.includes('"') && !stepCell.includes("{") && !stepCell.includes(":");
  });

  return (
    <div className="plan-timeline">
      {validRows.map((row, idx) => {
        const rawStep = row[stepIdx] || `${idx + 1}`;
        // Extract just the numeric part if present, else use ordinal
        const stepNum = rawStep.match(/\d+/)?.[0] ?? `${idx + 1}`;
        const agent = stripEmoji(row[agentIdx] || "Unknown");
        const title = row[titleIdx] || "Task Step";
        const desc = row[descIdx] || "";
        const statusRaw = stripEmoji(row[statusIdx] || "PENDING").toUpperCase();
        const status = statusRaw || "PENDING";

        const color = (Object.prototype.hasOwnProperty.call(STATUS_COLOR, status) ? STATUS_COLOR[status] : undefined) || "var(--text-muted)";

        return (
          <div key={idx} className="plan-step-card">
            <div className="plan-step-card__header">
              <span className="plan-step-card__badge">{TRANSLATIONS.step}{stepNum}</span>
              <span className="plan-step-card__agent">{agent}</span>
              <span className="plan-step-card__status" style={{ color }}>
                <span className="plan-step-card__status-dot" style={{ background: color }} />
                {status}
              </span>
            </div>
            <div className="plan-step-card__title">{title}</div>
            {desc && <div className="plan-step-card__desc">{desc}</div>}
          </div>
        );
      })}
    </div>
  );
});
