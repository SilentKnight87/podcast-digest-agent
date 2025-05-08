"use client";

import React from 'react';
import { FileText, Mic, Cpu, PlayCircle, UploadCloud } from 'lucide-react';

interface StepProps {
  icon: React.ElementType;
  title: string;
  description: string;
  index: number;
}

const Step: React.FC<StepProps> = ({ icon: Icon, title, description, index }) => {
  // Use predictable color assignment instead of random
  const getIconColor = (index: number) => {
    const colors = [
      'text-primary',
      'text-secondary',
      'text-primary-dark',
      'text-accent',
      'text-success',
    ];
    return colors[index % colors.length];
  };
  
  return (
    <div className="flex flex-col space-y-4 relative">
      {/* Connector line for all but last item */}
      {index < 4 && (
        <div className="absolute top-12 left-7 h-full w-0.5 bg-gradient-to-b from-primary/30 to-secondary/30 -z-10"></div>
      )}
      
      <div className="flex items-start space-x-4 p-6 rounded-xl bg-card border border-border/40 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1">
        <div className="flex-shrink-0 relative">
          <div className="flex items-center justify-center w-14 h-14 rounded-full bg-muted">
            <Icon className={`w-7 h-7 ${getIconColor(index)}`} />
          </div>
          <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-background border-2 border-primary flex items-center justify-center text-xs font-bold text-primary">
            {index + 1}
          </div>
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
    </div>
  );
};

const ProcessTimeline: React.FC = () => {
  const steps = [
    {
      icon: UploadCloud,
      title: 'Submit YouTube URL',
      description: 'Provide a YouTube video URL to begin the digest creation process.',
    },
    {
      icon: FileText,
      title: 'Transcribe Audio',
      description: 'The audio from the video is accurately transcribed into text.',
    },
    {
      icon: Cpu,
      title: 'Summarize Content',
      description: 'AI analyzes the transcript to extract key insights and main points.',
    },
    {
      icon: Mic,
      title: 'Generate Audio Digest',
      description: 'The summary is converted into a high-quality audio digest using Text-to-Speech.',
    },
    {
      icon: PlayCircle,
      title: 'Access Your Digest',
      description: 'Listen to your generated audio digest and view the text summary.',
    },
  ];

  return (
    <section className="py-16 bg-background">
      <div className="container px-4 md:px-6">
        <div className="rounded-xl border border-border/40 bg-card p-8 shadow-sm">
          <div className="mb-12 space-y-4 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gradient">
              How It Works
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Our AI-powered process transforms YouTube videos into digestible podcast content in just a few steps.
            </p>
          </div>
          
          <div className="max-w-4xl mx-auto">
            <div className="grid md:grid-cols-1 lg:grid-cols-1 gap-10">
              {steps.map((step, index) => (
                <Step 
                  key={index} 
                  icon={step.icon} 
                  title={step.title} 
                  description={step.description} 
                  index={index} 
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ProcessTimeline; 