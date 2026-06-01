import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./lib/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Neutral dark palette (Stitch-inspired)
        bg: {
          DEFAULT: "#0f0f0f",
          secondary: "#141414",
          tertiary: "#1a1a1a",
        },
        surface: {
          DEFAULT: "#1a1a1a",
          hover: "#222222",
          active: "#2a2a2a",
          border: "#2a2a2a",
          "border-light": "#333333",
        },
        // Subtle accent - muted blue/purple
        accent: {
          DEFAULT: "#6366f1",
          hover: "#7c7ff2",
          muted: "rgba(99, 102, 241, 0.12)",
          "muted-hover": "rgba(99, 102, 241, 0.18)",
        },
        // Text hierarchy
        text: {
          primary: "#ffffff",
          secondary: "#a1a1a1",
          tertiary: "#717171",
          muted: "#525252",
        },
        // Semantic colors
        success: {
          DEFAULT: "#22c55e",
          muted: "rgba(34, 197, 94, 0.12)",
        },
        warning: {
          DEFAULT: "#eab308",
          muted: "rgba(234, 179, 8, 0.12)",
        },
        danger: {
          DEFAULT: "#ef4444",
          muted: "rgba(239, 68, 68, 0.12)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        subtle: "0 2px 8px rgba(0, 0, 0, 0.3)",
        medium: "0 4px 16px rgba(0, 0, 0, 0.4)",
        large: "0 8px 32px rgba(0, 0, 0, 0.5)",
        glow: "0 0 20px rgba(99, 102, 241, 0.15)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fade-out": {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" },
        },
        "slide-up": {
          "0%": { transform: "translateY(4px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "slide-down": {
          "0%": { transform: "translateY(-4px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "scale-in": {
          "0%": { transform: "scale(0.97)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
        "fade-out": "fade-out 0.2s ease-out",
        "slide-up": "slide-up 0.2s ease-out",
        "slide-down": "slide-down 0.2s ease-out",
        "scale-in": "scale-in 0.15s ease-out",
        shimmer: "shimmer 2s infinite linear",
        pulse: "pulse 2s infinite",
      },
      typography: {
        DEFAULT: {
          css: {
            "--tw-prose-body": "#a1a1a1",
            "--tw-prose-headings": "#ffffff",
            "--tw-prose-links": "#6366f1",
            "--tw-prose-code": "#e5e5e5",
            "--tw-prose-pre-bg": "#1a1a1a",
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
