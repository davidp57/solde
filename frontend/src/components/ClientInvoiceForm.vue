<template>
  <form class="app-dialog-form" @submit.prevent="submit">
    <section class="app-dialog-intro">
      <p class="app-dialog-intro__eyebrow">{{ t('invoices.client.title') }}</p>
      <p class="app-dialog-intro__text">
        {{ t(isEditing ? 'invoices.client.form_intro_edit' : 'invoices.client.form_intro_create') }}
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
            :options="contacts"
            option-label="nom"
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
            <label class="app-field__label">{{ t('invoices.label') }}</label>
            <Select
              v-model="form.label"
              :options="labelOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('invoices.label_placeholder')"
              show-clear
              class="w-full"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('invoices.description') }}</label>
            <InputText v-model="form.description" class="w-full" />
          </div>
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
          :min="0"
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
          @click="removeLine(idx)"
        />
      </div>
      <div class="invoice-form__grand-total">{{ t('invoices.total') }}: {{ computedTotal }} €</div>
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
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Contact } from '../api/contacts'
import { createInvoiceApi, updateInvoiceApi, type Invoice } from '../api/invoices'

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

interface LineForm {
  description: string
  quantity: number
  unit_price: number
}

interface FormState {
  contact_id: number | null
  date: Date | null
  due_date: Date | null
  label: string | null
  description: string
  lines: LineForm[]
}

const form = reactive<FormState>({
  contact_id: null,
  date: null,
  due_date: null,
  label: null,
  description: '',
  lines: [],
})

const labelOptions = [
  { label: t('invoices.labels.cs'), value: 'cs' },
  { label: t('invoices.labels.a'), value: 'a' },
  { label: 'invoices.labels.cs_a', value: 'cs+a' },
  { label: t('invoices.labels.general'), value: 'general' },
]

function lineAmount(line: LineForm): string {
  return ((line.quantity || 0) * (line.unit_price || 0)).toFixed(2)
}

const computedTotal = computed(() =>
  form.lines.reduce((sum, l) => sum + (l.quantity || 0) * (l.unit_price || 0), 0).toFixed(2),
)

function addLine() {
  form.lines.push({ description: '', quantity: 1, unit_price: 0 })
}

function removeLine(idx: number) {
  form.lines.splice(idx, 1)
}

function resetForm() {
  form.contact_id = null
  form.date = null
  form.due_date = null
  form.label = null
  form.description = ''
  form.lines = []
}

function setFromInvoice(inv: Invoice) {
  form.contact_id = inv.contact_id
  form.date = new Date(inv.date)
  form.due_date = inv.due_date ? new Date(inv.due_date) : null
  form.label = inv.label
  form.description = inv.description ?? ''
  form.lines = inv.lines.map((l) => ({
    description: l.description,
    quantity: parseFloat(l.quantity),
    unit_price: parseFloat(l.unit_price),
  }))
}

watch(
  () => props.invoice,
  (inv) => {
    if (inv) setFromInvoice(inv)
    else resetForm()
  },
  { immediate: true },
)

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

async function submit() {
  if (!form.contact_id || !form.date) return
  saving.value = true
  try {
    const payload = {
      type: 'client' as const,
      contact_id: form.contact_id,
      date: formatDate(form.date),
      due_date: form.due_date ? formatDate(form.due_date) : null,
      label: (form.label as Invoice['label']) ?? null,
      description: form.description || null,
      lines: form.lines.map((l) => ({
        description: l.description,
        quantity: String(l.quantity),
        unit_price: String(l.unit_price),
      })),
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

onMounted(() => {
  if (form.lines.length === 0 && !props.invoice) addLine()
})
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
  grid-template-columns: minmax(0, 1.8fr) 110px 140px 110px auto;
  gap: var(--app-space-3);
  align-items: center;
}

.invoice-form__description,
.invoice-form__quantity,
.invoice-form__price {
  width: 100%;
}

.invoice-form__total {
  text-align: right;
  font-size: 0.95rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.invoice-form__grand-total {
  text-align: right;
  font-size: 1rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 900px) {
  .invoice-form__line-row {
    grid-template-columns: 1fr;
  }

  .invoice-form__total,
  .invoice-form__grand-total {
    text-align: left;
  }
}
</style>
