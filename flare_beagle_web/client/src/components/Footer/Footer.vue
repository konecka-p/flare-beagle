<template>
  <v-card
    flat
    tile
    class="text-center"
    style="width:100%;"
  >
    <v-card-text class="text-muted">
      {{ new Date().getFullYear() }} <span>&copy; Flare-beagle </span>
    </v-card-text>
  </v-card>
</template>


<script>

export default {
  props: {
  },
};

</script>
