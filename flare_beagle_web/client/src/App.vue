<template>
<v-app>
  <v-app-bar app color="grey darken-4" dark>
    <NavBar/>
  </v-app-bar>

  <v-content>
    <v-container fluid>
      <router-view></router-view>
      <Pagination/>
    </v-container>
  </v-content>

  <v-footer app padless absolute>
    <Footer/>
  </v-footer>
</v-app>
</template>

<script>
import NavBar from '@/components/NavBar/NavBar.vue';
import Footer from '@/components/Footer/Footer.vue';
import Pagination from '@/components/Pagination/Pagination.vue';

export default {
  name: 'App',

  components: {
    NavBar,
    Footer,
    Pagination,
  },

  data: () => ({
    //
  }),
};
</script>
