/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#07111A', // Deeper, more sophisticated slate-navy
          800: '#0e2136',
          700: '#1b344d',
        },
        neon: {
          blue: '#3b82f6', // Transformed into a solid, professional Tailwind blue-500
        },
        alert: {
          red: '#ef4444', // Tailwind red-500
          yellow: '#f59e0b', // Tailwind amber-500
          green: '#10b981' // Tailwind emerald-500
        }
      },
      fontFamily: {
        sans: ['Inter', 'Satoshi', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
