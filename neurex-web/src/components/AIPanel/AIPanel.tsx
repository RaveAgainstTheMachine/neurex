import { useRef, useEffect, useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import { Send, Loader2, Trash2, CheckCircle2, XCircle, ArrowUp, Mic, MicOff, Volume2, Paperclip, Shield } from "lucide-react";
import { useStore } from "../../lib/store";
import type { TaskNode } from "../../lib/types";
import "./AIPanel.css";

const API_BASE = "http://localhost:8000";

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

interface AIPanelProps {
  send: (payload: object) => void;
  conversationId: string;
}

export function AIPanel({ send, conversationId }: AIPanelProps) {
  const [tab, setTab] = useState<"chat" | "tasks" | "history">("chat");
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { 
    messages, tasks, wsStatus, clearTasks, 
    conversations, setConversations, setActiveConversation, newConversation,
    preferredModel, setPreferredModel
  } = useStore();

  const [isListening, setIsListening] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const recognitionRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Initialize Web Speech API for voice dictation
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      
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
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const nodes = Object.values(tasks).sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  const isWorking = nodes.some((t) =>
    ["THINKING", "WRITING", "TESTING"].includes(t.status)
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, tab]);

  // Fetch conversation list when history tab is opened
  useEffect(() => {
    if (tab === "history") {
      fetch(`${API_BASE}/api/chat/conversations`)
        .then(r => r.json())
        .then(setConversations)
        .catch(() => {});
    }
  }, [tab, setConversations]);

  // Fetch tasks for the current conversation
  useEffect(() => {
    if (tab === "tasks") {
      fetch(`${API_BASE}/api/tasks/?graph_id=${conversationId}`)
        .then(r => r.json())
        .then(ts => {
          ts.forEach((t: TaskNode) => useStore.getState().upsertTask(t));
        })
        .catch(() => {});
    }
  }, [tab, conversationId]);

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

  return (
    <div className="ai-panel">
      {/* Header */}
      <div className="ai-panel__header">
        <div className="ai-panel__tabs">
          <button className={`ai-tab ${tab === "chat" ? "ai-tab--active" : ""}`} onClick={() => setTab("chat")}>
            Chat
          </button>
          <button className={`ai-tab ${tab === "tasks" ? "ai-tab--active" : ""}`} onClick={() => setTab("tasks")}>
            Tasks {nodes.length > 0 && <span className="ai-tab__badge">{doneCount}/{nodes.length}</span>}
          </button>
          <button className={`ai-tab ${tab === "history" ? "ai-tab--active" : ""}`} onClick={() => setTab("history")}>
            History
          </button>
        </div>
        <div className="ai-panel__actions">
           <select 
             className="model-selector"
             value={preferredModel}
             onChange={(e) => setPreferredModel(e.target.value)}
             title="Select Active LLM"
           >
             <optgroup label="Local Mesh (GGUF)">
               <option value="qwen2.5-coder:7b">Qwen 2.5 Coder (Fast)</option>
               <option value="qwen2.5-coder:14b">Qwen 2.5 Coder 14B (Pro)</option>
               <option value="qwen2.5-coder:32b">Qwen 2.5 Coder 32B (Elite)</option>
               <option value="deepseek-r1:7b">DeepSeek R1 7B (Logic)</option>
               <option value="llama3.1:8b">Llama 3.1 8B (Chat)</option>
             </optgroup>
             <optgroup label="BYOK Gateway (Cloud)">
               <option value="gpt-4o">GPT-4o (Frontier)</option>
               <option value="claude-3-5-sonnet-20240620">Claude 3.5 Sonnet</option>
               <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
             </optgroup>
           </select>

           <select 
             className="autonomy-selector"
             defaultValue="limited"
             onChange={(e) => send({ type: "set_autonomy", level: e.target.value })}
             title="Set Autonomy Level"
           >
             <option value="restricted">🛡️ Restricted</option>
             <option value="limited">⚖️ Limited</option>
             <option value="full">🔥 Full Auto</option>
           </select>

           <button className="icon-btn" onClick={newConversation} title="New Chat">
             <Trash2 size={14} style={{ transform: "rotate(45deg)" }} />
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
                key={c.id} 
                className={`history-item ${c.id === conversationId ? "history-item--active" : ""}`}
                onClick={() => { setActiveConversation(c.id); setTab("chat"); }}
              >
                <div className="history-item__id">{c.id.slice(0, 8)}...</div>
                <div className="history-item__date">{new Date(c.last_message).toLocaleString()}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat tab */}
      {tab === "chat" && (
        <>
          <div ref={scrollRef} className="ai-messages">
            {messages.length === 0 && (
              <div className="ai-messages__empty">
                <div className="ai-messages__empty-icon">⬡</div>
                <div>Ask Neurex anything</div>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`message message--${msg.role}`}>
                <div className="message__content">
                  <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
                {msg.role === "assistant" && (
                  <button 
                    className="icon-btn message__tts" 
                    onClick={() => {
                      const utterance = new SpeechSynthesisUtterance(msg.content);
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
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                placeholder={wsStatus !== "connected" ? "Connecting…" : isWorking ? "Agent is working…" : isListening ? "Listening..." : "Ask Neurex anything…"}
                disabled={wsStatus !== "connected" || isWorking}
                rows={1}
                className="ai-input__textarea"
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
            <button
              onClick={handleSend}
              disabled={wsStatus !== "connected" || isWorking || !input.trim()}
              className="ai-input__send"
            >
              {isWorking ? <Loader2 size={14} className="animate-spin" /> : <ArrowUp size={14} />}
            </button>
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
