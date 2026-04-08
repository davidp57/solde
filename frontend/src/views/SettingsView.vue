<template>
  <div class="settings-view p-4">
    <h2 class="text-2xl font-semibold mb-6">{{ t('settings.title') }}</h2>

    <form @submit.prevent="save">
      <!-- Association info -->
      <Panel :header="t('settings.section_asso')" class="mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1">
            <label for="association_name" class="font-medium text-sm">
              {{ t('settings.asso_name') }}
            </label>
            <InputText
              id="association_name"
              v-model="form.association_name"
              :placeholder="t('settings.asso_name')"
              class="w-full"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label for="association_siret" class="font-medium text-sm">
              {{ t('settings.siret') }}
            </label>
            <InputText
              id="association_siret"
              v-model="form.association_siret"
              :placeholder="t('settings.siret')"
              class="w-full"
            />
          </div>

          <div class="flex flex-col gap-1 md:col-span-2">
            <label for="association_address" class="font-medium text-sm">
              {{ t('settings.address') }}
            </label>
            <Textarea
              id="association_address"
              v-model="form.association_address"
              :placeholder="t('settings.address')"
              rows="3"
              class="w-full"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label for="fiscal_year_start_month" class="font-medium text-sm">
              {{ t('settings.fiscal_year_start') }}
            </label>
            <Select
              id="fiscal_year_start_month"
              v-model="form.fiscal_year_start_month"
              :options="monthOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </div>
      </Panel>

      <!-- SMTP -->
      <Panel :header="t('settings.section_smtp')" class="mb-6" toggleable>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1">
            <label for="smtp_host" class="font-medium text-sm">{{ t('settings.smtp_host') }}</label>
            <InputText
              id="smtp_host"
              v-model="form.smtp_host"
              :placeholder="t('settings.smtp_host')"
              class="w-full"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label for="smtp_port" class="font-medium text-sm">{{ t('settings.smtp_port') }}</label>
            <InputNumber
              id="smtp_port"
              v-model="form.smtp_port"
              :min="1"
              :max="65535"
              :use-grouping="false"
              class="w-full"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label for="smtp_user" class="font-medium text-sm">
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

          <div class="flex flex-col gap-1">
            <label for="smtp_password" class="font-medium text-sm">
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

          <div class="flex flex-col gap-1">
            <label for="smtp_from_email" class="font-medium text-sm">
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

          <div class="flex items-center gap-2 mt-4">
            <ToggleSwitch id="smtp_use_tls" v-model="form.smtp_use_tls" />
            <label for="smtp_use_tls" class="font-medium text-sm">
              {{ t('settings.smtp_use_tls') }}
            </label>
          </div>
        </div>
      </Panel>

      <!-- Actions -->
      <div class="flex justify-end gap-3">
        <Button
          type="button"
          :label="t('common.cancel')"
          severity="secondary"
          :disabled="loading"
          @click="reset"
        />
        <Button
          type="submit"
          :label="t('common.save')"
          :loading="loading"
          icon="pi pi-check"
        />
      </div>
    </form>

    <Message v-if="successMessage" severity="success" class="mt-4" :closable="true">
      {{ successMessage }}
    </Message>
    <Message v-if="errorMessage" severity="error" class="mt-4" :closable="true">
      {{ errorMessage }}
    </Message>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { getSettingsApi, updateSettingsApi, type AppSettingsUpdate } from '@/api/settings'

const { t } = useI18n()

interface SettingsForm {
  association_name: string
  association_address: string
  association_siret: string
  fiscal_year_start_month: number
  smtp_host: string | null
  smtp_port: number
  smtp_user: string | null
  smtp_password: string | null
  smtp_from_email: string | null
  smtp_use_tls: boolean
}

const defaultForm = (): SettingsForm => ({
  association_name: '',
  association_address: '',
  association_siret: '',
  fiscal_year_start_month: 8,
  smtp_host: null,
  smtp_port: 587,
  smtp_user: null,
  smtp_password: null,
  smtp_from_email: null,
  smtp_use_tls: true,
})

const form = ref<SettingsForm>(defaultForm())
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const MONTHS = [
  'Janvier',
  'Février',
  'Mars',
  'Avril',
  'Mai',
  'Juin',
  'Juillet',
  'Août',
  'Septembre',
  'Octobre',
  'Novembre',
  'Décembre',
]
const monthOptions = MONTHS.map((label, i) => ({ label, value: i + 1 }))

async function load(): Promise<void> {
  try {
    const data = await getSettingsApi()
    form.value = {
      association_name: data.association_name,
      association_address: data.association_address,
      association_siret: data.association_siret,
      fiscal_year_start_month: data.fiscal_year_start_month,
      smtp_host: data.smtp_host,
      smtp_port: data.smtp_port,
      smtp_user: data.smtp_user,
      smtp_password: null, // never pre-filled
      smtp_from_email: data.smtp_from_email,
      smtp_use_tls: data.smtp_use_tls,
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
    const payload: AppSettingsUpdate = {
      association_name: form.value.association_name,
      association_address: form.value.association_address,
      association_siret: form.value.association_siret,
      fiscal_year_start_month: form.value.fiscal_year_start_month,
      smtp_host: form.value.smtp_host,
      smtp_port: form.value.smtp_port,
      smtp_user: form.value.smtp_user,
      smtp_from_email: form.value.smtp_from_email,
      smtp_use_tls: form.value.smtp_use_tls,
    }
    // Only include password if the user typed one
    if (form.value.smtp_password) {
      payload.smtp_password = form.value.smtp_password
    }
    await updateSettingsApi(payload)
    successMessage.value = t('settings.saved')
    form.value.smtp_password = null // clear after save
  } catch {
    errorMessage.value = t('settings.save_error')
  } finally {
    loading.value = false
  }
}

function reset(): void {
  void load()
}

onMounted(load)
</script>

