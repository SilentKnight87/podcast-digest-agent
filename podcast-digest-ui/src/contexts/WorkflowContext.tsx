"use client"; // Add this directive at the top

import { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from 'react';
import type { ReactNode, FC } from 'react';
import type {
  ActiveTask,
  AgentNode,
  DataFlow,
  ProcessingStatus,
  WorkflowContextType,
  VideoDetails,
  MockData,
  TaskStatusResponse // Import TaskStatusResponse from api-types
} from '../types';
import initialMockDataJson from '../../mock_data.json';
import React from 'react';
import { api } from '@/lib/api-client';
import { websocketManager } from '@/lib/websocket-manager';

// Use MockData type for initialMockDataJson
const initialMockData = initialMockDataJson as MockData;

const WorkflowContext = createContext<WorkflowContextType | undefined>(undefined);

interface WorkflowProviderProps {
  children: ReactNode;
}

const getInitialAgentState = (agent: AgentNode): AgentNode => ({
  ...agent,
  status: 'pending',
  progress: 0,
  startTime: undefined,
  endTime: undefined,
  logs: [],
});

const getInitialDataFlowState = (flow: DataFlow): DataFlow => ({
  ...flow,
  status: 'pending',
});

const defaultVideoDetails: VideoDetails = {
    title: 'Initializing...',
    thumbnail: '',
    channelName: '',
    url: '',
    duration: 0,
    uploadDate: ''
};

const createInitialProcessingStatus = (): ProcessingStatus => ({
  overallProgress: 0,
  status: 'idle',
  currentAgentId: null,
  startTime: undefined,
  elapsedTime: '00:00:00',
  remainingTime: undefined,
  estimatedEndTime: undefined,
});

// Helper function to convert API response to our internal state format
const mapApiResponseToWorkflowState = (response: TaskStatusResponse): ActiveTask => {
  console.log('[mapApiResponseToWorkflowState] Input response:', {
    task_id: response.task_id,
    audio_file_url: response.audio_file_url,
    status: response.processing_status?.status,
    hasAudioUrl: !!response.audio_file_url,
    audioUrlType: typeof response.audio_file_url
  });
  
  // Map API agents to our internal format
  const agents = response.agents.map(apiAgent => ({
    id: apiAgent.id,
    name: apiAgent.name,
    description: `${apiAgent.name} Agent`, // Default description
    type: apiAgent.id, // Using ID as type for now
    status: apiAgent.status,
    progress: apiAgent.progress,
    startTime: apiAgent.start_time,
    endTime: apiAgent.end_time,
    icon: getIconForAgentType(apiAgent.id), // Helper function to map agent type to icon
    logs: []
  }));

  // Map API data flows to our internal format
  const dataFlows: DataFlow[] = response.data_flows.map(flow => ({
    id: flow.id,
    fromAgentId: flow.from_agent_id,
    toAgentId: flow.to_agent_id,
    dataType: flow.data_type,
    status: flow.status
  }));

  // Create video details
  const videoDetails: VideoDetails = response.video_details ? {
    title: response.video_details.title,
    thumbnail: response.video_details.thumbnail,
    channelName: response.video_details.channel_name,
    url: response.video_details.url,
    duration: response.video_details.duration,
    uploadDate: response.video_details.upload_date
  } : defaultVideoDetails;

  // Map API timeline events to our internal format
  const timeline = response.timeline.map(event => ({
    timestamp: event.timestamp,
    event: event.event_type,
    agentId: event.agent_id,
    message: event.message
  }));

  const result = {
    taskId: response.task_id,
    videoDetails,
    processingStatus: {
      overallProgress: response.processing_status.overall_progress,
      status: response.processing_status.status,
      currentAgentId: response.processing_status.current_agent_id,
      startTime: response.processing_status.start_time,
      endTime: response.processing_status.end_time,
      elapsedTime: calculateElapsedTime(response.processing_status.start_time),
    },
    agents,
    dataFlows,
    timeline,
    outputUrl: response.audio_file_url || undefined  // Make sure undefined is explicit
  };
  
  console.log('[mapApiResponseToWorkflowState] Output result:', {
    outputUrl: result.outputUrl,
    rawAudioUrl: response.audio_file_url,
    status: result.processingStatus.status,
    isUrlDefined: result.outputUrl !== undefined,
    isUrlEmpty: result.outputUrl === ''
  });
  
  return result;
};

// Helper function to determine flow status based on connecting agent statuses
const determineFlowStatus = (fromAgent: AgentNode, toAgent: AgentNode): DataFlow['status'] => {
  if (fromAgent.status === 'completed' && toAgent.status === 'completed') {
    return 'completed';
  }
  if (fromAgent.status === 'completed' && toAgent.status === 'running') {
    return 'transferring';
  }
  if (fromAgent.status === 'error' || toAgent.status === 'error') {
    return 'error';
  }
  return 'pending';
};

// Helper function to get icon for agent type
const getIconForAgentType = (agentType: string): string => {
  const iconMap: Record<string, string> = {
    'youtube-node': 'Youtube',
    'transcript-fetcher': 'FileText',
    'transcript_fetcher': 'FileText',
    'summarizer-agent': 'FileSearch',
    'summarizer': 'FileSearch',
    'synthesizer-agent': 'FileEdit',
    'synthesizer': 'FileEdit',
    'audio-generator': 'Speaker',
    'audio_generator': 'Speaker',
    'ui-player': 'PlayCircle'
  };
  
  return iconMap[agentType] || 'Circle';
};

// Helper function to calculate elapsed time
const calculateElapsedTime = (startTime?: string): string => {
  if (!startTime) return '00:00:00';
  
  const elapsedMs = new Date().getTime() - new Date(startTime).getTime();
  return new Date(elapsedMs).toISOString().substr(11, 8);
};

export const WorkflowProvider: FC<WorkflowProviderProps> = ({ children }) => {
  const [workflowState, setWorkflowState] = useState<ActiveTask | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentNode | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const isInitializedRef = useRef(false);
  const elapsedTimeIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const initialAgents = useMemo(() => 
    initialMockData.activeTask ? initialMockData.activeTask.agents.map(getInitialAgentState) : [], 
  []);

  const initialDataFlows = useMemo(() => 
    initialMockData.activeTask ? initialMockData.activeTask.dataFlows.map(getInitialDataFlowState) : [],
  []);
  
  const initialVideoDetails = useMemo(() => 
      initialMockData.activeTask?.videoDetails || defaultVideoDetails,
  []);

  const resetToInitialState = useCallback(() => {
    console.log("[WORKFLOW_CONTEXT] resetToInitialState called");
    // Clean up any existing WebSocket connection
    websocketManager.disconnect();
    
    // Clean up elapsed time interval if any
    if (elapsedTimeIntervalRef.current) {
      clearInterval(elapsedTimeIntervalRef.current);
      elapsedTimeIntervalRef.current = null;
    }
    
    setCurrentTaskId(null);
    
    setWorkflowState(() => {
        console.log("[WORKFLOW_CONTEXT] Setting new initial workflow state");
        return {
            taskId: initialMockData.activeTask?.taskId || `task-${Date.now()}`,
            videoDetails: initialVideoDetails,
            processingStatus: createInitialProcessingStatus(),
            agents: initialAgents,
            dataFlows: initialDataFlows,
            timeline: [],
            outputUrl: undefined,
        };
    });
    
    setIsProcessing(false);
    setSelectedAgent(null);
    console.log("[WORKFLOW_CONTEXT] resetToInitialState finished");
  }, [initialAgents, initialDataFlows, initialVideoDetails]);

  // Update the elapsed time for active tasks
  useEffect(() => {
    if (isProcessing && workflowState?.processingStatus.startTime) {
      // Setup an interval to update the elapsed time
      elapsedTimeIntervalRef.current = setInterval(() => {
        setWorkflowState(prevState => {
          if (!prevState || !prevState.processingStatus.startTime) return prevState;
          
          return {
            ...prevState,
            processingStatus: {
              ...prevState.processingStatus,
              elapsedTime: calculateElapsedTime(prevState.processingStatus.startTime)
            }
          };
        });
      }, 1000);
    }
    
    return () => {
      if (elapsedTimeIntervalRef.current) {
        clearInterval(elapsedTimeIntervalRef.current);
        elapsedTimeIntervalRef.current = null;
      }
    };
  }, [isProcessing, workflowState?.processingStatus.startTime]);

  useEffect(() => {
    console.log("[WORKFLOW_CONTEXT] Mount/update useEffect runs", { 
        isInitialized: isInitializedRef.current, 
        workflowStatus: workflowState?.processingStatus?.status 
    });

    if (!isInitializedRef.current) {
        if (!workflowState || (workflowState.processingStatus.status !== 'completed' && !workflowState.outputUrl)) {
            console.log("[WORKFLOW_CONTEXT] Not initialized and condition met, calling resetToInitialState");
            resetToInitialState();
        }
        isInitializedRef.current = true;
    }
    
    return () => {
      // Clean up WebSocket connection when component unmounts
      websocketManager.disconnect();
      
      // Clean up elapsed time interval
      if (elapsedTimeIntervalRef.current) {
        clearInterval(elapsedTimeIntervalRef.current);
        elapsedTimeIntervalRef.current = null;
      }
    };
  }, [resetToInitialState, workflowState]);

  // Main function to start processing a YouTube URL
  function startProcessing(youtubeUrl: string) {
    console.log('[WORKFLOW] Starting processing for URL:', youtubeUrl);
    
    // Clean up any existing WebSocket connection
    websocketManager.disconnect();
    
    // Clear any existing elapsed time interval
    if (elapsedTimeIntervalRef.current) {
      clearInterval(elapsedTimeIntervalRef.current);
      elapsedTimeIntervalRef.current = null;
    }
    
    // Set initial loading state
    setIsProcessing(true);
    setSelectedAgent(null);
    
    // Initialize with a temporary state showing the URL is being processed
    setWorkflowState({
      taskId: `task-${Date.now()}`,
      videoDetails: {
        ...defaultVideoDetails,
        title: `Processing: ${youtubeUrl.substring(0, 30)}...`,
        url: youtubeUrl
      },
      processingStatus: {
        ...createInitialProcessingStatus(),
        status: 'processing',
        startTime: new Date().toISOString(),
      },
      agents: initialAgents,
      dataFlows: initialDataFlows,
      timeline: [{
        timestamp: new Date().toISOString(),
        event: 'process_started',
        message: `Starting processing for ${youtubeUrl}`
      }]
    });
    
    // Submit the URL to the API
    api.processYoutubeUrl(youtubeUrl)
      .then(response => {
        const { task_id } = response.data;
        console.log(`[WORKFLOW] Task created with ID: ${task_id}`);
        
        // Store the current task ID
        setCurrentTaskId(task_id);
        
        // Setup polling for status updates (both as fallback and to ensure we don't miss updates)
        const pollInterval = setInterval(() => {
          // Always poll to ensure we have the latest status
          console.log(`[WORKFLOW] Polling for status of task: ${task_id}`);
          api.getTaskStatus(task_id)
            .then(statusResponse => {
              console.log('[WORKFLOW] Polled task status:', {
                status: statusResponse.data.processing_status.status,
                audioUrl: statusResponse.data.audio_file_url,
                rawData: statusResponse.data
              });
              const pollState = mapApiResponseToWorkflowState(statusResponse.data);
              console.log('[WORKFLOW] Mapped poll state:', {
                outputUrl: pollState.outputUrl,
                status: pollState.processingStatus.status,
                taskId: pollState.taskId
              });
              setWorkflowState(pollState);
              
              // If task is complete, stop polling
              if (statusResponse.data.processing_status.status === 'completed' || 
                  statusResponse.data.processing_status.status === 'failed') {
                console.log('[WORKFLOW] Task completed, stopping poll');
                console.log('[WORKFLOW] Final audio URL:', statusResponse.data.audio_file_url);
                clearInterval(pollInterval);
                setIsProcessing(false);
              }
            })
            .catch(err => {
              console.error('[WORKFLOW] Error polling task status:', err);
            });
        }, 3000); // Poll every 3 seconds
        
        // Connect to WebSocket for real-time updates
        websocketManager.connect(task_id);
        
        // Subscribe to WebSocket updates
        const unsubscribe = websocketManager.subscribe(data => {
          console.log('[WORKFLOW] Received WebSocket update:', data);
          console.log('[WORKFLOW] Raw audio_file_url from API:', data.audio_file_url);
          
          try {
            // Map API response to our internal state format
            const newState = mapApiResponseToWorkflowState(data);
            console.log('[WORKFLOW] Mapped state:', {
              audioUrl: newState.outputUrl,
              rawApiAudioUrl: data.audio_file_url,
              status: newState.processingStatus.status,
              currentAgent: newState.processingStatus.currentAgentId,
              agents: newState.agents.map(a => `${a.id}: ${a.status}`),
              dataFlows: newState.dataFlows.map(f => `${f.fromAgentId}->${f.toAgentId}: ${f.status}`)
            });
            
            setWorkflowState(newState);
            
            // Check if processing has completed
            if (data.processing_status.status === 'completed' || 
                data.processing_status.status === 'failed') {
              console.log('[WORKFLOW] Processing completed with status:', data.processing_status.status);
              console.log('[WORKFLOW] Audio file URL from API:', data.audio_file_url);
              console.log('[WORKFLOW] Mapped audio URL in state:', newState.outputUrl);
              console.log('[WORKFLOW] All agents status:', newState.agents.map(a => `${a.id}: ${a.status}`));
              
              setIsProcessing(false);
              
              // Clean up interval when complete
              clearInterval(pollInterval);
              
              if (elapsedTimeIntervalRef.current) {
                clearInterval(elapsedTimeIntervalRef.current);
                elapsedTimeIntervalRef.current = null;
              }
            }
          } catch (error) {
            console.error('[WORKFLOW] Error processing WebSocket data:', error);
          }
        });
        
        // Fetch initial task status
        api.getTaskStatus(task_id)
          .then(statusResponse => {
            console.log('[WORKFLOW] Initial task status:', statusResponse.data);
            const initialState = mapApiResponseToWorkflowState(statusResponse.data);
            setWorkflowState(initialState);
          })
          .catch(error => {
            console.error('[WORKFLOW] Error fetching initial task status:', error);
            
            // Show error in the workflow state
            setWorkflowState(prevState => {
              if (!prevState) return null;
              
              return {
                ...prevState,
                processingStatus: {
                  ...prevState.processingStatus,
                  status: 'failed'
                },
                timeline: [
                  ...prevState.timeline,
                  {
                    timestamp: new Date().toISOString(),
                    event: 'process_failed',
                    message: `Error fetching task status: ${error.message || 'Unknown error'}`
                  }
                ]
              };
            });
            
            setIsProcessing(false);
            clearInterval(pollInterval);
          });
        
        // Return cleanup function
        return () => {
          unsubscribe();
          websocketManager.disconnect();
          clearInterval(pollInterval);
        };
      })
      .catch(error => {
        console.error('[WORKFLOW] Error starting processing:', error);
        
        // Update state with error
        setWorkflowState(prevState => {
          if (!prevState) return null;
          
          return {
            ...prevState,
            processingStatus: {
              ...prevState.processingStatus,
              status: 'failed'
            },
            timeline: [
              ...prevState.timeline,
              {
                timestamp: new Date().toISOString(),
                event: 'process_failed',
                message: `Error starting processing: ${error.message || 'Unknown error'}`
              }
            ]
          };
        });
        
        setIsProcessing(false);
      });
  }

  return (
    <WorkflowContext.Provider value={{ workflowState, isProcessing, startProcessing, selectedAgent, setSelectedAgent }}>
      {children}
    </WorkflowContext.Provider>
  );
};

export const useWorkflowContext = () => {
  const context = useContext(WorkflowContext);
  if (context === undefined) {
    throw new Error('useWorkflowContext must be used within a WorkflowProvider');
  }
  return context;
};