module.exports = {
  configureWebpack: {
    devServer: {
      host: '0.0.0.0',
      port: 8000,
      allowedHosts: ['localhost', 'cesium.tv'],
      proxy: {
        '/api': {
          'target': 'http://api:8000/',
        },
        '/static': {
          'target': 'http://api:8000/',
        },
      },
    },
  },
}
