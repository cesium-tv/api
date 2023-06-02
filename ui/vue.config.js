module.exports = {
  pages: {
    index: {
      entry: './src/pages/UI/main.js',
      template: 'public/index.html',
      title: 'Home',
      chunks: ['chunk-vendors', 'chunk-common', 'index'],
    },
    embed: {
      entry: './src/pages/Embed/main.js',
      template: 'public/embed.html',
      title: 'Embed',
      chunks: ['chunk-vendors', 'chunk-common', 'embed'],
    },
  },

  configureWebpack: {
    devServer: {
      host: '0.0.0.0',
      port: 8000,
      allowedHosts: [
        'localhost',
        '.cesium.tv'
      ],
      proxy: {
        '/api': {
          target: 'http://api:8000/',
          changeOrigin: true
        },
        '/admin': {
          target: 'http://api:8000/',
          changeOrigin: true
        },
        '/static': {
          target: 'http://api:8000/',
          changeOrigin: true
        },
        '/media': {
          target: 'http://api:8000/',
          changeOrigin: true
        },
        '/__debug__': {
          target: 'http://api:8000/',
          changeOrigin: true
        },
      },
    },
  },

  transpileDependencies: [
    'vuetify'
  ]
}
