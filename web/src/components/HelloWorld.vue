<script setup>
import { ref } from "vue";
import { ConnectError, Code } from "@connectrpc/connect";
import { logout } from "../libs/user";
import { getGreetingService } from "../libs/api"; 

const message = ref("connecting...");

const client = getGreetingService();
client.greet({ name: "Connect" })
  .then((response) => {
    message.value = response.message;
  })
  .catch((error) => {
    const connectErr = ConnectError.from(error);
    if (connectErr.code === Code.Unauthenticated) {
      logout();
    }
  });

</script>

<template>
  <section id="center">
    <h1>Test App</h1>
    <div>{{ message }}</div> 
  </section>
</template>
