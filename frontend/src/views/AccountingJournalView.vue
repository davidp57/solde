<template>
  <div class="view-container">
    <div class="view-header">
      <h1>{{ t('accounting.journal.title') }}</h1>
    </div>

    <!-- Filters -->
    <div class="filters-row">
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_from') }}</label>
        <InputText v-model="filters.from_date" type="date" />
      </div>
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_to') }}</label>
        <InputText v-model="filters.to_date" type="date" />
      </div>
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_account') }}</label>
        <InputText v-model="filters.account_number" :placeholder="t('accounting.accounts.number_placeholder')" />
      </div>
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_source') }}</label>
        <Select
          v-model="filters.source_type"
          :options="sourceTypeOptions"
          option-label="label"
          option-value="value"
          :placeholder="t('common.all')"
          show-clear
        />
      </div>
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_fiscal_year') }}</label>
        <Select
          v-model="filters.fiscal_year_id"
          :options="fiscalYears"
          option-label="name"
          option-value="id"
          :placeholder="t('common.all')"
          show-clear
        />
      </div>
      <Button :label="t('common.save')" icon="pi pi-search" @click="load" />
    </div>

    <!-- Manual entry button -->
    <div class="action-row">
      <Button
        :label="t('accounting.rules.activate')"
        icon="pi pi-plus"
        @click="showManualDialog = true"
      />
    </div>

    <!-- Table -->
    <DataTable
      :value="entries"
      :loading="loading"
      paginator
      :rows="50"
      striped-rows
    >
      <Column field="date" :header="t('accounting.journal.date')" sortable />
      <Column field="entry_number" :header="t('accounting.journal.entry_number')" />
      <Column field="account_number" :header="t('accounting.journal.account')" />
      <Column field="label" :header="t('accounting.journal.label')" />
      <Column field="debit" :header="t('accounting.journal.debit')" class="text-right">
        <template #body="{ data }">{{ data.debit !== '0.00' ? data.debit : '' }}</template>
      </Column>
      <Column field="credit" :header="t('accounting.journal.credit')" class="text-right">
        <template #body="{ data }">{{ data.credit !== '0.00' ? data.credit : '' }}</template>
      </Column>
      <Column field="source_type" :header="t('accounting.journal.source')">
        <template #body="{ data }">
          {{ data.source_type ? t(`accounting.journal.sources.${data.source_type}`) : '' }}
        </template>
      </Column>
      <template #empty>{{ t('accounting.journal.empty') }}</template>
    </DataTable>

    <!-- Manual entry dialog -->
    <Dialog
      v-model:visible="showManualDialog"
      :header="t('accounting.journal.sources.manual')"
      modal
      style="width: 480px"
    >
      <div class="form-fields">
        <div class="field">
          <label>{{ t('accounting.journal.date') }}</label>
          <InputText v-model="manualForm.date" type="date" />
        </div>
        <div class="field">
          <label>{{ t('accounting.journal.label') }}</label>
          <InputText v-model="manualForm.label" />
        </div>
        <div class="field">
          <label>{{ t('accounting.journal.debit') }} — {{ t('accounting.journal.account') }}</label>
          <InputText v-model="manualForm.debit_account" :placeholder="t('accounting.accounts.number_placeholder')" />
        </div>
        <div class="field">
          <label>{{ t('accounting.journal.credit') }} — {{ t('accounting.journal.account') }}</label>
          <InputText v-model="manualForm.credit_account" :placeholder="t('accounting.accounts.number_placeholder')" />
        </div>
        <div class="field">
          <label>{{ t('invoices.total') }}</label>
          <InputText v-model="manualForm.amount" type="number" step="0.01" min="0" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="showManualDialog = false" />
        <Button :label="t('common.save')" icon="pi pi-check" :loading="saving" @click="saveManualEntry" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import {
  getJournalApi,
  createManualEntryApi,
  listFiscalYearsApi,
  type AccountingEntryRead,
  type FiscalYearRead,
  type ManualEntryCreate,
} from '../api/accounting'

const { t } = useI18n()
const toast = useToast()

const entries = ref<AccountingEntryRead[]>([])
const fiscalYears = ref<FiscalYearRead[]>([])
const loading = ref(false)
const saving = ref(false)
const showManualDialog = ref(false)

const filters = ref({
  from_date: '',
  to_date: '',
  account_number: '',
  source_type: undefined as string | undefined,
  fiscal_year_id: undefined as number | undefined,
})

const manualForm = ref<ManualEntryCreate>({
  date: new Date().toISOString().substring(0, 10),
  debit_account: '',
  credit_account: '',
  amount: '',
  label: '',
})

const sourceTypeOptions = [
  { label: t('accounting.journal.sources.invoice'), value: 'invoice' },
  { label: t('accounting.journal.sources.payment'), value: 'payment' },
  { label: t('accounting.journal.sources.deposit'), value: 'deposit' },
  { label: t('accounting.journal.sources.salary'), value: 'salary' },
  { label: t('accounting.journal.sources.manual'), value: 'manual' },
  { label: t('accounting.journal.sources.cloture'), value: 'cloture' },
]

async function load() {
  loading.value = true
  try {
    entries.value = await getJournalApi({
      from_date: filters.value.from_date || undefined,
      to_date: filters.value.to_date || undefined,
      account_number: filters.value.account_number || undefined,
      source_type: filters.value.source_type as any,
      fiscal_year_id: filters.value.fiscal_year_id,
      limit: 500,
    })
  } finally {
    loading.value = false
  }
}

async function saveManualEntry() {
  saving.value = true
  try {
    await createManualEntryApi(manualForm.value)
    showManualDialog.value = false
    manualForm.value = { date: new Date().toISOString().substring(0, 10), debit_account: '', credit_account: '', amount: '', label: '' }
    await load()
    toast.add({ severity: 'success', summary: t('common.save'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  fiscalYears.value = await listFiscalYearsApi()
  await load()
})
</script>
