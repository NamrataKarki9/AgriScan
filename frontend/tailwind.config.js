/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: '#2E7D32', // Deep, professional Plantix-style green
        brandLight: '#E8F5E9',
      }
    },
  },
  plugins: [],
}