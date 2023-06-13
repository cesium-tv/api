import axios from 'axios';
import Vue from 'vue'
import VueRouter from 'vue-router';
import * as Sentry from '@sentry/vue';
import 'material-design-icons-iconfont/dist/material-design-icons.css';
import App from '@/pages/UI/App.vue'
import router from '@/pages/UI/router';
import vuetify from '@/plugins/vuetify'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.config.productionTip = false

Vue.use(VueRouter);

Sentry.init({
  Vue,
  dsn: "http://67371b505cce4bf0a15a33891223fbf4@localhost:9000/4",
  integrations: [
    new Sentry.BrowserTracing({
      tracePropagationTargets: ["localhost", /^http:\/\/watch\.cesium\.tv/],
      routingInstrumentation: Sentry.vueRouterInstrumentation(router),
    }),
  ],
  tracesSampleRate: 1.0,
});

new Vue({
  router,
  vuetify,
  render: h => h(App),
}).$mount('#app')
