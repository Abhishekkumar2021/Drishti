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
        background: {
          DEFAULT: "#030712",
          secondary: "#0a0f1a",
        },
        surface: {
          DEFAULT: "rgba(15, 23, 42, 0.6)",
          solid: "#0f172a",
          raised: "rgba(30, 41, 59, 0.5)",
          elevated: "rgba(51, 65, 85, 0.4)",
          border: "rgba(71, 85, 105, 0.4)",
          "border-light": "rgba(148, 163, 184, 0.2)",
        },
        accent: {
          DEFAULT: "#8b5cf6",
          light: "#a78bfa",
          dark: "#7c3aed",
          muted: "rgba(139, 92, 246, 0.15)",
          glow: "rgba(139, 92, 246, 0.4)",
        },
        primary: {
          DEFAULT: "#3b82f6",
          light: "#60a5fa",
          dark: "#2563eb",
          muted: "rgba(59, 130, 246, 0.15)",
        },
        success: {
          DEFAULT: "#10b981",
          muted: "rgba(16, 185, 129, 0.15)",
        },
        warning: {
          DEFAULT: "#f59e0b",
          muted: "rgba(245, 158, 11, 0.15)",
        },
        danger: {
          DEFAULT: "#ef4444",
          muted: "rgba(239, 68, 68, 0.15)",
        },
        text: {
          primary: "#f8fafc",
          secondary: "#cbd5e1",
          tertiary: "#94a3b8",
          muted: "#64748b",
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "glass-gradient": "linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 100%)",
        "glow-gradient": "radial-gradient(circle at center, var(--tw-gradient-stops))",
        "mesh-gradient": `
          radial-gradient(at 40% 20%, rgba(139, 92, 246, 0.15) 0px, transparent 50%),
          radial-gradient(at 80% 0%, rgba(59, 130, 246, 0.1) 0px, transparent 50%),
          radial-gradient(at 0% 50%, rgba(139, 92, 246, 0.1) 0px, transparent 50%),
          radial-gradient(at 80% 50%, rgba(59, 130, 246, 0.08) 0px, transparent 50%),
          radial-gradient(at 0% 100%, rgba(139, 92, 246, 0.1) 0px, transparent 50%)
        `,
      },
      boxShadow: {
        glow: "0 0 20px rgba(139, 92, 246, 0.3)",
        "glow-sm": "0 0 10px rgba(139, 92, 246, 0.2)",
        "glow-lg": "0 0 40px rgba(139, 92, 246, 0.4)",
        glass: "0 8px 32px rgba(0, 0, 0, 0.3)",
        "glass-sm": "0 4px 16px rgba(0, 0, 0, 0.2)",
        inner: "inset 0 1px 0 0 rgba(255, 255, 255, 0.05)",
        "inner-strong": "inset 0 2px 4px rgba(0, 0, 0, 0.2)",
      },
      backdropBlur: {
        xs: "2px",
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
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "slide-down": {
          "0%": { transform: "translateY(-10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "slide-left": {
          "0%": { transform: "translateX(10px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        "slide-right": {
          "0%": { transform: "translateX(-10px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        "scale-in": {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        "scale-out": {
          "0%": { transform: "scale(1)", opacity: "1" },
          "100%": { transform: "scale(0.95)", opacity: "0" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(139, 92, 246, 0.3)" },
          "50%": { boxShadow: "0 0 30px rgba(139, 92, 246, 0.5)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-5px)" },
        },
        "spin-slow": {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out",
        "fade-out": "fade-out 0.3s ease-out",
        "slide-up": "slide-up 0.3s ease-out",
        "slide-down": "slide-down 0.3s ease-out",
        "slide-left": "slide-left 0.3s ease-out",
        "slide-right": "slide-right 0.3s ease-out",
        "scale-in": "scale-in 0.2s ease-out",
        "scale-out": "scale-out 0.2s ease-out",
        shimmer: "shimmer 2s infinite linear",
        pulse: "pulse 2s infinite",
        "glow-pulse": "glow-pulse 2s infinite",
        float: "float 3s ease-in-out infinite",
        "spin-slow": "spin-slow 8s linear infinite",
      },
      typography: {
        invert: {
          css: {
            "--tw-prose-body": "#cbd5e1",
            "--tw-prose-headings": "#f1f5f9",
            "--tw-prose-links": "#a78bfa",
            "--tw-prose-code": "#e2e8f0",
            "--tw-prose-pre-bg": "rgba(15, 23, 42, 0.8)",
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
