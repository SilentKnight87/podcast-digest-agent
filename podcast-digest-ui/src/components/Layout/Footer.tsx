import { Github, Heart, Headphones, Twitter } from "lucide-react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border/40 py-8 md:py-12 bg-background">
      <div className="container px-4 md:px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="rounded-full p-1.5 bg-gradient-to-br from-primary to-secondary">
                <Headphones className="h-4 w-4 text-white" />
              </div>
              <span className="font-bold text-lg">
                Podcast<span className="text-primary">Digest</span>
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Transform YouTube videos into concise, insightful podcast digests using AI.
            </p>
          </div>
          
          <div className="space-y-4">
            <h4 className="font-medium text-sm uppercase tracking-wider text-muted-foreground">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="#" className="text-foreground/80 hover:text-primary transition-colors">
                  Documentation
                </Link>
              </li>
              <li>
                <Link href="#" className="text-foreground/80 hover:text-primary transition-colors">
                  GitHub Repo
                </Link>
              </li>
            </ul>
          </div>
          
          <div className="space-y-4">
            <h4 className="font-medium text-sm uppercase tracking-wider text-muted-foreground">Connect</h4>
            <div className="flex items-center gap-4">
              <a
                href="https://github.com/SilentKnight87"
                target="_blank"
                rel="noreferrer"
                className="rounded-full p-2 text-muted-foreground hover:text-foreground hover:bg-accent/10 transition-colors"
                aria-label="GitHub"
              >
                <Github className="h-5 w-5" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                className="rounded-full p-2 text-muted-foreground hover:text-foreground hover:bg-accent/10 transition-colors"
                aria-label="Twitter"
              >
                <Twitter className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
        
        <div className="flex flex-col items-center justify-between gap-4 mt-12 pt-6 border-t border-border/20 md:flex-row">
          <p className="text-center text-sm text-muted-foreground md:text-left">
            &copy; {new Date().getFullYear()} Podcast Digest. All rights reserved.
          </p>
          <p className="text-sm text-muted-foreground flex items-center">
            Made with <Heart className="h-3 w-3 text-error mx-1" /> using Next.js & shadcn/ui
          </p>
        </div>
      </div>
    </footer>
  );
} 