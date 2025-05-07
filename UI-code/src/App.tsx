import React, { useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout/Layout';
import Hero from './components/Hero/Hero';
import ProcessDisplay from './components/Process/ProcessDisplay';
import ResultsSection from './components/Results/ResultsSection';

const App: React.FC = () => {
  const [podcastUrl, setPodcastUrl] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentStage, setCurrentStage] = useState<number>(0);
  const [summary, setSummary] = useState<PodcastSummary | null>(null);

  // Mock function to simulate the podcast processing
  const handleGenerateSummary = () => {
    if (!podcastUrl.trim()) return;
    
    setIsProcessing(true);
    setSummary(null);
    setCurrentStage(1);
    
    // Simulate transcription stage
    setTimeout(() => {
      setCurrentStage(2);
      
      // Simulate summary agent stage
      setTimeout(() => {
        setCurrentStage(3);
        
        // Simulate digest creation stage
        setTimeout(() => {
          setIsProcessing(false);
          setSummary(mockSummary);
        }, 3000);
      }, 3000);
    }, 3000);
  };

  return (
    <ThemeProvider>
      <Layout>
        <Hero 
          podcastUrl={podcastUrl} 
          setPodcastUrl={setPodcastUrl} 
          onGenerateSummary={handleGenerateSummary}
          isProcessing={isProcessing}
        />
        
        <ProcessDisplay 
          isProcessing={isProcessing} 
          currentStage={currentStage} 
        />
        
        {summary && (
          <ResultsSection summary={summary} />
        )}
      </Layout>
    </ThemeProvider>
  );
};

// Mock summary data (would come from the API in a real implementation)
const mockSummary: PodcastSummary = {
  title: "The Future of AI in Healthcare",
  host: "Dr. Sarah Johnson",
  duration: "45 minutes",
  coverImage: "https://images.pexels.com/photos/4226215/pexels-photo-4226215.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
  mainPoints: [
    "AI algorithms can now predict patient readmissions with 85% accuracy",
    "Remote monitoring tools have reduced hospital visits by 35%",
    "Privacy concerns remain the biggest hurdle for AI adoption",
    "Integration with existing healthcare systems requires significant investment"
  ],
  highlights: [
    "The Mayo Clinic's AI diagnostic tool has achieved 91% accuracy in early cancer detection",
    "Wearable tech combined with AI can now predict heart attacks up to 48 hours before they occur",
    "Virtual nursing assistants could save the healthcare industry $20 billion annually"
  ],
  keyQuotes: [
    "'The future of medicine isn't replacing doctors with AI, but augmenting human capabilities with machine intelligence.'",
    "'We're moving from reactive to predictive healthcare, and AI is the engine driving that transformation.'",
    "'The most successful healthcare institutions will be those that balance technological innovation with the human touch.'"
  ]
};

export type PodcastSummary = {
  title: string;
  host: string;
  duration: string;
  coverImage: string;
  mainPoints: string[];
  highlights: string[];
  keyQuotes: string[];
};

export default App;