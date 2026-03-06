/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ohm-gold': '#D4AF37',
        'ohm-dark': '#1A1A1A',
        'ohm-light': '#F5F5F5',
      }
    },
  },
  plugins: [],
}
