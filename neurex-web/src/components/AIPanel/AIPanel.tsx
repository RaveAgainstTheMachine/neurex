// src/components/AIPanel/AIPanel.tsx
import { useRef, useEffect, useState } from "react";
import { Send, Loader2, Trash2, CheckCircle2, XCircle } from "lucide-react";
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
  const [tab, setTab] = useState<"chat" | "tasks">("chat");
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { messages, tasks, wsStatus, clearTasks } = useStore();

  const nodes = Object.values(tasks).sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  const isWorking = nodes.some((t) =>
    ["THINKING", "WRITING", "TESTING"].includes(t.status)
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, tab]);

  const handleSend = () => {
    const content = input.trim();
    if (!content || wsStatus !== "connected" || isWorking) return;
    useStore.getState().addMessage({ role: "user", content });
    send({ type: "message", content });
    setInput("");
    inputRef.current?.focus();
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
        </div>
        <div className="ai-panel__status">
          <span className={`ws-dot ws-dot--${wsStatus}`} />
          {wsStatus === "connected" ? "Connected" : wsStatus === "connecting" ? "Connecting…" : "Disconnected"}
        </div>
      </div>

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
                <div className="message__label">{msg.role === "user" ? "You" : "Neurex"}</div>
                <div className="message__content">{msg.content}</div>
              </div>
            ))}
            {isWorking && (
              <div className="message message--assistant">
                <div className="message__label">Neurex</div>
                <div className="message__thinking">
                  <span className="thinking-dot" />
                  <span className="thinking-dot" style={{ animationDelay: "0.2s" }} />
                  <span className="thinking-dot" style={{ animationDelay: "0.4s" }} />
                </div>
              </div>
            )}
          </div>
          <div className="ai-input">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder={wsStatus !== "connected" ? "Connecting…" : isWorking ? "Agent is working…" : "Ask Neurex anything…"}
              disabled={wsStatus !== "connected" || isWorking}
              rows={1}
              className="ai-input__textarea"
            />
            <button
              onClick={handleSend}
              disabled={wsStatus !== "connected" || isWorking || !input.trim()}
              className="ai-input__send"
            >
              {isWorking ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            </button>
          </div>
        </>
      )}

      {/* Tasks tab */}
      {tab === "tasks" && (
        <div className="ai-tasks">
          <div className="ai-tasks__toolbar">
            <span className="ai-tasks__count">{doneCount}/{nodes.length} done</span>
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
