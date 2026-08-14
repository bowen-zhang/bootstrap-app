<template>
  <v-app>
    <v-app-bar color="primary" flat>
      <v-app-bar-title>Bootstrap App</v-app-bar-title>

      <v-spacer />

      <template v-if="currentUser">
        <span class="mr-4">Hi, {{ currentUser.firstName }}</span>
      </template>

      <v-btn variant="text" to="/">Home</v-btn>
      <v-btn variant="text" to="/signup">Sign up</v-btn>
      <v-btn variant="text" to="/login">Login</v-btn>

      <v-btn
        class="ml-2"
        icon="mdi-theme-light-dark"
        @click="$vuetify.theme.cycle()"
      />
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

type CurrentUser = {
  id: string
  email: string
  firstName: string
  lastName: string
}

const currentUser = computed<CurrentUser | null>(() => {
  const raw = localStorage.getItem('currentUser')
  if (!raw) return null

  try {
    return JSON.parse(raw) as CurrentUser
  } catch {
    return null
  }
})
</script>
