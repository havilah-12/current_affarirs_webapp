/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Editorial navy brand for a serious current-affairs tone.
        brand: {
          50: "#eef4ff",
          100: "#dce8ff",
          200: "#c1d5ff",
          300: "#9bb9ff",
          400: "#7594ff",
          500: "#4f6df2",
          600: "#1e3a8a",
          700: "#1e40af",
          800: "#1e3a8a",
          900: "#172554",
        },
        // Muted gold accent for highlights and status chips.
        accent: {
          50: "#fff9eb",
          100: "#fdf0c7",
          200: "#f9df8a",
          300: "#f2c95b",
          400: "#e8b235",
          500: "#d4a017",
          600: "#b5840f",
          700: "#91660f",
          800: "#785211",
          900: "#654511",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
