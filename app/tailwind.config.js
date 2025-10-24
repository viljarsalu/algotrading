/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./backend/src/templates/**/*.{html,js}",
    "./backend/src/static/js/**/*.{html,js}",
    "./backend/**/*.py",  // For Python templates that might use Tailwind classes
  ],
  theme: {
    extend: {
      colors: {
        // dYdX Brand Colors
        dydx: {
          blue: '#1E40AF',
          'blue-light': '#3B82F6',
          'blue-dark': '#1E3A8A',
          green: '#10B981',
          'green-light': '#34D399',
          'green-dark': '#059669',
          red: '#EF4444',
          'red-light': '#F87171',
          'red-dark': '#DC2626',
          orange: '#F59E0B',
          'orange-light': '#FBBF24',
          'orange-dark': '#D97706',
        },
        // Trading specific colors
        trading: {
          profit: '#10B981',
          loss: '#EF4444',
          neutral: '#6B7280',
          warning: '#F59E0B',
          info: '#3B82F6',
        },
        // Dark theme colors
        dark: {
          background: '#111827',
          'background-secondary': '#1F2937',
          'background-tertiary': '#374151',
          surface: '#1F2937',
          'surface-secondary': '#374151',
          text: '#F9FAFB',
          'text-secondary': '#D1D5DB',
          'text-muted': '#9CA3AF',
          border: '#374151',
          'border-light': '#4B5563',
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'Monaco',
          'Consolas',
          'Liberation Mono',
          'Courier New',
          'monospace',
        ],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.75rem' }],
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'bounce-subtle': 'bounceSubtle 2s infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': {
            transform: 'translateY(0)',
            animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)',
          },
          '50%': {
            transform: 'translateY(-5%)',
            animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)',
          },
        },
      },
      boxShadow: {
        'glow': '0 0 20px rgba(59, 130, 246, 0.5)',
        'glow-green': '0 0 20px rgba(16, 185, 129, 0.5)',
        'glow-red': '0 0 20px rgba(239, 68, 68, 0.5)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
  darkMode: 'class', // Enable class-based dark mode
}