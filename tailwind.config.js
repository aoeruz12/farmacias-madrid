/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./*.html",
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        madrid: {
          blue: '#0A398A',
          darkblue: '#052258',
          yellow: '#FFC000',
          yellowhover: '#E5AC00',
          emerald: '#10B981',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
