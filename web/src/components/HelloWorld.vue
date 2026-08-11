<script setup>
import { ref } from "vue";
import { getGreetingService } from "../libs/api"; 

const message = ref("connecting...");

const client = getGreetingService();
client.greet({ name: "Connect" }).then((response) => {
  message.value = response.message;
  console.log(response.message);
});

</script>

<template>
  <section id="center">
    <h1>Test App</h1>
    <div>{{ message }}</div> 
  </section>
</template>
