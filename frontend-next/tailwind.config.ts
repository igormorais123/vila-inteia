import type { Config } from "tailwindcss";

const cfg: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        amber: { primary: "#d69e2e" },
        bg: { surface: "#1a1a1a", surface2: "#222" },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default cfg;
