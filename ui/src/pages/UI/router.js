import axios from 'axios';
import VueRouter from 'vue-router';
import Home from '@/components/Home';
import Login from '@/components/Login';
import Subscribe from '@/components/Subscribe';
import Verify from '@/components/Verify';


const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { path: '/subscribe', component: Subscribe },
  { path: '/verify', component: Verify },
]

const router = new VueRouter({
  mode: 'history',
  routes,
});

router.beforeEach((to, from, next) => {
  if (to == '/login') {
    next();
    return;
  }

  axios
    .get('/api/v1/users/whoami/')
    .then(() => {
      next();
    })
    .catch(() => {
      next('/login');
    });
});

export default router;
