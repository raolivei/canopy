/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fef9e7',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#D4AF37', // Main gold
          600: '#B8941F', // Darker gold
          700: '#9a7a1a',
          800: '#7c6015',
          900: '#5d4610',
        },
        gold: {
          light: '#F4D03F',
          DEFAULT: '#D4AF37',
          muted: '#C9A961',
          dark: '#B8941F',
        },
        warm: {
          gray: {
            50: '#FAF9F6',
            100: '#F5F3ED',
            200: '#E8E4D8',
            300: '#D4CFC0',
            400: '#B8B2A0',
            500: '#9C9580',
            600: '#7A7360',
            700: '#5C5648',
            800: '#3E3A30',
            900: '#1C1810',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem', letterSpacing: '-0.01em' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem', letterSpacing: '-0.01em' }],
        'base': ['1rem', { lineHeight: '1.5rem', letterSpacing: '-0.01em' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem', letterSpacing: '-0.02em' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem', letterSpacing: '-0.02em' }],
        '2xl': ['1.5rem', { lineHeight: '2rem', letterSpacing: '-0.02em' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem', letterSpacing: '-0.02em' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.02em' }],
      },
      borderRadius: {
        'organic': '16px',
        'card': '16px',
        'button': '12px',
        'input': '8px',
      },
      boxShadow: {
        'warm': '0 4px 6px -1px rgba(212, 175, 55, 0.1), 0 2px 4px -1px rgba(212, 175, 55, 0.06)',
        'warm-lg': '0 10px 15px -3px rgba(212, 175, 55, 0.1), 0 4px 6px -2px rgba(212, 175, 55, 0.05)',
        'warm-xl': '0 20px 25px -5px rgba(212, 175, 55, 0.1), 0 10px 10px -5px rgba(212, 175, 55, 0.04)',
        'golden': '0 0 20px rgba(212, 175, 55, 0.3)',
      },
      backgroundImage: {
        'golden-gradient': 'linear-gradient(135deg, #F4D03F 0%, #D4AF37 50%, #C9A961 100%)',
        'warm-gradient': 'linear-gradient(135deg, #FAF9F6 0%, #F5F3ED 100%)',
        'dark-warm-gradient': 'linear-gradient(135deg, #1C1810 0%, #3E3A30 100%)',
      },
      transitionTimingFunction: {
        'organic': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        '300': '300ms',
      },
    },
  },
  plugins: [],
}

