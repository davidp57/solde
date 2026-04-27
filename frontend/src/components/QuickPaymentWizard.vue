<template>
  <Dialog
    :visible="visible"
    :header="t('dashboard.payment_wizard.title')"
    modal
    :closable="true"
    class="app-dialog app-dialog--large"
    @update:visible="onClose"
  >
    <!-- Step 1 — choose invoice -->
    <template v-if="step === 1">
      <p class="app-dialog-intro__text qpw-intro">{{ t('dashboard.payment_wizard.invoice_intro') }}</p>

      <div v-if="loading" class="qpw-loading">
        <i class="pi pi-spin pi-spinner" />
        <span>{{ t('dashboard.payment_wizard.invoice_loading') }}</span>
      </div>

      <div v-else-if="invoices.length === 0" class="app-empty-state">
        {{ t('dashboard.payment_wizard.invoice_empty') }}
      </div>

      <DataTable
        v-else
        :value="invoiceRows"
        striped-rows
        size="small"
        class="qpw-table"
        sort-field="due_date"
        :sort-order="1"
      >
        <Column field="number" :header="t('dashboard.payment_wizard.col_number')" sortable style="width: 8rem" />
        <Column field="contact_name" :header="t('dashboard.payment_wizard.col_contact')" sortable />
        <Column field="date" :header="t('dashboard.payment_wizard.col_date')" sortable style="width: 7rem">
          <template #body="{ data }">{{ formatDate(data.date) }}</template>
        </Column>
        <Column field="remaining" :header="t('dashboard.payment_wizard.col_remaining')" sortable style="width: 7rem; text-align: right">
          <template #body="{ data }">
            <span :class="data.overdue ? 'qpw-overdue' : ''">{{ data.remaining.toFixed(2) }} €</span>
          </template>
        </Column>
        <Column style="width: 7rem; text-align: right">
          <template #body="{ data }">
            <Button
              :label="t('dashboard.payment_wizard.choose')"
              size="small"
              @click="selectInvoice(data.raw)"
            />
          </template>
        </Column>
      </DataTable>
    </template>

    <!-- Step 2 — payment form -->
    <template v-else-if="step === 2">
      <form class="app-dialog-form" @submit.prevent="submitPayment">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ selectedInvoice!.number }}</p>
          <p class="app-dialog-intro__text">{{ t('invoices.client.payment_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="qpw-summary">
            <div class="qpw-summary__metric">
              <div class="qpw-summary__label">{{ t('invoices.remaining') }}</div>
              <div class="qpw-summary__value">{{ remainingAmount.toFixed(2) }} €</div>
            </div>
          </div>
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('payments.date') }}</label>
              <AppDatePicker v-model="form.date" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('payments.amount') }}</label>
              <InputNumber
                v-model="form.amount"
                mode="decimal"
                :min="0.01"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
              />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('payments.method') }}</label>
              <Select
                v-model="form.method"
                :options="methodOptions"
                option-label="label"
                option-value="value"
              />
            </div>
            <div v-if="form.method === 'cheque'" class="app-field">
              <label class="app-field__label">{{ t('payments.cheque_number') }}</label>
              <InputText v-model="form.cheque_number" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('payments.reference') }}</label>
              <InputText v-model="form.reference" />
            </div>
            <div class="app-field app-field--span-2">
              <label class="app-field__label">{{ t('payments.notes') }}</label>
              <Textarea v-model="form.notes" rows="3" />
            </div>
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('dashboard.payment_wizard.back')"
            severity="secondary"
            text
            type="button"
            @click="step = 1"
          />
          <Button type="submit" :label="t('common.save')" :loading="saving" />
        </div>
      </form>
    </template>

    <!-- Step 3 — result -->
    <template v-else-if="step === 3">
      <div class="qpw-result">
        <div v-if="success" class="qpw-result__icon qpw-result__icon--success">
          <i class="pi pi-check-circle" />
        </div>
        <div v-else class="qpw-result__icon qpw-result__icon--error">
          <i class="pi pi-times-circle" />
        </div>
        <p v-if="success" class="qpw-result__title">{{ t('dashboard.payment_wizard.success_title') }}</p>
        <p v-else class="qpw-result__title">{{ t('dashboard.payment_wizard.error_title') }}</p>
        <p class="qpw-result__msg">
          <template v-if="success">
            {{ t('dashboard.payment_wizard.success_msg', {
              amount: savedAmount.toFixed(2),
              number: savedNumber,
            }) }}
          </template>
          <template v-else>
            {{ t('dashboard.payment_wizard.error_msg') }}
          </template>
        </p>
        <div class="qpw-result__actions">
          <Button
            v-if="success"
            :label="t('dashboard.payment_wizard.encode_another')"
            severity="secondary"
            outlined
            @click="restart"
          />
          <Button :label="t('dashboard.payment_wizard.close')" @click="onClose(false)" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import AppDatePicker from './ui/AppDatePicker.vue'
import { listInvoicesApi, type Invoice } from '../api/invoices'
import { listContactsApi, type Contact } from '../api/contacts'
import { createPayment } from '../api/payments'
import { remainingForInvoice, isOverdueInvoice } from '../composables/useInvoiceMetrics'
import { formatContactDisplayName } from '../utils/contact'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const { t } = useI18n()

// ── state ──────────────────────────────────────────────────────────────────
const step = ref<1 | 2 | 3>(1)
const loading = ref(false)
const saving = ref(false)
const success = ref(false)
const savedAmount = ref(0)
const savedNumber = ref('')

const invoices = ref<Invoice[]>([])
const contacts = ref<Contact[]>([])
const selectedInvoice = ref<Invoice | null>(null)

const form = ref({
  date: new Date(),
  amount: 0,
  method: 'cheque' as 'especes' | 'cheque',
  cheque_number: '',
  reference: '',
  notes: '',
})

// ── computed ───────────────────────────────────────────────────────────────
const contactMap = computed(() => {
  const m = new Map<number, Contact>()
  for (const c of contacts.value) m.set(c.id, c)
  return m
})

const invoiceRows = computed(() =>
  invoices.value.map((inv) => {
    const contact = contactMap.value.get(inv.contact_id)
    return {
      raw: inv,
      number: inv.number,
      contact_name: contact ? formatContactDisplayName(contact) : String(inv.contact_id),
      date: inv.date,
      due_date: inv.due_date ?? '',
      remaining: remainingForInvoice(inv),
      overdue: isOverdueInvoice(inv),
    }
  }),
)

const remainingAmount = computed(() =>
  selectedInvoice.value ? remainingForInvoice(selectedInvoice.value) : 0,
)

const methodOptions = [
  { label: t('payments.methods.especes'), value: 'especes' },
  { label: t('payments.methods.cheque'), value: 'cheque' },
]

// ── helpers ────────────────────────────────────────────────────────────────
function formatDate(iso: string): string {
  if (!iso) return ''
  return new Intl.DateTimeFormat('fr-FR').format(new Date(iso + 'T12:00:00'))
}

function toIsoDate(value: Date | string): string {
  if (typeof value === 'string') return value
  return value.toISOString().slice(0, 10)
}

// ── data loading ───────────────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const [allInvoices, allContacts] = await Promise.all([
      listInvoicesApi({ invoice_type: 'client', limit: 1000 }),
      listContactsApi({ active_only: false }),
    ])
    contacts.value = allContacts
    invoices.value = allInvoices.filter(
      (inv) =>
        inv.status !== 'draft' &&
        inv.status !== 'irrecoverable' &&
        inv.status !== 'paid' &&
        remainingForInvoice(inv) > 0,
    )
  } catch {
    invoices.value = []
  } finally {
    loading.value = false
  }
}

// ── actions ────────────────────────────────────────────────────────────────
function selectInvoice(invoice: Invoice) {
  selectedInvoice.value = invoice
  form.value = {
    date: new Date(),
    amount: remainingForInvoice(invoice),
    method: 'cheque',
    cheque_number: '',
    reference: '',
    notes: '',
  }
  step.value = 2
}

async function submitPayment() {
  if (!selectedInvoice.value) return
  const amount = Number(form.value.amount)
  if (!(amount > 0) || amount > remainingAmount.value + 0.001) return
  if (form.value.method === 'cheque' && !form.value.cheque_number.trim()) return

  saving.value = true
  try {
    await createPayment({
      invoice_id: selectedInvoice.value.id,
      contact_id: selectedInvoice.value.contact_id,
      amount: amount.toFixed(2),
      date: toIsoDate(form.value.date),
      method: form.value.method,
      cheque_number:
        form.value.method === 'cheque' ? form.value.cheque_number.trim() || null : null,
      reference: form.value.reference.trim() || null,
      notes: form.value.notes.trim() || null,
    })
    savedAmount.value = amount
    savedNumber.value = selectedInvoice.value.number
    success.value = true
  } catch {
    success.value = false
  } finally {
    saving.value = false
    step.value = 3
  }
}

function restart() {
  step.value = 1
  selectedInvoice.value = null
  void loadData()
}

function onClose(value: boolean | Event) {
  if (value === false || value instanceof Event) {
    emit('update:visible', false)
  }
}

// ── lifecycle ──────────────────────────────────────────────────────────────
watch(
  () => props.visible,
  (v) => {
    if (v) {
      step.value = 1
      selectedInvoice.value = null
      success.value = false
      void loadData()
    }
  },
)
</script>

<style scoped>
.qpw-intro {
  margin: 0 0 var(--app-space-4);
  color: var(--p-text-muted-color);
}

.qpw-loading {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  padding: var(--app-space-5) 0;
  color: var(--p-text-muted-color);
}

.qpw-table {
  margin-top: 0;
}

.qpw-overdue {
  color: var(--p-red-500);
  font-weight: 600;
}

.qpw-summary {
  display: flex;
  gap: var(--app-space-5);
  margin-bottom: var(--app-space-4);
  padding: var(--app-space-4);
  background: color-mix(in srgb, var(--app-surface-bg) 80%, transparent);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-surface-radius-sm);
}

.qpw-summary__metric {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.qpw-summary__label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.qpw-summary__value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--p-amber-600);
}

.qpw-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--app-space-4);
  padding: var(--app-space-6) 0;
  text-align: center;
}

.qpw-result__icon {
  font-size: 3.5rem;
  line-height: 1;
}

.qpw-result__icon--success {
  color: var(--p-green-500);
}

.qpw-result__icon--error {
  color: var(--p-red-500);
}

.qpw-result__title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
}

.qpw-result__msg {
  margin: 0;
  color: var(--p-text-muted-color);
  max-width: 42ch;
}

.qpw-result__actions {
  display: flex;
  gap: var(--app-space-3);
  flex-wrap: wrap;
  justify-content: center;
  margin-top: var(--app-space-2);
}
</style>
