<template>
  <form class="settings-form" @submit.prevent="save">
    <AppPanel :title="t('settings.section_smtp')" :subtitle="t('settings.section_smtp_subtitle')">
      <div class="app-form-grid">
        <div class="app-field">
          <label for="smtp_host" class="app-field__label">{{ t('settings.smtp_host') }}</label>
          <InputText
            id="smtp_host"
            v-model="form.smtp_host"
            :placeholder="t('settings.smtp_host')"
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="smtp_port" class="app-field__label">{{ t('settings.smtp_port') }}</label>
          <InputNumber
            id="smtp_port"
            v-model="form.smtp_port"
            :min="1"
            :max="65535"
            :use-grouping="false"
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="smtp_user" class="app-field__label">
            {{ t('settings.smtp_username') }}
          </label>
          <InputText
            id="smtp_user"
            v-model="form.smtp_user"
            :placeholder="t('settings.smtp_username')"
            autocomplete="username"
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="smtp_password" class="app-field__label">
            {{ t('settings.smtp_password') }}
          </label>
          <Password
            id="smtp_password"
            v-model="form.smtp_password"
            :placeholder="t('settings.smtp_password_placeholder')"
            :feedback="false"
            toggle-mask
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="smtp_from_email" class="app-field__label">
            {{ t('settings.smtp_from') }}
          </label>
          <InputText
            id="smtp_from_email"
            v-model="form.smtp_from_email"
            :placeholder="t('settings.smtp_from')"
            type="email"
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="smtp_bcc" class="app-field__label">
            {{ t('settings.smtp_bcc') }}
          </label>
          <InputText
            id="smtp_bcc"
            v-model="form.smtp_bcc"
            :placeholder="t('settings.smtp_bcc')"
            type="email"
            class="w-full"
          />
          <small class="app-field__help">{{ t('settings.smtp_bcc_help') }}</small>
        </div>

        <div class="settings-switch">
          <ToggleSwitch id="smtp_use_tls" v-model="form.smtp_use_tls" />
          <label for="smtp_use_tls" class="app-field__label">
            {{ t('settings.smtp_use_tls') }}
          </label>
        </div>
      </div>
    </AppPanel>

    <AppPanel
      :title="t('settings.section_email_templates')"
      :subtitle="t('settings.section_email_templates_subtitle')"
    >
      <div class="app-field">
        <label for="email_subject_template" class="app-field__label">
          {{ t('settings.email_subject_template') }}
        </label>
        <InputText
          id="email_subject_template"
          v-model="form.email_subject_template"
          :placeholder="t('settings.email_subject_template_placeholder')"
          class="w-full"
        />
        <small class="app-field__help">{{ t('settings.email_template_vars_help', { v1: '{invoice_number}', v2: '{description}', v3: '{association_name}', v4: '{invoice_ref}' }) }}</small>
      </div>
      <div class="app-field mt-3">
        <label for="email_body_template" class="app-field__label">
          {{ t('settings.email_body_template') }}
        </label>
        <Textarea
          id="email_body_template"
          v-model="form.email_body_template"
          :placeholder="t('settings.email_body_template_placeholder')"
          class="w-full"
          rows="7"
          auto-resize
        />
        <small class="app-field__help">{{ t('settings.email_template_vars_help', { v1: '{invoice_number}', v2: '{description}', v3: '{association_name}', v4: '{invoice_ref}' }) }}</small>
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
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { getSettingsApi, updateSettingsApi } from '@/api/settings'
import AppPanel from '@/components/ui/AppPanel.vue'

const { t } = useI18n()

interface SmtpForm {
  smtp_host: string | null
  smtp_port: number
  smtp_user: string | null
  smtp_password: string | null
  smtp_from_email: string | null
  smtp_use_tls: boolean
  smtp_bcc: string | null
  email_subject_template: string | null
  email_body_template: string | null
}

const defaultForm = (): SmtpForm => ({
  smtp_host: null,
  smtp_port: 587,
  smtp_user: null,
  smtp_password: null,
  smtp_from_email: null,
  smtp_use_tls: true,
  smtp_bcc: null,
  email_subject_template: null,
  email_body_template: null,
})

const form = ref<SmtpForm>(defaultForm())
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

async function load(): Promise<void> {
  try {
    const data = await getSettingsApi()
    form.value = {
      smtp_host: data.smtp_host,
      smtp_port: data.smtp_port,
      smtp_user: data.smtp_user,
      smtp_password: null,
      smtp_from_email: data.smtp_from_email,
      smtp_use_tls: data.smtp_use_tls,
      smtp_bcc: data.smtp_bcc,
      email_subject_template: data.email_subject_template,
      email_body_template: data.email_body_template,
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
      smtp_host: form.value.smtp_host,
      smtp_port: form.value.smtp_port,
      smtp_user: form.value.smtp_user,
      smtp_from_email: form.value.smtp_from_email,
      smtp_use_tls: form.value.smtp_use_tls,
      smtp_bcc: form.value.smtp_bcc,
      // Send empty string as null to clear the template
      email_subject_template: form.value.email_subject_template?.trim() || null,
      email_body_template: form.value.email_body_template?.trim() || null,
    }
    if (form.value.smtp_password) {
      payload.smtp_password = form.value.smtp_password
    }
    await updateSettingsApi(payload)
    successMessage.value = t('settings.saved')
    form.value.smtp_password = null
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

.settings-switch {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-3);
  padding-top: var(--app-space-4);
}
</style>
