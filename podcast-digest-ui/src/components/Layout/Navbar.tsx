"use client";

import Link from "next/link";
import { ThemeToggle } from "./theme-toggle";
import { Headphones, Github } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/50 backdrop-blur-md">
      <div className="flex h-16 items-center px-8 w-full">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="relative rounded-full p-1.5 bg-gradient-to-br from-primary to-secondary group-hover:from-secondary group-hover:to-primary transition-all duration-500">
            <Headphones className="h-5 w-5 text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">
            Podcast<span className="text-primary">Digest</span>
          </span>
        </Link>
        
        <div className="ml-auto flex items-center gap-4">
          <Link href="https://github.com/yourusername/podcast-digest-agent" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors">
            <Github className="h-5 w-5" />
            <span className="sr-only">GitHub</span>
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
} 