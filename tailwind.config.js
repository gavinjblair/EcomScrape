/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./docs/**/*.html",
    "./docs/assets/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#3A7BFF",
        primaryHover: "#5C93FF",
        accentFrom: "#3EEFEF",
        accentTo: "#4F79FF",
        success: "#3DFFAB",
        warning: "#FFE28A",
        textPrimary: "#FFFFFF",
        textSecondary: "#D0D7EA",
      },
    },
  },
  plugins: [],
};
