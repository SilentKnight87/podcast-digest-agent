import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { 
  Download, 
  Share2, 
  Copy, 
  Bookmark, 
  FileText, 
  Mail, 
  Twitter, 
  Facebook 
} from 'lucide-react';

const ActionBar: React.FC = () => {
  const { theme } = useTheme();
  
  return (
    <div className={`flex flex-wrap gap-2 p-6 border-b ${
      theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'
    }`}>
      <button className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        theme === 'dark' 
          ? 'bg-gray-700 hover:bg-gray-600 text-white' 
          : 'bg-white hover:bg-gray-100 text-gray-800 border border-gray-200'
      }`}>
        <Copy size={16} />
        <span>Copy</span>
      </button>
      
      <button className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        theme === 'dark' 
          ? 'bg-gray-700 hover:bg-gray-600 text-white' 
          : 'bg-white hover:bg-gray-100 text-gray-800 border border-gray-200'
      }`}>
        <Bookmark size={16} />
        <span>Save</span>
      </button>
      
      <div className="relative group">
        <button className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          theme === 'dark' 
            ? 'bg-gray-700 hover:bg-gray-600 text-white' 
            : 'bg-white hover:bg-gray-100 text-gray-800 border border-gray-200'
        }`}>
          <Share2 size={16} />
          <span>Share</span>
        </button>
        
        {/* Share dropdown menu */}
        <div className={`absolute left-0 mt-2 w-48 rounded-md shadow-lg z-10 transition-opacity duration-150 opacity-0 invisible group-hover:opacity-100 group-hover:visible ${
          theme === 'dark' ? 'bg-gray-800' : 'bg-white border border-gray-200'
        }`}>
          <div className="py-1">
            <a href="#" className={`flex items-center gap-2 px-4 py-2 text-sm ${
              theme === 'dark' ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
            }`}>
              <Twitter size={16} className="text-blue-400" />
              <span>Twitter</span>
            </a>
            <a href="#" className={`flex items-center gap-2 px-4 py-2 text-sm ${
              theme === 'dark' ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
            }`}>
              <Facebook size={16} className="text-blue-600" />
              <span>Facebook</span>
            </a>
            <a href="#" className={`flex items-center gap-2 px-4 py-2 text-sm ${
              theme === 'dark' ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
            }`}>
              <Mail size={16} className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} />
              <span>Email</span>
            </a>
          </div>
        </div>
      </div>
      
      <div className="relative group">
        <button className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          theme === 'dark' 
            ? 'bg-gray-700 hover:bg-gray-600 text-white' 
            : 'bg-white hover:bg-gray-100 text-gray-800 border border-gray-200'
        }`}>
          <Download size={16} />
          <span>Export</span>
        </button>
        
        {/* Export dropdown menu */}
        <div className={`absolute left-0 mt-2 w-48 rounded-md shadow-lg z-10 transition-opacity duration-150 opacity-0 invisible group-hover:opacity-100 group-hover:visible ${
          theme === 'dark' ? 'bg-gray-800' : 'bg-white border border-gray-200'
        }`}>
          <div className="py-1">
            <a href="#" className={`flex items-center gap-2 px-4 py-2 text-sm ${
              theme === 'dark' ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
            }`}>
              <FileText size={16} />
              <span>PDF</span>
            </a>
            <a href="#" className={`flex items-center gap-2 px-4 py-2 text-sm ${
              theme === 'dark' ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
            }`}>
              <FileText size={16} />
              <span>Text</span>
            </a>
            <a href="#" className={`flex items-center gap-2 px-4 py-2 text-sm ${
              theme === 'dark' ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-700'
            }`}>
              <Mail size={16} />
              <span>Email</span>
            </a>
          </div>
        </div>
      </div>
      
      <div className="flex-1"></div>
      
      <div className={`px-3 py-2 rounded-lg text-xs ${
        theme === 'dark' ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-600'
      }`}>
        Generated on {new Date().toLocaleDateString()}
      </div>
    </div>
  );
};

export default ActionBar;