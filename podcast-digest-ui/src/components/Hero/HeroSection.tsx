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
import PlayDigestButton from "./PlayDigestButton";

export function HeroSection() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const isClient = useIsClient();
  const { workflowState, isProcessing, startProcessing } = useWorkflowContext();

  useEffect(() => {
    console.log("HeroSection context state change:", {
      isProcessing,
      status: workflowState?.processingStatus?.status,
      outputUrl: workflowState?.outputUrl,
      fullState: workflowState
    });
  }, [isProcessing, workflowState]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    console.log("Processing URL:", youtubeUrl);

    if (!youtubeUrl.trim()) {
      setError("Please enter a YouTube URL");
      toast.error("Please enter a YouTube URL");
      return;
    }

    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
    if (!youtubeRegex.test(youtubeUrl)) {
      setError("Please enter a valid YouTube URL");
      toast.error("Please enter a valid YouTube URL");
      return;
    }

    try {
      startProcessing(youtubeUrl);
    } catch (error) {
      console.error("Error starting processing:", error);
      setError("Error starting processing. Please try again.");
      toast.error("Error starting processing. Please try again.");
    }
  };

  // More robust conditional rendering logic
  const processingStatus = workflowState?.processingStatus?.status;
  const hasOutputUrl = !!workflowState?.outputUrl;

  // More robust display logic with better logging
  console.log('[HeroSection] Decision factors:', {
    isProcessing,
    processingStatus,
    hasOutputUrl,
    rawOutputUrl: workflowState?.outputUrl,
    workflowState: workflowState,
    agents: workflowState?.agents?.map(a => `${a.id}: ${a.status}`),
    dataFlows: workflowState?.dataFlows?.map(f => `${f.fromAgentId}->${f.toAgentId}: ${f.status}`)
  });

  const showProcessingVisualizer = isProcessing && processingStatus === 'processing';
  // Show play button when completed AND we have an output URL
  const showPlayButton = (processingStatus === 'completed' && hasOutputUrl);
  // Only show waveform when not showing the other two components
  const showWaveform = !showProcessingVisualizer && !showPlayButton;

  // Display error notification if the processing failed
  useEffect(() => {
    if (processingStatus === 'failed') {
      toast.error("Processing failed. Please try again with a different URL.");
    }
  }, [processingStatus]);

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
              Perfect for those who want to consume the highlights from content on the go.
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
                  disabled={isProcessing}
                  aria-invalid={!!error}
                  aria-describedby={error ? "url-error" : undefined}
                />
                <YoutubeIcon className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
              </div>
              <Button
                type="submit"
                disabled={isProcessing || !youtubeUrl.trim()}
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
            {error && (
              <p id="url-error" className="text-destructive text-sm mt-1">
                {error}
              </p>
            )}
          </div>

          {isClient && (
            <div className="mt-12 w-full max-w-3xl mx-auto min-h-[300px] flex items-center justify-center">
              {showProcessingVisualizer && <ProcessingVisualizer agents={workflowState?.agents} dataFlows={workflowState?.dataFlows} />}
              {showPlayButton && (
                <div className="w-full">
                  {console.log('[HeroSection] Passing audioUrl to PlayDigestButton:', workflowState?.outputUrl)}
                  <PlayDigestButton audioUrl={workflowState?.outputUrl} />
                </div>
              )}
              {showWaveform && <Waveform isProcessing={isProcessing && processingStatus !== 'idle'} />}

              {processingStatus === 'failed' && (
                <div className="p-4 border border-destructive bg-destructive/10 rounded-md text-destructive">
                  <p>Processing failed. Please try again with a different URL.</p>
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </section>
  );
}
