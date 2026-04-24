// src/lib/types.ts

export type TaskStatus =
  | "PENDING"
  | "THINKING"
  | "WRITING"
  | "TESTING"
  | "DONE"
  | "FAILED"
  | "CANCELLED"
  | "AWAITING_APPROVAL";

export type AgentType = "planner" | "coder" | "tester" | "researcher" | "reviewer";

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

export interface OpenFile {
  path: string;
  content: string;
  language: string;
  isDirty: boolean;
}

export interface NeurexStore {
  // Chat
  messages: ChatMessage[];
  setMessages: (msgs: ChatMessage[]) => void;
  addMessage: (msg: Omit<ChatMessage, "id" | "timestamp">) => void;
  appendToken: (token: string) => void;

  // Tasks
  tasks: Record<string, TaskNode>;
  upsertTask: (task: TaskNode) => void;
  clearTasks: () => void;

  // Editor
  openFiles: OpenFile[];
  activeFile: string | null;
  openFile: (path: string, content: string, language: string) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string) => void;
  setFileContent: (path: string, content: string) => void;

  // WS
  wsStatus: "connecting" | "connected" | "disconnected";
  setWsStatus: (s: NeurexStore["wsStatus"]) => void;
}
