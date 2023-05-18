import axios from 'axios';
import Vue from 'vue'
import VueRouter from 'vue-router';
import 'material-design-icons-iconfont/dist/material-design-icons.css';
import App from '@/pages/UI/App.vue'
import router from '@/pages/UI/router';
import vuetify from '@/plugins/vuetify'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.config.productionTip = false

Vue.use(VueRouter);

new Vue({
  router,
  vuetify,
  render: h => h(App),
}).$mount('#app')
