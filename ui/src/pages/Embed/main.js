import Vue from 'vue'
import 'material-design-icons-iconfont/dist/material-design-icons.css';
import App from '@/pages/Embed/App.vue'
import vuetify from '@/plugins/vuetify'

Vue.config.productionTip = false

new Vue({
  vuetify,
  render: h => h(App),
}).$mount('#app')
