/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        geojit: {
          blue:    "#1B5E9B",
          lblue:   "#4A90D9",
          green:   "#1B7A3A",
          orange:  "#E8A020",
          bg:      "#F7F9FC",
          border:  "#DDE3EC",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
