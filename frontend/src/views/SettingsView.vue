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

          <div class="app-field">
            <label for="default_invoice_due_days" class="app-field__label">
              {{ t('settings.default_invoice_due_days') }}
            </label>
            <InputNumber
              id="default_invoice_due_days"
              v-model="form.default_invoice_due_days"
              :min="0"
              :max="365"
              :use-grouping="false"
              show-buttons
              class="w-full"
            />
            <small class="app-field__hint">
              {{ t('settings.default_invoice_due_days_help') }}
            </small>
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
        <Button type="submit" :label="t('common.save')" :loading="loading" icon="pi pi-check" />
      </div>
    </form>

    <Message v-if="successMessage" severity="success" class="mt-4" :closable="true">
      {{ successMessage }}
    </Message>
    <Message v-if="errorMessage" severity="error" class="mt-4" :closable="true">
      {{ errorMessage }}
    </Message>

    <form class="settings-form" @submit.prevent="saveSystemOpening">
      <AppPanel
        :title="t('settings.system_opening_title')"
        :subtitle="t('settings.system_opening_subtitle')"
      >
        <p class="settings-opening__hint">{{ t('settings.system_opening_hint') }}</p>

        <div class="settings-opening-grid">
          <section class="settings-opening-card">
            <div class="settings-opening-card__header">
              <div>
                <h3 class="settings-opening-card__title">
                  {{ t('settings.system_opening_bank_title') }}
                </h3>
                <p class="settings-opening-card__subtitle">
                  {{ t('settings.system_opening_bank_subtitle') }}
                </p>
              </div>
              <Tag
                :value="
                  systemOpeningForm.bank.configured
                    ? t('settings.system_opening_status_configured')
                    : t('settings.system_opening_status_pending')
                "
                :severity="systemOpeningForm.bank.configured ? 'success' : 'warn'"
              />
            </div>

            <div class="app-form-grid">
              <div class="app-field">
                <label for="system_opening_bank_date" class="app-field__label">
                  {{ t('settings.system_opening_date') }}
                </label>
                <DatePicker
                  id="system_opening_bank_date"
                  v-model="systemOpeningForm.bank.date"
                  date-format="yy-mm-dd"
                  show-icon
                  class="w-full"
                />
              </div>

              <div class="app-field">
                <label for="system_opening_bank_amount" class="app-field__label">
                  {{ t('settings.system_opening_amount') }}
                </label>
                <InputNumber
                  id="system_opening_bank_amount"
                  v-model="systemOpeningForm.bank.amount"
                  mode="decimal"
                  :min-fraction-digits="2"
                  :max-fraction-digits="2"
                  class="w-full"
                />
              </div>

              <div class="app-field app-field--full">
                <label for="system_opening_bank_reference" class="app-field__label">
                  {{ t('settings.system_opening_reference') }}
                </label>
                <InputText
                  id="system_opening_bank_reference"
                  v-model="systemOpeningForm.bank.reference"
                  :placeholder="t('settings.system_opening_reference_placeholder')"
                  class="w-full"
                />
              </div>
            </div>
          </section>

          <section class="settings-opening-card">
            <div class="settings-opening-card__header">
              <div>
                <h3 class="settings-opening-card__title">
                  {{ t('settings.system_opening_cash_title') }}
                </h3>
                <p class="settings-opening-card__subtitle">
                  {{ t('settings.system_opening_cash_subtitle') }}
                </p>
              </div>
              <Tag
                :value="
                  systemOpeningForm.cash.configured
                    ? t('settings.system_opening_status_configured')
                    : t('settings.system_opening_status_pending')
                "
                :severity="systemOpeningForm.cash.configured ? 'success' : 'warn'"
              />
            </div>

            <div class="app-form-grid">
              <div class="app-field">
                <label for="system_opening_cash_date" class="app-field__label">
                  {{ t('settings.system_opening_date') }}
                </label>
                <DatePicker
                  id="system_opening_cash_date"
                  v-model="systemOpeningForm.cash.date"
                  date-format="yy-mm-dd"
                  show-icon
                  class="w-full"
                />
              </div>

              <div class="app-field">
                <label for="system_opening_cash_amount" class="app-field__label">
                  {{ t('settings.system_opening_amount') }}
                </label>
                <InputNumber
                  id="system_opening_cash_amount"
                  v-model="systemOpeningForm.cash.amount"
                  mode="decimal"
                  :min-fraction-digits="2"
                  :max-fraction-digits="2"
                  class="w-full"
                />
              </div>

              <div class="app-field app-field--full">
                <label for="system_opening_cash_reference" class="app-field__label">
                  {{ t('settings.system_opening_reference') }}
                </label>
                <InputText
                  id="system_opening_cash_reference"
                  v-model="systemOpeningForm.cash.reference"
                  :placeholder="t('settings.system_opening_reference_placeholder')"
                  class="w-full"
                />
              </div>
            </div>
          </section>
        </div>

        <p v-if="systemOpeningDefaultDateLabel" class="settings-opening__default-date">
          {{ t('settings.system_opening_default_date', { date: systemOpeningDefaultDateLabel }) }}
        </p>

        <div class="app-form-actions">
          <Button
            type="button"
            :label="t('common.cancel')"
            severity="secondary"
            :disabled="systemOpeningSaving"
            @click="resetSystemOpening"
          />
          <Button
            type="submit"
            :label="t('settings.system_opening_save')"
            :loading="systemOpeningSaving"
            icon="pi pi-wallet"
          />
        </div>
      </AppPanel>
    </form>

    <Message v-if="systemOpeningSuccessMessage" severity="success" class="mt-4" :closable="true">
      {{ systemOpeningSuccessMessage }}
    </Message>
    <Message v-if="systemOpeningErrorMessage" severity="error" class="mt-4" :closable="true">
      {{ systemOpeningErrorMessage }}
    </Message>

    <AppPanel
      class="danger-panel"
      :title="t('settings.danger_zone')"
      :subtitle="t('settings.reset_db_desc')"
    >
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
        <section class="settings-selective-reset">
          <div class="settings-selective-reset__header">
            <h3 class="settings-selective-reset__title">
              {{ t('settings.selective_reset_title') }}
            </h3>
            <p class="settings-selective-reset__subtitle">
              {{ t('settings.selective_reset_subtitle') }}
            </p>
          </div>
          <p class="settings-selective-reset__hint">{{ t('settings.selective_reset_help') }}</p>

          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('settings.selective_reset_type') }}</label>
              <Select
                v-model="selectiveResetForm.importType"
                :options="selectiveResetImportTypeOptions"
                option-label="label"
                option-value="value"
                class="w-full"
              />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('settings.selective_reset_fiscal_year') }}</label>
              <Select
                v-model="selectiveResetForm.fiscalYearId"
                :options="selectiveResetFiscalYearOptions"
                option-label="label"
                option-value="value"
                class="w-full"
              />
            </div>
          </div>

          <div class="app-form-actions">
            <Button
              :label="t('settings.selective_reset_preview')"
              icon="pi pi-search"
              severity="secondary"
              outlined
              :loading="selectiveResetPreviewLoading"
              @click="previewSelectiveReset"
            />
            <Button
              :label="t('settings.selective_reset_apply')"
              icon="pi pi-trash"
              severity="danger"
              :disabled="!canApplySelectiveReset"
              :loading="selectiveResetApplying"
              @click="confirmSelectiveReset"
            />
          </div>

          <Message
            v-if="selectiveResetSuccessMessage"
            severity="success"
            class="mt-2"
            :closable="true"
          >
            {{ selectiveResetSuccessMessage }}
          </Message>
          <Message
            v-if="selectiveResetErrorMessage"
            severity="error"
            class="mt-2"
            :closable="true"
          >
            {{ selectiveResetErrorMessage }}
          </Message>

          <div v-if="selectiveResetPreview" class="settings-selective-reset__preview">
            <div class="settings-selective-reset__groups">
              <section>
                <h4>{{ t('settings.selective_reset_root_objects') }}</h4>
                <ul>
                  <li v-for="entry in selectiveResetRootEntries" :key="`root-${entry.key}`">
                    {{ selectiveResetObjectLabel(entry.key) }} : {{ entry.count }}
                  </li>
                </ul>
              </section>
              <section>
                <h4>{{ t('settings.selective_reset_derived_objects') }}</h4>
                <ul>
                  <li v-for="entry in selectiveResetDerivedEntries" :key="`derived-${entry.key}`">
                    {{ selectiveResetObjectLabel(entry.key) }} : {{ entry.count }}
                  </li>
                </ul>
              </section>
              <section>
                <h4>{{ t('settings.selective_reset_delete_plan') }}</h4>
                <ul>
                  <li v-for="entry in selectiveResetDeleteEntries" :key="`delete-${entry.key}`">
                    {{ selectiveResetObjectLabel(entry.key) }} : {{ entry.count }}
                  </li>
                </ul>
              </section>
            </div>
          </div>
        </section>
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
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import ConfirmDialog from 'primevue/confirmdialog'
import DatePicker from 'primevue/datepicker'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { useConfirm } from 'primevue/useconfirm'
import {
  applySelectiveResetApi,
  bootstrapAccountingApi,
  getSystemOpeningApi,
  getSettingsApi,
  previewSelectiveResetApi,
  resetDbApi,
  updateSystemOpeningApi,
  updateSettingsApi,
  type AppSettingsUpdate,
  type SelectiveResetImportType,
  type SelectiveResetPreview,
  type SystemOpening,
  type TreasurySystemOpening,
  type TreasurySystemOpeningUpdate,
} from '@/api/settings'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import { useFiscalYearStore } from '@/stores/fiscalYear'
import { useDarkMode } from '../composables/useDarkMode'

const { t } = useI18n()
const { isDark } = useDarkMode()
const fiscalYearStore = useFiscalYearStore()

const dangerHeaderBg = computed(() => (isDark.value ? 'rgba(239,68,68,0.08)' : 'var(--p-red-50)'))
const dangerBorderColor = computed(() =>
  isDark.value ? 'rgba(239,68,68,0.25)' : 'var(--p-red-200)',
)
const dangerTitleColor = computed(() => (isDark.value ? 'var(--p-red-400)' : 'var(--p-red-600)'))

interface SettingsForm {
  association_name: string
  association_address: string
  association_siret: string
  fiscal_year_start_month: number
  default_invoice_due_days: number | null
  smtp_host: string | null
  smtp_port: number
  smtp_user: string | null
  smtp_password: string | null
  smtp_from_email: string | null
  smtp_use_tls: boolean
}

interface SystemOpeningFormValue {
  configured: boolean
  date: Date | null
  amount: number | null
  reference: string
}

interface TreasurySystemOpeningForm {
  bank: SystemOpeningFormValue
  cash: SystemOpeningFormValue
}

interface SelectiveResetForm {
  importType: SelectiveResetImportType
  fiscalYearId: number | null
}

const defaultForm = (): SettingsForm => ({
  association_name: '',
  association_address: '',
  association_siret: '',
  fiscal_year_start_month: 8,
  default_invoice_due_days: null,
  smtp_host: null,
  smtp_port: 587,
  smtp_user: null,
  smtp_password: null,
  smtp_from_email: null,
  smtp_use_tls: true,
})

const defaultSystemOpeningForm = (): TreasurySystemOpeningForm => ({
  bank: {
    configured: false,
    date: null,
    amount: null,
    reference: '',
  },
  cash: {
    configured: false,
    date: null,
    amount: null,
    reference: '',
  },
})

const confirm = useConfirm()
const form = ref<SettingsForm>(defaultForm())
const systemOpeningForm = ref<TreasurySystemOpeningForm>(defaultSystemOpeningForm())
const loading = ref(false)
const resetting = ref(false)
const bootstrapping = ref(false)
const systemOpeningSaving = ref(false)
const systemOpeningDefaultDate = ref<string | null>(null)
const successMessage = ref('')
const errorMessage = ref('')
const resetMessage = ref('')
const bootstrapMessage = ref('')
const systemOpeningSuccessMessage = ref('')
const systemOpeningErrorMessage = ref('')
const selectiveResetForm = ref<SelectiveResetForm>({
  importType: 'gestion',
  fiscalYearId: null,
})
const selectiveResetPreview = ref<SelectiveResetPreview | null>(null)
const selectiveResetPreviewLoading = ref(false)
const selectiveResetApplying = ref(false)
const selectiveResetSuccessMessage = ref('')
const selectiveResetErrorMessage = ref('')

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
const selectiveResetImportTypeOptions = computed(() => [
  { label: t('settings.selective_reset_import_type_gestion'), value: 'gestion' },
  { label: t('settings.selective_reset_import_type_comptabilite'), value: 'comptabilite' },
])
const selectiveResetFiscalYearOptions = computed(() =>
  fiscalYearStore.fiscalYears.map((fiscalYear) => ({
    label: fiscalYear.name,
    value: fiscalYear.id,
  })),
)
const selectiveResetRootEntries = computed(() =>
  Object.entries(selectiveResetPreview.value?.root_objects ?? {}).map(([key, count]) => ({ key, count })),
)
const selectiveResetDerivedEntries = computed(() =>
  Object.entries(selectiveResetPreview.value?.derived_objects ?? {}).map(([key, count]) => ({ key, count })),
)
const selectiveResetDeleteEntries = computed(() =>
  Object.entries(selectiveResetPreview.value?.delete_plan ?? {}).map(([key, count]) => ({ key, count })),
)
const canApplySelectiveReset = computed(
  () =>
    selectiveResetPreview.value !== null &&
    selectiveResetPreviewLoading.value === false &&
    selectiveResetDeleteEntries.value.length > 0,
)
const systemOpeningDefaultDateLabel = computed(() =>
  systemOpeningDefaultDate.value
    ? systemOpeningDefaultDate.value.split('-').reverse().join('/')
    : '',
)

function selectiveResetObjectLabel(key: string): string {
  return t(`settings.selective_reset_object_${key}`)
}

function toIsoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function fromIsoDate(value: string | null): Date | null {
  if (!value) {
    return null
  }

  const [year = 1970, month = 1, day = 1] = value.split('-').map(Number)
  return new Date(year, month - 1, day, 12)
}

function toSystemOpeningFormValue(
  data: SystemOpening,
  defaultDate: string | null,
): SystemOpeningFormValue {
  return {
    configured: data.configured,
    date: fromIsoDate(data.date ?? defaultDate),
    amount: data.amount !== null ? Number(data.amount) : null,
    reference: data.reference ?? '',
  }
}

function applySystemOpening(data: TreasurySystemOpening): void {
  systemOpeningDefaultDate.value = data.default_date
  systemOpeningForm.value = {
    bank: toSystemOpeningFormValue(data.bank, data.default_date),
    cash: toSystemOpeningFormValue(data.cash, data.default_date),
  }
}

async function loadSystemOpening(): Promise<void> {
  try {
    const data = await getSystemOpeningApi()
    applySystemOpening(data)
  } catch {
    systemOpeningErrorMessage.value = t('settings.system_opening_load_error')
  }
}

async function load(): Promise<void> {
  try {
    const data = await getSettingsApi()
    form.value = {
      association_name: data.association_name,
      association_address: data.association_address,
      association_siret: data.association_siret,
      fiscal_year_start_month: data.fiscal_year_start_month,
      default_invoice_due_days: data.default_invoice_due_days,
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
      default_invoice_due_days: form.value.default_invoice_due_days,
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

function resetSystemOpening(): void {
  void loadSystemOpening()
}

function buildSystemOpeningPayload(): TreasurySystemOpeningUpdate | null {
  const bank = systemOpeningForm.value.bank
  const cash = systemOpeningForm.value.cash

  if (!bank.date || bank.amount === null || !cash.date || cash.amount === null) {
    systemOpeningErrorMessage.value = t('settings.system_opening_validation_error')
    return null
  }

  if (bank.amount === 0 || cash.amount === 0) {
    systemOpeningErrorMessage.value = t('settings.system_opening_zero_error')
    return null
  }

  return {
    bank: {
      date: toIsoDate(bank.date),
      amount: bank.amount.toFixed(2),
      reference: bank.reference.trim() || null,
    },
    cash: {
      date: toIsoDate(cash.date),
      amount: cash.amount.toFixed(2),
      reference: cash.reference.trim() || null,
    },
  }
}

async function saveSystemOpening(): Promise<void> {
  systemOpeningSaving.value = true
  systemOpeningSuccessMessage.value = ''
  systemOpeningErrorMessage.value = ''

  const payload = buildSystemOpeningPayload()
  if (!payload) {
    systemOpeningSaving.value = false
    return
  }

  try {
    const data = await updateSystemOpeningApi(payload)
    applySystemOpening(data)
    systemOpeningSuccessMessage.value = t('settings.system_opening_saved')
  } catch {
    systemOpeningErrorMessage.value = t('settings.system_opening_save_error')
  } finally {
    systemOpeningSaving.value = false
  }
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

function buildSelectiveResetPayload(): { import_type: SelectiveResetImportType; fiscal_year_id: number } | null {
  if (selectiveResetForm.value.fiscalYearId === null) {
    selectiveResetErrorMessage.value = t('settings.selective_reset_missing_fiscal_year')
    return null
  }

  return {
    import_type: selectiveResetForm.value.importType,
    fiscal_year_id: selectiveResetForm.value.fiscalYearId,
  }
}

async function previewSelectiveReset(): Promise<void> {
  selectiveResetPreviewLoading.value = true
  selectiveResetSuccessMessage.value = ''
  selectiveResetErrorMessage.value = ''

  const payload = buildSelectiveResetPayload()
  if (!payload) {
    selectiveResetPreviewLoading.value = false
    return
  }

  try {
    const preview = await previewSelectiveResetApi(payload)
    selectiveResetPreview.value = preview
    selectiveResetSuccessMessage.value =
      Object.keys(preview.delete_plan).length > 0
        ? t('settings.selective_reset_preview_ready', {
            type: t(`settings.selective_reset_import_type_${preview.import_type}`),
            year: preview.fiscal_year_name,
          })
        : t('settings.selective_reset_preview_empty')
  } catch {
    selectiveResetErrorMessage.value = t('settings.selective_reset_error')
  } finally {
    selectiveResetPreviewLoading.value = false
  }
}

function confirmSelectiveReset(): void {
  confirm.require({
    message: t('settings.selective_reset_confirm'),
    header: t('settings.selective_reset_confirm_header'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('settings.selective_reset_apply_yes') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: applySelectiveReset,
  })
}

async function applySelectiveReset(): Promise<void> {
  selectiveResetApplying.value = true
  selectiveResetSuccessMessage.value = ''
  selectiveResetErrorMessage.value = ''

  const payload = buildSelectiveResetPayload()
  if (!payload) {
    selectiveResetApplying.value = false
    return
  }

  try {
    const result = await applySelectiveResetApi(payload)
    selectiveResetPreview.value = result
    const deletedCount = Object.values(result.delete_plan).reduce((sum, value) => sum + value, 0)
    selectiveResetSuccessMessage.value = t('settings.selective_reset_done', {
      count: deletedCount,
      type: t(`settings.selective_reset_import_type_${result.import_type}`),
      year: result.fiscal_year_name,
    })
  } catch {
    selectiveResetErrorMessage.value = t('settings.selective_reset_error')
  } finally {
    selectiveResetApplying.value = false
  }
}

watch(
  () => [selectiveResetForm.value.importType, selectiveResetForm.value.fiscalYearId],
  () => {
    selectiveResetPreview.value = null
    selectiveResetSuccessMessage.value = ''
    selectiveResetErrorMessage.value = ''
  },
)

onMounted(() => {
  void Promise.all([load(), loadSystemOpening(), fiscalYearStore.initialize()]).then(() => {
    selectiveResetForm.value.fiscalYearId =
      fiscalYearStore.selectedFiscalYearId ?? fiscalYearStore.fiscalYears[0]?.id ?? null
  })
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

.settings-opening__hint,
.settings-opening__default-date {
  margin: 0;
  color: var(--app-text-muted);
}

.settings-opening-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--app-space-4);
}

.settings-opening-card {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
  padding: var(--app-space-4);
  border: 1px solid var(--app-border-subtle);
  border-radius: var(--app-radius-lg);
  background: var(--app-surface-subtle);
}

.settings-opening-card__header {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-3);
  align-items: flex-start;
}

.settings-opening-card__title,
.settings-opening-card__subtitle {
  margin: 0;
}

.settings-opening-card__title {
  font-size: 1rem;
}

.settings-opening-card__subtitle {
  margin-top: var(--app-space-1);
  color: var(--app-text-muted);
}

.settings-danger {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.settings-selective-reset {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border: 1px solid var(--app-border-subtle);
  border-radius: var(--app-radius-lg);
  background: var(--app-surface-subtle);
}

.settings-selective-reset__header,
.settings-selective-reset__title,
.settings-selective-reset__subtitle {
  margin: 0;
}

.settings-selective-reset__subtitle,
.settings-selective-reset__hint {
  color: var(--app-text-muted);
}

.settings-selective-reset__preview {
  border-top: 1px solid var(--app-border-subtle);
  padding-top: var(--app-space-3);
}

.settings-selective-reset__groups {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--app-space-4);
}

.settings-selective-reset__groups h4,
.settings-selective-reset__groups ul {
  margin: 0;
}

.settings-selective-reset__groups ul {
  padding-left: 1rem;
}

.danger-panel :deep(.app-panel__header) {
  background-color: v-bind(dangerHeaderBg);
  border-bottom: 1px solid v-bind(dangerBorderColor);
}

.danger-panel :deep(.app-panel__title) {
  color: v-bind(dangerTitleColor);
  font-weight: 600;
}

@media (max-width: 767px) {
  .settings-opening-grid {
    grid-template-columns: 1fr;
  }

  .settings-selective-reset__groups {
    grid-template-columns: 1fr;
  }

  .settings-opening-card__header {
    flex-direction: column;
  }
}
</style>
