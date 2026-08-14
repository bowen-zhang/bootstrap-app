<template>
  <v-container class="d-flex justify-center align-center" style="min-height: 70vh;">
    <v-card width="420" class="pa-6">
      <v-card-title class="text-h5 mb-4">Sign up</v-card-title>

      <v-text-field
        v-model="firstName"
        label="First Name"
        variant="outlined"
        prepend-inner-icon="mdi-account"
      />

      <v-text-field
        v-model="lastName"
        label="Last Name"
        variant="outlined"
        prepend-inner-icon="mdi-account"
      />

      <v-text-field
        v-model="email"
        label="Email"
        variant="outlined"
        prepend-inner-icon="mdi-email"
        type="email"
      />

      <v-text-field
        v-model="password"
        label="Password"
        variant="outlined"
        prepend-inner-icon="mdi-lock"
        type="password"
        @keydown.enter="handleSignUp"
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
        @click="handleSignUp"
      >
        Sign up
      </v-btn>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAccountService } from '@/libs/api'

const router = useRouter()
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const password = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)

async function handleSignUp() {
  const trimmedFirstName = firstName.value.trim()
  const trimmedLastName = lastName.value.trim()
  const trimmedEmail = email.value.trim()
  const trimmedPassword = password.value.trim()

  if (!trimmedFirstName || !trimmedLastName || !trimmedEmail || !trimmedPassword) {
    errorMessage.value = 'First name, last name, email, and password are required.'
    successMessage.value = ''
    return
  }

  try {
    isSubmitting.value = true
    errorMessage.value = ''

    await getAccountService().create({
      firstName: trimmedFirstName,
      lastName: trimmedLastName,
      email: trimmedEmail,
      password: trimmedPassword,
    })

    successMessage.value = 'Account created successfully.'
    firstName.value = ''
    lastName.value = ''
    email.value = ''
    password.value = ''
    await router.push('/')
  } catch (error) {
    successMessage.value = ''
    errorMessage.value = error instanceof Error ? error.message : 'Unable to create account.'
  } finally {
    isSubmitting.value = false
  }
}
</script>
