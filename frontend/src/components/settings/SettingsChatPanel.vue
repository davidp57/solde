<template>
  <form class="settings-form" @submit.prevent="save">
    <AppPanel :title="t('settings.section_chat')" :subtitle="t('settings.section_chat_subtitle')">
      <div class="app-form-grid">
        <div class="app-field">
          <label for="chat_provider" class="app-field__label">
            {{ t('settings.chat_provider') }}
          </label>
          <Select
            id="chat_provider"
            v-model="form.chat_provider"
            :options="providerOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="chat_model" class="app-field__label">
            {{ t('settings.chat_model') }}
          </label>
          <InputText
            id="chat_model"
            v-model="form.chat_model"
            :placeholder="t('settings.chat_model_placeholder')"
            class="w-full"
          />
        </div>

        <div class="app-field app-field--full">
          <label for="chat_api_key" class="app-field__label">
            {{ t('settings.chat_api_key') }}
          </label>
          <Password
            id="chat_api_key"
            v-model="form.chat_api_key"
            :placeholder="t('settings.chat_api_key_placeholder')"
            :feedback="false"
            toggle-mask
            class="w-full"
          />
          <small v-if="chatEnabled" class="app-field__hint app-field__hint--success">
            <i class="pi pi-check-circle" />
            {{ t('settings.chat_api_key_configured') }}
          </small>
          <small v-else class="app-field__hint app-field__hint--warning">
            <i class="pi pi-exclamation-triangle" />
            {{ t('settings.chat_api_key_not_configured') }}
          </small>
        </div>
      </div>
    </AppPanel>

    <div class="app-form-actions">
      <Button
        type="button"
        :label="t('common.cancel')"
        severity="secondary"
        :disabled="loading"
        @click="cancel"
      />
      <Button type="submit" :label="t('common.save')" :loading="loading" icon="pi pi-check" />
    </div>
  </form>

  <Message v-if="successMessage" severity="success" class="mt-4" :closable="true">
    {{ successMessage }}
  </Message>
  <Message v-if="errorMessage" severity="error" class="mt-4" :closable="true">
    {{ errorMessage }}
  </Message>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import { getSettingsApi, updateSettingsApi } from '@/api/settings'
import AppPanel from '@/components/ui/AppPanel.vue'

const { t } = useI18n()

interface ChatForm {
  chat_provider: string
  chat_api_key: string | null
  chat_model: string | null
}

const providerOptions = [
  { label: 'Google Gemini', value: 'gemini' },
  { label: 'OpenAI', value: 'openai' },
]

const defaultForm = (): ChatForm => ({
  chat_provider: 'gemini',
  chat_api_key: null,
  chat_model: null,
})

const form = ref<ChatForm>(defaultForm())
const chatEnabled = ref(false)
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

async function load(): Promise<void> {
  try {
    const data = await getSettingsApi()
    chatEnabled.value = data.chat_enabled
    form.value = {
      chat_provider: data.chat_provider,
      chat_api_key: null,
      chat_model: data.chat_model,
    }
  } catch {
    errorMessage.value = t('common.error.unknown')
  }
}

async function save(): Promise<void> {
  loading.value = true
  successMessage.value = ''
  errorMessage.value = ''
  try {
    const payload: Parameters<typeof updateSettingsApi>[0] = {
      chat_provider: form.value.chat_provider,
      chat_model: form.value.chat_model || null,
    }
    if (form.value.chat_api_key) {
      payload.chat_api_key = form.value.chat_api_key
    }
    const updated = await updateSettingsApi(payload)
    chatEnabled.value = updated.chat_enabled
    successMessage.value = t('settings.saved')
    form.value.chat_api_key = null
  } catch {
    errorMessage.value = t('settings.save_error')
  } finally {
    loading.value = false
  }
}

function cancel(): void {
  void load()
}

onMounted(() => {
  void load()
})
</script>

<style scoped>
.settings-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-6);
}

.app-field__hint--success {
  color: var(--p-green-600);
}
</style>
