/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
      },
      colors: {
        cream: "#FDF8F3",
        ink: "#1E293B",
        sage: "#5B8C7A",
        sageDark: "#3D6B5C",
        peach: "#E8A87C",
        skySoft: "#E0EEF5",
      },
    },
  },
  plugins: [],
};
