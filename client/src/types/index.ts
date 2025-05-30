// Based on mock_data.json and FEATURE_ROADMAP.md

// Export API types
export * from "./api-types";

export interface VideoDetails {
  title: string;
  thumbnail: string;
  channelName: string;
  url: string;
  duration: number; // in seconds
  uploadDate: string;
}

export interface AgentLog {
  timestamp: string;
  level: "info" | "warning" | "error";
  message: string;
}

// Conforms to FEATURE_ROADMAP.md and mock_data.json
export interface AgentNode {
  id: string;
  name: string;
  description: string;
  type: string;
  status: "pending" | "running" | "completed" | "error";
  progress: number; // 0-100
  startTime?: string;
  endTime?: string;
  duration?: string; // from mock_data
  icon: string; // Lucide icon name or other identifier
  logs?: AgentLog[];
  metrics?: Record<string, unknown>; // Changed any to unknown
  preliminaryData?: Record<string, unknown>; // Changed any to unknown
  configuration?: Record<string, unknown>; // Changed any to unknown
  estimatedDuration?: string; // from mock_data
}

// Conforms to FEATURE_ROADMAP.md and mock_data.json
export interface DataFlow {
  id: string;
  fromAgentId: string;
  toAgentId: string;
  dataType: string;
  status: "pending" | "transferring" | "completed" | "error";
  metadata?: Record<string, unknown>; // Changed any to unknown
}

// Conforms to FEATURE_ROADMAP.md and mock_data.json
export interface ProcessingStatus {
  overallProgress: number;
  status: "idle" | "processing" | "completed" | "failed"; // Added 'idle'
  currentAgentId: string | null; // Can be null initially
  startTime?: string;
  estimatedEndTime?: string;
  elapsedTime?: string;
  remainingTime?: string;
  endTime?: string; // Added endTime to match mock_data.json for completed/failed tasks
}

export interface TimelineEvent {
  timestamp: string;
  event: string; // e.g., 'process_started', 'agent_completed', 'progress_update'
  agentId?: string;
  message: string;
}

export interface ActiveTask {
  taskId: string;
  videoDetails: VideoDetails;
  processingStatus: ProcessingStatus;
  agents: AgentNode[];
  dataFlows: DataFlow[];
  timeline: TimelineEvent[];
  outputUrl?: string; // Added for completed audio URL
}

export interface AudioOutput {
  url: string;
  duration: string;
  fileSize: string;
}

export interface SummaryDetails {
  title: string;
  host?: string; // Optional as seen in mock
  duration?: string; // Optional
  mainPoints: string[];
  highlights?: string[]; // Optional
  keyQuotes?: string[]; // Optional
}

export interface CompletedTask {
  taskId: string;
  videoDetails: VideoDetails;
  completionTime: string;
  processingDuration: string;
  audioOutput: AudioOutput;
  summary: SummaryDetails;
}

export interface ConfigVoice {
  id: string;
  name: string;
  language: string;
}

export interface ConfigSummaryLength {
  id: string;
  name: string;
  description: string;
  default?: boolean;
}

export interface ConfigAudioStyle {
  id: string;
  name: string;
  description: string;
  default?: boolean;
}

export interface ConfigOptions {
  availableVoices: ConfigVoice[];
  summaryLengths: ConfigSummaryLength[];
  audioStyles: ConfigAudioStyle[];
}

export interface NavLink {
  name: string;
  url: string;
  icon: string; // Lucide icon name
}

export interface Alert {
  id: string;
  type: "info" | "warning" | "error" | "success";
  message: string;
  duration?: number; // Optional: auto-dismiss duration in ms
}

export interface UiState {
  theme: "light" | "dark";
  navLinks: NavLink[];
  alerts: Alert[]; // Use the defined Alert interface
}

// Root structure of mock_data.json
export interface MockData {
  activeTask: ActiveTask | null; // Can be null if no task is active
  completedTasks: CompletedTask[];
  configOptions: ConfigOptions;
  uiState: UiState;
}

// Specific types for the Workflow Context
// export interface WorkflowState extends ActiveTask { // Commenting out as it's currently empty
//   // We might add more UI-specific state here if needed
// }

export interface WorkflowContextType {
  workflowState: ActiveTask | null; // Changed from WorkflowState to ActiveTask
  isProcessing: boolean;
  startProcessing: (youtubeUrl: string) => void; // To initiate with a URL
  // Function to manually advance state for testing (optional)
  // advanceState?: () => void;
  selectedAgent: AgentNode | null;
  setSelectedAgent: (agent: AgentNode | null) => void;
}
