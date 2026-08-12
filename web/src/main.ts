/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Composables
import { createApp } from 'vue'

// Plugins
import { registerPlugins } from '@/plugins'
import router from '@/router'

// Components
import App from './App.vue'

// Styles
import 'unfonts.css'

const app = createApp(App)

app.use(router)
registerPlugins(app)

app.mount('#app')
