import type { Config } from "tailwindcss";
import daisyui from "daisyui";

/**
 * Archival theme. 1-bit / paper / document, restrained physical depth.
 * Mono-per-type inks are LOW-SATURATION archive colours (not the raw mock
 * hues). DaisyUI is kept only for input/button affordances.
 */
const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // Typewriter / monospace first, everywhere.
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "SF Mono",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
        // A neutral grotesk for the few non-typewriter headings (Werk-like).
        sans: [
          "ui-sans-serif",
          "Helvetica Neue",
          "Helvetica",
          "Arial",
          "system-ui",
          "sans-serif",
        ],
      },
      colors: {
        paper: "#ECE7D9",
        "paper-2": "#E3DCCB",
        "paper-3": "#D8CFB9",
        ink: "#1A1714",
        "ink-soft": "#6E665A",
        // Low-saturation archival inks, one per folder type.
        region: "#3A4A6B",
        theme: "#33302B",
        medium: "#8A4B3B",
        movement: "#8A7430",
      },
      borderRadius: {
        none: "0",
        sm: "1px",
        DEFAULT: "1px",
        md: "2px",
      },
      boxShadow: {
        // Restrained physical depth (no glow, no gradient).
        sheet: "0 1px 0 rgba(26,23,20,0.25), 0 6px 18px rgba(26,23,20,0.18)",
        folder: "0 1px 0 rgba(26,23,20,0.30), 0 10px 22px rgba(26,23,20,0.22)",
        lift: "0 2px 0 rgba(26,23,20,0.30), 0 18px 34px rgba(26,23,20,0.30)",
      },
    },
  },
  plugins: [daisyui],
  daisyui: {
    themes: [
      {
        archive: {
          primary: "#1A1714",
          "primary-content": "#ECE7D9",
          secondary: "#6E665A",
          "secondary-content": "#ECE7D9",
          accent: "#3A4A6B",
          "accent-content": "#ECE7D9",
          neutral: "#1A1714",
          "neutral-content": "#ECE7D9",
          "base-100": "#ECE7D9",
          "base-200": "#E3DCCB",
          "base-300": "#D8CFB9",
          "base-content": "#1A1714",
          info: "#3A4A6B",
          success: "#4A5D3A",
          warning: "#8A7430",
          error: "#8A3B2E",
          "--rounded-box": "1px",
          "--rounded-btn": "1px",
          "--rounded-badge": "1px",
          "--border-btn": "1px",
          "--animation-btn": "0",
          "--animation-input": "0",
        },
      },
    ],
    darkTheme: false,
    logs: false,
  },
};

export default config;
