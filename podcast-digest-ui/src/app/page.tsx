"use client";

import { HeroSection } from '@/components/Hero/HeroSection';
import ProcessTimeline from '@/components/Process/ProcessTimeline';
import { Navbar } from '@/components/Layout/Navbar';
import { Footer } from '@/components/Layout/Footer';

export default function Home() {


  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Navbar />

      <main className="flex-grow">
        {/* Hero Section */}
        <HeroSection />
        {/* Process Visualization Section */}
        <ProcessTimeline />
 
      </main>

      <Footer />
    </div>
  );
}
