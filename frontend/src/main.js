import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
// Import CSS in correct order: tokens → typography → animations → main → responsive → accessibility
import './styles/tokens.css'
import './styles/typography.css'
import './styles/animations.css'
import './assets/main.css'
import './styles/responsive.css'
import './styles/accessibility.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
