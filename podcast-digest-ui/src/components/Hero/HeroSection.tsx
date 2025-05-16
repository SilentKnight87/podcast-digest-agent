"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { YoutubeIcon, Sparkles } from "lucide-react";
import { useIsClient } from "@/lib/hooks/use-is-client";
import Waveform from "../ui/Waveform";
import ProcessingVisualizer from "../Process/ProcessingVisualizer";
import { useWorkflowContext } from "@/contexts/WorkflowContext";
import PlayDigestButton from "./PlayDigestButton"; // Placeholder for now

// Helper to define text color classes based on theme for h1
// This is a conceptual representation. In a real scenario,
// you might use CSS variables or a more sophisticated theme handling approach
// if shadcn/ui's default text colors aren't sufficient.
// For now, we'll directly use Tailwind classes.

export function HeroSection() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const isClient = useIsClient();
  const { workflowState, isProcessing, startProcessing } = useWorkflowContext();

  // Diagnostic useEffect
  useEffect(() => {
    console.log("HeroSection context state change detective:", {
      isProcessingChanged: isProcessing,
      workflowStatusChanged: workflowState?.processingStatus?.status,
      outputUrlChanged: workflowState?.outputUrl,
      currentWorkflowState: workflowState, // Log the whole state for deep dive
    });
    // Log derived states explicitly to see their calculation
    const processingStatus = workflowState?.processingStatus?.status;
    const hasOutputUrl = !!workflowState?.outputUrl;
    const shouldShowProcessingVisualizer = isProcessing && processingStatus === 'processing';
    const shouldShowPlayButton = !isProcessing && (processingStatus === 'completed' || hasOutputUrl);
    const shouldShowWaveform = !shouldShowProcessingVisualizer && !shouldShowPlayButton;
    console.log("HeroSection derived states:", {
        shouldShowProcessingVisualizer,
        shouldShowPlayButton,
        shouldShowWaveform
    });

  }, [isProcessing, workflowState]); // Dependencies: isProcessing and workflowState

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log("BUTTON CLICKED - handleSubmit called with URL:", youtubeUrl);
    console.log("Context values:", { 
      isWorkflowContextPresent: !!startProcessing,
      isProcessing
    });
    
    if (!youtubeUrl.trim()) {
      toast.error("Please enter a YouTube URL");
      return;
    }

    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
    if (!youtubeRegex.test(youtubeUrl)) {
      toast.error("Please enter a valid YouTube URL");
      return;
    }

    console.log("URL validation passed, calling startProcessing with:", youtubeUrl);
    try {
      startProcessing(youtubeUrl); // Trigger processing via context
      console.log("startProcessing called successfully");
    } catch (error) {
      console.error("Error calling startProcessing:", error);
      toast.error("Error starting the processing. See console for details.");
    }
  };
  
  // More robust conditional rendering logic
  const processingStatus = workflowState?.processingStatus?.status;
  const hasOutputUrl = !!workflowState?.outputUrl;
  
  const showProcessingVisualizer = isProcessing && processingStatus === 'processing';
  const showPlayButton = !isProcessing && (processingStatus === 'completed' || hasOutputUrl);
  const showWaveform = !showProcessingVisualizer && !showPlayButton;

  // Diagnostic logging in render method
  console.log("HeroSection render state:", { 
    isProcessing, 
    processingStatus,
    outputUrl: workflowState?.outputUrl,
    hasOutputUrl,
    showProcessingVisualizer,
    showPlayButton,
    showWaveform
  });

  return (
    <section className="relative py-16 md:py-24 lg:py-32">
      <div className="container px-4 md:px-6 mx-auto">
        <div className="flex flex-col items-center space-y-10 text-center">
          <div className="space-y-6 max-w-4xl">
            <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl">
              <span className="text-primary">Transform Any</span>{' '}
              <span className="relative inline-block text-primary">
                YouTube Video
                <span className="absolute -bottom-1 left-0 w-full h-1 bg-accent rounded-full" />
              </span>
              <br /> 
              <span>Into Podcast Digests</span>
            </h1>
            <p className="mx-auto max-w-[700px] text-muted-foreground text-lg md:text-xl">
              Enter a YouTube URL and get a concise AI-powered audio digest with natural voice narration.
              Perfect for busy professionals who want to consume the highlights from content on the go.
            </p>
          </div>
          
          <div className="w-full max-w-lg space-y-4">
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row w-full items-center space-y-3 sm:space-y-0 sm:space-x-3">
              <div className="relative w-full">
                <Input
                  type="url"
                  placeholder="Paste YouTube URL here..."
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  className="w-full pl-4 pr-12 py-6 rounded-xl shadow-md focus:ring-2 focus:ring-primary/30 transition-all border-input"
                  disabled={isProcessing} // Disable input while processing
                />
                <YoutubeIcon className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
              </div>
              <Button 
                type="submit" 
                disabled={isProcessing || !youtubeUrl.trim()} // Use isProcessing from context
                variant={(youtubeUrl.trim() && !isProcessing) ? "default" : "secondary"}
                className="px-8 py-6 rounded-xl font-medium shadow-lg hover:shadow-primary/20 transition-all w-full sm:w-auto"
              >
                {isProcessing && processingStatus === 'processing' ? (
                  <span className="flex items-center gap-2">
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Processing...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    Generate
                  </span>
                )}
              </Button>
            </form>
          </div>
          
          {isClient && (
            <div className="mt-12 w-full max-w-3xl mx-auto min-h-[300px] flex items-center justify-center">
              {showProcessingVisualizer && <ProcessingVisualizer />}
              {showPlayButton && (
                <div className="w-full">
                  <PlayDigestButton audioUrl={workflowState?.outputUrl} />
                </div>
              )}
              {showWaveform && <Waveform isProcessing={isProcessing && processingStatus !== 'idle'} />}
            </div>
          )}
        </div>
      </div>
    </section>
  );
} 