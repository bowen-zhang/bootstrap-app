<template>
  <v-container class="d-flex justify-center align-center" style="min-height: 70vh;">
    <v-card width="420" class="pa-6">
      <v-card-title class="text-h5 mb-4">Login</v-card-title>

      <v-text-field
        v-model="username"
        label="Username"
        variant="outlined"
        prepend-inner-icon="mdi-account"
      />

      <v-text-field
        v-model="password"
        label="Password"
        variant="outlined"
        prepend-inner-icon="mdi-lock"
        type="password"
        @keydown.enter="handleLogin"
      />

      <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4">
        {{ errorMessage }}
      </v-alert>

      <v-alert v-if="successMessage" type="success" variant="tonal" class="mb-4">
        {{ successMessage }}
      </v-alert>

      <v-btn
        color="primary"
        block
        size="large"
        :loading="isSubmitting"
        :disabled="isSubmitting"
        @click="handleLogin"
      >
        Login
      </v-btn>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAccountService } from '@/libs/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)

async function handleLogin() {
  const trimmedUsername = username.value.trim()
  const trimmedPassword = password.value.trim()

  if (!trimmedUsername || !trimmedPassword) {
    errorMessage.value = 'Username and password are required.'
    successMessage.value = ''
    return
  }

  try {
    isSubmitting.value = true
    errorMessage.value = ''

    await getAccountService().login({
      username: trimmedUsername,
      password: trimmedPassword,
    })

    successMessage.value = 'Login successful.'
    username.value = ''
    password.value = ''
    await router.push('/')
  } catch (error) {
    successMessage.value = ''
    errorMessage.value = error instanceof Error ? error.message : 'Unable to login.'
  } finally {
    isSubmitting.value = false
  }
}
</script>
