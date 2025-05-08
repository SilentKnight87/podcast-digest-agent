import * as React from 'react';
import { useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout/Layout';
import Hero from './components/Hero/Hero';
import ProcessDisplay from './components/Process/ProcessDisplay';
import ResultsSection from './components/Results/ResultsSection';

// Types
export type PodcastSummary = {
  title: string;
  host: string;
  duration: string;
  coverImage: string;
  mainPoints: string[];
  highlights: string[];
  keyQuotes: string[];
};

// Constants
const PROCESSING_STAGES = {
  IDLE: 0,
  TRANSCRIPTION: 1,
  SUMMARIZATION: 2,
  DIGEST_CREATION: 3
};

// Mock summary data (moved outside component for better performance)
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

/**
 * Main application component for the Podcast Digest tool
 */
const App: React.FC = () => {
  // State management
  const [podcastUrl, setPodcastUrl] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentStage, setCurrentStage] = useState<number>(PROCESSING_STAGES.IDLE);
  const [summary, setSummary] = useState<PodcastSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Reset error when URL changes
  React.useEffect(() => {
    if (error) setError(null);
  }, [podcastUrl, error]);

  // Validate podcast URL
  const isValidUrl = React.useMemo(() => {
    if (!podcastUrl.trim()) return false;
    try {
      new URL(podcastUrl);
      return true;
    } catch (e) {
      return false;
    }
  }, [podcastUrl]);

  // Mock function to simulate the podcast processing with better error handling
  const handleGenerateSummary = React.useCallback(() => {
    // Validate URL
    if (!isValidUrl) {
      setError('Please enter a valid podcast URL');
      return;
    }
    
    // Reset states
    setError(null);
    setIsProcessing(true);
    setSummary(null);
    setCurrentStage(PROCESSING_STAGES.TRANSCRIPTION);
    
    // Using a cleaner approach for the staged processing simulation
    const processStages = async () => {
      try {
        // Simulate transcription stage
        await new Promise(resolve => setTimeout(resolve, 3000));
        setCurrentStage(PROCESSING_STAGES.SUMMARIZATION);
        
        // Simulate summary agent stage
        await new Promise(resolve => setTimeout(resolve, 3000));
        setCurrentStage(PROCESSING_STAGES.DIGEST_CREATION);
        
        // Simulate digest creation stage
        await new Promise(resolve => setTimeout(resolve, 3000));
        setSummary(mockSummary);
      } catch (err) {
        setError('An error occurred during processing');
      } finally {
        setIsProcessing(false);
      }
    };
    
    processStages();
  }, [podcastUrl, isValidUrl]);

  // Render component
  return (
    <ThemeProvider>
      <Layout>
        <Hero 
          podcastUrl={podcastUrl} 
          setPodcastUrl={setPodcastUrl} 
          onGenerateSummary={handleGenerateSummary}
          isProcessing={isProcessing}
          error={error}
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

export default App;