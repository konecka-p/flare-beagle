import Vue from 'vue';
import VueRouter from 'vue-router';
import Events from '@/components/Events/Events.vue';

Vue.use(VueRouter);

export default new VueRouter({
  routes: [
    {
      path: '/',
      name: 'Events',
      component: Events,
    },
  ],
  mode: 'history',
});
