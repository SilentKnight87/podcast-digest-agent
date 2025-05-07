import React from 'react';
import { Headphones } from 'lucide-react';
import ThemeToggle from '../UI/ThemeToggle';
import { useTheme } from '../../contexts/ThemeContext';

const Header: React.FC = () => {
  const { theme } = useTheme();
  
  return (
    <header className={`sticky top-0 z-10 transition-colors duration-300 ${
      theme === 'dark' ? 'bg-gray-900/90 backdrop-blur-md border-b border-gray-800' : 'bg-white/90 backdrop-blur-md shadow-sm'
    }`}>
      <div className="container mx-auto px-4 py-4 flex items-center justify-between max-w-7xl">
        <div className="flex items-center gap-2">
          <Headphones className="h-8 w-8 text-purple-600" />
          <h1 className="text-xl md:text-2xl font-bold">
            <span className="text-purple-600">Pod</span>
            <span>Digest</span>
          </h1>
        </div>
        
        <div className="flex items-center gap-4">
          <nav className="hidden md:flex space-x-6">
            <a href="#" className="font-medium hover:text-purple-600 transition-colors">Home</a>
            <a href="#" className="font-medium hover:text-purple-600 transition-colors">How It Works</a>
            <a href="#" className="font-medium hover:text-purple-600 transition-colors">Pricing</a>
            <a href="#" className="font-medium hover:text-purple-600 transition-colors">Blog</a>
          </nav>
          
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <button className={`hidden sm:block px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              theme === 'dark' 
                ? 'bg-purple-600 hover:bg-purple-700 text-white' 
                : 'bg-purple-600 hover:bg-purple-700 text-white'
            }`}>
              Sign In
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;