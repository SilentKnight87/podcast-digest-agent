"use client";

import React, { useEffect, useRef, useState } from 'react';
import { Button } from "@/components/ui/button";
import { PlayCircle, PauseCircle, Download } from 'lucide-react';
import { toast } from 'sonner';

interface PlayDigestButtonProps {
  audioUrl?: string;
}

const PlayDigestButton: React.FC<PlayDigestButtonProps> = ({ audioUrl }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // Debug rendering and props
  console.log('[PlayDigestButton] Rendering with audioUrl:', {
    audioUrl,
    isUndefined: audioUrl === undefined,
    isNull: audioUrl === null,
    isEmpty: audioUrl === '',
    type: typeof audioUrl
  });
  
  // Debug logging
  console.log('[PlayDigestButton] Received audioUrl prop:', audioUrl);

  // We're now using the HTML audio element directly in the JSX, so we don't
  // need the complex JavaScript Audio API management in useEffect anymore.
  // Instead, we'll use a simpler effect to clean up blob URLs on unmount.
  useEffect(() => {
    // Cleanup on unmount - just for blob URL cleanup
    return () => {
      console.log('[PlayDigestButton] useEffect cleanup called');
      if (audioRef.current) {
        console.log('[PlayDigestButton] Cleaning up audio element');
        audioRef.current.pause();
        
        // Clean up any blob URL we might have created
        if (audioRef.current.dataset.blobUrl) {
          console.log('[PlayDigestButton] Revoking blob URL:', audioRef.current.dataset.blobUrl);
          URL.revokeObjectURL(audioRef.current.dataset.blobUrl);
        }
      }
    };
  }, []);

  if (!audioUrl || audioUrl === '') {
    console.log('[PlayDigestButton] No valid audioUrl provided:', audioUrl);
    return (
      <div className="text-center p-8">
        <p className="text-muted-foreground">Audio digest is ready, but URL is missing.</p>
        <p className="text-sm text-muted-foreground mt-2">URL value: {JSON.stringify(audioUrl)}</p>
      </div>
    );
  }

  const handlePlayPause = () => {
    if (!audioRef.current) {
      console.error('[PlayDigestButton] No audio element available');
      return;
    }
    
    console.log('[PlayDigestButton] handlePlayPause called, audio state:', {
      src: audioRef.current.src,
      currentSrc: audioRef.current.currentSrc,
      readyState: audioRef.current.readyState,
      networkState: audioRef.current.networkState,
      error: audioRef.current.error
    });
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(error => {
        console.error("[PlayDigestButton] Error playing audio:", error);
        console.error("[PlayDigestButton] Audio element at error:", {
          src: audioRef.current?.src,
          currentSrc: audioRef.current?.currentSrc
        });
        toast.error(`Error playing audio: ${error.message || 'Unknown error'}`);
      });
    }
    
    setIsPlaying(!isPlaying);
  };

  const handleDownload = () => {
    if (!audioUrl || audioUrl === '') {
      console.error('[PlayDigestButton] Cannot download - no audio URL');
      toast.error('Audio URL is not available');
      return;
    }
    
    // Ensure we have a properly formed URL with more accurate handling of URL formats
    let fullUrl;
    if (audioUrl.startsWith('http')) {
      // Already a full URL
      fullUrl = audioUrl;
    } else {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Handle the case where NEXT_PUBLIC_API_URL is just '/api'
      if (apiBaseUrl === '/api') {
        // Use the current domain
        const origin = window.location.origin; // e.g., http://localhost:3000
        fullUrl = `${origin}${audioUrl}`;
      } else {
        // Use the configured API URL
        fullUrl = `${apiBaseUrl}${audioUrl.startsWith('/') ? '' : '/'}${audioUrl}`;
      }
    }
    
    console.log(`[PlayDigestButton] Downloading from: ${fullUrl}`);
    
    // Create a hidden anchor element
    const downloadLink = document.createElement('a');
    downloadLink.href = fullUrl;
    downloadLink.download = `podcast-digest-${new Date().toISOString().split('T')[0]}.mp3`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    
    toast.success("Download started");
  };

  const handleTest = async () => {
    console.log('[PlayDigestButton] Testing audio loading...');
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Try both test files
    const testUrls = [
      `${apiBaseUrl}/api/v1/audio/test_tone.wav`,
      `${apiBaseUrl}/api/v1/audio/sample.mp3`
    ];
    
    for (const testUrl of testUrls) {
      try {
        console.log(`[PlayDigestButton] Testing file: ${testUrl}`);
        
        // Test direct fetch
        const response = await fetch(testUrl);
        console.log('[PlayDigestButton] Test fetch response:', {
          url: testUrl,
          ok: response.ok,
          status: response.status,
          headers: Object.fromEntries(response.headers.entries())
        });
        
        if (!response.ok) {
          console.error(`[PlayDigestButton] Fetch failed for ${testUrl}`);
          continue;
        }
        
        // Get the blob and analyze it
        const blob = await response.blob();
        console.log('[PlayDigestButton] Received blob:', {
          size: blob.size,
          type: blob.type
        });
        
        if (blob.size === 0) {
          console.error("[PlayDigestButton] Empty blob received");
          continue;
        }
        
        // Create blob URL and try to play it
        const blobUrl = URL.createObjectURL(blob);
        const testAudio = new Audio(blobUrl);
        
        testAudio.addEventListener('loadstart', () => console.log('[Test] loadstart'));
        testAudio.addEventListener('canplaythrough', () => {
          console.log('[Test] canplaythrough');
          testAudio.play()
            .then(() => {
              console.log('[PlayDigestButton] Test audio played successfully');
              setTimeout(() => {
                testAudio.pause();
                URL.revokeObjectURL(blobUrl);
              }, 2000);
            })
            .catch(err => {
              console.error('[PlayDigestButton] Test audio playback failed:', err);
              URL.revokeObjectURL(blobUrl);
            });
        });
        
        testAudio.addEventListener('error', (e) => {
          const audio = e.target as HTMLAudioElement;
          let errorMessage = "Unknown error";
          
          if (audio.error) {
            switch (audio.error.code) {
              case MediaError.MEDIA_ERR_ABORTED:
                errorMessage = "Media download was aborted";
                break;
              case MediaError.MEDIA_ERR_NETWORK:
                errorMessage = "Network error while downloading";
                break;
              case MediaError.MEDIA_ERR_DECODE:
                errorMessage = "Error decoding media";
                break;
              case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                errorMessage = "Media format not supported";
                break;
            }
          }
          
          console.error('[Test] error:', errorMessage, audio.error);
          URL.revokeObjectURL(blobUrl);
        });
        
        testAudio.load();
      } catch (error) {
        console.error(`[PlayDigestButton] Test failed for ${testUrl}:`, error);
      }
    }
    
    // Now test the actual audio URL
    if (audioUrl) {
      try {
        console.log('[PlayDigestButton] Testing actual audio URL:', audioUrl);
        
        // Ensure we have a properly formed URL with more accurate handling of URL formats
        let fullUrl;
        if (audioUrl.startsWith('http')) {
          // Already a full URL
          fullUrl = audioUrl;
        } else {
          // Use the configured API URL - improved handling of paths
          const normalizedApiUrl = apiBaseUrl.endsWith('/') ? apiBaseUrl.slice(0, -1) : apiBaseUrl;
          
          // Special handling for the case where audioUrl already contains 'api/v1/audio/'
          let normalizedPath;
          if (audioUrl.startsWith('/api/v1/audio/')) {
            // API v1 path already included, just extract the filename
            const filename = audioUrl.split('/').pop();
            normalizedPath = `/api/v1/audio/${filename}`;
          } else if (audioUrl.startsWith('/')) {
            // Already has leading slash
            normalizedPath = audioUrl;
          } else {
            // Add leading slash
            normalizedPath = `/${audioUrl}`;
          }
          
          fullUrl = `${normalizedApiUrl}${normalizedPath}`;
        }
        
        console.log(`[PlayDigestButton] Full actual audio URL: ${fullUrl}`);
        
        const actualResponse = await fetch(fullUrl);
        console.log('[PlayDigestButton] Actual audio response:', {
          ok: actualResponse.ok,
          status: actualResponse.status,
          headers: Object.fromEntries(actualResponse.headers.entries())
        });
        
        if (!actualResponse.ok) {
          console.error(`[PlayDigestButton] Actual audio fetch failed: ${actualResponse.status} ${actualResponse.statusText}`);
          return;
        }
        
        const blob = await actualResponse.blob();
        console.log('[PlayDigestButton] Actual audio blob:', {
          size: blob.size,
          type: blob.type
        });
        
        // Read first few bytes to check file format
        const arrayBuffer = await blob.slice(0, 12).arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join(' ');
        console.log('[PlayDigestButton] First 12 bytes (hex):', hex);
        
        // Check for common audio file signatures
        if (hex.startsWith('49 44 33')) {
          console.log('[PlayDigestButton] File starts with ID3 tag (MP3)');
        } else if (hex.startsWith('ff fb') || hex.startsWith('ff fa') || hex.startsWith('ff f3')) {
          console.log('[PlayDigestButton] File starts with MPEG frame header (MP3)');
        } else if (hex.startsWith('52 49 46 46')) {
          console.log('[PlayDigestButton] File starts with RIFF header (WAV)');
        } else {
          console.log('[PlayDigestButton] Unknown file format');
        }
        
        // Try playing the blob
        const blobUrl = URL.createObjectURL(blob);
        const actualAudio = new Audio(blobUrl);
        
        actualAudio.addEventListener('loadstart', () => console.log('[Actual] loadstart'));
        actualAudio.addEventListener('canplaythrough', () => {
          console.log('[Actual] canplaythrough');
          actualAudio.play()
            .then(() => {
              console.log('[PlayDigestButton] Actual audio played successfully');
              setTimeout(() => {
                actualAudio.pause();
                URL.revokeObjectURL(blobUrl);
              }, 2000);
            })
            .catch(err => {
              console.error('[PlayDigestButton] Actual audio playback failed:', err);
              URL.revokeObjectURL(blobUrl);
            });
        });
        
        actualAudio.addEventListener('error', (e) => {
          console.error('[Actual] error:', (e.target as HTMLAudioElement).error);
          URL.revokeObjectURL(blobUrl);
        });
        
        actualAudio.load();
      } catch (error) {
        console.error('[PlayDigestButton] Actual audio test failed:', error);
      }
    }
  };

  // Format time from seconds to MM:SS
  const formatTime = (timeInSeconds: number) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
  };

  // Calculate progress percentage
  const progressPercentage = duration ? (currentTime / duration) * 100 : 0;

  // Prepare the proper full URL for the audio source
  let audioSourceUrl = '';
  if (audioUrl) {
    if (audioUrl.startsWith('http')) {
      audioSourceUrl = audioUrl;
    } else {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      if (apiBaseUrl === '/api') {
        audioSourceUrl = `${window.location.origin}${audioUrl.startsWith('/') ? audioUrl : `/${audioUrl}`}`;
      } else {
        const normalizedApiUrl = apiBaseUrl.endsWith('/') ? apiBaseUrl.slice(0, -1) : apiBaseUrl;
        const normalizedPath = audioUrl.startsWith('/') ? audioUrl : `/${audioUrl}`;
        audioSourceUrl = `${normalizedApiUrl}${normalizedPath}`;
      }
    }
  }
  
  console.log('[PlayDigestButton] Final audio source URL:', audioSourceUrl);

  return (
    <div className="flex flex-col items-center justify-center space-y-6 p-8 bg-card/50 backdrop-blur-sm rounded-lg shadow-xl w-full max-w-md mx-auto">
      <h2 className="text-2xl font-semibold text-primary">Your Podcast Digest is Ready!</h2>
      <p className="text-muted-foreground">
        Click play to listen to your generated audio digest.
      </p>
      
      {/* Native HTML5 audio element - more reliable than JS Audio API */}
      <audio 
        src={audioSourceUrl}
        ref={(el) => {
          // Only update the ref if it's not already set to avoid unnecessary re-renders
          if (el && (!audioRef.current || audioRef.current.src !== el.src)) {
            console.log('[PlayDigestButton] Setting audio element ref with src:', el.src);
            audioRef.current = el;
            
            // Add event listeners to the new audio element
            el.addEventListener('loadedmetadata', () => {
              console.log('[PlayDigestButton] Audio metadata loaded. Duration:', el.duration);
              setDuration(el.duration);
            });
            
            el.addEventListener('timeupdate', () => {
              setCurrentTime(el.currentTime);
            });
            
            el.addEventListener('ended', () => {
              console.log('[PlayDigestButton] Audio playback ended');
              setIsPlaying(false);
              setCurrentTime(0);
              el.currentTime = 0;
            });
            
            el.addEventListener('error', (e) => {
              console.error('[PlayDigestButton] Audio element error:', el.error);
              console.error('[PlayDigestButton] Error event:', e);
              console.error('[PlayDigestButton] Current src:', el.currentSrc);
              
              // Fall back to blob URL approach if direct playback fails
              fetch(audioSourceUrl)
                .then(response => {
                  console.log('[PlayDigestButton] Fetch result:', {
                    ok: response.ok,
                    status: response.status
                  });
                  
                  if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                  return response.blob();
                })
                .then(blob => {
                  console.log('[PlayDigestButton] Creating blob URL from blob:', {
                    size: blob.size,
                    type: blob.type
                  });
                  
                  // Create blob URL
                  const blobUrl = URL.createObjectURL(blob);
                  el.src = blobUrl;
                  
                  // Store the blob URL to revoke it later
                  el.dataset.blobUrl = blobUrl;
                  
                  console.log('[PlayDigestButton] Set audio src to blob URL:', blobUrl);
                })
                .catch(error => {
                  console.error('[PlayDigestButton] Fetch failed:', error);
                  toast.error(`Error loading audio: ${error.message}`);
                });
            });
          }
        }}
        className="hidden" // Hide the native controls, we'll use our own UI
      />
      
      <div className="w-full bg-muted/50 rounded-full h-2 mb-2 overflow-hidden">
        <div 
          className="h-full bg-primary rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>
      
      <div className="flex justify-between w-full text-sm text-muted-foreground mb-3">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>
      
      <div className="flex items-center justify-center space-x-4">
        <Button 
          onClick={() => {
            if (!audioRef.current) {
              console.error('[PlayDigestButton] No audio element available');
              return;
            }
            
            console.log('[PlayDigestButton] Play/Pause clicked, audio state:', {
              paused: audioRef.current.paused,
              ended: audioRef.current.ended,
              readyState: audioRef.current.readyState
            });
            
            if (isPlaying) {
              audioRef.current.pause();
              setIsPlaying(false);
            } else {
              // Try to play and handle any errors
              audioRef.current.play().catch(error => {
                console.error('[PlayDigestButton] Error playing audio:', error);
                toast.error(`Error playing audio: ${error.message || 'Unknown error'}`);
              });
              setIsPlaying(true);
            }
          }} 
          size="lg"
          className="px-8 py-6 text-lg font-semibold rounded-full shadow-lg hover:shadow-primary/30 transition-all group bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background"
        >
          {isPlaying ? (
            <PauseCircle className="w-7 h-7 mr-3 transition-transform duration-300 ease-in-out group-hover:scale-110" />
          ) : (
            <PlayCircle className="w-7 h-7 mr-3 transition-transform duration-300 ease-in-out group-hover:scale-110" />
          )}
          {isPlaying ? 'Pause' : 'Play'} Digest
        </Button>
        
        <Button
          onClick={handleDownload}
          variant="outline"
          size="icon"
          className="rounded-full h-12 w-12 hover:bg-accent/10"
          title="Download audio"
        >
          <Download className="h-5 w-5" />
        </Button>
        
        <Button
          onClick={handleTest}
          variant="outline"
          size="sm"
          className="rounded px-4 py-2"
        >
          Test Audio
        </Button>
      </div>
    </div>
  );
};

export default PlayDigestButton;