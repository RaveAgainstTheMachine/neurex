// src/lib/types.ts

export type TaskStatus =
  | "pending"
  | "thinking"
  | "writing"
  | "testing"
  | "done"
  | "failed"
  | "cancelled";

export type AgentType = "planner" | "coder" | "tester";

export interface TaskNode {
  id: string;
  graph_id: string;
  parent_id: string | null;
  agent_type: AgentType;
  title: string;
  description: string;
  status: TaskStatus;
  result: string | null;
  error: string | null;
  iteration: number;
  created_at: string;
  updated_at: string;
}

export interface FileNode {
  name: string;
  type: "file" | "dir";
  path?: string;
  children?: FileNode[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  graph_id?: string;
  timestamp: Date;
}

export interface WsEvent {
  event: "task_created" | "task_updated" | "token" | "done" | "error" | "cancelled";
  data: unknown;
}

// Zustand store shape
export interface NeurexStore {
  // Chat
  messages: ChatMessage[];
  setMessages: (msgs: ChatMessage[]) => void;
  addMessage: (msg: Omit<ChatMessage, "id" | "timestamp">) => void;
  appendToken: (token: string) => void;


  // Tasks
  tasks: Record<string, TaskNode>;
  upsertTask: (task: TaskNode) => void;

  // Editor
  openFile: string | null;
  setOpenFile: (path: string | null) => void;
  fileContents: Record<string, string>;
  setFileContent: (path: string, content: string) => void;

  // Scratchpad
  scratchpad: string;
  setScratchpad: (text: string) => void;

  // Connection
  wsStatus: "connecting" | "connected" | "disconnected";
  setWsStatus: (s: NeurexStore["wsStatus"]) => void;
}
