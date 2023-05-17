import VueRouter from 'vue-router';
import Home from '@/components/Home';
import Login from '@/components/Login';
import Subscribe from '@/components/Subscribe';


const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { path: '/subscribe', component: Subscribe },
]

export default new VueRouter({
  mode: 'history',
  routes,
});
