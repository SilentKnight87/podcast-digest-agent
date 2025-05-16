"use client"; // Add this directive at the top

import { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from 'react';
import type { ReactNode, FC } from 'react'; // Import ReactNode and FC as types
import type {
  ActiveTask,
  AgentNode,
  DataFlow,
  ProcessingStatus,
  WorkflowContextType,
  VideoDetails,
  MockData // Import MockData for initial data typing
} from '../types';
import initialMockDataJson from '../../mock_data.json';
import React from 'react';

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

export const WorkflowProvider: FC<WorkflowProviderProps> = ({ children }) => {
  const [workflowState, setWorkflowState] = useState<ActiveTask | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentNode | null>(null);
  const [simulationTimeoutId, setSimulationTimeoutId] = useState<NodeJS.Timeout | null>(null);
  const isInitializedRef = useRef(false); // Added for controlling initialization

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
    setSimulationTimeoutId(currentId => {
        if (currentId) {
            console.log("[WORKFLOW_CONTEXT] Clearing simulationTimeoutId in resetToInitialState", currentId);
            clearTimeout(currentId);
        }
        return null;
    });
    setWorkflowState(() => {
        console.log("[WORKFLOW_CONTEXT] Setting new initial workflow state");
        return {
            taskId: initialMockData.activeTask?.taskId || `task-${Date.now()}`,
            videoDetails: initialVideoDetails,
            processingStatus: createInitialProcessingStatus(),
            agents: initialAgents,
            dataFlows: initialDataFlows,
            timeline: [],
            outputUrl: undefined, // Explicitly reset outputUrl
        };
    });
    setIsProcessing(false);
    setSelectedAgent(null);
    console.log("[WORKFLOW_CONTEXT] resetToInitialState finished");
  }, [initialAgents, initialDataFlows, initialVideoDetails]);

  useEffect(() => {
    console.log("[WORKFLOW_CONTEXT] Mount/update useEffect runs", { 
        isInitialized: isInitializedRef.current, 
        workflowStatus: workflowState?.processingStatus?.status 
    });

    if (!isInitializedRef.current) {
        // This condition ensures resetToInitialState is called only once initially.
        // The original condition for resetting was:
        // if (!workflowState || (workflowState.processingStatus.status !== 'completed' && !workflowState.outputUrl))
        // We only apply this logic if not yet initialized.
        if (!workflowState || (workflowState.processingStatus.status !== 'completed' && !workflowState.outputUrl)) {
            console.log("[WORKFLOW_CONTEXT] Not initialized and condition met, calling resetToInitialState");
            resetToInitialState();
        }
        isInitializedRef.current = true;
    }
    
    // This cleanup handles the case where the WorkflowProvider might unmount while a timeout is active.
    // The active management of simulationTimeoutId (clearing and setting) is done within 
    // startProcessing and simulateWorkflowStep.
    return () => {
      if (simulationTimeoutId) {
        console.log("[WORKFLOW_CONTEXT] useEffect cleanup (unmount/deps change): Clearing simulationTimeoutId", simulationTimeoutId);
        clearTimeout(simulationTimeoutId);
        // Do not call setSimulationTimeoutId(null) here, as this effect's role is cleanup, not state management
        // of the ID itself, which is handled by other functions.
      }
    };
  }, [resetToInitialState, simulationTimeoutId, workflowState]); // Dependencies for re-running effect and cleanup

  function simulateWorkflowStep() {
    console.log("[WORKFLOW] simulateWorkflowStep called");
    setWorkflowState(prevState => {
      if (!prevState || prevState.processingStatus.status !== 'processing' || !prevState.agents.length) {
        console.log("[WORKFLOW] Cannot simulate step: invalid state", { 
          hasState: !!prevState, 
          status: prevState?.processingStatus?.status,
          agentsCount: prevState?.agents?.length 
        });
        return prevState;
      }

      console.log("[WORKFLOW] Simulating next workflow step");
      const updatedState = JSON.parse(JSON.stringify(prevState)) as ActiveTask; // Deep copy
      const now = new Date().toISOString();

      let currentAgentInLoop: AgentNode | undefined = updatedState.agents.find(agent => agent.id === updatedState.processingStatus.currentAgentId);

      if (currentAgentInLoop && currentAgentInLoop.status === 'running') {
        if (currentAgentInLoop.progress < 100) {
          currentAgentInLoop.progress = Math.min(currentAgentInLoop.progress + 20, 100);
          updatedState.timeline.push({
            timestamp: now, event: 'progress_update', agentId: currentAgentInLoop.id,
            message: `${currentAgentInLoop.name} progress: ${currentAgentInLoop.progress}%`
          });
          
          const agentId = currentAgentInLoop.id;
          const activeFlow = updatedState.dataFlows.find(df => df.fromAgentId === agentId && df.status === 'transferring');
          if (activeFlow) {
            activeFlow.metadata = { ...(activeFlow.metadata || {}), percentComplete: currentAgentInLoop.progress };
          }

        } else {
          currentAgentInLoop.status = 'completed';
          currentAgentInLoop.endTime = now;
          updatedState.timeline.push({
            timestamp: now, event: 'agent_completed', agentId: currentAgentInLoop.id,
            message: `${currentAgentInLoop.name} completed.`
          });
          const agentId = currentAgentInLoop.id;
          const outgoingFlow = updatedState.dataFlows.find(df => df.fromAgentId === agentId);
          if (outgoingFlow) outgoingFlow.status = 'completed';
          
          updatedState.processingStatus.currentAgentId = null;
          currentAgentInLoop = undefined;
        }
      } else {
        const nextAgentToProcess = updatedState.agents.find(agent => agent.status === 'pending');
        if (nextAgentToProcess) {
          nextAgentToProcess.status = 'running';
          nextAgentToProcess.startTime = now;
          nextAgentToProcess.progress = 0;
          updatedState.processingStatus.currentAgentId = nextAgentToProcess.id;
          updatedState.timeline.push({
            timestamp: now, event: 'agent_started', agentId: nextAgentToProcess.id,
            message: `${nextAgentToProcess.name} started.`
          });
          const agentId = nextAgentToProcess.id;
          const incomingFlow = updatedState.dataFlows.find(df => df.toAgentId === agentId);
          if (incomingFlow) incomingFlow.status = 'transferring';
          currentAgentInLoop = nextAgentToProcess;
        } else {
          const allDone = updatedState.agents.every(a => a.status === 'completed' || a.status === 'error');
          if (allDone) {
            const allCompletedSuccessfully = updatedState.agents.every(a => a.status === 'completed');
            updatedState.processingStatus.status = allCompletedSuccessfully ? 'completed' : 'failed';
            updatedState.processingStatus.overallProgress = 100;
            (updatedState.processingStatus as ProcessingStatus).endTime = now; 
            updatedState.processingStatus.currentAgentId = null;
            
            if (allCompletedSuccessfully) {
              updatedState.outputUrl = "/audio/mock-digest-audio.mp3"; // Populate mock audio URL
              console.log("[WORKFLOW] Process completed successfully. Setting status to completed, isProcessing to false, and outputUrl to:", updatedState.outputUrl);
            } else {
              console.log("[WORKFLOW] Process completed with errors. Setting status to failed and isProcessing to false");
            }

            setIsProcessing(false);
            updatedState.timeline.push({
              timestamp: now, event: allCompletedSuccessfully ? 'process_completed' : 'process_failed',
              message: allCompletedSuccessfully ? 'Workflow completed successfully.' : 'Workflow failed.'
            });
            if (simulationTimeoutId) clearTimeout(simulationTimeoutId);
            setSimulationTimeoutId(null);
            return updatedState;
          }
        }
      }
      
      const totalProgress = updatedState.agents.reduce((sum, agent) => sum + agent.progress, 0);
      updatedState.processingStatus.overallProgress = updatedState.agents.length > 0 ? 
        Math.round(totalProgress / updatedState.agents.length) : 0;

      if (updatedState.processingStatus.startTime) {
        const elapsedMs = new Date().getTime() - new Date(updatedState.processingStatus.startTime).getTime();
        updatedState.processingStatus.elapsedTime = new Date(elapsedMs).toISOString().substr(11, 8);
      }

      if (updatedState.processingStatus.status === 'processing') {
        console.log("[WORKFLOW] Setting timeout for next workflow step");
        const nextTimeoutId = setTimeout(simulateWorkflowStep, 1000);
        setSimulationTimeoutId(nextTimeoutId);
      }
      return updatedState;
    });
  }

  function startProcessing(youtubeUrl: string) {
    console.log('[WORKFLOW] Starting mock processing for URL:', youtubeUrl);
    if (simulationTimeoutId) {
      console.log('[WORKFLOW] Clearing existing timeout');
      clearTimeout(simulationTimeoutId);
      setSimulationTimeoutId(null); // Clear the old timeout ID state
    }
    
    console.log('[WORKFLOW] Setting initial workflow state');
    // No prevState needed here as we are setting a fresh state
    setWorkflowState(() => {
        console.log('[WORKFLOW] Preparing initial agents', {
          hasAgents: !!initialMockData.activeTask?.agents,
          agentCount: initialMockData.activeTask?.agents?.length || 0
        });
        const currentAgents = initialMockData.activeTask?.agents.map(getInitialAgentState) || [];
        const currentDataFlows = initialMockData.activeTask?.dataFlows.map(getInitialDataFlowState) || [];
        const currentVideoDetails = initialMockData.activeTask?.videoDetails ? 
            { ...initialMockData.activeTask.videoDetails, title: `Processing: ${youtubeUrl.substring(0,30)}...` } 
            : { ...defaultVideoDetails, title: `Processing: ${youtubeUrl.substring(0,30)}...` };

        const newState: ActiveTask = {
            taskId: initialMockData.activeTask?.taskId || `task-${Date.now()}`,
            videoDetails: currentVideoDetails,
            processingStatus: {
                ...createInitialProcessingStatus(),
                status: 'processing', // This is a valid status from the enum
                startTime: new Date().toISOString(),
            },
            agents: currentAgents,
            dataFlows: currentDataFlows,
            timeline: [{
                timestamp: new Date().toISOString(),
                event: 'process_started',
                message: `Workflow started for ${youtubeUrl}`
            }]
        };
        
        console.log('[WORKFLOW] Created new workflow state:', {
          hasAgents: newState.agents.length > 0,
          agentCount: newState.agents.length,
          status: newState.processingStatus.status
        });
        
        return newState;
    });

    console.log('[WORKFLOW] Setting isProcessing to true');
    setIsProcessing(true);
    setSelectedAgent(null);
    
    console.log('[WORKFLOW] Scheduling first workflow step');
    const nextTimeoutId = setTimeout(() => {
        console.log('[WORKFLOW] Initial timeout fired, triggering first workflow step');
        simulateWorkflowStep();
    }, 100);
    setSimulationTimeoutId(nextTimeoutId);
    console.log('[WORKFLOW] Timeout set with ID:', nextTimeoutId);
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