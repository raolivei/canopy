/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Inter var"', 'sans-serif']
      },
      colors: {
        ledger: {
          light: '#fdfcf8',
          primary: '#2563eb',
          accent: '#f97316'
        }
      }
    }
  },
  plugins: []
};

