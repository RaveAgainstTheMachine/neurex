import { useRef, useEffect, useState, useCallback, useMemo } from "react";
import { 
  DndContext, 
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  horizontalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { CustomSelect } from '../CustomSelect/CustomSelect';
import { VoiceLangSelect } from '../CustomSelect/VoiceLangSelect';
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import { Send, Loader2, Trash2, CheckCircle2, XCircle, ArrowUp, Mic, MicOff, Volume2, Paperclip, Shield, Plus } from "lucide-react";
import { useStore } from "../../lib/store";
import type { TaskNode } from "../../lib/types";
import toast from "react-hot-toast";
import "./AIPanel.css";

import { API_BASE } from "../../lib/config";

const STATUS_COLOR: Record<string, string> = {
  PENDING:          "var(--status-pending)",
  THINKING:         "var(--status-thinking)",
  WRITING:          "var(--status-writing)",
  TESTING:          "var(--status-writing)",
  DONE:             "var(--status-done)",
  FAILED:           "var(--status-failed)",
  CANCELLED:        "var(--status-failed)",
  AWAITING_APPROVAL:"var(--status-approval)",
};

const STATUS_LABEL: Record<string, string> = {
  PENDING: "Pending", THINKING: "Thinking…", WRITING: "Writing…",
  TESTING: "Testing…", DONE: "Done", FAILED: "Failed",
  CANCELLED: "Cancelled", AWAITING_APPROVAL: "Awaiting Approval",
};


const AUTONOMY_OPTIONS = [
  { value: "restricted", label: "Restricted" },
  { value: "limited", label: "Limited" },
  { value: "full", label: "Full Auto" }
];

const VOICE_OPTIONS = [
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "freeman", label: "Freeman" },
  { value: "attenborough", label: "Attenborough" },
  { value: "rick", label: "Rick" }
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

function SortableItem(props: { id: string; children: React.ReactNode }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: props.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    cursor: 'grab',
    display: 'flex',
    alignItems: 'center'
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      {props.children}
    </div>
  );
}

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
  const store = useStore();
  const { 
    messages, tasks, wsStatus, clearTasks, 
    conversations, setConversations, setActiveConversation, newConversation,
    preferredModel, setPreferredModel, speechLang, setSpeechLang, activeFile,
    fileTree, infraRegistry
  } = store;

  const [isListening, setIsListening] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [voicePreset, setVoicePreset] = useState("male");
  const [mentionQuery, setMentionQuery] = useState("");
  const [showMentions, setShowMentions] = useState(false);
  const [mentionIndex, setMentionIndex] = useState(0);
  const recognitionRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Initialize Web Speech API for voice dictation
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
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setInput(prev => prev + (prev ? " " : "") + finalTranscript);
        }
      };

      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
  }, []);

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

  const nodes = Object.values(tasks || {}).sort(
    (a, b) => new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime()
  );

  const isWorking = nodes.some((t) =>
    ["THINKING", "WRITING", "TESTING"].includes(t.status)
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, tab]);

  // Fetch conversation list when history tab is opened
  useEffect(() => {
    if (tab === "history" && isActive) {
      fetch(`${API_BASE}/api/chat/conversations`)
        .then(r => r.json())
        .then(data => {
          if (Array.isArray(data)) setConversations(data);
        })
        .catch(() => {});
    }
  }, [tab, setConversations, isActive]);

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
    const val = forceValue || filteredMentions[mentionIndex % filteredMentions.length];
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
    } catch {}
  };

  const handleApprovePlan = (graphId: string) => {
    send({ type: "approve_plan", graph_id: graphId });
  };

  const handleApproveShell = (taskId: string, approved: boolean) => {
    send({ type: "approve_shell", task_id: taskId, approved });
  };

  const doneCount = nodes.filter((n) => n.status === "DONE").length;

  const [headerOrder, setHeaderOrder] = useState<string[]>(() => {
    const saved = localStorage.getItem("neurex_header_order");
    return saved ? JSON.parse(saved) : ["tabs", "model", "autonomy", "voice", "actions"];
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDragEnd = (event: DragEndEvent) => {
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
    if (store.infraRegistry.length === 0) {
      // Fallback to currently preferred model if registry is not yet loaded
      return [{ value: preferredModel, label: preferredModel, group: "Active" }];
    }
    return store.infraRegistry.map(m => ({
      value: m.name,
      label: `${m.name} (${m.params || 'Local'})`,
      group: m.is_community ? "Community" : "Open Source"
    }));
  }, [store.infraRegistry, preferredModel]);

  const headerElements: Record<string, React.ReactNode> = {
    tabs: (
      <div className="ai-panel__tabs">
        <button className={`ai-tab ${tab === "chat" ? "ai-tab--active" : ""}`} onClick={() => setTab("chat")}>Chat</button>
        <button className={`ai-tab ${tab === "tasks" ? "ai-tab--active" : ""}`} onClick={() => setTab("tasks")}>
          Tasks {nodes.length > 0 && <span className="ai-tab__badge">{doneCount}/{nodes.length}</span>}
        </button>
        <button className={`ai-tab ${tab === "history" ? "ai-tab--active" : ""}`} onClick={() => setTab("history")}>History</button>
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
        value="limited"
        onChange={(val) => send({ type: "set_autonomy", level: val })}
        options={AUTONOMY_OPTIONS}
        title="Set Autonomy Level"
      />
    ),
    voice: (
      <CustomSelect 
        className="voice-selector" 
        value={voicePreset} 
        onChange={(val) => setVoicePreset(val)} 
        options={[
          { value: "male", label: "Male" },
          { value: "female", label: "Female" },
          { value: "freeman", label: "Freeman" },
          { value: "attenborough", label: "Attenborough" },
          { value: "rick", label: "Rick" }
        ]}
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
          <div className="ai-history__list">
            {conversations.length === 0 && <div className="ai-history__empty">No previous chats.</div>}
             {conversations.map((c) => (
               <button 
                 key={c.conversation_id} 
                 className={`history-item ${c.conversation_id === conversationId ? "history-item--active" : ""}`}
                 onClick={() => { setActiveConversation(c.conversation_id); setTab("chat"); }}
               >
                 <div className="history-item__id">{c.conversation_id ? c.conversation_id.slice(0, 8) : "unknown"}...</div>
                 <div className="history-item__date">{c.last_message ? new Date(c.last_message).toLocaleString() : "No date"}</div>
               </button>
             ))}
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
                <div>Ask Neurex anything</div>
                <div className="ai-messages__attribution">
                  Powered by Open Source Intelligence.
                </div>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`message message--${msg.role}`}>
                <div className="message__content">
                  <ReactMarkdown 
                    rehypePlugins={[rehypeHighlight]}
                    components={{
                      code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || "");
                        const codeContent = String(children).replace(/\n$/, "");
                        
                        if (!inline && match) {
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
                              <pre className={className} {...props}>
                                <code>{children}</code>
                              </pre>
                            </div>
                          );
                        }
                        return <code className={className} {...props}>{children}</code>;
                      }
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
                {msg.role === "assistant" && (
                  <button 
                    className="icon-btn message__tts" 
                    onClick={() => {
                      const utterance = new SpeechSynthesisUtterance(msg.content);
                      utterance.lang = speechLang;
                      
                      // Personality Presets
                      if (voicePreset === "freeman") {
                        utterance.pitch = 0.8; utterance.rate = 0.85;
                      } else if (voicePreset === "attenborough") {
                        utterance.pitch = 0.9; utterance.rate = 0.8;
                      } else if (voicePreset === "rick") {
                        utterance.pitch = 1.4; utterance.rate = 1.2;
                      } else if (voicePreset === "female") {
                        utterance.pitch = 1.2;
                      } else {
                        utterance.pitch = 1.0;
                      }

                      window.speechSynthesis.speak(utterance);
                    }}
                    title="Read Aloud"
                  >
                    <Volume2 size={12} />
                  </button>
                )}
              </div>
            ))}
            {isWorking && (
              <div className="message message--assistant">
                <div className="message__thinking">
                  <span className="thinking-dot" />
                  <span className="thinking-dot" style={{ animationDelay: "0.2s" }} />
                  <span className="thinking-dot" style={{ animationDelay: "0.4s" }} />
                </div>
              </div>
            )}
          </div>
          <div className="ai-input">
            <div className="ai-input__wrapper">
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
                    value="limited"
                    onChange={(val) => send({ type: "set_autonomy", level: val })}
                    options={AUTONOMY_OPTIONS}
                    title="Set Autonomy Level"
                  />
                </div>
                <div className="ai-input__footer-right">
                  <VoiceLangSelect 
                    voiceValue={voicePreset}
                    voiceOnChange={setVoicePreset}
                    voiceOptions={VOICE_OPTIONS}
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
        </>
      )}

      {/* Tasks tab */}
      {tab === "tasks" && (
        <div className="ai-tasks">
          <div className="ai-tasks__toolbar">
            <span className="ai-tasks__count">{doneCount}/{nodes.length} done</span>
            {nodes.some(n => n.status === "AWAITING_APPROVAL" || n.result?.includes("APPROVAL_REQUIRED")) && (
              <button 
                className="btn btn--purple btn--sm tasks-bulk-approve"
                onClick={async () => {
                  const graph_id = nodes[0]?.graph_id;
                  if (!graph_id) return;
                  await fetch(`${API_BASE}/api/tasks/${graph_id}/approve_all`, { method: "POST" });
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
              <div className="ai-tasks__empty">No tasks yet. Ask Neurex to build something.</div>
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

function TaskCard({
  task,
  onApprove,
  onApproveShell,
}: {
  task: TaskNode;
  onApprove: () => void;
  onApproveShell: (approved: boolean) => void;
}) {
  const color = STATUS_COLOR[task.status] ?? "var(--text-muted)";
  const isActive = ["THINKING", "WRITING", "TESTING"].includes(task.status);

  return (
    <div className={`task-card ${isActive ? "task-card--active" : ""}`}>
      <div className="task-card__header">
        <span className="task-card__agent">{task.agent_type}</span>
        <span className="task-card__status" style={{ color }}>
          <span className={`task-dot ${isActive ? "animate-pulse" : ""}`} style={{ background: color }} />
          {STATUS_LABEL[task.status] ?? task.status}
        </span>
      </div>
      <div className="task-card__title">{task.title}</div>
      {task.approval_reason && (
        <div className="task-card__approval-reason">
          <Shield size={12} /> {task.approval_reason}
        </div>
      )}
      {task.error && <div className="task-card__error">{task.error}</div>}
      {isActive && <div className="task-card__progress"><div className="task-card__progress-bar" style={{ background: color }} /></div>}

      {task.status === "AWAITING_APPROVAL" && (
        <button className="btn btn--purple btn--full" onClick={onApprove}>
          ▶ Approve & Execute Plan
        </button>
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
}
