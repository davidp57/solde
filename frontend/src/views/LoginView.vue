<template>
  <div class="login-wrapper">
    <Card class="login-card">
      <template #header>
        <div class="login-header">
          <span class="login-logo">⚖️</span>
          <h1 class="login-title">{{ t('app.name') }}</h1>
          <p class="login-subtitle">{{ t('auth.login.subtitle') }}</p>
        </div>
      </template>

      <template #content>
        <form class="login-form" @submit.prevent="handleSubmit">
          <Message v-if="errorMessage" severity="error" :closable="false">
            {{ errorMessage }}
          </Message>

          <div class="field">
            <label for="username">{{ t('auth.login.username') }}</label>
            <InputText
              id="username"
              v-model="username"
              :disabled="auth.loading"
              autocomplete="username"
              autofocus
              class="w-full"
            />
          </div>

          <div class="field">
            <label for="password">{{ t('auth.login.password') }}</label>
            <Password
              id="password"
              v-model="password"
              :disabled="auth.loading"
              :feedback="false"
              toggle-mask
              autocomplete="current-password"
              class="w-full"
              input-class="w-full"
            />
          </div>

          <Button
            type="submit"
            :label="t('auth.login.submit')"
            :loading="auth.loading"
            class="w-full"
          />

          <p class="login-help">{{ t('auth.login.reset_hint') }}</p>
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Card from 'primevue/card'
import { useDarkMode } from '../composables/useDarkMode'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { isDark } = useDarkMode()

const wrapperBg = computed(() => (isDark.value ? 'var(--p-surface-950)' : 'var(--p-surface-100)'))

const username = ref('')
const password = ref('')

const errorMessage = computed(() => {
  if (!auth.error) return null
  switch (auth.error) {
    case 'invalid_credentials':
      return t('auth.login.error.invalid')
    case 'network_error':
      return t('auth.login.error.network')
    default:
      return t('auth.login.error.unknown')
  }
})

async function handleSubmit(): Promise<void> {
  if (!username.value || !password.value) return
  await auth.login(username.value, password.value)
  if (auth.isAuthenticated) {
    if (auth.mustChangePassword) {
      await router.push('/profile')
    } else {
      const redirect = (route.query.redirect as string) || '/dashboard'
      await router.push(redirect)
    }
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: v-bind(wrapperBg);
  padding: 1rem;
}

.login-card {
  width: 100%;
  max-width: 420px;
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem 1.5rem 0;
  gap: 0.5rem;
}

.login-logo {
  font-size: 3rem;
  line-height: 1;
}

.login-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--p-primary-color);
}

.login-subtitle {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field label {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--p-text-color);
}

.login-help {
  margin: 0;
  text-align: center;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}
</style>
