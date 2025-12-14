/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          cyan: '#06b6d4',
          blue: '#2563eb',
        }
      },
      backgroundImage: {
        'mesh-gradient': 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(6, 182, 212, 0.15) 0%, transparent 50%), radial-gradient(ellipse 60% 40% at 90% 20%, rgba(37, 99, 235, 0.12) 0%, transparent 50%), radial-gradient(ellipse 50% 30% at 10% 80%, rgba(6, 182, 212, 0.08) 0%, transparent 50%), radial-gradient(ellipse 70% 50% at 80% 90%, rgba(37, 99, 235, 0.1) 0%, transparent 50%)',
        'mesh-gradient-light': 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(6, 182, 212, 0.08) 0%, transparent 50%), radial-gradient(ellipse 60% 40% at 90% 20%, rgba(37, 99, 235, 0.06) 0%, transparent 50%), radial-gradient(ellipse 50% 30% at 10% 80%, rgba(6, 182, 212, 0.04) 0%, transparent 50%), radial-gradient(ellipse 70% 50% at 80% 90%, rgba(37, 99, 235, 0.05) 0%, transparent 50%)',
      }
    },
  },
  plugins: [],
}


