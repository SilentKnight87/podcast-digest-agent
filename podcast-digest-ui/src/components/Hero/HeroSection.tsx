"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { YoutubeIcon, Sparkles } from "lucide-react";
import { useIsClient } from "@/lib/hooks/use-is-client";
import Waveform from "../ui/Waveform";

// Helper to define text color classes based on theme for h1
// This is a conceptual representation. In a real scenario,
// you might use CSS variables or a more sophisticated theme handling approach
// if shadcn/ui's default text colors aren't sufficient.
// For now, we'll directly use Tailwind classes.

export function HeroSection() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const isClient = useIsClient();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!youtubeUrl.trim()) {
      toast.error("Please enter a YouTube URL");
      return;
    }

    // Simple validation for YouTube URL
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
    if (!youtubeRegex.test(youtubeUrl)) {
      toast.error("Please enter a valid YouTube URL");
      return;
    }

    setIsLoading(true);
    
    try {
      // This will be replaced with actual API call
      toast.info("Processing YouTube URL...");
      setTimeout(() => {
        toast.success("URL submitted successfully");
        setIsLoading(false);
      }, 1500);
      
      // TODO: Implement actual API call
      // const response = await fetch('/api/v1/process_youtube_url', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ url: youtubeUrl }),
      // });
      // const data = await response.json();
    } catch (error) {
      console.error("Error submitting URL:", error);
      toast.error("Failed to process URL. Please try again.");
      setIsLoading(false);
    }
  };

  return (
    <section className="relative py-16 md:py-24 lg:py-32 bg-background overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-[30%] -left-[20%] w-[70%] h-[70%] rounded-full blur-3xl opacity-20 bg-primary animate-gentle-pulse"></div>
        <div className="absolute -bottom-[30%] -right-[20%] w-[70%] h-[70%] rounded-full blur-3xl opacity-20 bg-secondary animate-gentle-pulse"></div>
      </div>
      
      <div className="container px-4 md:px-6 mx-auto">
        <div className="flex flex-col items-center space-y-10 text-center">
          <div className="space-y-6 max-w-4xl">
            <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl">
              <span className="text-primary">Transform Any</span>{' '}
              <span className="relative inline-block text-primary">
                YouTube Video
                <span className="absolute -bottom-1 left-0 w-full h-1 bg-accent rounded-full"></span>
              </span>
              <br /> 
              <span className="text-secondary">Into Podcast Digests</span>
            </h1>
            <p className="mx-auto max-w-[700px] text-muted-foreground text-lg md:text-xl">
              Enter a YouTube URL and get a concise audio summary of the content. 
              Perfect for busy professionals who want to stay informed.
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
                />
                <YoutubeIcon className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
              </div>
              <Button 
                type="submit" 
                disabled={isLoading || !youtubeUrl.trim()}
                variant={youtubeUrl.trim() ? "default" : "secondary"}
                className="px-8 py-6 rounded-xl font-medium shadow-lg hover:shadow-primary/20 transition-all w-full sm:w-auto"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Processing
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
            <div className="mt-12 w-full max-w-md mx-auto">
              <Waveform isProcessing={isLoading} />
            </div>
          )}
        </div>
      </div>
    </section>
  );
} 