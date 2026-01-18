module.exports = {
  purge: [
    './refi_monitor/templates/**/*.jinja2',
    './refi_monitor/templates/**/*.html',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        glass: {
          white: 'rgba(255, 255, 255, 0.1)',
          dark: 'rgba(17, 25, 40, 0.75)',
          border: 'rgba(255, 255, 255, 0.125)',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glass-inset': 'inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
      },
    },
  },
  variants: {
    extend: {
      backdropBlur: ['responsive'],
      backdropFilter: ['responsive'],
    },
  },
  plugins: [],
}
