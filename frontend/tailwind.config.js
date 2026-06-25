/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        felt: {
          DEFAULT: '#1a5c38',
          dark: '#0f3d25',
          light: '#2a7a4e',
        },
        card: {
          bg: '#fefefe',
          border: '#d4b896',
          shadow: 'rgba(0,0,0,0.4)',
        },
      },
      boxShadow: {
        card: '2px 4px 8px rgba(0,0,0,0.4)',
        'card-hover': '4px 8px 16px rgba(0,0,0,0.5)',
        'card-selected': '0 0 0 3px #fbbf24, 2px 4px 8px rgba(0,0,0,0.4)',
      },
      animation: {
        'deal-in': 'dealIn 0.3s ease-out',
        'flip-card': 'flipCard 0.4s ease-in-out',
        'slide-to-center': 'slideToCenter 0.5s ease-out',
        'score-pop': 'scorePop 0.4s ease-out',
      },
      keyframes: {
        dealIn: {
          '0%': { transform: 'translateY(-100px) scale(0.5)', opacity: '0' },
          '100%': { transform: 'translateY(0) scale(1)', opacity: '1' },
        },
        flipCard: {
          '0%': { transform: 'rotateY(90deg)' },
          '100%': { transform: 'rotateY(0deg)' },
        },
        slideToCenter: {
          '0%': { transform: 'translate(0, 0) scale(1)' },
          '50%': { transform: 'translate(var(--tx), var(--ty)) scale(1.1)' },
          '100%': { transform: 'translate(var(--tx), var(--ty)) scale(0.8)', opacity: '0' },
        },
        scorePop: {
          '0%': { transform: 'scale(0.8)', opacity: '0' },
          '60%': { transform: 'scale(1.1)', opacity: '1' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
