import { useStore } from "../../lib/store";
import { Bot, ChevronDown, ChevronRight, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { useState, useMemo } from "react";
import "./AgentPanel.css";

export function AgentPanel() {
  const tasksObj = useStore((s) => s.tasks);
  const tasks = useMemo(() => Object.values(tasksObj), [tasksObj]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Sort tasks by updated_at
  const sortedTasks = useMemo(() => [...tasks].sort((a, b) => 
    new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  ), [tasks]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "DONE": return <CheckCircle size={14} className="text-green" />;
      case "FAILED": return <XCircle size={14} className="text-red" />;
      case "AWAITING_APPROVAL": return <Bot size={14} className="text-purple" />;
      default: return <Loader2 size={14} className="animate-spin text-cyan" />;
    }
  };

  return (
    <div className="agent-panel">
      <div className="agent-panel__header">
        <Bot size={16} />
        Active Agent Intelligence
      </div>
      <div className="agent-panel__list">
        {sortedTasks.map(task => {
          const isExpanded = selectedId === task.id;
          return (
            <div 
              key={task.id} 
              className={`agent-task-item agent-task-item--${task.status.toLowerCase()} ${isExpanded ? 'active' : ''}`}
              onClick={() => setSelectedId(isExpanded ? null : task.id)}
            >
              <div className="task-item__header">
                <span className="task-item__status">{getStatusIcon(task.status)}</span>
                <span className="task-item__agent">[{task.agent_type.toUpperCase()}]</span>
                <span className="task-item__title">{task.title}</span>
              </div>
              
              <div className="task-item__meta">
                <span>Status: {task.status}</span> • <span>{new Date(task.updated_at).toLocaleTimeString()}</span>
              </div>

              {isExpanded && (
                <div className="task-item__details">
                  <div className="detail-section">
                    <strong>Objective:</strong>
                    <p>{task.description}</p>
                  </div>
                  {task.result && (
                    <div className="detail-section result">
                      <strong>Outcome:</strong>
                      <pre>{task.result}</pre>
                    </div>
                  )}
                  {task.error && (
                    <div className="detail-section error">
                      <strong>Failure Reason:</strong>
                      <pre>{task.error}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
        {tasks.length === 0 && (
          <div className="agent-panel__empty">No active agent tasks.</div>
        )}
      </div>
    </div>
  );
}
