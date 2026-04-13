<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('settings.title')"
      :subtitle="t('settings.subtitle')"
    />

    <form class="settings-form" @submit.prevent="save">
      <AppPanel :title="t('settings.section_asso')" :subtitle="t('settings.section_asso_subtitle')">
        <div class="app-form-grid">
          <div class="app-field">
            <label for="association_name" class="app-field__label">
              {{ t('settings.asso_name') }}
            </label>
            <InputText
              id="association_name"
              v-model="form.association_name"
              :placeholder="t('settings.asso_name')"
              class="w-full"
            />
          </div>

          <div class="app-field">
            <label for="association_siret" class="app-field__label">
              {{ t('settings.siret') }}
            </label>
            <InputText
              id="association_siret"
              v-model="form.association_siret"
              :placeholder="t('settings.siret')"
              class="w-full"
            />
          </div>

          <div class="app-field app-field--full">
            <label for="association_address" class="app-field__label">
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

          <div class="app-field">
            <label for="fiscal_year_start_month" class="app-field__label">
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
      </AppPanel>

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

          <div class="settings-switch">
            <ToggleSwitch id="smtp_use_tls" v-model="form.smtp_use_tls" />
            <label for="smtp_use_tls" class="app-field__label">
              {{ t('settings.smtp_use_tls') }}
            </label>
          </div>
        </div>
      </AppPanel>

      <div class="app-form-actions">
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

    <AppPanel class="danger-panel" :title="t('settings.danger_zone')" :subtitle="t('settings.reset_db_desc')">
      <div class="settings-danger">
        <div>
          <Button
            :label="t('settings.bootstrap_accounting')"
            icon="pi pi-refresh"
            severity="secondary"
            outlined
            :loading="bootstrapping"
            @click="bootstrapAccounting"
          />
        </div>
        <div>
          <Button
            :label="t('settings.reset_db')"
            icon="pi pi-trash"
            severity="danger"
            outlined
            :loading="resetting"
            @click="confirmReset"
          />
        </div>
        <Message v-if="resetMessage" severity="warn" class="mt-2" :closable="true">
          {{ resetMessage }}
        </Message>
        <Message v-if="bootstrapMessage" severity="info" class="mt-2" :closable="true">
          {{ bootstrapMessage }}
        </Message>
      </div>
    </AppPanel>

    <ConfirmDialog />
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import ConfirmDialog from 'primevue/confirmdialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { useConfirm } from 'primevue/useconfirm'
import {
  bootstrapAccountingApi,
  getSettingsApi,
  resetDbApi,
  updateSettingsApi,
  type AppSettingsUpdate,
} from '@/api/settings'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import { useFiscalYearStore } from '@/stores/fiscalYear'
import { useDarkMode } from '../composables/useDarkMode'

const { t } = useI18n()
const { isDark } = useDarkMode()
const fiscalYearStore = useFiscalYearStore()

const dangerHeaderBg = computed(() => isDark.value ? 'rgba(239,68,68,0.08)' : 'var(--p-red-50)')
const dangerBorderColor = computed(() => isDark.value ? 'rgba(239,68,68,0.25)' : 'var(--p-red-200)')
const dangerTitleColor = computed(() => isDark.value ? 'var(--p-red-400)' : 'var(--p-red-600)')

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

const confirm = useConfirm()
const form = ref<SettingsForm>(defaultForm())
const loading = ref(false)
const resetting = ref(false)
const bootstrapping = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const resetMessage = ref('')
const bootstrapMessage = ref('')

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

function confirmReset(): void {
  confirm.require({
    message: t('settings.reset_db_confirm'),
    header: t('settings.reset_db'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('settings.reset_db_yes') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: doReset,
  })
}

async function doReset(): Promise<void> {
  resetting.value = true
  resetMessage.value = ''
  try {
    const deleted = await resetDbApi()
    const total = Object.values(deleted).reduce((s, n) => s + n, 0)
    resetMessage.value = t('settings.reset_db_done', { count: total })
  } catch {
    resetMessage.value = t('settings.reset_db_error')
  } finally {
    resetting.value = false
  }
}

async function bootstrapAccounting(): Promise<void> {
  bootstrapping.value = true
  bootstrapMessage.value = ''
  errorMessage.value = ''
  try {
    const result = await bootstrapAccountingApi()
    await fiscalYearStore.refresh()
    bootstrapMessage.value = t('settings.bootstrap_accounting_done', {
      accounts: result.accounts_inserted,
      rules: result.rules_inserted,
      fiscalYears: result.fiscal_years_created,
    })
  } catch {
    errorMessage.value = t('settings.bootstrap_accounting_error')
  } finally {
    bootstrapping.value = false
  }
}

onMounted(load)
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

.settings-danger {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.danger-panel :deep(.app-panel__header) {
  background-color: v-bind(dangerHeaderBg);
  border-bottom: 1px solid v-bind(dangerBorderColor);
}

.danger-panel :deep(.app-panel__title) {
  color: v-bind(dangerTitleColor);
  font-weight: 600;
}
</style>

