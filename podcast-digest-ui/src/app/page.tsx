"use client";

import { useState } from 'react';
import { HeroSection } from '@/components/Hero/HeroSection';
import ProcessTimeline from '@/components/Process/ProcessTimeline';
import { Navbar } from '@/components/Layout/Navbar';
import { Footer } from '@/components/Layout/Footer';
import Waveform from '@/components/ui/Waveform';
import { useIsClient } from '@/lib/hooks/use-is-client';

export default function Home() {
  const [isProcessing, setIsProcessing] = useState(false);
  const isClient = useIsClient();

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Navbar />

      <main className="flex-grow">
        {/* Hero Section */}
        <HeroSection />
        
        {/* Visualization Demo */}
        <section className="py-12 bg-muted/50">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="flex flex-col items-center space-y-6 text-center">
              <h2 className="text-2xl font-semibold text-gradient">Visualization Demo</h2>
              <p className="text-muted-foreground">See how our process works in real-time</p>
              
              {isClient && (
                <>
                  <button 
                    onClick={() => setIsProcessing(prev => !prev)}
                    className="px-6 py-2 bg-primary hover:bg-primary-dark text-white font-medium rounded-lg transition duration-150 ease-in-out shadow-md hover:shadow-lg">
                    {isProcessing ? 'Stop Animation' : 'Run Animation'}
                  </button>
                  
                  <div className="mt-8 w-full max-w-lg mx-auto bg-card rounded-xl p-6 shadow-md border border-border/40">
                    <Waveform isProcessing={isProcessing} />
                  </div>
                </>
              )}
            </div>
          </div>
        </section>

        {/* Process Visualization Section */}
        <ProcessTimeline />
        
        {/* Features Section */}
        <section className="py-16 bg-gradient-to-b from-background to-muted/30">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="text-center mb-12 space-y-4">
              <h2 className="text-3xl font-bold tracking-tight text-gradient-accent">
                Powerful Features
              </h2>
              <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                Our podcast digest service comes with everything you need to save time and stay informed.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[
                {
                  title: "Accurate Transcription",
                  description: "High-quality transcription that captures every important detail from the video."
                },
                {
                  title: "Smart Summarization",
                  description: "AI-powered summaries that extract key insights and main points."
                },
                {
                  title: "Audio Digests",
                  description: "Listen to your summaries on the go with natural-sounding text-to-speech."
                },
                {
                  title: "Time Saving",
                  description: "Get the essence of hour-long content in just minutes."
                },
                {
                  title: "Key Highlights",
                  description: "Important quotes and critical points are automatically identified."
                },
                {
                  title: "Easy Sharing",
                  description: "Share your digests with colleagues or friends with a single click."
                }
              ].map((feature, index) => (
                <div key={index} className="bg-card border border-border/40 p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300">
                  <div className="h-2 w-16 bg-gradient-to-r from-primary to-secondary rounded-full mb-4"></div>
                  <h3 className="text-xl font-semibold mb-2 text-foreground">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
