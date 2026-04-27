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
  approval_reason?: string;
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
  status?: "M" | "U" | "D" | null;
  has_m?: boolean;
  has_u?: boolean;
  errors?: number;
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
  originalContent?: string;
  language: string;
  isDirty: boolean;
}

export interface ModelProfile {
  name: string;
  engine: string;
  params: string;
  context_window: number;
  vram_required_gb: number;
  recommended_tasks: string[];
  description?: string;
  benchmarks?: Record<string, string>;
  repo_url?: string;
  is_downloaded?: boolean;
}

export interface InfraEngine {
  name: string;
  status: "running" | "stopped" | "missing";
  version?: string;
  installed: boolean;
  details?: string;
}

export interface InfraMetrics {
  vram_gb: number;
  ram_used_gb: number;
  cpu_usage: number;
}

export interface MeshPeer {
  name: string;
  url: string;
  status: "online" | "offline";
  vram_gb: number;
  latency_ms: number;
  models?: string[];
}

export interface Presence {
  user_id: string;
  cursor: { line: number; ch: number } | null;
  active_file: string | null;
  status: string;
}

export interface FileLock {
  path: string;
  locked_by: string;
  expires_at: string;
}

export interface User {
  id: string;
  username: string;
  role: "admin" | "developer" | "viewer";
}

export interface SearchResult {
  path: string;
  line: number;
  content: string;
}

export interface SearchState {
  query: string;
  results: SearchResult[];
  includeGlob: string;
  excludeGlob: string;
  caseSensitive: boolean;
  useRegex: boolean;
  wholeWord: boolean;
}

export interface NeurexStore {
  // App Lifecycle
  isInitialized: boolean;
  isInitializing: boolean;
  setIsInitialized: (val: boolean) => void;
  setIsInitializing: (val: boolean) => void;

  // Auth
  onboardingRequired: boolean;
  setOnboardingRequired: (val: boolean) => void;
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;

  // Infra
  infraEngines: InfraEngine[];
  infraMetrics: InfraMetrics | null;
  infraRegistry: ModelProfile[];
  infraSkills: any[];
  infraPeers: MeshPeer[];
  refreshInfra: () => Promise<void>;

  // Speech
  speechLang: string;
  setSpeechLang: (lang: string) => void;

  // File Tree
  fileTree: FileNode[];
  setFileTree: (tree: FileNode[]) => void;
  refreshFileTree: () => Promise<void>;

  // Chat
  messages: ChatMessage[];
  activeConversationId: string;
  preferredModel: string;
  conversations: { conversation_id: string; last_message: string }[];
  setMessages: (msgs: ChatMessage[]) => void;
  addMessage: (msg: Omit<ChatMessage, "id" | "timestamp">) => void;
  appendToken: (token: string) => void;
  setActiveConversation: (id: string) => void;
  setConversations: (convs: { conversation_id: string; last_message: string }[]) => void;
  setPreferredModel: (model: string) => void;
  newConversation: () => void;

  // Tasks
  tasks: Record<string, TaskNode>;
  upsertTask: (task: TaskNode) => void;
  clearTasks: () => void;

  // Editor
  setFileLanguage: (path: string, language: string) => void;
  openFiles: OpenFile[];
  activeFile: string | null;
  openFile: (path: string, content: string, language: string) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string) => void;
  setFileContent: (path: string, content: string) => void;
  setDiff: (path: string, original: string, modified: string) => void;
  acceptDiff: (path: string) => void;
  discardDiff: (path: string) => void;
  saveFile: (path: string) => Promise<void>;
  pendingJump: { path: string; line: number; timestamp: number } | null;
  setPendingJump: (path: string, line: number) => void;
  clearPendingJump: () => void;

  // WS
  wsStatus: "connecting" | "connected" | "disconnected";
  setWsStatus: (s: NeurexStore["wsStatus"]) => void;
  presence: Presence[];
  setPresence: (p: Presence[]) => void;
  locks: Record<string, FileLock>;
  setLocks: (l: Record<string, FileLock>) => void;

  // Search
  search: SearchState;
  setSearch: (state: Partial<SearchState>) => void;
  clearSearch: () => void;
  // Modals
  modalOpen: boolean;
  setModalOpen: (val: boolean) => void;
  // Hive
  hiveStats: { total_nodes: number; memory_count: number };
  // Theme
  theme: { accent_color: string; glow_color: string; enable_glassmorphism: boolean; enable_animations: boolean; enable_swarm_glow: boolean };
  setTheme: (theme: any) => void;
  refreshTheme: () => Promise<void>;
}
