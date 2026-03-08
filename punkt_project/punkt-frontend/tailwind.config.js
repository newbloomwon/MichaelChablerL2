/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#111111', // Ink Black
          dark: '#000000',
        },
        secondary: {
          DEFAULT: '#f0f0f0', // Paper White
          dark: '#e0e0e0',
        },
        accent: {
          DEFAULT: '#ffeb3b', // Highlighter Yellow
          dark: '#fdd835',
        },
        tape: '#ff0000', // Red Tape
        paper: '#f5f5f5',
        ink: '#111111',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#06b6d4',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Courier Prime', 'Fira Code', 'monospace'],
        marker: ['Permanent Marker', 'cursive'],
        typewriter: ['Courier Prime', 'monospace'],
      },
      backgroundImage: {
        'paper-pattern': "url('https://www.transparenttextures.com/patterns/crumpled-paper.png')", // Fallback texture
      },
    },
  },
  plugins: [],
}
