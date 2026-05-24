import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0f1419",
          raised: "#1a2332",
          border: "#2d3a4f",
        },
        accent: {
          DEFAULT: "#6366f1",
          muted: "#4f46e5",
        },
      },
    },
  },
  plugins: [],
};

export default config;
