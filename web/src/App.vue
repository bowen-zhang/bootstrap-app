<template>
  <v-app>
    <v-app-bar color="primary" flat>
      <v-app-bar-title>Bootstrap App</v-app-bar-title>

      <v-spacer />

      <template v-if="currentUser">
        <span class="mr-4">Hi, {{ currentUser.firstName }}</span>
        <v-btn variant="text" @click="logout">Logout</v-btn>
      </template>

      <template v-else>
        <v-btn variant="text" to="/signup">Sign up</v-btn>
        <v-btn variant="text" to="/login">Login</v-btn>
      </template>

      <v-btn
        class="ml-2"
        icon="mdi-theme-light-dark"
        @click="$vuetify.theme.cycle()"
      />
    </v-app-bar>

    <v-main class="h-screen">
      <router-view />
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router'
import { currentUser, refreshCurrentUser, logout } from '@/libs/user'

const router = useRouter();

if (!currentUser.value) {
  refreshCurrentUser();
}

</script>
