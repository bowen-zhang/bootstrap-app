<template>
  <v-container>
    <v-row compact>
      <v-col cols="12" sm="6">
        <v-text-field
          v-model="firstName"
          label="First Name"
          variant="outlined"
          prepend-inner-icon="mdi-account"
          :rules="[requiredRule]"
          hide-details="auto"
          @change="handleFieldChange"
        />
      </v-col>
      <v-col cols="12" sm="6">
        <v-text-field
          v-model="lastName"
          label="Last Name"
          variant="outlined"
          prepend-inner-icon="mdi-account"
          :rules="[requiredRule]"
          hide-details="auto"
          @change="handleFieldChange"
        />
      </v-col>
    </v-row>
    <v-row compact>
      <v-col cols="12">
        <v-text-field
          v-model="email"
          label="Email"
          variant="outlined"
          prepend-inner-icon="mdi-email"
          type="email"
          :rules="[requiredRule]"
          hide-details="auto"
          @change="handleFieldChange"
        />
      </v-col>
    </v-row>
    <v-row compact>
      <v-col cols="12">
        <v-btn
          prepend-icon="mdi-lock"
          color="primary"
          variant="tonal"
          @click="showChangePassword = true"
        >
          Change Password
        </v-btn>        
      </v-col>
    </v-row>
    <v-row compact>
      <v-col cols="12">
      <v-text-field
        v-model="apiKey"
        label="API Key"
        variant="outlined"
        prepend-inner-icon="mdi-key"
        readonly
        append-inner-icon="mdi-content-copy"
        @click:append-inner="copyApiKey"
      >
        <template v-slot:append>
          <v-btn
            color="primary"
            variant="tonal"
            :loading="isRegeneratingApiKey"
            :disabled="isRegeneratingApiKey"
            @click="regenerateApiKey"
          >
            Regenerate
          </v-btn>
        </template>
      </v-text-field>
      </v-col>
    </v-row>

    <v-alert v-if="errorMessage" type="error" variant="tonal" class="mt-4">
      {{ errorMessage }}
    </v-alert>

    <v-alert v-if="successMessage" type="success" variant="tonal" class="mt-4" timeout="3000">
      {{ successMessage }}
    </v-alert>

    <v-dialog v-model="showChangePassword" max-width="400" persistent>
      <v-card class="pa-6">
        <v-card-title class="text-h6 mb-4">Change Password</v-card-title>
        <v-form v-model="isPasswordValid">
          <v-text-field
            v-model="newPassword"
            label="New Password"
            variant="outlined"
            prepend-inner-icon="mdi-lock"
            type="password"
            :rules="[requiredRule]"
            autofocus
          />
          <v-text-field
            v-model="confirmPassword"
            label="Re-enter New Password"
            variant="outlined"
            prepend-inner-icon="mdi-lock"
            type="password"
            :rules="[requiredRule, confirmPasswordRule]"
            @keydown.enter="handleChangePassword"
          />
        </v-form>
        <v-card-actions>
          <v-btn variant="text" color="primary" @click="showChangePassword = false">
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="tonal"
            :loading="isSaving"
            :disabled="isSaving || !isPasswordValid"
            @click="handleChangePassword"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue'
import { getAccountService } from '@/libs/api'
import { currentUser, refreshCurrentUser } from '@/libs/user'

const requiredRule = (v: string | null | undefined) =>
  !!(v && String(v).trim()) || 'Required'

const confirmPasswordRule = (v: string | null | undefined) =>
  v === newPassword.value || 'Passwords do not match'

const firstName = ref(currentUser.value?.firstName ?? '')
const lastName = ref(currentUser.value?.lastName ?? '')
const email = ref(currentUser.value?.email ?? '')
const password = ref('')
const apiKey = ref('')

const errorMessage = ref('')
const successMessage = ref('')
const isSaving = ref(false)
const isRegeneratingApiKey = ref(false)

const showChangePassword = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')
const isPasswordValid = ref(false)

onMounted(async () => {
  try {
    const response = await getAccountService().getApiKey({ refresh: false });
    apiKey.value = response.apiKey;
  } catch (error) {
    console.error('Failed to load API key', error);
  }
});

async function handleFieldChange() {
  await updateAccount();
}

async function regenerateApiKey() {
  isRegeneratingApiKey.value = true;
  errorMessage.value = '';
  try {
    const response = await getAccountService().getApiKey({ refresh: true });
    apiKey.value = response.apiKey;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to regenerate API key.';
  } finally {
    isRegeneratingApiKey.value = false;
  }
}

function copyApiKey() {
  if (apiKey.value) {
    navigator.clipboard.writeText(apiKey.value);
  }
}

async function handleChangePassword() {
  password.value = newPassword.value;
  if (await updateAccount()) {
    successMessage.value = 'Password changed successfully.';
  } else {
    errorMessage.value = 'Failed to change password.';
  }
  password.value = '';
  showChangePassword.value = false;
  newPassword.value = '';
  confirmPassword.value = '';
}

async function updateAccount(): Promise<boolean> {
  errorMessage.value = '';
  successMessage.value = '';
  isSaving.value = true;
  try {
    await getAccountService().update({
      email: email.value.trim(),
      password: password.value,
      firstName: firstName.value,
      lastName: lastName.value,
    });
    await refreshCurrentUser();
    successMessage.value = 'Account updated successfully.';
    return true;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to update account.';
    return false;
  } finally {
    isSaving.value = false;
  }
}
</script>
