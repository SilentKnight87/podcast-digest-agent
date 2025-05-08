import React from 'react';
import { Search } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import AnimatedWaveform from './AnimatedWaveform';

interface HeroProps {
  podcastUrl: string;
  setPodcastUrl: (url: string) => void;
  onGenerateSummary: () => void;
  isProcessing: boolean;
  error?: string | null;
}

const Hero: React.FC<HeroProps> = ({
  podcastUrl,
  setPodcastUrl,
  onGenerateSummary,
  isProcessing,
  error
}) => {
  const { theme } = useTheme();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerateSummary();
  };

  return (
    <section className="py-16 md:py-24 text-center relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className={`absolute -top-[40%] -left-[20%] w-[70%] h-[70%] rounded-full blur-3xl opacity-20 ${
          theme === 'dark' ? 'bg-purple-800' : 'bg-purple-500'
        }`}></div>
        <div className={`absolute -bottom-[40%] -right-[20%] w-[70%] h-[70%] rounded-full blur-3xl opacity-20 ${
          theme === 'dark' ? 'bg-cyan-800' : 'bg-cyan-500'
        }`}></div>
      </div>
      
      <div className="container mx-auto px-4 max-w-4xl relative z-0">
        <h1 className={`text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight ${
          theme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          Transform Any Podcast into
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-cyan-500">
            Digestible Insights
          </span>
        </h1>
        
        <p className={`text-lg md:text-xl max-w-2xl mx-auto mb-12 ${
          theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
        }`}>
          Save hours by getting AI-generated summaries of your favorite podcasts. 
          Key points, insights, and quotes - all in one place.
        </p>
        
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-center gap-4 max-w-3xl mx-auto mb-12">
          <div className={`flex-1 w-full relative ${
            isProcessing ? 'opacity-50 pointer-events-none' : ''
          }`}>
            <input
              type="text"
              placeholder="Paste podcast URL or RSS feed link here..."
              value={podcastUrl}
              onChange={(e) => setPodcastUrl(e.target.value)}
              disabled={isProcessing}
              className={`w-full py-4 px-5 pr-12 rounded-xl text-gray-900 placeholder-gray-500 border focus:ring focus:outline-none transition-shadow ${
                theme === 'dark' 
                ? 'bg-gray-800 border-gray-700 focus:ring-purple-600/50' 
                : 'bg-white border-gray-300 focus:ring-purple-600/30 shadow-md'
              }`}
            />
            <Search className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          </div>
          
          <button
            type="submit"
            disabled={isProcessing || !podcastUrl.trim()}
            className={`px-8 py-4 rounded-xl font-medium text-white transition-all ${
              isProcessing 
                ? 'bg-gray-500 cursor-not-allowed' 
                : podcastUrl.trim() 
                  ? 'bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 shadow-lg hover:shadow-purple-600/20' 
                  : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            {isProcessing ? 'Processing...' : 'Generate Summary'}
          </button>
        </form>
        
        {/* Error message display */}
        {error && (
          <div className="mt-4 text-red-500 bg-red-100 border border-red-200 rounded-lg p-3 max-w-3xl mx-auto">
            <p>{error}</p>
          </div>
        )}
        
        {/* Animated waveform visualization */}
        <div className="mt-16 max-w-md mx-auto">
          <AnimatedWaveform isProcessing={isProcessing} />
        </div>
      </div>
    </section>
  );
};

export default Hero;