import './assets/main.css'
import './assets/print.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import 'primeicons/primeicons.css'

import App from './App.vue'
import router from './router'
import i18n from './i18n'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: '.dark-mode',
    },
  },
})
app.use(ToastService)
app.use(ConfirmationService)

app.mount('#app')

// Fix Home/End cursor navigation inside PrimeVue InputNumber fields.
// PrimeVue intercepts those keys and calls preventDefault(), preventing the
// browser from moving the cursor. We schedule a setSelectionRange() after all
// synchronous handlers so the cursor moves to start / end as expected.
document.addEventListener(
  'keydown',
  (e: KeyboardEvent) => {
    if ((e.key === 'Home' || e.key === 'End') && e.target instanceof HTMLInputElement) {
      const wrapper = (e.target as HTMLInputElement).closest('[data-pc-name="inputnumber"]')
      if (wrapper) {
        const input = e.target as HTMLInputElement
        const pos = e.key === 'Home' ? 0 : input.value.length
        requestAnimationFrame(() => input.setSelectionRange(pos, pos))
      }
    }
  },
  true,
)
