import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { List, Star, Quote } from 'lucide-react';

interface SummaryCardProps {
  title: string;
  items: string[];
  icon: 'list' | 'star' | 'quote';
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, items, icon }) => {
  const { theme } = useTheme();
  
  const getIcon = () => {
    switch (icon) {
      case 'list':
        return <List size={18} />;
      case 'star':
        return <Star size={18} />;
      case 'quote':
        return <Quote size={18} />;
      default:
        return <List size={18} />;
    }
  };
  
  return (
    <div className={`rounded-xl p-6 transition-colors duration-300 ${
      theme === 'dark' ? 'bg-gray-700/50' : 'bg-gray-50'
    }`}>
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          theme === 'dark' ? 'bg-gray-600 text-purple-400' : 'bg-purple-100 text-purple-600'
        }`}>
          {getIcon()}
        </div>
        <h3 className={`text-lg font-bold ${
          theme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          {title}
        </h3>
      </div>
      
      <ul className="space-y-3">
        {items.map((item, index) => (
          <li key={index} className={`${
            icon === 'quote' 
              ? 'italic border-l-4 pl-3 py-1 border-purple-500/30' 
              : 'flex items-start gap-2'
          }`}>
            {icon !== 'quote' && (
              <span className={`mt-1.5 flex-shrink-0 w-1.5 h-1.5 rounded-full ${
                theme === 'dark' ? 'bg-purple-500' : 'bg-purple-600'
              }`} />
            )}
            <span className={`text-sm ${
              theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
            } leading-relaxed`}>
              {item}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SummaryCard;