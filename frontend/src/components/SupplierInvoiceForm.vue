<template>
  <form class="app-dialog-form" @submit.prevent="submit">
    <section class="app-dialog-intro">
      <p class="app-dialog-intro__eyebrow">{{ t('invoices.supplier.title') }}</p>
      <p class="app-dialog-intro__text">
        {{
          t(isEditing ? 'invoices.supplier.form_intro_edit' : 'invoices.supplier.form_intro_create')
        }}
      </p>
    </section>

    <section class="app-dialog-section">
      <div class="app-dialog-section__header">
        <h3 class="app-dialog-section__title">{{ t('invoices.supplier.identity_title') }}</h3>
        <p class="app-dialog-section__copy">{{ t('invoices.supplier.identity_subtitle') }}</p>
      </div>
      <div class="supplier-invoice-form">
        <div class="app-field">
          <label class="app-field__label">{{ t('invoices.contact') }}</label>
          <Select
            v-model="form.contact_id"
            :options="contactOptions"
            option-label="displayName"
            option-value="id"
            :placeholder="t('invoices.contact_placeholder')"
            filter
            class="w-full"
            required
          />
        </div>

        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('invoices.date') }}</label>
            <DatePicker v-model="form.date" date-format="dd/mm/yy" class="w-full" required />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('invoices.due_date') }}</label>
            <DatePicker v-model="form.due_date" date-format="dd/mm/yy" class="w-full" show-clear />
          </div>
        </div>

        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('invoices.reference') }}</label>
            <InputText
              v-model="form.reference"
              :placeholder="t('invoices.reference_placeholder')"
              class="w-full"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('invoices.total') }} €</label>
            <InputNumber
              v-model="form.total_amount"
              :min="0"
              :max-fraction-digits="2"
              class="w-full"
              required
            />
          </div>
        </div>
      </div>
    </section>

    <section class="app-dialog-section">
      <div class="app-dialog-section__header">
        <h3 class="app-dialog-section__title">{{ t('invoices.supplier.details_title') }}</h3>
        <p class="app-dialog-section__copy">{{ t('invoices.supplier.details_subtitle') }}</p>
      </div>
      <div class="app-field">
        <label class="app-field__label">{{ t('invoices.description') }}</label>
        <Textarea v-model="form.description" rows="2" class="w-full" auto-resize />
      </div>
    </section>

    <div class="app-form-actions">
      <Button
        :label="t('common.cancel')"
        severity="secondary"
        type="button"
        outlined
        @click="emit('cancel')"
      />
      <Button :label="t('common.save')" type="submit" :loading="saving" />
    </div>
  </form>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Contact } from '../api/contacts'
import { createInvoiceApi, updateInvoiceApi, type Invoice } from '../api/invoices'
import { getSettingsApi } from '../api/settings'
import { formatContactDisplayName } from '../utils/contact'

const props = defineProps<{
  invoice: Invoice | null
  contacts: Contact[]
}>()
const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const { t } = useI18n()
const toast = useToast()
const saving = ref(false)
const isEditing = computed(() => props.invoice !== null)
const defaultInvoiceDueDays = ref<number | null>(null)
const suggestedDueDateIso = ref<string | null>(null)

interface FormState {
  contact_id: number | null
  date: Date | null
  due_date: Date | null
  reference: string
  total_amount: number | null
  description: string
}

const form = reactive<FormState>({
  contact_id: null,
  date: null,
  due_date: null,
  reference: '',
  total_amount: null,
  description: '',
})

const contactOptions = computed(() =>
  props.contacts.map((contact) => ({
    ...contact,
    displayName: formatContactDisplayName(contact),
  })),
)

function resetForm() {
  form.contact_id = null
  form.date = null
  form.due_date = null
  form.reference = ''
  form.total_amount = null
  form.description = ''
  suggestedDueDateIso.value = null
}

function setFromInvoice(inv: Invoice) {
  form.contact_id = inv.contact_id
  form.date = new Date(inv.date)
  form.due_date = inv.due_date ? new Date(inv.due_date) : null
  form.reference = inv.reference ?? ''
  form.total_amount = parseFloat(inv.total_amount)
  form.description = inv.description ?? ''
  suggestedDueDateIso.value = inv.due_date
}

watch(
  () => props.invoice,
  (inv) => {
    if (inv) setFromInvoice(inv)
    else resetForm()
  },
  { immediate: true },
)

function toIsoDate(value: Date | null): string | null {
  if (!value) {
    return null
  }
  return value.toISOString().slice(0, 10)
}

function addDays(value: Date, days: number): Date {
  const next = new Date(value)
  next.setDate(next.getDate() + days)
  return next
}

function applySuggestedDueDate(): void {
  if (isEditing.value || !form.date || defaultInvoiceDueDays.value === null) {
    return
  }
  const currentDueDateIso = toIsoDate(form.due_date)
  if (form.due_date !== null && currentDueDateIso !== suggestedDueDateIso.value) {
    return
  }
  form.due_date = addDays(form.date, defaultInvoiceDueDays.value)
  suggestedDueDateIso.value = toIsoDate(form.due_date)
}

watch(
  () => [form.date, defaultInvoiceDueDays.value] as const,
  () => {
    applySuggestedDueDate()
  },
)

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

async function submit() {
  if (!form.contact_id || !form.date || form.total_amount === null) return
  saving.value = true
  try {
    const payload = {
      type: 'fournisseur' as const,
      contact_id: form.contact_id,
      date: formatDate(form.date),
      due_date: form.due_date ? formatDate(form.due_date) : null,
      reference: form.reference || null,
      total_amount: String(form.total_amount),
      description: form.description || null,
    }
    if (props.invoice) {
      await updateInvoiceApi(props.invoice.id, payload)
    } else {
      await createInvoiceApi(payload)
    }
    emit('saved')
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    saving.value = false
  }
}

void getSettingsApi()
  .then((settings) => {
    defaultInvoiceDueDays.value = settings.default_invoice_due_days
    applySuggestedDueDate()
  })
  .catch(() => {
    defaultInvoiceDueDays.value = null
  })
</script>

<style scoped>
.supplier-invoice-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-5);
}
</style>
