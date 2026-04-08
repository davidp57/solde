<template>
  <form @submit.prevent="submit">
    <div class="flex flex-col gap-4">
      <!-- Contact -->
      <div class="flex flex-col gap-1">
        <label class="font-medium">{{ t('invoices.contact') }}</label>
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

      <!-- Date / Due date -->
      <div class="flex gap-3">
        <div class="flex flex-col gap-1 flex-1">
          <label class="font-medium">{{ t('invoices.date') }}</label>
          <DatePicker v-model="form.date" date-format="dd/mm/yy" class="w-full" required />
        </div>
        <div class="flex flex-col gap-1 flex-1">
          <label class="font-medium">{{ t('invoices.due_date') }}</label>
          <DatePicker v-model="form.due_date" date-format="dd/mm/yy" class="w-full" show-clear />
        </div>
      </div>

      <!-- Reference / Amount -->
      <div class="flex gap-3">
        <div class="flex flex-col gap-1 flex-1">
          <label class="font-medium">{{ t('invoices.reference') }}</label>
          <InputText
            v-model="form.reference"
            :placeholder="t('invoices.reference_placeholder')"
            class="w-full"
          />
        </div>
        <div class="flex flex-col gap-1 flex-1">
          <label class="font-medium">{{ t('invoices.total') }} €</label>
          <InputNumber
            v-model="form.total_amount"
            :min="0"
            :max-fraction-digits="2"
            class="w-full"
            required
          />
        </div>
      </div>

      <!-- Description -->
      <div class="flex flex-col gap-1">
        <label class="font-medium">{{ t('invoices.description') }}</label>
        <Textarea v-model="form.description" rows="2" class="w-full" auto-resize />
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-2 mt-2">
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          type="button"
          outlined
          @click="emit('cancel')"
        />
        <Button :label="t('common.save')" type="submit" :loading="saving" />
      </div>
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
import { reactive, ref, watch } from 'vue'
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

function resetForm() {
  form.contact_id = null
  form.date = null
  form.due_date = null
  form.reference = ''
  form.total_amount = null
  form.description = ''
}

function setFromInvoice(inv: Invoice) {
  form.contact_id = inv.contact_id
  form.date = new Date(inv.date)
  form.due_date = inv.due_date ? new Date(inv.due_date) : null
  form.reference = inv.reference ?? ''
  form.total_amount = parseFloat(inv.total_amount)
  form.description = inv.description ?? ''
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
  return d.toISOString().split('T')[0]
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
</script>
