/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/renderer/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        app: {
          bg: '#0b0d12',
          topbar: '#0f1218',
          sidebar: '#11151d',
          panel: '#151a23',
          card: '#171d27',
          hover: '#202737',
          selected: '#263044',
          badge: '#202b3f',
          border: '#293241',
          text: '#e8ecf3',
          secondary: '#b2b9c8',
          muted: '#7f8899',
          accent: '#7c3aed',
        },
      },
    },
  },
  plugins: [],
}
