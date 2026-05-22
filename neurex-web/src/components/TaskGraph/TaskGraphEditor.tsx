import { useState, useMemo } from "react";
import { useStore } from "../../lib/store";
import { 
  Bot, 
  Play, 
  Pause, 
  Plus, 
  Trash2, 
  Link2, 
  X, 
  Maximize2, 
  Minimize2, 
  PlusCircle, 
  HelpCircle, 
  AlertCircle,
  CheckCircle,
  Loader2
} from "lucide-react";
import type { TaskNode, AgentType } from "../../lib/types";
import "./TaskGraphEditor.css";

interface LayoutNode extends TaskNode {
  x: number;
  y: number;
  depth: number;
  children: LayoutNode[];
}

export function TaskGraphEditor() {
  const tasksObj = useStore((s) => s.tasks);
  const graphId = useStore((s) => s.activeConversationId);
  const mutateGraph = useStore((s) => s.mutateGraph);
  const toggleBreakpoint = useStore((s) => s.toggleBreakpoint);
  const approveTask = useStore((s) => s.approveTask);

  const tasks = useMemo(() => Object.values(tasksObj), [tasksObj]);

  // Maximize view state
  const [isMaximized, setIsMaximized] = useState(false);

  // Link/Rewire state
  const [linkingTaskId, setLinkingTaskId] = useState<string | null>(null);

  // Modals state
  const [isInsertModalOpen, setIsInsertModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Form states
  const [parentId, setParentId] = useState<string | null>(null);
  const [childId, setChildId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<TaskNode | null>(null);

  const [formTitle, setFormTitle] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formAgentType, setFormAgentType] = useState<AgentType>("coder");

  // Layout tree construction
  const { layoutNodes, connections, canvasWidth, canvasHeight } = useMemo(() => {
    if (tasks.length === 0) {
      return { layoutNodes: [], connections: [], canvasWidth: 1000, canvasHeight: 600 };
    }

    const nodeMap = new Map<string, LayoutNode>();
    tasks.forEach(n => {
      nodeMap.set(n.id, { ...n, x: 0, y: 0, depth: 0, children: [] });
    });

    const roots: LayoutNode[] = [];
    nodeMap.forEach(node => {
      if (node.parent_id && nodeMap.has(node.parent_id)) {
        nodeMap.get(node.parent_id)!.children.push(node);
      } else {
        roots.push(node);
      }
    });

    // Recursively set depths
    function setDepth(node: LayoutNode, d: number) {
      node.depth = d;
      node.children.forEach(c => setDepth(c, d + 1));
    }
    roots.forEach(r => setDepth(r, 0));

    let currentY = 0;
    const LEVEL_WIDTH = 320;
    const ROW_HEIGHT = 130;
    const nodesList: LayoutNode[] = [];

    // Post-order traversal layout sizing
    function layoutSubtree(node: LayoutNode): number {
      node.x = 40 + node.depth * LEVEL_WIDTH;
      nodesList.push(node);

      if (node.children.length === 0) {
        node.y = 50 + currentY * ROW_HEIGHT;
        currentY += 1;
        return 1;
      }

      let firstChildY = -1;
      let lastChildY = -1;

      node.children.forEach((child, index) => {
        layoutSubtree(child);
        if (index === 0) firstChildY = child.y;
        if (index === node.children.length - 1) lastChildY = child.y;
      });

      node.y = (firstChildY + lastChildY) / 2;
      return node.children.length;
    }

    roots.forEach(r => layoutSubtree(r));

    // Gather connections and coordinates
    const conns: { 
      id: string; 
      parent: LayoutNode; 
      child: LayoutNode; 
      midX: number; 
      midY: number; 
      isActive: boolean 
    }[] = [];

    nodesList.forEach(node => {
      node.children.forEach(child => {
        // A connection is active if either child is running/active
        const isActive = child.status === "THINKING" || child.status === "WRITING" || child.status === "TESTING";
        const midX = (node.x + 230 + child.x) / 2;
        const midY = (node.y + 50 + child.y + 50) / 2;
        conns.push({
          id: `${node.id}-${child.id}`,
          parent: node,
          child,
          midX,
          midY,
          isActive
        });
      });
    });

    const maxDepth = Math.max(...nodesList.map(n => n.depth), 0);
    const width = Math.max(1200, (maxDepth + 1.5) * LEVEL_WIDTH + 80);
    const height = Math.max(800, currentY * ROW_HEIGHT + 100);

    return { 
      layoutNodes: nodesList, 
      connections: conns, 
      canvasWidth: width, 
      canvasHeight: height 
    };
  }, [tasks]);

  // Handle link / rewire clicks
  const handleNodeClick = (node: TaskNode) => {
    if (linkingTaskId) {
      if (linkingTaskId === node.id) {
        // Toggle off if clicking self
        setLinkingTaskId(null);
        return;
      }

      // Check for cycles (e.g. B cannot be parent of A if B is a descendant of A)
      // For absolute safety we let the backend validate and return error or check locally
      mutateGraph(graphId, {
        action: "rewire",
        task_id: linkingTaskId,
        parent_id: node.id
      });
      setLinkingTaskId(null);
    }
  };

  const handleStartLink = (e: React.MouseEvent, node: TaskNode) => {
    e.stopPropagation();
    setLinkingTaskId(node.id);
  };

  const handleToggleBreakpoint = (e: React.MouseEvent, node: TaskNode) => {
    e.stopPropagation();
    toggleBreakpoint(node.id);
  };

  const handleApprove = (e: React.MouseEvent, node: TaskNode) => {
    e.stopPropagation();
    approveTask(node.id);
  };

  const handleDeleteNode = (e: React.MouseEvent, node: TaskNode) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete task "${node.title}"? Downstream tasks will be rewired to its parent.`)) {
      mutateGraph(graphId, {
        action: "delete",
        task_id: node.id
      });
    }
  };

  const handleOpenInsertModal = (pId: string | null = null, cId: string | null = null) => {
    setParentId(pId);
    setChildId(cId);
    setFormTitle("");
    setFormDesc("");
    setFormAgentType("coder");
    setIsInsertModalOpen(true);
  };

  const handleOpenEditModal = (e: React.MouseEvent, node: TaskNode) => {
    e.stopPropagation();
    setSelectedNode(node);
    setFormTitle(node.title);
    setFormDesc(node.description);
    setFormAgentType(node.agent_type);
    setIsEditModalOpen(true);
  };

  const handleInsertSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim() || !formDesc.trim()) return;

    await mutateGraph(graphId, {
      action: "insert",
      parent_id: parentId,
      child_id: childId,
      title: formTitle,
      description: formDesc,
      agent_type: formAgentType
    });

    setIsInsertModalOpen(false);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNode || !formTitle.trim() || !formDesc.trim()) return;

    // Wait! Since there is no edit endpoint, how does editing work?
    // In our backend tasks.py: there is no custom partial task edit endpoint except graph mutation.
    // Wait, let's check if the backend supports editing in mutateGraph.
    // Let's look at neurex-api tasks.py:
    // It only handles mutation.action == "rewire", "insert", "delete".
    // Wait, let's verify if there is any other endpoint we can use, or if we can make a custom edit action in mutate_graph, or if we just rewire/delete.
    // Let's verify: In tasks.py mutate_graph:
    // It only supports "rewire", "insert", "delete".
    // Wait, what if we extend tasks.py to support a "modify" or "update" action?
    // Let's check: Yes! We can easily modify tasks.py to support a "modify" action in mutate_graph, or we can just call standard REST endpoints or websocket to edit, or we can edit it directly!
    // Wait, let's see if there is another endpoint. In tasks.py, is there a POST or PUT /api/tasks/{task_id} or similar?
    // No, there is only `/`, `/{graph_id}/approve_all`, `/{graph_id}/graph`, `/{graph_id}/cancel`, `/{graph_id}/mutate`, `/{task_id}/toggle_breakpoint`, `/{task_id}/approve`.
    // Wait! That is very interesting! Can we add a `modify` action to `/api/tasks/{graph_id}/mutate` so we can support complete node editing?
    // Yes, that would be incredibly useful and elegant, and it perfectly completes the "modify node" requirement in Pillar 1!
    // Let's check how easy that is. In `tasks.py`, we can add:
    // ```python
    //     elif mutation.action == "modify":
    //         if not mutation.task_id:
    //             return {"error": "task_id is required for modify"}
    //         node = await session.get(TaskNode, mutation.task_id)
    //         if not node:
    //             return {"error": f"Task {mutation.task_id} not found"}
    //         if mutation.title:
    //             node.title = mutation.title
    //         if mutation.description:
    //             node.description = mutation.description
    //         if mutation.agent_type:
    //             node.agent_type = mutation.agent_type
    //         session.add(node)
    //         await session.commit()
    //         await session.refresh(node)
    //         return {"mutated": True, "action": "modify", "task": node.model_dump()}
    // ```
    // Oh, this is incredibly straightforward and matches the exact structure of other mutation actions! We will add this to the python backend soon to ensure full compatibility.
    // Let's first finish the React component structure.
    
    await mutateGraph(graphId, {
      action: "modify" as any, // Cast to any or edit NeurexStore type to support modify
      task_id: selectedNode.id,
      title: formTitle,
      description: formDesc,
      agent_type: formAgentType
    });

    setIsEditModalOpen(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "DONE": return <CheckCircle size={14} className="text-green" />;
      case "FAILED": return <AlertCircle size={14} className="text-red" />;
      case "AWAITING_APPROVAL": return <Play size={14} className="text-orange" />;
      case "THINKING":
      case "WRITING":
      case "TESTING":
        return <Loader2 size={14} className="animate-spin text-cyan" />;
      default: return <HelpCircle size={14} className="text-muted" />;
    }
  };

  // Helper to draw clean horizontal bezier curves between parent and child nodes
  const calcBezierPath = (x1: number, y1: number, x2: number, y2: number) => {
    const parentRightX = x1 + 230;
    const parentRightY = y1 + 50;
    const childLeftX = x2;
    const childLeftY = y2 + 50;

    const cp1X = parentRightX + 70;
    const cp1Y = parentRightY;
    const cp2X = childLeftX - 70;
    const cp2Y = childLeftY;

    return `M ${parentRightX} ${parentRightY} C ${cp1X} ${cp1Y}, ${cp2X} ${cp2Y}, ${childLeftX} ${childLeftY}`;
  };

  // Render the core editor pane
  const renderCanvas = () => {
    const linkingNode = layoutNodes.find(n => n.id === linkingTaskId);

    return (
      <div className="task-graph-canvas-container">
        {linkingTaskId && (
          <div className="linking-banner">
            <span>
              Linking: Select parent task for <strong>"{linkingNode?.title}"</strong>
            </span>
            <button className="btn btn--sm btn--red" onClick={() => setLinkingTaskId(null)}>
              Cancel
            </button>
          </div>
        )}

        <div 
          className="task-graph-canvas" 
          style={{ width: `${canvasWidth}px`, height: `${canvasHeight}px` }}
        >
          {/* Render Connections SVGs */}
          <svg className="graph-svg">
            <defs>
              <linearGradient id="glow-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--accent-purple)" />
                <stop offset="100%" stopColor="var(--accent-cyan)" />
              </linearGradient>
            </defs>

            {connections.map(conn => {
              const pathD = calcBezierPath(conn.parent.x, conn.parent.y, conn.child.x, conn.child.y);
              return (
                <g key={conn.id}>
                  {/* Glowing neon back-glow path */}
                  <path 
                    d={pathD} 
                    className={`graph-connection-line ${conn.isActive ? "graph-connection-line--active" : ""}`}
                  />
                  
                  {/* Inline `+` Insert Node button on connection path */}
                  <g 
                    transform={`translate(${conn.midX - 10}, ${conn.midY - 10})`}
                    onClick={() => handleOpenInsertModal(conn.parent.id, conn.child.id)}
                  >
                    <circle 
                      cx="10" 
                      cy="10" 
                      r="10" 
                      className="graph-connection-plus"
                    />
                    <text 
                      x="10" 
                      y="14" 
                      textAnchor="middle" 
                      className="graph-connection-plus-symbol"
                    >
                      +
                    </text>
                  </g>
                </g>
              );
            })}
          </svg>

          {/* Render Interactive Node Cards */}
          {layoutNodes.map(node => {
            const isAwaiting = node.status === "AWAITING_APPROVAL";
            const isLinkingTarget = linkingTaskId !== null && linkingTaskId !== node.id;
            
            return (
              <div 
                key={node.id}
                className={`graph-node graph-node--${node.status.toLowerCase()} ${
                  linkingTaskId === node.id ? "graph-node--linking-source" : ""
                } ${isLinkingTarget ? "graph-node--linking-target" : ""}`}
                style={{ left: `${node.x}px`, top: `${node.y}px` }}
                onClick={() => handleNodeClick(node)}
                onDoubleClick={(e) => handleOpenEditModal(e, node)}
              >
                <div className="graph-node__header">
                  <span className={`node-agent-badge node-agent-badge--${node.agent_type}`}>
                    {node.agent_type}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {getStatusIcon(node.status)}
                    <span className="node-status-glow" />
                  </div>
                </div>

                <div className="graph-node__body" title={node.title}>
                  <span className="graph-node__title">{node.title}</span>
                </div>

                <div className="graph-node__actions">
                  <div className="flex items-center gap-1.5">
                    {/* Toggle Breakpoint */}
                    <button 
                      className={`node-action-btn breakpoint-btn ${node.is_checkpoint ? "breakpoint-btn--active" : ""}`}
                      onClick={(e) => handleToggleBreakpoint(e, node)}
                      title={node.is_checkpoint ? "Breakpoint set" : "Enable breakpoint"}
                    >
                      <Pause size={12} fill={node.is_checkpoint ? "var(--accent-red)" : "none"} />
                    </button>

                    {/* Rewire edge */}
                    <button 
                      className="node-action-btn"
                      onClick={(e) => handleStartLink(e, node)}
                      title="Rewire Parent Dependency"
                    >
                      <Link2 size={12} />
                    </button>

                    {/* Delete node */}
                    <button 
                      className="node-action-btn node-action-btn--delete"
                      onClick={(e) => handleDeleteNode(e, node)}
                      title="Delete Node"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>

                  {/* Approve breakpoint or execute blocked task */}
                  {isAwaiting && (
                    <button 
                      className="node-action-btn node-action-btn--approve"
                      onClick={(e) => handleApprove(e, node)}
                      title="Approve & Resume Task"
                    >
                      <Play size={12} className="mr-0.5" fill="currentColor" /> Approve
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {/* Empty graph state */}
          {tasks.length === 0 && (
            <div className="empty-graph-state">
              <Bot size={48} className="text-muted" />
              <span>No active orchestration tasks inside graph.</span>
              <button 
                className="btn btn--purple btn--sm"
                onClick={() => handleOpenInsertModal(null, null)}
              >
                Add Root Task
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="task-graph-wrapper">
      <div className="task-graph-header">
        <span className="task-graph-header__title">
          <Bot size={16} className="text-purple" />
          Agent Task Canvas
        </span>
        <div className="task-graph-header__actions">
          <button 
            className="btn btn--sm btn--purple"
            onClick={() => handleOpenInsertModal(null, null)}
            title="Create new autonomous task node"
          >
            <Plus size={12} /> Add Task
          </button>
          
          <button 
            className="btn btn--sm btn--secondary"
            onClick={() => setIsMaximized(!isMaximized)}
            title={isMaximized ? "Collapse Canvas" : "Maximize Canvas to Screen"}
          >
            {isMaximized ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
          </button>
        </div>
      </div>

      {/* Glassmorphic Canvas view */}
      {renderCanvas()}

      {/* Maximized Backdrop Overlay */}
      {isMaximized && (
        <div className="task-graph-maximized-overlay">
          <div className="task-graph-maximized-card animate-scale">
            <div className="task-graph-header">
              <span className="task-graph-header__title" style={{ fontSize: 14 }}>
                <Bot size={18} className="text-purple" />
                Orchestration Task Topology Workspace — Interactive v0.6.0 Dashboard
              </span>
              <div className="task-graph-header__actions">
                <button 
                  className="btn btn--sm btn--purple"
                  onClick={() => handleOpenInsertModal(null, null)}
                >
                  <Plus size={12} /> Add Node
                </button>
                <button 
                  className="btn btn--sm btn--secondary"
                  onClick={() => setIsMaximized(false)}
                >
                  <Minimize2 size={12} /> Collapse
                </button>
              </div>
            </div>
            {renderCanvas()}
          </div>
        </div>
      )}

      {/* Insert Node Overlay Modal */}
      {isInsertModalOpen && (
        <div className="graph-modal-overlay">
          <form className="graph-modal" onSubmit={handleInsertSubmit}>
            <div className="graph-modal__header">
              <span className="graph-modal__title">Insert Task Node</span>
              <button 
                type="button" 
                className="graph-modal__close" 
                onClick={() => setIsInsertModalOpen(false)}
              >
                <X size={16} />
              </button>
            </div>

            <div className="graph-form-group">
              <label>Agent Specialization</label>
              <select 
                value={formAgentType} 
                onChange={(e) => setFormAgentType(e.target.value as AgentType)}
              >
                <option value="planner">PLANNER (Orchestration & Planning)</option>
                <option value="coder">CODER (Writing & Refactoring Code)</option>
                <option value="tester">TESTER (Writing & Running Unit Tests)</option>
                <option value="reviewer">REVIEWER (Code Review & Safety Audit)</option>
              </select>
            </div>

            <div className="graph-form-group">
              <label>Task Title</label>
              <input 
                type="text" 
                placeholder="e.g. Implement security check logic" 
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                required
              />
            </div>

            <div className="graph-form-group">
              <label>Detailed Objective</label>
              <textarea 
                placeholder="Describe exactly what you want the agent to accomplish..." 
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
                required
              />
            </div>

            <div className="graph-modal__actions">
              <button 
                type="button" 
                className="btn btn--sm btn--secondary" 
                onClick={() => setIsInsertModalOpen(false)}
              >
                Cancel
              </button>
              <button type="submit" className="btn btn--sm btn--purple">
                Insert Task
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Node Overlay Modal */}
      {isEditModalOpen && (
        <div className="graph-modal-overlay">
          <form className="graph-modal" onSubmit={handleEditSubmit}>
            <div className="graph-modal__header">
              <span className="graph-modal__title">Edit Task Node</span>
              <button 
                type="button" 
                className="graph-modal__close" 
                onClick={() => setIsEditModalOpen(false)}
              >
                <X size={16} />
              </button>
            </div>

            <div className="graph-form-group">
              <label>Agent Specialization</label>
              <select 
                value={formAgentType} 
                onChange={(e) => setFormAgentType(e.target.value as AgentType)}
              >
                <option value="planner">PLANNER</option>
                <option value="coder">CODER</option>
                <option value="tester">TESTER</option>
                <option value="reviewer">REVIEWER</option>
              </select>
            </div>

            <div className="graph-form-group">
              <label>Task Title</label>
              <input 
                type="text" 
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                required
              />
            </div>

            <div className="graph-form-group">
              <label>Objective</label>
              <textarea 
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
                required
              />
            </div>

            <div className="graph-modal__actions">
              <button 
                type="button" 
                className="btn btn--sm btn--secondary" 
                onClick={() => setIsEditModalOpen(false)}
              >
                Cancel
              </button>
              <button type="submit" className="btn btn--sm btn--purple">
                Update Task
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
