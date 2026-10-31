/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0a0d14',
        surface: {
          DEFAULT: '#111726',
          hover: '#172033',
          border: '#1e293b',
          muted: '#0e1422'
        },
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
          glow: 'rgba(59, 130, 246, 0.15)',
        },
        verdict: {
          consistent: '#10b981',
          conflicting: '#f43f5e',
          inconclusive: '#f59e0b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
