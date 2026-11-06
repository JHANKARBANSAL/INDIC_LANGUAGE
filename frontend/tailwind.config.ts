import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ashoka: {
          50: "#f0f5fa",
          100: "#e1ecf5",
          200: "#c3d9eb",
          300: "#95bedd",
          400: "#609dc9",
          500: "#3d82b4",
          600: "#2c6796",
          700: "#24537a",
          800: "#1e3a5f", // Ashoka Navy
          900: "#0f2942", // Deep Ashoka Navy
          950: "#081624",
        },
        saffron: {
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
        },
        emerald: {
          500: "#10b981",
          600: "#059669",
          700: "#047857",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "'Segoe UI'",
          "Roboto",
          "'Noto Sans Devanagari'",
          "'Noto Sans Bengali'",
          "'Noto Sans Tamil'",
          "'Noto Sans Telugu'",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;

