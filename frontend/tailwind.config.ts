import type { Config } from "tailwindcss";
import daisyui from "daisyui";

/**
 * Open-library / printed-ephemera theme.
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
        canvas: "#FFFCF2",
        paper: "#F7F2E2",
        "paper-2": "#EDE7D6",
        "paper-3": "#E9DDBB",
        surface: "#EDE7D6",
        line: "#CFC6AF",
        "line-soft": "#B8AE9A",
        ink: "#2E2925",
        "ink-soft": "#5B524A",
        region: "#1F5FD1",
        theme: "#138B5E",
        movement: "#7466D6",
        medium: "#E83D3B",
        "region-readable": "#174A9F",
        "theme-readable": "#0F6747",
        "movement-readable": "#5549A9",
        "medium-readable": "#B72828",
        "ticket-cream": "#E9DDBB",
        "newsprint-grey": "#BFC2B8",
        "cardboard-tan": "#C79255",
        "ochre-stock": "#D7A94C",
        "signal-yellow": "#F3D64E",
        "process-orange": "#FF8A24",
        "grass-stock": "#78C98D",
        "olive-card": "#A9B15A",
        "harbor-teal": "#287F82",
        "grid-mint": "#9AD9C9",
        "station-sky": "#69B5D6",
        "railway-blue": "#2F74B7",
        "transit-indigo": "#3B4D9B",
        "register-pink": "#F239A6",
        "ledger-mauve": "#C59BC7",
        "copper-ink": "#B46A45",
      },
      borderRadius: {
        none: "0",
        sm: "1px",
        DEFAULT: "1px",
        md: "2px",
      },
      boxShadow: {
        // Restrained physical depth (no glow, no gradient).
        sheet: "0 1px 0 rgba(46,41,37,0.25), 0 6px 18px rgba(46,41,37,0.18)",
        folder: "0 1px 0 rgba(46,41,37,0.30), 0 10px 22px rgba(46,41,37,0.22)",
        lift: "0 2px 0 rgba(46,41,37,0.30), 0 18px 34px rgba(46,41,37,0.30)",
      },
    },
  },
  plugins: [daisyui],
  daisyui: {
    themes: [
      {
        archive: {
          primary: "#2E2925",
          "primary-content": "#F7F2E2",
          secondary: "#5B524A",
          "secondary-content": "#F7F2E2",
          accent: "#E83D3B",
          "accent-content": "#2E2925",
          neutral: "#2E2925",
          "neutral-content": "#F7F2E2",
          "base-100": "#F7F2E2",
          "base-200": "#EDE7D6",
          "base-300": "#E9DDBB",
          "base-content": "#2E2925",
          info: "#1F5FD1",
          success: "#138B5E",
          warning: "#F3D64E",
          error: "#E83D3B",
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
