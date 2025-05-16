'use client';

import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { AgentWorkflowState, AgentNode, DataFlow, ProcessingStatus } from '@/types/workflow';

// Define the shape of the context state
interface AgentWorkflowContextType {
  state: AgentWorkflowState;
  dispatch: React.Dispatch<AgentWorkflowAction>; // We'll define AgentWorkflowAction later
  // We can add more specific updater functions here later if needed, e.g.:
  // startProcessing: (initialState: Partial<AgentWorkflowState>) => void;
  // updateAgentStatus: (agentId: string, status: AgentNode['status'], progress?: number) => void;
}

// Initial state for the workflow
const initialWorkflowState: AgentWorkflowState = {
  taskId: 'unknown-task',
  processingStatus: {
    overallProgress: 0,
    status: 'idle',
    startTime: new Date().toISOString(),
    elapsedTime: '00:00:00',
  },
  agents: [],
  dataFlows: [],
  timeline: [],
};

// Create the context
const AgentWorkflowContext = createContext<AgentWorkflowContextType | undefined>(
  undefined
);

// Define actions for the reducer
// We'll expand this with more specific actions as we build out functionality
type AgentWorkflowAction = 
  | { type: 'INITIALIZE_WORKFLOW'; payload: Partial<AgentWorkflowState> }
  | { type: 'RESET_WORKFLOW' }
  | { type: 'SET_PROCESSING_STATUS'; payload: Partial<ProcessingStatus> }
  | { type: 'UPDATE_AGENT'; payload: Partial<AgentNode> & { id: string } }
  | { type: 'ADD_AGENT'; payload: AgentNode }
  | { type: 'UPDATE_DATA_FLOW'; payload: Partial<DataFlow> & { id: string } }
  | { type: 'ADD_DATA_FLOW'; payload: DataFlow }
  | { type: 'ADD_TIMELINE_EVENT'; payload: AgentWorkflowState['timeline'][0] };

// Reducer function to manage state updates
const agentWorkflowReducer = (state: AgentWorkflowState, action: AgentWorkflowAction): AgentWorkflowState => {
  switch (action.type) {
    case 'INITIALIZE_WORKFLOW':
      return {
        ...state,
        ...action.payload,
        processingStatus: {
          ...state.processingStatus,
          ...action.payload.processingStatus,
          status: action.payload.processingStatus?.status || 'processing',
          startTime: action.payload.processingStatus?.startTime || new Date().toISOString(),
        },
        agents: action.payload.agents || state.agents,
        dataFlows: action.payload.dataFlows || state.dataFlows,
        timeline: action.payload.timeline || state.timeline,
      };
    case 'RESET_WORKFLOW':
      return initialWorkflowState;
    case 'SET_PROCESSING_STATUS':
      return {
        ...state,
        processingStatus: { ...state.processingStatus, ...action.payload },
      };
    case 'UPDATE_AGENT':
      return {
        ...state,
        agents: state.agents.map(agent => 
          agent.id === action.payload.id ? { ...agent, ...action.payload } : agent
        ),
      };
    case 'ADD_AGENT':
      // Avoid adding duplicate agents
      if (state.agents.find(agent => agent.id === action.payload.id)) {
        return state;
      }
      return {
        ...state,
        agents: [...state.agents, action.payload],
      };
    case 'UPDATE_DATA_FLOW':
      return {
        ...state,
        dataFlows: state.dataFlows.map(flow => 
          flow.id === action.payload.id ? { ...flow, ...action.payload } : flow
        ),
      };
    case 'ADD_DATA_FLOW':
        // Avoid adding duplicate data flows
      if (state.dataFlows.find(df => df.id === action.payload.id)) {
        return state;
      }
      return {
        ...state,
        dataFlows: [...state.dataFlows, action.payload],
      };
    case 'ADD_TIMELINE_EVENT':
      return {
        ...state,
        timeline: [...state.timeline, action.payload].sort((a,b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
      };
    default:
      return state;
  }
};

// Context Provider component
export const AgentWorkflowProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(agentWorkflowReducer, initialWorkflowState);

  return (
    <AgentWorkflowContext.Provider value={{ state, dispatch }}>
      {children}
    </AgentWorkflowContext.Provider>
  );
};

// Custom hook to use the AgentWorkflow context
export const useAgentWorkflow = (): AgentWorkflowContextType => {
  const context = useContext(AgentWorkflowContext);
  if (context === undefined) {
    throw new Error('useAgentWorkflow must be used within an AgentWorkflowProvider');
  }
  return context;
}; 