import { useStore } from "@/lib/store";
import { useParams } from "next/navigation";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { TaskNode, TaskStatus } from "@/lib/types";


const STATUS_COLORS: Record<TaskStatus, string> = {
  pending:   "var(--status-pending)",
  thinking:  "var(--status-thinking)",
  awaiting_approval: "var(--accent-purple)",
  writing:   "var(--status-writing)",
  testing:   "var(--status-testing)",
  done:      "var(--status-done)",
  failed:    "var(--status-failed)",
  cancelled: "var(--text-muted)",
};


const STATUS_LABEL: Record<TaskStatus, string> = {
  pending:   "Waiting",
  thinking:  "Thinking…",
  awaiting_approval: "Approve Plan?",
  writing:   "Writing…",
  testing:   "Testing…",
  done:      "Done",
  failed:    "Failed",
  cancelled: "Cancelled",
};


const AGENT_ICON: Record<string, string> = {
  planner: "🗺️",
  coder:   "⚡",
  tester:  "🧪",
  researcher: "🔍",
  reviewer: "⚖️",
};


export function AgentDashboard() {
  const { conversationId } = useParams();
  const { send } = useWebSocket(conversationId as string);
  const tasks = useStore((s) => s.tasks);
  const nodes = Object.values(tasks);

  const approvePlan = (graphId: string) => {
    send({ type: "approve_plan", graph_id: graphId });
  };

  return (

    <div style={{
      flex: 1,
      overflow: "auto",
      display: "flex",
      flexDirection: "column",
    }}>
      <div style={{
        padding: "8px 12px",
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.08em",
        color: "var(--text-muted)",
        textTransform: "uppercase",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <span>Agent Team</span>
        <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 8 }}>
          {nodes.filter(n => n.status === "done").length}/{nodes.length}
          <button 
            style={{
              padding: "2px 6px",
              background: "var(--bg-elevated)",
              border: "1px solid var(--border)",
              borderRadius: 3,
              color: "var(--text-primary)",
              fontSize: 9,
              cursor: "pointer"
            }}
            onClick={() => {
              const task = prompt("What should the agent do?");
              if (task) {
                send({ type: "message", content: task });
              }
            }}
          >
            + Task
          </button>
        </span>
      </div>


      {nodes.length === 0 && (
        <div style={{
          padding: 16,
          color: "var(--text-muted)",
          fontSize: 11,
          textAlign: "center",
        }}>
          No active tasks
        </div>
      )}

      {nodes.map((task) => (
        <TaskCard key={task.id} task={task} onApprove={() => approvePlan(task.graph_id)} />
      ))}
    </div>
  );
}

interface TaskCardProps {
  task: TaskNode;
  onApprove: () => void;
}

function TaskCard({ task, onApprove }: TaskCardProps) {

  const isActive = ["thinking", "writing", "testing"].includes(task.status);
  const color    = STATUS_COLORS[task.status];

  return (
    <div style={{
      padding: "10px 12px",
      borderBottom: "1px solid var(--border)",
      animation: isActive ? undefined : "fade-in 0.2s ease",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        marginBottom: 4,
      }}>
        {/* Agent icon */}
        <span style={{ fontSize: 14 }}>{AGENT_ICON[task.agent_type] ?? "🤖"}</span>

        {/* Agent type label */}
        <span style={{
          fontSize: 10,
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: task.agent_type === "planner"
            ? "var(--agent-planner)"
            : task.agent_type === "coder"
            ? "var(--agent-coder)"
            : task.agent_type === "tester"
            ? "var(--agent-tester)"
            : task.agent_type === "reviewer"
            ? "var(--agent-reviewer)"
            : "var(--agent-researcher)",

        }}>
          {task.agent_type}
        </span>

        {/* Status dot + label */}
        <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 5, fontSize: 11 }}>
          <span style={{
            width: 6, height: 6, borderRadius: "50%",
            background: color,
            animation: isActive ? "pulse-glow 1.2s ease-in-out infinite" : undefined,
          }} />
          <span style={{ color }}>{STATUS_LABEL[task.status]}</span>
        </span>
      </div>

      {/* Task title */}
      <div style={{ fontSize: 12, color: "var(--text-primary)", fontWeight: 500 }}>
        {task.title}
      </div>

      {/* Error */}
      {task.error && (
        <div style={{
          marginTop: 4, padding: "4px 8px",
          background: "#ef444420",
          borderRadius: 4,
          fontSize: 11,
          color: "var(--accent-red)",
          fontFamily: "JetBrains Mono, monospace",
        }}>
          {task.error}
        </div>
      )}

      {/* Progress bar */}
      {isActive && (
        <div style={{
          marginTop: 8,
          height: 2,
          background: "var(--border)",
          borderRadius: 1,
          overflow: "hidden",
        }}>
          <div style={{
            height: "100%",
            width: "60%",
            background: color,
            borderRadius: 1,
            animation: "slide-in-right 1.5s ease-in-out infinite alternate",
          }} />
        </div>
      )}

      {/* Approval Button */}
      {task.status === "awaiting_approval" && (
        <button
          onClick={onApprove}
          style={{

            marginTop: 10,
            width: "100%",
            padding: "6px 0",
            background: "var(--accent-purple)",
            color: "white",
            border: "none",
            borderRadius: 4,
            fontSize: 11,
            fontWeight: 600,
            cursor: "pointer",
            transition: "opacity 0.2s",
          }}
          onMouseOver={(e) => (e.currentTarget.style.opacity = "0.8")}
          onMouseOut={(e) => (e.currentTarget.style.opacity = "1")}
        >
          Approve & Execute Plan
        </button>
      )}
    </div>
  );
}

