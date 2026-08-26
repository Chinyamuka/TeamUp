/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'logic-blue': '#3B4AF5',
        'logic-blue-dark': '#313ec9',
        'terminal-indigo': '#21222C',
        'mint-success': '#25C2A0',
        'amber-urgency': '#FFB800',
        'error': '#ba1a1a',
        'error-light': '#ffdad6',
        'on-error-container': '#93000a',
        'background': '#f8f9fa',
        'surface': '#ffffff',
        'border': '#E2E8F0',
        'text-primary': '#191c1d',
        'text-secondary': '#47464b',
        'text-muted': '#77767c',
        'surface-hover': '#f3f4f5',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
