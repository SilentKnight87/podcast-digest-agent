// API Request and Response Types - matching FastAPI backend Pydantic models

export interface ProcessUrlRequest {
  youtube_url: string;
}

export interface ProcessUrlResponse {
  task_id: string;
  status: string;
}

export interface AgentLog {
  timestamp: string;
  level: string;
  message: string;
}

export interface AgentStatus {
  id: string;
  name: string;
  description?: string;
  type?: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  start_time?: string;
  end_time?: string;
  icon?: string;
  logs?: AgentLog[];
  metrics?: Record<string, any>;
}

export interface VideoDetails {
  title: string;
  thumbnail: string;
  channel_name: string;
  duration: number; // in seconds
  upload_date: string;
  url: string;
}

export interface DataFlow {
  id: string;
  from_agent_id: string;
  to_agent_id: string;
  data_type: string;
  status: 'pending' | 'transferring' | 'completed' | 'error';
  metadata?: Record<string, any>;
}

export interface Timeline {
  timestamp: string;
  event_type: string;
  message: string;
  agent_id?: string;
}

export interface TaskStatusResponse {
  task_id: string;
  processing_status: {
    status: 'queued' | 'processing' | 'completed' | 'failed';
    overall_progress: number;
    current_agent_id: string | null;
    start_time?: string;
    end_time?: string;
    estimated_end_time?: string;
    elapsed_time?: string;
    remaining_time?: string;
  };
  agents: AgentStatus[];
  summary_text?: string;
  audio_file_url?: string;
  video_details?: VideoDetails;
  data_flows: DataFlow[];
  timeline: Timeline[];
  error_message?: string;
}

export interface HistoryResponse {
  items: TaskStatusResponse[];
  total: number;
  offset: number;
  limit: number;
}

export interface ConfigResponse {
  available_voices: Array<{
    id: string;
    name: string;
    language: string;
  }>;
  summary_lengths: Array<{
    id: string;
    name: string;
    description: string;
    default?: boolean;
  }>;
  audio_styles: Array<{
    id: string;
    name: string;
    description: string;
    default?: boolean;
  }>;
}

// Error response from API
export interface ApiError {
  detail: string;
  status_code: number;
  error_code?: string;
}