import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        safe: {
          DEFAULT: '#10b981', // Green
          light: '#d1fae5',
          dark: '#059669',
        },
        caution: {
          DEFAULT: '#f59e0b', // Yellow
          light: '#fef3c7',
          dark: '#d97706',
        },
        danger: {
          DEFAULT: '#ef4444', // Red
          light: '#fee2e2',
          dark: '#dc2626',
        },
      },
    },
  },
  plugins: [],
}
export default config
