"use client";

import { useState, useEffect } from "react";
import { Clock, AlertCircle, CheckCircle2, RefreshCw } from "lucide-react";
import { Button } from "./button";

interface RateLimitNoticeProps {
  resetTime: Date;
  requestsLimit: number;
}

export function RateLimitNotice({ resetTime, requestsLimit }: RateLimitNoticeProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>("");
  const [isExpired, setIsExpired] = useState<boolean>(false);

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();
      const diff = resetTime.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeRemaining("Ready to retry!");
        setIsExpired(true);
        return;
      }

      const hours = Math.floor(diff / 3600000);
      const minutes = Math.floor((diff % 3600000) / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);

      if (hours > 0) {
        setTimeRemaining(`${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
      } else {
        setTimeRemaining(`${minutes}:${seconds.toString().padStart(2, '0')}`);
      }
      
      setIsExpired(false);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [resetTime]);

  return (
    <div className={`relative overflow-hidden rounded-xl border backdrop-blur-sm transition-all duration-500 ease-out animate-slide-up ${
      isExpired 
        ? 'border-emerald-500/30 bg-emerald-500/5 shadow-lg shadow-emerald-500/20' 
        : 'border-destructive/30 bg-destructive/5 shadow-lg shadow-destructive/20'
    }`}>
      {/* Gradient overlay */}
      <div className={`absolute inset-0 ${
        isExpired 
          ? 'bg-gradient-to-br from-emerald-500/15 via-transparent to-emerald-500/10' 
          : 'bg-gradient-to-br from-destructive/15 via-transparent to-destructive/10'
      }`} />
      
      <div className="relative p-6 md:p-8">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={`flex-shrink-0 p-2 rounded-lg transition-colors duration-300 ${
            isExpired 
              ? 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/20' 
              : 'bg-destructive/15 text-destructive'
          }`}>
            {isExpired ? (
              <CheckCircle2 className="h-6 w-6" />
            ) : (
              <AlertCircle className="h-6 w-6" />
            )}
          </div>
          
          <div className="flex-1 space-y-4">
            {/* Header */}
            <div>
              <h3 className={`text-xl font-semibold mb-2 transition-colors duration-300 ${
                isExpired 
                  ? 'text-emerald-500' 
                  : 'text-destructive'
              }`}>
                {isExpired ? 'Rate Limit Reset!' : 'Rate Limit Reached'}
              </h3>
              
              <p className="text-sm text-muted-foreground leading-relaxed">
                {isExpired 
                  ? 'Great! You can now make another request and continue using the service.'
                  : `You've used all ${requestsLimit} requests for this hour. This helps us keep the service running smoothly for everyone.`
                }
              </p>
            </div>
            
            {!isExpired ? (
              <>
                {/* Countdown Display - Centered with inline clock */}
                <div className="flex flex-col items-center justify-center gap-4 p-6 rounded-lg bg-background/50 border border-destructive/20 shadow-sm">
                  <div className="flex flex-col items-center gap-3">
                    <div className="flex items-center gap-3">
                      <Clock className="h-6 w-6 text-destructive" />
                      <span className="font-mono text-3xl font-bold text-destructive tracking-wider">
                        {timeRemaining}
                      </span>
                    </div>
                    <span className="text-sm text-muted-foreground font-medium">
                      until next request
                    </span>
                  </div>
                </div>
                
                {/* Reset Time Info */}
                <div className="text-center text-xs text-muted-foreground bg-background/30 px-4 py-3 rounded-md border border-destructive/10">
                  <Clock className="inline h-3 w-3 mr-1" />
                  You can try again at {resetTime.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: true 
                  })}
                </div>
              </>
            ) : (
              /* Success State - Centered */
              <div className="flex flex-col items-center gap-4">
                <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20 shadow-sm">
                  <div className="flex flex-col items-center gap-3">
                    <div className="p-3 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                      <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                    </div>
                    <p className="text-sm text-emerald-500 font-medium text-center">
                      Ready to process your next request
                    </p>
                  </div>
                </div>
                <Button 
                  onClick={() => window.location.reload()}
                  variant="default"
                  className="shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 transition-all duration-300 bg-emerald-500 hover:bg-emerald-500/90 text-white"
                  size="lg"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}