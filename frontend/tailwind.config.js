export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      colors: {
        amber2: "#fbbf24",
        space: {
          950: "#060a12",
          900: "#0b1220",
          800: "#121d33",
          700: "#1b2b4a"
        },
        agri: {
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a"
        },
        nasa: {
          400: "#38bdf8",
          500: "#0ea5e9"
        }
      }
    }
  },
  plugins: []
};
