import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#7C3AED", // Violet 600
        "primary-dark": "#6D28D9", // Violet 700
        secondary: "#06B6D4", // Cyan 500
        accent: "#F59E0B", // Amber 500
        success: "#10B981", // Emerald 500
        error: "#EF4444", // Red 500
        warning: "#F59E0B", // Amber 500
        background: {
          light: "#FFFFFF",
          dark: "#0F172A", // Slate 900
        },
        surface: {
          light: "#F8FAFC", // Slate 50
          dark: "#1E293B", // Slate 800
        },
        text: {
          light: "#1E293B", // Slate 800
          dark: "#F1F5F9", // Slate 100
        },
        muted: {
          light: "#64748B", // Slate 500
          dark: "#94A3B8", // Slate 400
        },
        violet: {
          600: "#7C3AED",
          700: "#6D28D9",
        },
        cyan: {
          500: "#06B6D4",
        },
        amber: {
          500: "#F59E0B",
        },
      },
      borderRadius: {
        sm: "2px",
        md: "6px",
        lg: "8px",
        xl: "12px",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)"],
        mono: ["var(--font-geist-mono)"],
      },
      animation: {
        "fade-in": "fade-in 150ms ease",
        "slide-up": "slide-up 300ms ease",
        "gentle-pulse": "gentle-pulse 3s infinite",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "gentle-pulse": {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config; 