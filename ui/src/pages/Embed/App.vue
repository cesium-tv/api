<template>
  <v-app :style="style"></v-app>
</template>

<script>
import axios from 'axios';

export default {
  name: 'App',

  data() {
    let params = new URLSearchParams(window.location.search);

    return {
      user: null,
      video: null,
      style: {
        background: params.get('bg'),
      },
    };
  },

  mounted() {
    let params = new URLSearchParams(window.location.search);
    let videoId = params.get('video');

    axios.get('/api/v1/users/whoami/')
      .catch((e) => console.error(e))
      .then((r) => {
        this.user = r.data;
      });
    if (!videoId) {
      return;
    }
    axios.get(`/api/v1/videos/${videoId}/`)
      .catch((e) => console.error(e))
      .then((r) => {
        this.video = r.data;
      })
  },
}
</script>

<style>
</style>
