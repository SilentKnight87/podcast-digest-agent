/**
 * Represents a single agent or node in the processing pipeline.
 */
export interface AgentNode {
  id: string;
  name: string;
  description: string;
  type: string; // e.g., 'transcription', 'summarization', 'tts'
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number; // Percentage, 0-100
  startTime?: string; // ISO 8601 date-time string
  endTime?: string; // ISO 8601 date-time string
  icon: string; // Can be a Lucide icon name (e.g., "FileText") or other identifier like "fa/FaYoutube"
  logs?: Array<{
    timestamp: string; // ISO 8601 date-time string
    level: 'info' | 'warn' | 'error' | 'debug';
    message: string;
  }>;
  metrics?: Record<string, unknown>; // Optional: for agent-specific metrics like word count, confidence, etc.
}

/**
 * Represents the flow of data between two agents in the pipeline.
 */
export interface DataFlow {
  id: string;
  fromAgentId: string;
  toAgentId: string;
  dataType: string; // e.g., 'transcript', 'summary', 'audio_script'
  status: 'pending' | 'transferring' | 'completed' | 'error';
  metadata?: Record<string, unknown>; // Optional: for data-specific metadata
}

/**
 * Represents the overall status of the podcast digest generation process.
 */
export interface ProcessingStatus {
  overallProgress: number; // Percentage, 0-100
  status: 'idle' | 'processing' | 'completed' | 'failed'; // 'idle' can be pre-processing
  currentAgentId?: string; // ID of the currently active agent, if any
  startTime: string; // ISO 8601 date-time string
  estimatedEndTime?: string; // ISO 8601 date-time string
  elapsedTime: string; // Formatted string e.g., "00:11:30"
  remainingTime?: string; // Formatted string e.g., "00:03:30"
  currentStepDescription?: string; // e.g. "Transcribing audio..."
}

/**
 * Represents the entire state of the agent workflow visualization.
 */
export interface AgentWorkflowState {
  taskId: string;
  processingStatus: ProcessingStatus;
  agents: AgentNode[];
  dataFlows: DataFlow[];
  timeline: Array<{ // Chronological events in the processing pipeline
    timestamp: string; // ISO 8601 date-time string
    eventType: string; // e.g., 'agent_started', 'data_transfer_completed'
    agentId?: string;
    dataFlowId?: string;
    message: string;
    details?: Record<string, unknown>;
  }>;
  videoDetails?: {
    title: string;
    thumbnail: string;
    channelName: string;
    duration: number; // in seconds
  };
  result?: {
    summaryText?: string;
    audioUrl?: string;
    // Potentially other results like key points, quotes, etc.
  };
  error?: {
    message: string;
    agentId?: string;
    details?: unknown;
  };
}
