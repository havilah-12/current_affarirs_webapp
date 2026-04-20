/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Deep teal brand: an editorial, "world-news" tone that reads as
        // serious and timeless without falling back on corporate blue.
        brand: {
          50: "#effcf6",
          100: "#d2f7e6",
          200: "#a6efcf",
          300: "#6fdfb1",
          400: "#36c690",
          500: "#15a874",
          600: "#0c8a5e",
          700: "#0a6e4c",
          800: "#0a563d",
          900: "#0a4632",
        },
        // Warm amber accent: pairs with teal for a high-contrast,
        // "breaking-news / highlight" feel without being shouty.
        accent: {
          50: "#fff8eb",
          100: "#ffeac6",
          200: "#ffd388",
          300: "#ffb84a",
          400: "#fb9a1f",
          500: "#ef7c0a",
          600: "#cc5d05",
          700: "#a7430a",
          800: "#86340f",
          900: "#6e2b10",
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
