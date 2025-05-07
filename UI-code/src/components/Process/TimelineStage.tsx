import React from 'react';
import { DivideIcon as LucideIcon } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

interface StageType {
  id: number;
  title: string;
  description: string;
  icon: LucideIcon;
  estimatedTime: string;
}

interface TimelineStageProps {
  stage: StageType;
}

const TimelineStage: React.FC<TimelineStageProps> = ({ stage }) => {
  const { theme } = useTheme();
  const { title, description, icon: Icon } = stage;
  
  return (
    <div className="relative flex flex-col items-center text-center transition-all duration-300">
      {/* Stage icon */}
      <div className={`relative mb-6 z-10 ${
        theme === 'dark' 
          ? 'bg-gray-800 text-purple-500' 
          : 'bg-white text-purple-600'
      }`}>
        <div className={`w-16 h-16 rounded-full flex items-center justify-center 
          ${theme === 'dark' 
            ? 'bg-gray-800 border-2 border-purple-500' 
            : 'bg-purple-100 border-2 border-purple-200'
          } transition-all duration-300`}>
          <Icon size={28} />
        </div>
        
        {/* Stage number */}
        <div className={`absolute -bottom-2 -right-2 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
          theme === 'dark' 
            ? 'bg-purple-600 text-white' 
            : 'bg-purple-600 text-white'
        }`}>
          {stage.id}
        </div>
      </div>
      
      {/* Stage title */}
      <h3 className={`text-lg font-bold mb-2 ${
        theme === 'dark' ? 'text-white' : 'text-gray-900'
      }`}>
        {title}
      </h3>
      
      {/* Stage description */}
      <p className={`text-sm ${
        theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
      }`}>
        {description}
      </p>
    </div>
  );
};

export default TimelineStage;