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

export type AgentType = "planner" | "coder" | "tester" | "researcher" | "reviewer" | "debater" | "commander" | "swarm";

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
  is_checkpoint?: boolean;
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
  isRoot?: boolean;
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
  root?: string;
  content: string;
  originalContent?: string;
  language: string;
  isDirty: boolean;
  isPreview?: boolean;
  isPinned?: boolean;
}

export interface SwarmDiff {
  path: string;
  original: string;
  modified: string;
  status: 'pending' | 'accepted' | 'discarded';
}

export interface DebateMessage {
  id: string;
  agent: string;
  role: 'planner' | 'coder' | 'reviewer' | 'judge';
  content: string;
  timestamp: string;
}

export interface ModelProfile {
  name: string;
  engine: string;
  params: string;
  size_gb?: number;
  context_window: number;
  vram_required_gb: number;
  recommended_tasks: string[];
  description?: string;
  benchmarks?: Record<string, string>;
  repo_url?: string;
  is_downloaded?: boolean;
  is_community?: boolean;
  deployed?: boolean;
  variants?: { name: string; size_gb: number; params: string }[];
}

export type CatalogOrigin = 'LOCAL' | 'HF' | 'RPC' | 'NODE';

export interface CatalogEntry extends ModelProfile {
  origin: CatalogOrigin;
  nodeName?: string;
  is_active?: boolean;
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
  ram_total_gb: number;
  ram_used_gb: number;
  ram_available_gb: number;
  ram_percent: number;
  cpu_percent: number;
  disk_total_gb?: number;
  disk_used_gb?: number;
  disk_free_gb?: number;
  disk_percent?: number;
  storage_health?: Record<string, {
    exists: boolean;
    writable: boolean;
    status: "ok" | "error";
  }>;
}

export interface MeshPeer {
  name: string;
  url: string;
  status: "online" | "offline";
  vram_gb: number;
  ram_total_gb?: number;
  cpu_percent?: number;
  latency_ms: number;
  models?: string[];
  rpc_endpoint?: string;
  predicted_load?: number;
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
  is_active?: boolean;
}

export interface ModelRoute {
  model: string;
  params?: string;
}

export interface Settings {
  model_routes: Record<string, string | ModelRoute>;
  [key: string]: any;
}

export interface SearchResult {
  path: string;
  root?: string;
  line: number;
  content: string;
}

export interface Diagnostic {
  path: string;
  message: string;
  severity: number;
  line: number;
  column: number;
  source: string;
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

export interface TerminalSession {
  id: string;
  name: string;
  cwd?: string;
}

export interface NeurexStore {
  // App Lifecycle
  isInitialized: boolean;
  isInitializing: boolean;
  setIsInitialized: (val: boolean) => void;
  setIsInitializing: (val: boolean) => void;
  lastLocalSave: number;

  // Auth
  onboardingRequired: boolean;
  setOnboardingRequired: (val: boolean) => void;
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  refreshMe: () => Promise<void>;

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
  diagnostics: Diagnostic[];
  workspaceDiagnostics: Record<string, Diagnostic[]>;
  collapseSignal: number;
  setFileTree: (tree: FileNode[]) => void;
  refreshFileTree: () => Promise<void>;
  fetchSubtree: (path: string) => Promise<void>;
  expandedFolders: Set<string>;
  collapsedFolders: Set<string>;
  toggleFolder: (path: string, val?: boolean) => void;
  gitBranch: string;
  gitChanges: any[];
  refreshGitStatus: () => Promise<void>;
  workspaceFolders: string[];
  addWorkspaceFolder: (path: string) => Promise<void>;
  removeWorkspaceFolder: (path: string) => void;
  setWorkspace: (path: string) => Promise<void>;
  closeWorkspace: () => Promise<void>;
  createFile: (path: string, root_path?: string) => Promise<void>;
  createFolder: (path: string, root_path?: string) => Promise<void>;
  collapseAllFolders: () => void;
  updateDiagnostics: (path: string, diagnostics: Diagnostic[]) => void;

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
  sendMessage: (content: string) => void;

  // Tasks
  tasks: Record<string, TaskNode>;
  upsertTask: (task: TaskNode) => void;
  clearTasks: () => void;
  mutateGraph: (graphId: string, payload: {
    action: "rewire" | "insert" | "delete";
    task_id?: string;
    parent_id?: string | null;
    child_id?: string | null;
    title?: string;
    description?: string;
    agent_type?: AgentType;
  }) => Promise<any>;
  toggleBreakpoint: (taskId: string) => Promise<void>;
  approveTask: (taskId: string) => Promise<void>;

  // Editor
  setFileLanguage: (path: string, language: string) => void;
  cursorPosition: { line: number, ch: number };
  setCursorPosition: (line: number, ch: number) => void;
  openFiles: OpenFile[];
  activeFile: string | null;
  activeFileLanguage: string;
  openFile: (path: string, content: string, language: string, isPreview?: boolean, root?: string) => void;
  closeFile: (path: string) => void;
  closeOthers: (path: string) => void;
  closeToRight: (path: string) => void;
  closeSaved: () => void;
  closeAllFiles: () => void;
  togglePin: (path: string) => void;
  setActiveFile: (path: string | null) => void;
  editorPanes: { id: string; path: string | null }[];
  setEditorPanes: (panes: { id: string; path: string | null }[]) => void;
  splitEditor: (direction: "horizontal" | "vertical") => void;
  closePane: (id: string) => void;
  setPaneFile: (paneId: string, path: string | null) => void;
  setFileContent: (path: string, content: string) => void;
  setDiff: (path: string, original: string, modified: string) => void;
  acceptDiff: (path: string) => void;
  discardDiff: (path: string) => void;
  saveFile: (path: string) => Promise<void>;
  diffFile: (path: string) => Promise<void>;
  renameFile: (oldPath: string, newPath: string, root_path?: string) => Promise<void>;
  deleteFile: (path: string, root_path?: string) => Promise<void>;
  pendingJump: { path: string; line: number; timestamp: number; root?: string } | null;
  setPendingJump: (path: string, line: number, root?: string) => void;
  clearPendingJump: () => void;

  // Swarm Diffs
  swarmDiffs: Record<string, SwarmDiff>;
  setSwarmDiffs: (diffs: Record<string, SwarmDiff>) => void;
  acceptSwarmDiff: (path: string) => void;
  discardSwarmDiff: (path: string) => void;
  clearSwarmDiffs: () => void;

  // Debate Arena
  debateMessages: DebateMessage[];
  addDebateMessage: (msg: DebateMessage) => void;
  clearDebateMessages: () => void;

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

  // Terminal
  terminalSessions: TerminalSession[];
  activeTerminalId: string;
  addTerminalSession: (name?: string, cwd?: string) => void;
  closeTerminalSession: (id: string) => void;
  setActiveTerminalId: (id: string) => void;
  clearActiveTerminal: () => void;
  runActiveFile: () => void;

  // Modals
  modalOpen: boolean;
  setModalOpen: (val: boolean | ((v: boolean) => boolean)) => void;

  // Theme
  theme: { 
    accent_color: string; 
    glow_color: string; 
    enable_glassmorphism: boolean; 
    enable_animations: boolean; 
    enable_swarm_glow: boolean; 
    menu_mode: "vertical" | "horizontal";  
    terminal_line_height: number;
    terminal_font_size: number;
    terminal_font_family: string;
    terminal_cursor_style: "block" | "bar" | "underline";
  };
  setTheme: (theme: any) => void;
  refreshTheme: () => Promise<void>;
  // Settings
  settings: Settings | null;
  setSettings: (settings: Settings) => void;
   refreshSettings: () => Promise<void>;
  hiveStats: { total_nodes: number; memory_count: number };
  refreshHiveStats: () => Promise<void>;
  send: (payload: any) => void;

  // UI State & Panel Management
  sidebarTab: string;
  setSidebarTab: (tab: string) => void;
  sidebarOrder: string[];
  setSidebarOrder: (order: string[]) => void;
  showAIPanel: boolean;
  setShowAIPanel: (val: boolean | ((v: boolean) => boolean)) => void;
  showSettings: boolean;
  setShowSettings: (val: boolean | ((v: boolean) => boolean)) => void;

  showAbout: boolean;
  setShowAbout: (val: boolean | ((v: boolean) => boolean)) => void;
}
