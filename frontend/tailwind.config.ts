import type { Config } from "tailwindcss";
import daisyui from "daisyui";

/**
 * Archival theme. 1-bit / paper / document, restrained physical depth.
 * Shared palette tokens are kept here so Tailwind utilities, DaisyUI, and
 * custom CSS resolve to the same named colours.
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
        mono: [
          "var(--font-plex-mono)",
          "ui-monospace",
          "SFMono-Regular",
          "SF Mono",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
        sans: [
          "var(--font-plex-sans)",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
      },
      colors: {
        "dark-blue": "#1A00B9",
        "portland-orange": "#FF5E39",
        "white-chocolate": "#EFEAD3",
        "june-bud": "#B7CE4F",
        paper: "#F3EEDB",
        "paper-2": "#EBE3CC",
        "paper-3": "#DED3B8",
        ink: "#1A1714",
        "ink-soft": "#3F372D",
        "rail-red": "#FF5E39",
        "instruction-cyan": "#18B7C8",
        "signal-green": "#B7CE4F",
        "aux-brown": "#332D28",
        region: "#1A00B9",
        theme: "#B7CE4F",
        medium: "#FF5E39",
        movement: "#1A00B9",
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
          "primary-content": "#F3EEDB",
          secondary: "#3F372D",
          "secondary-content": "#F3EEDB",
          accent: "#FF5E39",
          "accent-content": "#F3EEDB",
          neutral: "#1A1714",
          "neutral-content": "#F3EEDB",
          "base-100": "#F3EEDB",
          "base-200": "#EBE3CC",
          "base-300": "#DED3B8",
          "base-content": "#1A1714",
          info: "#18B7C8",
          success: "#B7CE4F",
          warning: "#18B7C8",
          error: "#FF5E39",
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
