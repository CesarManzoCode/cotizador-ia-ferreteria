/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Paleta de colores del sistema — modifica aquí para cambiar el tema
      colors: {
        surface: {
          DEFAULT: '#0D1117',  // Fondo principal (negro GitHub)
          1: '#161B22',        // Fondo secundario (paneles)
          2: '#21262D',        // Fondo terciario (inputs, cards)
          3: '#30363D',        // Bordes y separadores
        },
        accent: {
          DEFAULT: '#58A6FF',  // Azul principal (GitHub blue)
          dim: '#1F6FEB',      // Azul más oscuro
          glow: '#388BFD',     // Azul brillante para hover
        },
        text: {
          primary: '#E6EDF3',   // Texto principal
          secondary: '#8B949E', // Texto secundario
          muted: '#484F58',     // Texto muy tenue
        },
        warn: {
          yellow: '#D29922',    // Advertencia amarilla
          'yellow-bg': '#161209', // Fondo advertencia
          red: '#F85149',       // Error/no encontrado
          'red-bg': '#160B0B',  // Fondo error
          green: '#3FB950',     // Éxito
          'green-bg': '#0A1D0E', // Fondo éxito
        }
      },
      fontFamily: {
        // Fuente principal — estilo terminal/código profesional
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-soft': 'pulseSoft 2s infinite',
        'blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(12px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
