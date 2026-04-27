<template>
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
                form.bank.configured
                  ? t('settings.system_opening_status_configured')
                  : t('settings.system_opening_status_pending')
              "
              :severity="form.bank.configured ? 'success' : 'warn'"
            />
          </div>

          <div class="app-form-grid">
            <div class="app-field">
              <label for="system_opening_bank_date" class="app-field__label">
                {{ t('settings.system_opening_date') }}
              </label>
              <AppDatePicker
                id="system_opening_bank_date"
                v-model="form.bank.date"
                class="w-full"
              />
            </div>

            <div class="app-field">
              <label for="system_opening_bank_amount" class="app-field__label">
                {{ t('settings.system_opening_amount') }}
              </label>
              <InputNumber
                id="system_opening_bank_amount"
                v-model="form.bank.amount"
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
                v-model="form.bank.reference"
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
                form.cash.configured
                  ? t('settings.system_opening_status_configured')
                  : t('settings.system_opening_status_pending')
              "
              :severity="form.cash.configured ? 'success' : 'warn'"
            />
          </div>

          <div class="app-form-grid">
            <div class="app-field">
              <label for="system_opening_cash_date" class="app-field__label">
                {{ t('settings.system_opening_date') }}
              </label>
              <AppDatePicker
                id="system_opening_cash_date"
                v-model="form.cash.date"
                class="w-full"
              />
            </div>

            <div class="app-field">
              <label for="system_opening_cash_amount" class="app-field__label">
                {{ t('settings.system_opening_amount') }}
              </label>
              <InputNumber
                id="system_opening_cash_amount"
                v-model="form.cash.amount"
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
                v-model="form.cash.reference"
                :placeholder="t('settings.system_opening_reference_placeholder')"
                class="w-full"
              />
            </div>
          </div>
        </section>
      </div>

      <p v-if="defaultDateLabel" class="settings-opening__default-date">
        {{ t('settings.system_opening_default_date', { date: defaultDateLabel }) }}
      </p>

      <div class="app-form-actions">
        <Button
          type="button"
          :label="t('common.cancel')"
          severity="secondary"
          :disabled="saving"
          @click="cancel"
        />
        <Button
          type="submit"
          :label="t('settings.system_opening_save')"
          :loading="saving"
          icon="pi pi-wallet"
        />
      </div>
    </AppPanel>
  </form>

  <Message v-if="successMessage" severity="success" class="mt-4" :closable="true">
    {{ successMessage }}
  </Message>
  <Message v-if="errorMessage" severity="error" class="mt-4" :closable="true">
    {{ errorMessage }}
  </Message>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import AppDatePicker from '@/components/ui/AppDatePicker.vue'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import {
  getSystemOpeningApi,
  updateSystemOpeningApi,
  type SystemOpening,
  type TreasurySystemOpening,
  type TreasurySystemOpeningUpdate,
} from '@/api/settings'
import AppPanel from '@/components/ui/AppPanel.vue'

const { t } = useI18n()

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

const defaultForm = (): TreasurySystemOpeningForm => ({
  bank: { configured: false, date: null, amount: null, reference: '' },
  cash: { configured: false, date: null, amount: null, reference: '' },
})

const form = ref<TreasurySystemOpeningForm>(defaultForm())
const saving = ref(false)
const defaultDate = ref<string | null>(null)
const successMessage = ref('')
const errorMessage = ref('')

const defaultDateLabel = computed(() =>
  defaultDate.value ? defaultDate.value.split('-').reverse().join('/') : '',
)

function toIsoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function fromIsoDate(value: string | null): Date | null {
  if (!value) return null
  const [year = 1970, month = 1, day = 1] = value.split('-').map(Number)
  return new Date(year, month - 1, day, 12)
}

function toFormValue(data: SystemOpening, fallbackDate: string | null): SystemOpeningFormValue {
  return {
    configured: data.configured,
    date: fromIsoDate(data.date ?? fallbackDate),
    amount: data.amount !== null ? Number(data.amount) : null,
    reference: data.reference ?? '',
  }
}

function applyData(data: TreasurySystemOpening): void {
  defaultDate.value = data.default_date
  form.value = {
    bank: toFormValue(data.bank, data.default_date),
    cash: toFormValue(data.cash, data.default_date),
  }
}

async function load(): Promise<void> {
  try {
    const data = await getSystemOpeningApi()
    applyData(data)
  } catch {
    errorMessage.value = t('settings.system_opening_load_error')
  }
}

function buildPayload(): TreasurySystemOpeningUpdate | null {
  const { bank, cash } = form.value
  if (!bank.date || bank.amount === null || !cash.date || cash.amount === null) {
    errorMessage.value = t('settings.system_opening_validation_error')
    return null
  }
  if (bank.amount === 0 || cash.amount === 0) {
    errorMessage.value = t('settings.system_opening_zero_error')
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
  saving.value = true
  successMessage.value = ''
  errorMessage.value = ''
  const payload = buildPayload()
  if (!payload) {
    saving.value = false
    return
  }
  try {
    const data = await updateSystemOpeningApi(payload)
    applyData(data)
    successMessage.value = t('settings.system_opening_saved')
  } catch {
    errorMessage.value = t('settings.system_opening_save_error')
  } finally {
    saving.value = false
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

@media (max-width: 767px) {
  .settings-opening-grid {
    grid-template-columns: 1fr;
  }

  .settings-opening-card__header {
    flex-direction: column;
  }
}
</style>
