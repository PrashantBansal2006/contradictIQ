/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#080a0f',
        surface: {
          DEFAULT: 'rgba(12, 16, 26, 0.40)', // transparent glassmorphic
          hover: 'rgba(232, 0, 120, 0.12)',
          border: 'rgba(255, 255, 255, 0.12)',
          muted: 'rgba(8, 10, 16, 0.25)',
        },
        primary: {
          DEFAULT: '#e80078',
          hover: '#c9006a',
          glow: 'rgba(232, 0, 120, 0.25)',
          dim: 'rgba(232, 0, 120, 0.12)',
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
      boxShadow: {
        glow: '0 0 20px rgba(232, 0, 120, 0.25)',
        'glow-sm': '0 0 10px rgba(232, 0, 120, 0.15)',
      },
    },
  },
  plugins: [],
}
