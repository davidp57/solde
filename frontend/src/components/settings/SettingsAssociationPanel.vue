<template>
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

        <div class="app-field">
          <label for="client_invoice_seq_digits" class="app-field__label">
            {{ t('settings.client_invoice_seq_digits') }}
          </label>
          <InputNumber
            id="client_invoice_seq_digits"
            v-model="form.client_invoice_seq_digits"
            :min="2"
            :max="6"
            :use-grouping="false"
            show-buttons
            class="w-full"
          />
          <small class="app-field__hint app-field__hint--warning">
            <i class="pi pi-exclamation-triangle" />
            {{ t('settings.client_invoice_seq_digits_help') }}
          </small>
        </div>

        <div class="app-field">
          <label for="client_invoice_number_template" class="app-field__label">
            {{ t('settings.client_invoice_number_template') }}
          </label>
          <InputText
            id="client_invoice_number_template"
            v-model="form.client_invoice_number_template"
            class="w-full"
            :placeholder="t('settings.client_invoice_number_template_placeholder')"
          />
          <small class="app-field__hint app-field__hint--warning">
            <i class="pi pi-exclamation-triangle" />
            {{ t('settings.client_invoice_number_template_help') }}
          </small>
        </div>

        <div class="app-field">
          <label for="supplier_invoice_number_template" class="app-field__label">
            {{ t('settings.supplier_invoice_number_template') }}
          </label>
          <InputText
            id="supplier_invoice_number_template"
            v-model="form.supplier_invoice_number_template"
            class="w-full"
            :placeholder="t('settings.supplier_invoice_number_template_placeholder')"
          />
          <small class="app-field__hint app-field__hint--warning">
            <i class="pi pi-exclamation-triangle" />
            {{ t('settings.supplier_invoice_number_template_help') }}
          </small>
        </div>
      </div>
    </AppPanel>

    <AppPanel
      :title="t('settings.section_default_prices')"
      :subtitle="t('settings.section_default_prices_subtitle')"
    >
      <div class="app-form-grid">
        <div class="app-field">
          <label for="default_price_cours" class="app-field__label">
            {{ t('settings.default_price_cours') }}
          </label>
          <InputNumber
            id="default_price_cours"
            v-model="form.default_price_cours"
            :min="0"
            :max-fraction-digits="2"
            :min-fraction-digits="2"
            suffix=" €"
            class="w-full"
          />
          <small class="app-field__hint">{{ t('settings.default_price_help') }}</small>
        </div>

        <div class="app-field">
          <label for="default_price_adhesion" class="app-field__label">
            {{ t('settings.default_price_adhesion') }}
          </label>
          <InputNumber
            id="default_price_adhesion"
            v-model="form.default_price_adhesion"
            :min="0"
            :max-fraction-digits="2"
            :min-fraction-digits="2"
            suffix=" €"
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="default_price_autres" class="app-field__label">
            {{ t('settings.default_price_autres') }}
          </label>
          <InputNumber
            id="default_price_autres"
            v-model="form.default_price_autres"
            :min="0"
            :max-fraction-digits="2"
            :min-fraction-digits="2"
            suffix=" €"
            class="w-full"
          />
        </div>
      </div>
    </AppPanel>

    <AppPanel
      :title="t('settings.section_payment')"
      :subtitle="t('settings.section_payment_subtitle')"
    >
      <div class="app-form-grid">
        <div class="app-field">
          <label for="payment_iban" class="app-field__label">{{ t('settings.payment_iban') }}</label>
          <InputText
            id="payment_iban"
            v-model="form.payment_iban"
            :placeholder="t('settings.payment_iban_placeholder')"
            class="w-full"
          />
        </div>
        <div class="app-field">
          <label for="payment_bic" class="app-field__label">{{ t('settings.payment_bic') }}</label>
          <InputText
            id="payment_bic"
            v-model="form.payment_bic"
            :placeholder="t('settings.payment_bic_placeholder')"
            class="w-full"
          />
        </div>
        <div class="app-field app-field--full">
          <label for="payment_check_payee" class="app-field__label">{{ t('settings.payment_check_payee') }}</label>
          <InputText
            id="payment_check_payee"
            v-model="form.payment_check_payee"
            :placeholder="t('settings.payment_check_payee_placeholder')"
            class="w-full"
          />
          <small class="app-field__hint">{{ t('settings.payment_instructions_help') }}</small>
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
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import { getSettingsApi, updateSettingsApi } from '@/api/settings'
import AppPanel from '@/components/ui/AppPanel.vue'

const { t } = useI18n()

interface AssociationForm {
  association_name: string
  association_address: string
  association_siret: string
  fiscal_year_start_month: number
  default_invoice_due_days: number | null
  client_invoice_seq_digits: number
  client_invoice_number_template: string
  supplier_invoice_number_template: string
  default_price_cours: number | null
  default_price_adhesion: number | null
  default_price_autres: number | null
  payment_iban: string
  payment_bic: string
  payment_check_payee: string
}

const monthFormatter = new Intl.DateTimeFormat('fr-FR', { month: 'long' })
const monthOptions = Array.from({ length: 12 }, (_, i) => {
  const label = monthFormatter.format(new Date(2000, i, 1))
  return { label: label.charAt(0).toUpperCase() + label.slice(1), value: i + 1 }
})

const defaultForm = (): AssociationForm => ({
  association_name: '',
  association_address: '',
  association_siret: '',
  fiscal_year_start_month: 8,
  default_invoice_due_days: null,
  client_invoice_seq_digits: 3,
  client_invoice_number_template: '{year}-{seq}',
  supplier_invoice_number_template: 'FF-%Y%m%d%H.%M.%S',
  default_price_cours: null,
  default_price_adhesion: null,
  default_price_autres: null,
  payment_iban: '',
  payment_bic: '',
  payment_check_payee: '',
})

const form = ref<AssociationForm>(defaultForm())
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

async function load(): Promise<void> {
  try {
    const data = await getSettingsApi()
    form.value = {
      association_name: data.association_name,
      association_address: data.association_address,
      association_siret: data.association_siret,
      fiscal_year_start_month: data.fiscal_year_start_month,
      default_invoice_due_days: data.default_invoice_due_days,
      client_invoice_seq_digits: data.client_invoice_seq_digits,
      client_invoice_number_template: data.client_invoice_number_template,
      supplier_invoice_number_template: data.supplier_invoice_number_template,
      default_price_cours: data.default_price_cours,
      default_price_adhesion: data.default_price_adhesion,
      default_price_autres: data.default_price_autres,
      payment_iban: data.payment_iban ?? '',
      payment_bic: data.payment_bic ?? '',
      payment_check_payee: data.payment_check_payee ?? '',
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
    await updateSettingsApi({
      association_name: form.value.association_name,
      association_address: form.value.association_address,
      association_siret: form.value.association_siret,
      fiscal_year_start_month: form.value.fiscal_year_start_month,
      default_invoice_due_days: form.value.default_invoice_due_days,
      client_invoice_seq_digits: form.value.client_invoice_seq_digits,
      client_invoice_number_template: form.value.client_invoice_number_template,
      supplier_invoice_number_template: form.value.supplier_invoice_number_template,
      default_price_cours: form.value.default_price_cours,
      default_price_adhesion: form.value.default_price_adhesion,
      default_price_autres: form.value.default_price_autres,
      payment_iban: form.value.payment_iban || null,
      payment_bic: form.value.payment_bic || null,
      payment_check_payee: form.value.payment_check_payee || null,
    })
    successMessage.value = t('settings.saved')
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
</style>
