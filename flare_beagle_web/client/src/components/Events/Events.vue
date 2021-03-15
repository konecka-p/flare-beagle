<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-10">
        <h1>Events</h1>

        <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">Sun</th>
              <th scope="col">Date start</th>
              <th scope="col">Date end</th>
              <th scope="col">Area(km^2)</th>
              <th scope="col">ap</th>
              <th scope="col">Duration(s)</th>

              <th></th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="(event, index) in events.reverse()" :key="index">
              <td width="130">
                <video width="120" height="120" controls="controls">
                  <source src="video/y_sun.mp4" type='video/mp4;
                  codecs="avc1.42E01E, mp4a.40.2"'>
                  Sorry :(
                </video>
              </td>
              <td>{{ event.date_start }}</td>
              <td>{{ event.date_end }}</td>
              <td>{{ event.area }}</td>
              <td>{{ event.ap }}</td>
              <td>{{ event.duration }}</td>
            </tr>

          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>

import axios from 'axios';

export default {
  data() {
    return {
      events: [],
    };
  },
  methods: {
    get_events() {
      const path = 'http://localhost:5000/api/events';
      axios.get(path, { page: 1, per_page: 1 })
        .then((res) => {
          this.events = res.data.events;
          console.log(res.data.events);
        })
        .catch((error) => {
          console.error(error);
        });
    },
  },
  created() {
    this.get_events();
  },
};

</script>
