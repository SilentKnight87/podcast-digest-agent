import React from 'react';
import TimelineStage from './TimelineStage';
import ProcessingStage from './ProcessingStage';
import { Mic, Brain, FileText } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

interface ProcessDisplayProps {
  isProcessing: boolean;
  currentStage: number;
}

const ProcessDisplay: React.FC<ProcessDisplayProps> = ({ isProcessing, currentStage }) => {
  const { theme } = useTheme();
  
  // Define the processing stages
  const stages = [
    { 
      id: 1, 
      title: 'Transcription Bot', 
      description: 'Converting audio to text with advanced speech recognition',
      icon: Mic,
      estimatedTime: '~30 seconds' 
    },
    { 
      id: 2, 
      title: 'Summary Agent', 
      description: 'Analyzing content and identifying key insights',
      icon: Brain,
      estimatedTime: '~45 seconds' 
    },
    { 
      id: 3, 
      title: 'Digest Creator', 
      description: 'Organizing information into a structured format',
      icon: FileText,
      estimatedTime: '~15 seconds' 
    }
  ];

  return (
    <section className={`py-16 transition-colors duration-300 ${
      theme === 'dark' ? 'bg-gray-800/50' : 'bg-white'
    } rounded-xl my-8`}>
      <div className="container mx-auto px-4">
        <h2 className={`text-2xl md:text-3xl font-bold text-center mb-12 ${
          theme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          {isProcessing 
            ? 'Processing Your Podcast...' 
            : 'How PodDigest Works'}
        </h2>
        
        {isProcessing ? (
          <div className="max-w-4xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4">
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Stage {currentStage} of 3
              </p>
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Estimated time remaining: {
                  currentStage === 1 ? '~90 seconds' :
                  currentStage === 2 ? '~60 seconds' : '~15 seconds'
                }
              </p>
            </div>
            
            <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-8">
              <div 
                className="absolute h-full bg-gradient-to-r from-purple-600 to-cyan-500 transition-all duration-700 ease-out" 
                style={{ width: `${(currentStage / 3) * 100}%` }}
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {stages.map((stage) => (
                <ProcessingStage 
                  key={stage.id}
                  stage={stage}
                  isActive={currentStage === stage.id}
                  isCompleted={currentStage > stage.id}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="relative max-w-5xl mx-auto">
            {/* Connector line */}
            <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gray-200 dark:bg-gray-700 -translate-y-1/2 z-0 hidden md:block" />
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-10 z-10 relative">
              {stages.map((stage) => (
                <TimelineStage key={stage.id} stage={stage} />
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default ProcessDisplay;