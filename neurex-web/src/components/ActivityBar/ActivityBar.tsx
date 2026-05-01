import React from "react";
import { 
  Files, Search, GitBranch, Clock, MessageSquare, 
  Cpu, Shield, Puzzle, Bot, BrainCircuit, Settings 
} from "lucide-react";
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
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useStore } from "../../lib/store";
import { MenuBar } from "../MenuBar/MenuBar";
import "./ActivityBar.css";

const SIDEBAR_ITEMS: { id: string; icon: React.FC<any>; label: string }[] = [
  { id: "explorer", icon: Files,          label: "Explorer" },
  { id: "search",   icon: Search,         label: "Search" },
  { id: "git",      icon: GitBranch,      label: "Source Control" },
  { id: "timeline", icon: Clock,          label: "File Timeline" },
  { id: "history",  icon: MessageSquare,  label: "Chat History" },
  { id: "infra",    icon: Cpu,            label: "AI Infrastructure" },
  { id: "system",   icon: Shield,         label: "System Logs" },
  { id: "skills",   icon: Puzzle,         label: "Skills & Extensions" },
  { id: "agent",    icon: Bot,            label: "Agents" },
  { id: "evolution", icon: BrainCircuit, label: "Neural Evolution" },
];

function SortableActivityItem({ id, active, onClick, icon: Icon, label, badge }: { id: string; active: boolean; onClick: () => void; icon: React.FC<any>; label: string; badge?: number | string }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 10 : 1,
    cursor: "pointer",
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="activity-item-wrapper">
      <button className={`activity-btn ${active ? "active" : ""}`} onClick={onClick} title={label}>
        <Icon size={24} />
        {badge && <span className="activity-badge animate-scale">{badge}</span>}
        {active && <div className="activity-indicator" />}
      </button>
    </div>
  );
}

export function ActivityBar() {
  // Phase 44.22: Strict State Selection (Prevent Navigation churn)
  const sidebarTab = useStore(s => s.sidebarTab);
  const setSidebarTab = useStore(s => s.setSidebarTab);
  const sidebarOrder = useStore(s => s.sidebarOrder);
  const setSidebarOrder = useStore(s => s.setSidebarOrder);
  const showSettings = useStore(s => s.showSettings);
  const setShowSettings = useStore(s => s.setShowSettings);
  const showHiveMind = useStore(s => s.showHiveMind);
  const setShowHiveMind = useStore(s => s.setShowHiveMind);
  
  // Phase 44.22: Derived Selector (Re-render only when count changes)
  const activeTaskCount = useStore(s => 
    Object.values(s.tasks).filter(t => ["THINKING", "WRITING", "TESTING"].includes(t.status)).length
  );

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleSidebarDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = sidebarOrder.indexOf(active.id as string);
      const newIndex = sidebarOrder.indexOf(over.id as string);
      const next = arrayMove(sidebarOrder, oldIndex, newIndex);
      setSidebarOrder(next);
    }
  };


  return (
    <div className="activity-bar">
      <div className="activity-bar__top">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleSidebarDragEnd}>
          <SortableContext items={sidebarOrder} strategy={verticalListSortingStrategy}>
            {sidebarOrder.map(id => {
              const item = SIDEBAR_ITEMS.find(i => i.id === id);
              if (!item) return null;
              let badge = undefined;
              if (id === "agent" && activeTaskCount > 0) badge = activeTaskCount;
              return (
                <SortableActivityItem
                  key={id} id={id} icon={item.icon} label={item.label}
                  active={sidebarTab === id && !showSettings && !showHiveMind}
                  onClick={() => setSidebarTab(id)}
                  badge={badge}
                />
              );
            })}
          </SortableContext>
        </DndContext>
      </div>
      <div className="activity-bar__bottom">
        <button className={`activity-btn ${showHiveMind ? "active" : ""}`} onClick={() => setShowHiveMind(!showHiveMind)} title="Accounts">
          <BrainCircuit size={24} />
        </button>
        <button className={`activity-btn ${showSettings ? "active" : ""}`} onClick={() => setShowSettings(!showSettings)} title="Manage">
          <Settings size={24} />
          {showSettings && <div className="activity-indicator" />}
        </button>
      </div>
    </div>
  );
}
