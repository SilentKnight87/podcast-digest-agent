import React, { useEffect, useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';

interface AnimatedWaveformProps {
  isProcessing: boolean;
}

const AnimatedWaveform: React.FC<AnimatedWaveformProps> = ({ isProcessing }) => {
  const { theme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Number of bars in the waveform
  const barCount = 30;

  useEffect(() => {
    if (!containerRef.current) return;
    
    const bars = containerRef.current.children;
    
    if (isProcessing) {
      // Animate the bars when processing
      Array.from(bars).forEach((bar, index) => {
        const htmlBar = bar as HTMLElement;
        const delay = index * 50; // Stagger the animations
        
        htmlBar.style.animationDelay = `${delay}ms`;
        htmlBar.classList.add('animate-pulse-height');
      });
    } else {
      // Reset the animations when not processing
      Array.from(bars).forEach((bar) => {
        const htmlBar = bar as HTMLElement;
        htmlBar.classList.remove('animate-pulse-height');
        
        // Gentle idle animation for non-processing state
        htmlBar.style.animationDelay = `${Math.random() * 1000}ms`;
        htmlBar.classList.add('animate-gentle-pulse');
      });
    }
    
    return () => {
      Array.from(bars).forEach((bar) => {
        const htmlBar = bar as HTMLElement;
        htmlBar.classList.remove('animate-pulse-height', 'animate-gentle-pulse');
      });
    };
  }, [isProcessing]);

  return (
    <div 
      ref={containerRef}
      className="flex items-center justify-center h-20 gap-1"
    >
      {Array.from({ length: barCount }).map((_, i) => (
        <div
          key={i}
          className={`w-1.5 rounded-full transform transition-all duration-300 animate-gentle-pulse ${
            theme === 'dark' ? 'bg-purple-500' : 'bg-purple-600'
          }`}
          style={{
            height: `${Math.random() * 50 + 10}%`,
            opacity: 0.3 + Math.random() * 0.7,
            animationDuration: `${0.8 + Math.random() * 0.4}s`,
          }}
        />
      ))}
    </div>
  );
};

export default AnimatedWaveform;