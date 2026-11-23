import { type Config } from "tailwindcss";

export default {
  content: [
    "./index.html",
    "./src/**/*.{tsx,ts}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Plus Jakarta Sans Variable", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;