"use client";

import React, { useEffect, useRef, useState } from 'react';
import { useIsClient } from '@/lib/hooks/use-is-client';

interface WaveformProps {
  isProcessing: boolean;
  barCount?: number;
}

const Waveform = ({
  isProcessing,
  barCount = 40,
}: WaveformProps): JSX.Element => {
  const isClient = useIsClient();
  const containerRef = useRef<HTMLDivElement>(null);
  const [initialBarData, setInitialBarData] = useState<Array<{
    height: number;
    opacity: number;
    animationDuration: number;
    colorIndex: number;
  }>>([]);

  // Generate random data only on client side
  useEffect(() => {
    if (isClient) {
      setInitialBarData(
        Array.from({ length: barCount }).map(() => ({
          height: Math.random() * 50 + 20, // Initial height between 20% and 70%
          opacity: 0.3 + Math.random() * 0.7,
          animationDuration: 0.8 + Math.random() * 0.4,
          colorIndex: Math.floor(Math.random() * 3),
        }))
      );
    }
  }, [barCount, isClient]);

  useEffect(() => {
    if (!containerRef.current || !isClient) return;

    const bars = Array.from(containerRef.current.children) as HTMLElement[];

    bars.forEach((bar, index) => {
      bar.classList.remove('animate-pulse-height', 'animate-gentle-pulse');
      bar.style.animationDelay = '0ms';

      if (isProcessing) {
        const delay = index * 50;
        bar.style.animationDelay = `${delay}ms`;
        bar.classList.add('animate-pulse-height');
      } else {
        bar.style.animationDelay = `${Math.random() * 1000}ms`;
        bar.classList.add('animate-gentle-pulse');
      }
    });

    return () => {
      if (containerRef.current) {
        const currentBars = Array.from(containerRef.current.children) as HTMLElement[];
        currentBars.forEach((bar) => {
          bar.classList.remove('animate-pulse-height', 'animate-gentle-pulse');
          bar.style.animationDelay = '0ms';
        });
      }
    };
  }, [isProcessing, initialBarData, isClient]);

  // Get the color classes based on position (for gradient effect)
  const getBarColor = (index: number, totalBars: number) => {
    // Create a gradient effect from left to right
    const position = index / totalBars;

    if (position < 0.33) {
      return "from-primary to-primary-dark";
    } else if (position < 0.66) {
      return "from-secondary to-primary";
    } else {
      return "from-accent to-secondary";
    }
  };

  // If not client, return an empty placeholder
  if (!isClient) {
    return <div className="h-24" aria-hidden="true"></div>;
  }

  return (
    <div
      ref={containerRef}
      className="flex items-end justify-center h-24 gap-px sm:gap-0.5 md:gap-1"
      aria-hidden="true"
    >
      {initialBarData.map((data, i) => (
        <div
          key={i}
          className={`w-1 sm:w-1.5 rounded-full transform transition-all duration-300 bg-gradient-to-t ${getBarColor(i, initialBarData.length)}`}
          style={{
            ['--bar-base-height' as string]: `${data.height}%`,
            height: `${data.height}%`,
            opacity: isProcessing ? 0.9 : data.opacity,
            animationDuration: `${data.animationDuration}s`,
          }}
        />
      ))}
    </div>
  );
};

export default Waveform;
