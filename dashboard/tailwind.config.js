/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#020617',
          card: '#0b1329',
          border: '#1e293b',
          cyan: '#00f0ff',
          pink: '#ff007f',
          green: '#00ff66',
          amber: '#ffb703',
          red: '#ff0055',
          blue: '#3a86ff',
          muted: '#64748b'
        }
      },
      fontFamily: {
        mono: ['Courier New', 'Courier', 'monospace'],
        sans: ['Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      animation: {
        'scanline': 'scanline 6s linear infinite',
        'laser': 'laser 3s ease-in-out infinite',
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glitch': 'glitch 1s linear infinite',
        'glow-cyan': 'glowCyan 2s infinite alternate',
        'glow-red': 'glowRed 2.5s infinite alternate',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        laser: {
          '0%, 100%': { transform: 'translateY(0%)', opacity: 0.2 },
          '50%': { transform: 'translateY(100%)', opacity: 0.8 },
        },
        glowCyan: {
          '0%': { boxShadow: '0 0 5px rgba(0, 240, 255, 0.2), 0 0 10px rgba(0, 240, 255, 0.1)' },
          '100%': { boxShadow: '0 0 15px rgba(0, 240, 255, 0.6), 0 0 30px rgba(0, 240, 255, 0.3)' },
        },
        glowRed: {
          '0%': { boxShadow: '0 0 5px rgba(255, 0, 85, 0.2), 0 0 10px rgba(255, 0, 85, 0.1)' },
          '100%': { boxShadow: '0 0 15px rgba(255, 0, 85, 0.6), 0 0 30px rgba(255, 0, 85, 0.3)' },
        }
      }
    },
  },
  plugins: [],
}
