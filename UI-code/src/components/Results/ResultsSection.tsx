import React from 'react';
import { PodcastSummary } from '../../App';
import SummaryCard from './SummaryCard';
import ActionBar from './ActionBar';
import { useTheme } from '../../contexts/ThemeContext';

interface ResultsSectionProps {
  summary: PodcastSummary;
}

const ResultsSection: React.FC<ResultsSectionProps> = ({ summary }) => {
  const { theme } = useTheme();
  
  return (
    <section className="py-12 mb-8">
      <div className="container mx-auto px-4">
        <div className={`rounded-2xl overflow-hidden transition-colors duration-300 ${
          theme === 'dark' ? 'bg-gray-800/50' : 'bg-white shadow-xl'
        }`}>
          {/* Podcast info header */}
          <div className={`px-6 py-8 md:p-10 border-b ${
            theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
          }`}>
            <div className="flex flex-col md:flex-row gap-6 items-center md:items-start">
              <div className="w-32 h-32 flex-shrink-0 rounded-xl overflow-hidden shadow-lg">
                <img 
                  src={summary.coverImage} 
                  alt={summary.title} 
                  className="w-full h-full object-cover"
                />
              </div>
              
              <div className="flex-1 text-center md:text-left">
                <h2 className={`text-2xl md:text-3xl font-bold mb-2 ${
                  theme === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>
                  {summary.title}
                </h2>
                
                <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3 mb-4">
                  <p className={`text-sm ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    <span className="font-medium">Host:</span> {summary.host}
                  </p>
                  <span className="hidden md:inline text-gray-400">•</span>
                  <p className={`text-sm ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    <span className="font-medium">Duration:</span> {summary.duration}
                  </p>
                </div>
                
                <div className="mt-4">
                  <span className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${
                    theme === 'dark' 
                      ? 'bg-green-900/30 text-green-400' 
                      : 'bg-green-100 text-green-600'
                  }`}>
                    Summary Ready
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Action buttons */}
          <ActionBar />
          
          {/* Summary content */}
          <div className="p-6 md:p-10 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <SummaryCard 
              title="Main Points" 
              items={summary.mainPoints}
              icon="list"
            />
            
            <SummaryCard 
              title="Episode Highlights" 
              items={summary.highlights}
              icon="star"
            />
            
            <SummaryCard 
              title="Key Quotes" 
              items={summary.keyQuotes}
              icon="quote"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default ResultsSection;