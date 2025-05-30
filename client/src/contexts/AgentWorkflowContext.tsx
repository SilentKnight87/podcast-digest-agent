"use client";

import React, {
  createContext,
  useContext,
  useReducer,
  ReactNode,
  useEffect,
  useCallback,
  useState,
} from "react";
import {
  AgentWorkflowState,
  AgentNode,
  DataFlow,
  ProcessingStatus,
} from "@/types/workflow";
import { api } from "@/lib/api-client";
import { websocketManager } from "@/lib/websocket-manager";
import { TaskStatusResponse } from "@/types/api-types";
import { toast } from "sonner";

// Define the shape of the context state
interface AgentWorkflowContextType {
  state: AgentWorkflowState;
  dispatch: React.Dispatch<AgentWorkflowAction>;
  startProcessing: (youtubeUrl: string) => Promise<void>;
  isProcessing: boolean;
}

// Initial state for the workflow
const initialWorkflowState: AgentWorkflowState = {
  taskId: "unknown-task",
  processingStatus: {
    overallProgress: 0,
    status: "idle",
    startTime: new Date().toISOString(),
    elapsedTime: "00:00:00",
  },
  agents: [],
  dataFlows: [],
  timeline: [],
};

// Create the context
const AgentWorkflowContext = createContext<
  AgentWorkflowContextType | undefined
>(undefined);

// Define actions for the reducer
type AgentWorkflowAction =
  | { type: "INITIALIZE_WORKFLOW"; payload: Partial<AgentWorkflowState> }
  | { type: "RESET_WORKFLOW" }
  | { type: "SET_PROCESSING_STATUS"; payload: Partial<ProcessingStatus> }
  | { type: "UPDATE_AGENT"; payload: Partial<AgentNode> & { id: string } }
  | { type: "ADD_AGENT"; payload: AgentNode }
  | { type: "UPDATE_DATA_FLOW"; payload: Partial<DataFlow> & { id: string } }
  | { type: "ADD_DATA_FLOW"; payload: DataFlow }
  | { type: "ADD_TIMELINE_EVENT"; payload: AgentWorkflowState["timeline"][0] }
  | { type: "SET_TASK_ID"; payload: string }
  | { type: "SET_VIDEO_DETAILS"; payload: AgentWorkflowState["videoDetails"] }
  | { type: "SET_RESULT"; payload: Partial<AgentWorkflowState["result"]> }
  | { type: "UPDATE_FROM_API_RESPONSE"; payload: TaskStatusResponse };

// Reducer function to manage state updates
const agentWorkflowReducer = (
  state: AgentWorkflowState,
  action: AgentWorkflowAction,
): AgentWorkflowState => {
  switch (action.type) {
    case "INITIALIZE_WORKFLOW":
      return {
        ...state,
        ...action.payload,
        processingStatus: {
          ...state.processingStatus,
          ...action.payload.processingStatus,
          status: action.payload.processingStatus?.status || "processing",
          startTime:
            action.payload.processingStatus?.startTime ||
            new Date().toISOString(),
        },
        agents: action.payload.agents || state.agents,
        dataFlows: action.payload.dataFlows || state.dataFlows,
        timeline: action.payload.timeline || state.timeline,
      };
    case "RESET_WORKFLOW":
      return initialWorkflowState;
    case "SET_PROCESSING_STATUS":
      return {
        ...state,
        processingStatus: { ...state.processingStatus, ...action.payload },
      };
    case "UPDATE_AGENT":
      return {
        ...state,
        agents: state.agents.map((agent) =>
          agent.id === action.payload.id
            ? { ...agent, ...action.payload }
            : agent,
        ),
      };
    case "ADD_AGENT":
      // Avoid adding duplicate agents
      if (state.agents.find((agent) => agent.id === action.payload.id)) {
        return state;
      }
      return {
        ...state,
        agents: [...state.agents, action.payload],
      };
    case "UPDATE_DATA_FLOW":
      return {
        ...state,
        dataFlows: state.dataFlows.map((flow) =>
          flow.id === action.payload.id ? { ...flow, ...action.payload } : flow,
        ),
      };
    case "ADD_DATA_FLOW":
      // Avoid adding duplicate data flows
      if (state.dataFlows.find((df) => df.id === action.payload.id)) {
        return state;
      }
      return {
        ...state,
        dataFlows: [...state.dataFlows, action.payload],
      };
    case "ADD_TIMELINE_EVENT":
      return {
        ...state,
        timeline: [...state.timeline, action.payload].sort(
          (a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
        ),
      };
    case "SET_TASK_ID":
      return {
        ...state,
        taskId: action.payload,
      };
    case "SET_VIDEO_DETAILS":
      return {
        ...state,
        videoDetails: action.payload,
      };
    case "SET_RESULT":
      return {
        ...state,
        result: {
          ...state.result,
          ...action.payload,
        },
      };
    case "UPDATE_FROM_API_RESPONSE":
      // Map API response to our state format
      const apiData = action.payload;

      // Map agents
      const mappedAgents = apiData.agents.map((apiAgent) => {
        // Try to find existing agent to preserve any additional data
        const existingAgent = state.agents.find((a) => a.id === apiAgent.id);

        return {
          id: apiAgent.id,
          name: apiAgent.name,
          description: `${apiAgent.name} Agent`,
          type: apiAgent.id,
          status: apiAgent.status,
          progress: apiAgent.progress,
          startTime: apiAgent.start_time,
          endTime: apiAgent.end_time,
          icon: getIconForAgentType(apiAgent.id),
          // Preserve any existing agent data not in the API response
          ...(existingAgent || {}),
        };
      });

      // Map data flows from API response
      const mappedDataFlows: DataFlow[] = apiData.data_flows.map((flow) => {
        // Map API data flow to our internal format
        return {
          id: flow.id,
          fromAgentId: flow.from_agent_id,
          toAgentId: flow.to_agent_id,
          dataType: flow.data_type,
          status: flow.status,
        };
      });

      // Create video details from API response
      const videoDetails = apiData.video_details
        ? {
            title: apiData.video_details.title,
            thumbnail: apiData.video_details.thumbnail,
            channelName: apiData.video_details.channel_name,
            duration: apiData.video_details.duration,
          }
        : state.videoDetails;

      // Map processing status
      const processingStatus: ProcessingStatus = {
        ...state.processingStatus,
        overallProgress: apiData.processing_status.overall_progress,
        status: apiData.processing_status.status,
        currentAgentId: apiData.processing_status.current_agent_id || undefined,
        startTime:
          apiData.processing_status.start_time ||
          state.processingStatus.startTime,
        // Only override endTime if it's provided in the response
        ...(apiData.processing_status.end_time && {
          endTime: apiData.processing_status.end_time,
        }),
      };

      // Create result data from API response
      const result = {
        ...state.result,
        ...(apiData.summary_text && { summaryText: apiData.summary_text }),
        ...(apiData.audio_file_url && { audioUrl: apiData.audio_file_url }),
      };

      return {
        ...state,
        taskId: apiData.task_id,
        processingStatus,
        agents: mappedAgents,
        dataFlows: mappedDataFlows,
        videoDetails,
        result,
      };
    default:
      return state;
  }
};

// Helper function to determine flow status based on connecting agent statuses
const determineFlowStatus = (
  fromAgent: AgentNode,
  toAgent: AgentNode,
): DataFlow["status"] => {
  if (fromAgent.status === "completed" && toAgent.status === "completed") {
    return "completed";
  }
  if (fromAgent.status === "completed" && toAgent.status === "running") {
    return "transferring";
  }
  if (fromAgent.status === "error" || toAgent.status === "error") {
    return "error";
  }
  return "pending";
};

// Helper function to get icon for agent type
const getIconForAgentType = (agentType: string): string => {
  const iconMap: Record<string, string> = {
    transcript_fetcher: "FileText",
    summarizer: "FileSearch",
    synthesizer: "FileEdit",
    audio_generator: "Speaker",
  };

  return iconMap[agentType] || "Circle";
};

// Context Provider component
export const AgentWorkflowProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(
    agentWorkflowReducer,
    initialWorkflowState,
  );
  const [isProcessing, setIsProcessing] = useState(false);

  // Clean up WebSocket connection when component unmounts
  useEffect(() => {
    return () => {
      websocketManager.disconnect();
    };
  }, []);

  // Start processing a YouTube URL
  const startProcessing = useCallback(async (youtubeUrl: string) => {
    try {
      setIsProcessing(true);

      // Reset the workflow state
      dispatch({ type: "RESET_WORKFLOW" });

      // Initialize with temporary state
      dispatch({
        type: "INITIALIZE_WORKFLOW",
        payload: {
          processingStatus: {
            status: "processing",
            overallProgress: 0,
            startTime: new Date().toISOString(),
          },
          timeline: [
            {
              timestamp: new Date().toISOString(),
              eventType: "process_started",
              message: `Processing started for ${youtubeUrl}`,
            },
          ],
          videoDetails: {
            title: `Processing ${youtubeUrl}...`,
            thumbnail: "",
            channelName: "",
            duration: 0,
          },
        },
      });

      // Submit the URL to the API
      const response = await api.processYoutubeUrl(youtubeUrl);
      const { task_id } = response.data;

      // Update the task ID
      dispatch({ type: "SET_TASK_ID", payload: task_id });

      // Connect WebSocket for real-time updates
      websocketManager.connect(task_id);

      // Subscribe to WebSocket updates
      const unsubscribe = websocketManager.subscribe((data) => {
        console.log("[AgentWorkflow] Received WebSocket update:", data);

        // Update state from API response
        dispatch({ type: "UPDATE_FROM_API_RESPONSE", payload: data });

        // Check if processing has completed
        if (
          data.processing_status.status === "completed" ||
          data.processing_status.status === "failed"
        ) {
          setIsProcessing(false);

          // Show success or error notification
          if (data.processing_status.status === "completed") {
            toast.success("Podcast digest created successfully!");
          } else {
            toast.error("Failed to create podcast digest. Please try again.");
          }

          // Disconnect WebSocket
          websocketManager.disconnect();
        }
      });

      // Fetch initial task status
      const statusResponse = await api.getTaskStatus(task_id);
      dispatch({
        type: "UPDATE_FROM_API_RESPONSE",
        payload: statusResponse.data,
      });

      // Return cleanup function
      return () => {
        unsubscribe();
        websocketManager.disconnect();
      };
    } catch (error) {
      console.error("Error starting processing:", error);
      setIsProcessing(false);

      // Add error to timeline
      dispatch({
        type: "ADD_TIMELINE_EVENT",
        payload: {
          timestamp: new Date().toISOString(),
          eventType: "process_failed",
          message: `Error starting processing: ${(error as Error).message || "Unknown error"}`,
        },
      });

      // Update processing status to failed
      dispatch({
        type: "SET_PROCESSING_STATUS",
        payload: {
          status: "failed",
          endTime: new Date().toISOString(),
        },
      });

      // Show error notification
      toast.error("Failed to start processing. Please try again.");

      throw error;
    }
  }, []);

  return (
    <AgentWorkflowContext.Provider
      value={{ state, dispatch, startProcessing, isProcessing }}
    >
      {children}
    </AgentWorkflowContext.Provider>
  );
};

// Custom hook to use the AgentWorkflow context
export const useAgentWorkflow = (): AgentWorkflowContextType => {
  const context = useContext(AgentWorkflowContext);
  if (context === undefined) {
    throw new Error(
      "useAgentWorkflow must be used within an AgentWorkflowProvider",
    );
  }
  return context;
};
