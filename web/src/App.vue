<template>
  <v-app>
    <v-app-bar color="primary" flat>
      <v-app-bar-title>Bootstrap App</v-app-bar-title>

      <v-spacer />

      <template v-if="currentUser">
        <v-btn class="hidden-md-and-up mr-2" icon="mdi-account" to="/settings" />
        <v-btn class="hidden-sm-and-down" prepend-icon="mdi-account" to="/settings">Hi, {{ currentUser.firstName }}</v-btn>
        <v-btn icon="mdi-logout" @click="logout" />
      </template>

      <template v-else>
        <v-btn variant="text" to="/signup">Sign up</v-btn>
        <v-btn variant="text" to="/login">Login</v-btn>
      </template>
    </v-app-bar>

    <v-main class="h-screen">
      <router-view />
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router'
import { currentUser, logout } from '@/libs/user'

const router = useRouter();

</script>
