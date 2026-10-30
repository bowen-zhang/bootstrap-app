<template>
  <v-container class="fill-height">
    <v-card class="mx-auto pa-4" max-width="640">
      <v-card-title>Settings</v-card-title>

      <v-tabs v-model="tab" color="primary">
        <v-tab value="account">Account</v-tab>
        <v-tab value="preferences">Preferences</v-tab>
      </v-tabs>

      <v-tabs-window v-model="tab">
        <v-tabs-window-item value="account">
          <Account />
        </v-tabs-window-item>

        <v-tabs-window-item value="preferences">
          <Preference />
        </v-tabs-window-item>
      </v-tabs-window>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import Account from '@/components/settings/Account.vue'
import Preference from '@/components/settings/Preference.vue'

const tab = ref('account')
</script>
