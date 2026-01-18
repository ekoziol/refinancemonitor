// postcss.config.js

const path = require('path');

module.exports = (ctx) => ({
  plugins: [
    require('tailwindcss')(path.resolve(__dirname, 'tailwind.config.js')),
    require('autoprefixer'),
    process.env.FLASK_PROD === 'production' && require('@fullhuman/postcss-purgecss')({
      content: [
        path.resolve(__dirname, 'refi_monitor/templates/**/*.html'),
        path.resolve(__dirname, 'refi_monitor/templates/**/*.jinja2'),
        path.resolve(__dirname, 'refi_monitor/static/src/**/*.{js,jsx}')
      ],
      defaultExtractor: content => content.match(/[A-Za-z0-9-_:/]+/g) || []
    })
  ],
});
