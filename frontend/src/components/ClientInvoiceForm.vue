<template>
  <form class="app-dialog-form" @submit.prevent="submit">
    <section class="app-dialog-intro">
      <p class="app-dialog-intro__eyebrow">{{ t('invoices.client.title') }}</p>
      <p class="app-dialog-intro__text">
        {{ t(isEditing ? 'invoices.client.form_intro_edit' : 'invoices.client.form_intro_create') }}
      </p>
      <p v-if="!isEditing && nextNumber" class="app-dialog-intro__number-preview">
        {{ t('invoices.client.next_number_preview', { number: nextNumber }) }}
      </p>
    </section>

    <section class="app-dialog-section">
      <div class="app-dialog-section__header">
        <h3 class="app-dialog-section__title">{{ t('invoices.client.identity_title') }}</h3>
        <p class="app-dialog-section__copy">{{ t('invoices.client.identity_subtitle') }}</p>
      </div>
      <div class="invoice-form">
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
          <small v-if="fieldErrors['contact_id']" class="p-error">{{ fieldErrors['contact_id'] }}</small>
        </div>

        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('invoices.date') }}</label>
            <AppDatePicker v-model="form.date" class="w-full" required />
            <small v-if="fieldErrors['date']" class="p-error">{{ fieldErrors['date'] }}</small>
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('invoices.due_date') }}</label>
            <AppDatePicker v-model="form.due_date" class="w-full" show-clear />
          </div>
        </div>

        <div class="app-field">
          <label class="app-field__label">{{ t('invoices.description') }}</label>
          <InputText v-model="form.description" class="w-full" />
        </div>
      </div>
    </section>

    <section class="invoice-form__lines app-dialog-section">
      <div class="app-dialog-section__header">
        <h3 class="app-dialog-section__title">{{ t('invoices.client.lines_title') }}</h3>
        <p class="app-dialog-section__copy">{{ t('invoices.client.lines_subtitle') }}</p>
      </div>
      <div class="invoice-form__lines-header">
        <label class="app-field__label">{{ t('invoices.lines') }}</label>
        <Button
          :label="t('invoices.add_line')"
          icon="pi pi-plus"
          size="small"
          type="button"
          severity="secondary"
          @click="addLine"
        />
      </div>
      <div v-for="(line, idx) in form.lines" :key="idx" class="invoice-form__line-row">
        <Select
          v-model="line.line_type"
          :options="lineTypeOptions"
          option-label="label"
          option-value="value"
          :placeholder="t('invoices.client.line_type')"
          class="invoice-form__type"
          @update:model-value="onLineTypeChange(line)"
        />
        <InputText
          v-model="line.description"
          :placeholder="t('invoices.line_description')"
          class="invoice-form__description"
        />
        <InputNumber
          v-model="line.quantity"
          :placeholder="t('invoices.line_qty')"
          :min="0"
          :max-fraction-digits="3"
          class="invoice-form__quantity"
        />
        <InputNumber
          v-model="line.unit_price"
          :placeholder="t('invoices.line_price')"
          :max-fraction-digits="2"
          class="invoice-form__price"
          suffix=" €"
        />
        <span class="invoice-form__total"> {{ lineAmount(line) }} € </span>
        <Button
          icon="pi pi-trash"
          size="small"
          severity="danger"
          text
          type="button"
          class="invoice-form__remove"
          @click="removeLine(idx)"
        />
      </div>
      <div class="invoice-form__grand-total">{{ t('invoices.total') }}: {{ computedTotal }} €</div>
      <p v-if="hasNegativeTotal" class="invoice-form__error">
        {{ t('invoices.client.negative_total_error') }}
      </p>
    </section>

    <div class="app-form-actions">
      <Button
        :label="t('common.cancel')"
        severity="secondary"
        type="button"
        outlined
        @click="emit('cancel')"
      />
      <Button :label="t('common.save')" type="submit" :loading="saving" :disabled="saveDisabled" />
    </div>
  </form>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import AppDatePicker from './ui/AppDatePicker.vue'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import axios from 'axios'
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Contact } from '../api/contacts'
import { getSettingsApi } from '../api/settings'
import {
  createInvoiceApi,
  getNextClientInvoiceNumberApi,
  updateInvoiceApi,
  type Invoice,
  type InvoiceLineType,
} from '../api/invoices'
import { formatContactDisplayName } from '../utils/contact'

const props = defineProps<{
  invoice: Invoice | null
  contacts: Contact[]
}>()
const emit = defineEmits<{
  saved: [invoice: Invoice]
  cancel: []
}>()

const { t } = useI18n()
const toast = useToast()
const saving = ref(false)
const fieldErrors = ref<Record<string, string>>({})
const initialSnapshot = ref('')
const isEditing = computed(() => props.invoice !== null)
const defaultInvoiceDueDays = ref<number | null>(null)
const suggestedDueDateIso = ref<string | null>(null)
const defaultPrices = ref<Record<string, number | null>>({
  cours: null,
  adhesion: null,
  autres: null,
})
const nextNumber = ref<string | null>(null)

interface LineForm {
  line_type: InvoiceLineType | null
  description: string
  quantity: number
  unit_price: number
}

interface FormState {
  contact_id: number | null
  date: Date | null
  due_date: Date | null
  description: string
  lines: LineForm[]
}

const form = reactive<FormState>({
  contact_id: null,
  date: null,
  due_date: null,
  description: '',
  lines: [],
})

function formSnapshot(): string {
  return JSON.stringify({
    contact_id: form.contact_id,
    date: form.date?.toISOString().slice(0, 10) ?? null,
    due_date: form.due_date?.toISOString().slice(0, 10) ?? null,
    description: form.description,
    lines: form.lines.map((l) => ({ ...l })),
  })
}

const isDirty = computed(() => formSnapshot() !== initialSnapshot.value)

const lineTypeOptions = [
  { label: t('invoices.client.line_types.cours'), value: 'cours' },
  { label: t('invoices.client.line_types.adhesion'), value: 'adhesion' },
  { label: t('invoices.client.line_types.autres'), value: 'autres' },
]

const contactOptions = computed(() =>
  props.contacts.map((contact) => ({
    ...contact,
    displayName: formatContactDisplayName(contact),
  })),
)

const defaultLineDescriptions: Record<InvoiceLineType, string> = {
  cours: 'Cours de soutien',
  adhesion: 'Adhesion annuelle',
  autres: 'Autres prestations',
}

function lineAmount(line: LineForm): string {
  return ((line.quantity || 0) * (line.unit_price || 0)).toFixed(2)
}

const computedTotal = computed(() =>
  form.lines.reduce((sum, l) => sum + (l.quantity || 0) * (l.unit_price || 0), 0).toFixed(2),
)

const hasNegativeTotal = computed(
  () => form.lines.reduce((sum, l) => sum + (l.quantity || 0) * (l.unit_price || 0), 0) < 0,
)

const saveDisabled = computed(
  () =>
    saving.value ||
    !form.contact_id ||
    !form.date ||
    form.lines.length === 0 ||
    hasNegativeTotal.value ||
    form.lines.some((line) => !line.description.trim() || !line.line_type),
)

function inferLineType(description: string, label: Invoice['label']): InvoiceLineType {
  const normalizedDescription = description.toLocaleLowerCase('fr-FR')
  if (normalizedDescription.includes('adhesion')) return 'adhesion'
  if (normalizedDescription.includes('cours') || normalizedDescription.includes('soutien')) {
    return 'cours'
  }
  if (label === 'cs') return 'cours'
  if (label === 'a') return 'adhesion'
  return 'autres'
}

function onLineTypeChange(line: LineForm) {
  if (!line.line_type) return
  if (
    !line.description.trim() ||
    Object.values(defaultLineDescriptions).includes(line.description)
  ) {
    line.description = defaultLineDescriptions[line.line_type]
  }
  if (line.unit_price === 0) {
    const defaultPrice = defaultPrices.value[line.line_type]
    if (defaultPrice !== null && defaultPrice !== undefined) {
      line.unit_price = defaultPrice
    }
  }
}

function addLine() {
  const defaultUnitPrice = defaultPrices.value['cours'] ?? 0
  form.lines.push({
    line_type: 'cours',
    description: 'Cours de soutien',
    quantity: 1,
    unit_price: defaultUnitPrice,
  })
}

function removeLine(idx: number) {
  form.lines.splice(idx, 1)
}

function resetForm() {
  form.contact_id = null
  form.date = new Date()
  form.due_date = null
  form.description = ''
  form.lines = []
  suggestedDueDateIso.value = null
}

function setFromInvoice(inv: Invoice) {
  form.contact_id = inv.contact_id
  form.date = new Date(inv.date)
  form.due_date = inv.due_date ? new Date(inv.due_date) : null
  form.description = inv.description ?? ''
  form.lines = inv.lines.map((l) => ({
    line_type: l.line_type ?? inferLineType(l.description, inv.label),
    description: l.description,
    quantity: parseFloat(l.quantity),
    unit_price: parseFloat(l.unit_price),
  }))
  suggestedDueDateIso.value = inv.due_date ?? null
}

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
  () => props.invoice,
  (inv) => {
    if (inv) setFromInvoice(inv)
    else resetForm()
    nextTick(() => { initialSnapshot.value = formSnapshot() })
  },
  { immediate: true },
)

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
  if (!form.contact_id || !form.date) return
  saving.value = true
  fieldErrors.value = {}
  try {
    const payload = {
      type: 'client' as const,
      contact_id: form.contact_id,
      date: formatDate(form.date),
      due_date: form.due_date ? formatDate(form.due_date) : null,
      description: form.description || null,
      lines: form.lines.map((l) => ({
        description: l.description,
        line_type: l.line_type,
        quantity: String(l.quantity),
        unit_price: String(l.unit_price),
      })),
    }
    let savedInvoice: Invoice
    if (props.invoice) {
      savedInvoice = await updateInvoiceApi(props.invoice.id, payload)
    } else {
      savedInvoice = await createInvoiceApi(payload)
    }
    emit('saved', savedInvoice)
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 422) {
      const detail = error.response.data?.detail
      if (Array.isArray(detail)) {
        const errors: Record<string, string> = {}
        for (const item of detail) {
          if (Array.isArray(item.loc) && item.loc.length > 0) {
            errors[String(item.loc[item.loc.length - 1])] = item.msg
          }
        }
        fieldErrors.value = errors
      } else {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
      }
    } else {
      toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const settings = await getSettingsApi()
    defaultInvoiceDueDays.value = settings.default_invoice_due_days
    defaultPrices.value = {
      cours: settings.default_price_cours,
      adhesion: settings.default_price_adhesion,
      autres: settings.default_price_autres,
    }
  } catch {
    defaultInvoiceDueDays.value = null
  }
  if (!props.invoice) {
    getNextClientInvoiceNumberApi().then((n) => { nextNumber.value = n }).catch(() => {})
  }
  if (form.lines.length === 0 && !props.invoice) addLine()
  applySuggestedDueDate()
})

defineExpose({ submit, isDirty })
</script>

<style scoped>
.invoice-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-5);
}

.invoice-form__lines {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--app-surface-bg) 84%, transparent 16%);
  border: 1px solid var(--app-surface-border);
}

.invoice-form__lines-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-3);
  flex-wrap: wrap;
}

.invoice-form__line-row {
  display: grid;
  grid-template-columns:
    minmax(8.5rem, 1.05fr) minmax(0, 1.8fr) minmax(5.5rem, 0.7fr) minmax(7rem, 0.9fr)
    minmax(6.5rem, 0.75fr) auto;
  grid-template-areas: 'type description quantity price total remove';
  gap: var(--app-space-3);
  align-items: center;
}

.invoice-form__line-row > * {
  min-width: 0;
}

.invoice-form__type,
.invoice-form__description,
.invoice-form__quantity,
.invoice-form__price {
  width: 100%;
}

.invoice-form__type {
  grid-area: type;
}

.invoice-form__description {
  grid-area: description;
}

.invoice-form__quantity {
  grid-area: quantity;
}

.invoice-form__price {
  grid-area: price;
}

.invoice-form__line-row :deep(.p-select),
.invoice-form__line-row :deep(.p-inputtext),
.invoice-form__line-row :deep(.p-inputnumber),
.invoice-form__line-row :deep(.p-inputnumber-input) {
  width: 100%;
  min-width: 0;
}

.invoice-form__total {
  grid-area: total;
  text-align: right;
  font-size: 0.95rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.invoice-form__remove {
  grid-area: remove;
  justify-self: end;
}

.invoice-form__grand-total {
  text-align: right;
  font-size: 1rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.invoice-form__error {
  color: var(--p-red-600);
  font-size: 0.92rem;
}

@media (max-width: 1080px) {
  .invoice-form__line-row {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    grid-template-areas:
      'type description description remove'
      'quantity price total remove';
    align-items: start;
  }

  .invoice-form__remove {
    align-self: center;
  }
}

@media (max-width: 700px) {
  .invoice-form__line-row {
    grid-template-columns: 1fr;
    grid-template-areas:
      'type'
      'description'
      'quantity'
      'price'
      'total'
      'remove';
  }

  .invoice-form__total,
  .invoice-form__grand-total {
    text-align: left;
  }

  .invoice-form__remove {
    justify-self: start;
  }
}
</style>
