'use client';

import React from 'react';
import { motion, AnimatePresence } from "motion/react"
import { FileText, Brain, MessageSquare, Mic, PlayCircle, XIcon } from 'lucide-react';
import { FaYoutube } from 'react-icons/fa';

// Define specific types for agents and data flows
interface AgentNode {
  id: string;
  name: string;
  icon: React.ElementType; // General type for icon components
  type: 'input' | 'processing' | 'output';
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  description: string;
  startTime?: string;
  endTime?: string;
  logs?: Array<{timestamp: string, level: 'info' | 'warn' | 'error', message: string}>;
  metrics?: Record<string, string | number>;
}

interface DataFlow {
  id: string;
  fromAgentId: string;
  toAgentId: string;
  dataType: 'video_url' | 'transcript' | 'summary' | 'dialogue' | 'audio_file';
  status: 'pending' | 'transferring' | 'completed' | 'error';
}

// Mock data with defined types
const mockAgents: AgentNode[] = [
  {
    id: 'youtube-node',
    name: 'YouTube Video',
    icon: FaYoutube,
    type: 'input',
    status: 'completed',
    progress: 100,
    description: 'Accepts the initial YouTube video URL provided by the user.',
    startTime: '2023-07-01T15:30:00Z',
    endTime: '2023-07-01T15:30:05Z',
    logs: [{ timestamp: '2023-07-01T15:30:02Z', level: 'info', message: 'YouTube URL received.'}],
    metrics: { 'URL Length': 54 }
  },
  {
    id: 'transcript-fetcher',
    name: 'Transcript Fetcher',
    icon: FileText,
    type: 'processing',
    status: 'completed',
    progress: 100,
    description: 'Fetches the transcript for the provided YouTube video.',
    startTime: '2023-07-01T15:30:05Z',
    endTime: '2023-07-01T15:31:00Z',
    logs: [
      { timestamp: '2023-07-01T15:30:10Z', level: 'info', message: 'Starting transcript download.'},
      { timestamp: '2023-07-01T15:30:55Z', level: 'info', message: 'Transcript processed successfully.'}
    ],
    metrics: { 'Transcript Length (chars)': 15230, 'Segments': 250 }
  },
  {
    id: 'summarizer-agent',
    name: 'Summarizer',
    icon: Brain,
    type: 'processing',
    status: 'running',
    progress: 50,
    description: 'Processes the transcript to generate a concise summary.',
    startTime: '2023-07-01T15:31:00Z',
    logs: [
      { timestamp: '2023-07-01T15:31:05Z', level: 'info', message: 'Summarization started.'},
      { timestamp: '2023-07-01T15:32:00Z', level: 'info', message: 'Analyzing text segments...'}
    ],
    metrics: { 'Input Word Count': 2800 }
  },
  {
    id: 'synthesizer-agent',
    name: 'Synthesizer',
    icon: MessageSquare,
    type: 'processing',
    status: 'pending',
    progress: 0,
    description: 'Converts the summary into a natural-sounding dialogue script.'
  },
  {
    id: 'audio-generator',
    name: 'Audio Generator',
    icon: Mic,
    type: 'processing',
    status: 'pending',
    progress: 0,
    description: 'Generates the final audio output from the dialogue script using Text-to-Speech.'
  },
  {
    id: 'ui-player',
    name: 'UI/Player',
    icon: PlayCircle,
    type: 'output',
    status: 'pending',
    progress: 0,
    description: 'Delivers the generated audio digest to the user interface for playback.'
  },
];

const mockDataFlows: DataFlow[] = [
  { id: 'flow1', fromAgentId: 'youtube-node', toAgentId: 'transcript-fetcher', dataType: 'video_url', status: 'completed' },
  { id: 'flow2', fromAgentId: 'transcript-fetcher', toAgentId: 'summarizer-agent', dataType: 'transcript', status: 'transferring' },
  { id: 'flow3', fromAgentId: 'summarizer-agent', toAgentId: 'synthesizer-agent', dataType: 'summary', status: 'pending' },
  { id: 'flow4', fromAgentId: 'synthesizer-agent', toAgentId: 'audio-generator', dataType: 'dialogue', status: 'pending' },
  { id: 'flow5', fromAgentId: 'audio-generator', toAgentId: 'ui-player', dataType: 'audio_file', status: 'pending' },
];

interface ProcessingVisualizerProps {
  agents?: AgentNode[];
  dataFlows?: DataFlow[];
}

const ProcessingVisualizer: React.FC<ProcessingVisualizerProps> = ({ 
  agents = mockAgents, 
  dataFlows = mockDataFlows 
}) => {
  const [selectedAgent, setSelectedAgent] = React.useState<AgentNode | null>(null);

  const nodePositions = agents.reduce((acc, agent, index) => {
    acc[agent.id] = { x: index * 180 + 100, y: 150 };
    return acc;
  }, {} as Record<string, { x: number; y: number }>);

  const getStatusColor = (status: AgentNode['status']) => {
    switch (status) {
      case 'pending': return 'border-gray-500 text-gray-500';
      case 'running': return 'border-blue-500 text-blue-500 animate-pulse';
      case 'completed': return 'border-green-500 text-green-500';
      case 'error': return 'border-red-500 text-red-500';
      default: return 'border-gray-400 text-gray-400';
    }
  };
  
  const getFlowColor = (dataType: DataFlow['dataType']) => {
    switch (dataType) {
      case 'transcript': return 'stroke-primary fill-primary shadow-primary';
      case 'summary': return 'stroke-secondary fill-secondary shadow-secondary';
      case 'audio_file': return 'stroke-accent fill-accent shadow-accent';
      default: return 'stroke-muted-foreground fill-muted-foreground';
    }
  };

  const handleNodeClick = (agent: AgentNode) => {
    setSelectedAgent(agent);
  };

  const closePanel = () => {
    setSelectedAgent(null);
  };
  
  // Calculate dynamic width for SVG to ensure all nodes are visible
  const svgWidth = agents.length > 0 ? agents.length * 180 + 20 : '100%';

  return (
    <div className="w-full h-[450px] bg-card/70 backdrop-blur-md p-4 rounded-lg shadow-lg relative overflow-x-auto overflow-y-hidden flex flex-col border border-border/40">
      <div className="flex-grow relative">
        <svg width={svgWidth} height="100%" aria-labelledby="processing-visualizer-title">
          <title id="processing-visualizer-title">Processing Workflow Visualization</title>
          
          {/* Background glow effects for active nodes */}
          {agents.filter(a => a.status === 'running' || a.status === 'completed').map((agent) => {
            const position = nodePositions[agent.id];
            if (!position) return null;
            const glowColor = agent.status === 'running' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.15)';
            
            return (
              <motion.circle
                key={`glow-${agent.id}`}
                cx={position.x}
                cy={position.y}
                r={40}
                fill={glowColor}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ 
                  opacity: [0.4, 0.6, 0.4], 
                  scale: [0.9, 1.1, 0.9],
                  transition: { 
                    repeat: Number.POSITIVE_INFINITY,
                    duration: agent.status === 'running' ? 3 : 0,
                    ease: "easeInOut"
                  }
                }}
              />
            );
          })}

          {/* Data flows with enhanced styling */}
          {dataFlows.map((flow) => {
            const fromNode = nodePositions[flow.fromAgentId];
            const toNode = nodePositions[flow.toAgentId];
            if (!fromNode || !toNode) return null;

            const flowColorClasses = getFlowColor(flow.dataType);
            const strokeClass = flowColorClasses.split(' ')[0];
            const fillClass = flowColorClasses.split(' ')[1];
            
            // Calculate midpoint for adding a subtle glow effect
            const midX = (fromNode.x + toNode.x) / 2;
            const midY = (fromNode.y + toNode.y) / 2;

            return (
              <React.Fragment key={`flow-group-${flow.id}`}>
                {/* Optional subtle glow under active connections */}
                {(flow.status === 'transferring' || flow.status === 'completed') && (
                  <motion.circle
                    cx={midX}
                    cy={midY}
                    r={8}
                    className={`${flowColorClasses.split(' ')[1]}/20`}
                    filter="blur(8px)"
                    initial={{ opacity: 0 }}
                    animate={{ 
                      opacity: flow.status === 'transferring' ? [0.4, 0.8, 0.4] : 0.2,
                      scale: flow.status === 'transferring' ? [0.8, 1.2, 0.8] : 1,
                    }}
                    transition={{ 
                      duration: 2,
                      repeat: Number.POSITIVE_INFINITY,
                      repeatType: "loop"
                    }}
                  />
                )}
                
                {/* Flowing lines with enhanced styling */}
                <motion.line
                  key={flow.id}
                  x1={fromNode.x}
                  y1={fromNode.y}
                  x2={toNode.x}
                  y2={toNode.y}
                  className={`stroke-2 ${strokeClass}`}
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: (flow.status === 'completed' || flow.status === 'transferring') ? 1 : 0 }}
                  transition={{ duration: 1, ease: "easeInOut" }}
                />
                
                {/* Particle Animation with enhanced styling */}
                {(flow.status === 'transferring' || flow.status === 'completed') && 
                  Array.from({ length: 5 }).map((_, index) => (
                    <motion.circle
                      key={`${flow.id}-particle-${index}`}
                      cx={fromNode.x}
                      cy={fromNode.y}
                      r={flow.status === 'transferring' ? 3.5 : 2.5} // Slightly larger particles for active flows
                      className={`${fillClass} shadow-sm`}
                      filter={flow.status === 'transferring' ? "drop-shadow(0 0 2px currentColor)" : ""}
                      initial={{ opacity: 0 }}
                      animate={{
                        opacity: [0, 0.8, 0.8, 0],
                        scale: flow.status === 'transferring' ? [0.8, 1.2, 0.8] : [1, 1, 1],
                        transition: {
                          duration: flow.status === 'transferring' ? 2 : 3,
                          ease: "linear",
                          repeat: Number.POSITIVE_INFINITY,
                          delay: index * (flow.status === 'transferring' ? 0.3 : 0.5),
                          repeatType: "loop"
                        }
                      }}
                      style={{ 
                        offsetPath: `path('M${fromNode.x},${fromNode.y} L${toNode.x},${toNode.y}')`,
                      }}
                    >
                      <animate
                        attributeName="offsetDistance"
                        from="0%"
                        to="100%"
                        dur={flow.status === 'transferring' ? '2s' : '3s'}
                        repeatCount="indefinite"
                        begin={`${index * (flow.status === 'transferring' ? 0.3 : 0.5)}s`}
                      />
                    </motion.circle>
                  ))
                }
              </React.Fragment>
            );
          })}

          {/* Agent nodes with transparent backgrounds and borders */}
          {agents.map((agent) => {
            const position = nodePositions[agent.id];
            if (!position) return null;
            const IconComponent = agent.icon;
            const statusColorClasses = getStatusColor(agent.status);

            return (
              <motion.g
                key={agent.id}
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="cursor-pointer group"
                onClick={() => handleNodeClick(agent)} 
                tabIndex={0} 
                onKeyPress={(e) => e.key === 'Enter' && handleNodeClick(agent)} 
              >
                <title>{agent.description}</title> 
                <foreignObject x={position.x - 40} y={position.y - 40} width="80" height="110">
                  <div className="flex flex-col items-center justify-center w-full h-full p-1">
                    <div
                      className={`w-16 h-16 rounded-full flex items-center justify-center 
                        bg-background/30 backdrop-blur-sm border-2 
                        ${statusColorClasses} 
                        transition-all duration-300 
                        group-hover:shadow-lg group-hover:ring-2 group-hover:ring-primary/40 
                        shrink-0`}
                    >
                      <IconComponent className={`w-8 h-8 transition-all ${statusColorClasses.split(' ')[1]}`} /> 
                    </div>
                    <div className="mt-1 text-xs text-center text-foreground w-full break-words">
                      {agent.name}
                    </div>
                    {(agent.status === 'running' || agent.status === 'completed') && agent.progress > 0 && (
                      <div className="w-16 h-1.5 mt-1 bg-gray-300/30 backdrop-blur-sm dark:bg-gray-700/30 rounded-full overflow-hidden shrink-0">
                        <motion.div
                          className={`h-full ${agent.status === 'completed' ? 'bg-green-500/80' : 'bg-blue-500/80'}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${agent.progress}%`}}
                          transition={{ duration: 0.5, ease: "linear" }}
                        />
                      </div>
                    )}
                  </div>
                </foreignObject>
              </motion.g>
            );
          })}
        </svg>
      </div>

      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            key="details-panel"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="absolute bottom-0 left-0 right-0 bg-card/95 backdrop-blur-sm border-t border-border/40 p-4 shadow-lg max-h-[45%] overflow-y-auto rounded-b-lg z-10"
          >
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold text-foreground">{selectedAgent.name}</h3>
              <button 
                  type="button" 
                  onClick={closePanel} 
                  className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-full hover:bg-muted"
                  aria-label="Close details panel"
              >
                <XIcon size={20} />
              </button>
            </div>
            <p className="text-sm text-muted-foreground mb-2">{selectedAgent.description}</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-sm mb-3">
              <p><strong className="text-foreground">Status:</strong> <span className={`capitalize font-medium ${selectedAgent.status === 'running' ? 'text-blue-500' : selectedAgent.status === 'completed' ? 'text-green-500' : selectedAgent.status === 'error' ? 'text-red-500' : 'text-gray-500'}`}>{selectedAgent.status}</span></p>
              <p><strong className="text-foreground">Progress:</strong> {selectedAgent.progress}%</p>
              {selectedAgent.startTime && <p><strong className="text-foreground">Start:</strong> {new Date(selectedAgent.startTime).toLocaleTimeString()}</p>}
              {selectedAgent.endTime && <p><strong className="text-foreground">End:</strong> {new Date(selectedAgent.endTime).toLocaleTimeString()}</p>}
            </div>
            
            {selectedAgent.metrics && Object.keys(selectedAgent.metrics).length > 0 && (
              <div className="mb-3">
                <h4 className="text-sm font-semibold text-foreground mb-1">Metrics:</h4>
                <ul className="list-disc list-inside pl-1 text-xs text-muted-foreground space-y-0.5">
                  {Object.entries(selectedAgent.metrics).map(([key, value]) => (
                    <li key={key}><strong className="text-foreground/80">{key}:</strong> {value}</li>
                  ))}
                </ul>
              </div>
            )}

            {selectedAgent.logs && selectedAgent.logs.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-foreground mb-1">Recent Logs:</h4>
                <div className="max-h-28 overflow-y-auto bg-muted/50 p-2 rounded text-xs space-y-1 font-mono scrollbar-thin scrollbar-thumb-muted-foreground/50 scrollbar-track-transparent">
                  {selectedAgent.logs.slice(-10).map((log, index) => (
                    <p key={`${log.timestamp}-${index}-${log.message.slice(0,10)}`} className={`${log.level === 'error' ? 'text-red-400' : log.level === 'warn' ? 'text-yellow-400' : 'text-muted-foreground/90'}`}>
                      <span className="text-foreground/60">[{new Date(log.timestamp).toLocaleTimeString()}]</span> <span className={`font-semibold ${log.level === 'error' ? 'text-red-500' : log.level === 'warn' ? 'text-yellow-500' : 'text-sky-500'}`}>[{log.level.toUpperCase()}]</span>: {log.message}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProcessingVisualizer; 