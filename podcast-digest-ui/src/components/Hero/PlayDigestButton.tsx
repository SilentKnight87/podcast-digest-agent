"use client";

import React from 'react';
import { Button } from "@/components/ui/button";
import { PlayCircle } from 'lucide-react';

interface PlayDigestButtonProps {
  audioUrl?: string;
}

const PlayDigestButton: React.FC<PlayDigestButtonProps> = ({ audioUrl }) => {
  if (!audioUrl) {
    return (
      <div className="text-center p-8">
        <p className="text-muted-foreground">Audio digest is ready, but URL is missing.</p>
      </div>
    );
  }

  const handlePlay = () => {
    // Basic play functionality, can be expanded to a full player
    console.log("Playing audio from:", audioUrl);
    // In a real scenario, you'd use an <audio> element or a library
    const audio = new Audio(audioUrl);
    audio.play().catch(error => {
      console.error("Error playing audio:", error);
      alert("Error playing audio. Check console for details.");
    });
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-6 p-8 bg-card/50 backdrop-blur-sm rounded-lg shadow-xl w-full max-w-md mx-auto">
      <h2 className="text-2xl font-semibold text-primary">Your Podcast Digest is Ready!</h2>
      <p className="text-muted-foreground">
        Click the button below to listen to your generated audio digest.
      </p>
      <Button 
        onClick={handlePlay} 
        size="lg"
        className="px-8 py-6 text-lg font-semibold rounded-full shadow-lg hover:shadow-primary/30 transition-all group bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background"
      >
        <PlayCircle className="w-7 h-7 mr-3 transition-transform duration-300 ease-in-out group-hover:scale-110" />
        Play Digest
      </Button>
      <p className="text-xs text-muted-foreground mt-2">Audio URL: {audioUrl}</p>
    </div>
  );
};

export default PlayDigestButton; 