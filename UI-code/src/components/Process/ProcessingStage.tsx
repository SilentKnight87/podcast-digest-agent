import React from 'react';
import { DivideIcon as LucideIcon, Check } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

interface StageType {
  id: number;
  title: string;
  description: string;
  icon: LucideIcon;
  estimatedTime: string;
}

interface ProcessingStageProps {
  stage: StageType;
  isActive: boolean;
  isCompleted: boolean;
}

const ProcessingStage: React.FC<ProcessingStageProps> = ({ stage, isActive, isCompleted }) => {
  const { theme } = useTheme();
  const { title, description, icon: Icon, estimatedTime } = stage;
  
  return (
    <div className={`rounded-xl p-6 transition-all duration-300 ${
      theme === 'dark' 
        ? isActive 
          ? 'bg-gray-700 border-2 border-purple-600 shadow-lg shadow-purple-600/10' 
          : isCompleted 
            ? 'bg-gray-700/50 border border-green-500/30' 
            : 'bg-gray-700/30 border border-gray-700'
        : isActive 
          ? 'bg-white border-2 border-purple-500 shadow-lg' 
          : isCompleted 
            ? 'bg-white/80 border border-green-500/30' 
            : 'bg-gray-100/50 border border-gray-200'
    }`}>
      <div className="flex items-start gap-4">
        <div className={`mt-1 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isCompleted
            ? theme === 'dark' ? 'bg-green-800 text-green-400' : 'bg-green-100 text-green-600'
            : isActive
              ? theme === 'dark' ? 'bg-purple-800 text-purple-400' : 'bg-purple-100 text-purple-600'
              : theme === 'dark' ? 'bg-gray-800 text-gray-500' : 'bg-gray-200 text-gray-500'
        } transition-all duration-300`}>
          {isCompleted ? <Check size={20} /> : <Icon size={20} />}
        </div>
        
        <div className="flex-1">
          <div className="flex justify-between items-start mb-2">
            <h3 className={`font-bold ${
              isActive
                ? theme === 'dark' ? 'text-white' : 'text-gray-900'
                : isCompleted
                  ? theme === 'dark' ? 'text-green-400' : 'text-green-600'
                  : theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              {title}
            </h3>
            
            <span className={`text-xs px-2 py-1 rounded-full ${
              isActive
                ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400 animate-pulse'
                : isCompleted
                  ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
            }`}>
              {isCompleted ? 'Completed' : isActive ? 'In progress' : estimatedTime}
            </span>
          </div>
          
          <p className={`text-sm ${
            isActive
              ? theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              : theme === 'dark' ? 'text-gray-500' : 'text-gray-600'
          }`}>
            {description}
          </p>
          
          {/* Active stage has progress indicator */}
          {isActive && (
            <div className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full mt-4 overflow-hidden">
              <div className="h-full bg-purple-600 dark:bg-purple-500 transition-all duration-300 animate-loading-progress" style={{ width: '60%' }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProcessingStage;