<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('ui.page.accounting_eyebrow')"
      :title="t('accounting.journal.title')"
      :subtitle="t('accounting.journal.subtitle')"
    >
      <template #actions>
        <Button
          :label="t('bilan.export_csv')"
          icon="pi pi-download"
          severity="secondary"
          outlined
          @click="downloadCsv"
        />
        <Button
          :label="t('accounting.journal.new_manual_entry')"
          icon="pi pi-plus"
          @click="showManualDialog = true"
        />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('accounting.journal.summary_entries')"
        :value="summary.entryCount"
        :caption="t('accounting.journal.summary_filtered')"
      />
      <AppStatCard
        :label="t('accounting.journal.summary_debit')"
        :value="formatAmount(summary.totalDebit) + ' €'"
        :caption="t('accounting.journal.summary_balance_caption')"
      />
      <AppStatCard
        :label="t('accounting.journal.summary_credit')"
        :value="formatAmount(summary.totalCredit) + ' €'"
        :caption="t('accounting.journal.summary_search', { count: filtered.length })"
        tone="success"
      />
      <AppStatCard
        :label="t('accounting.journal.summary_sources')"
        :value="summary.sourceCount"
        :caption="summary.periodCaption"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('accounting.journal.workspace_title')" :subtitle="t('accounting.journal.workspace_subtitle')">
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('accounting.journal.filters_hint') }}</p>
          <span class="app-chip">{{ t('accounting.journal.summary_search', { count: filtered.length }) }}</span>
        </div>

        <div class="app-filter-grid journal-filters">
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_from') }}</label>
            <InputText v-model="filters.from_date" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_to') }}</label>
            <InputText v-model="filters.to_date" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_account') }}</label>
            <InputText v-model="filters.account_number" :placeholder="t('accounting.accounts.number_placeholder')" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_source') }}</label>
            <Select
              v-model="filters.source_type"
              :options="sourceTypeOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_fiscal_year') }}</label>
            <Select
              v-model="filters.fiscal_year_id"
              :options="fiscalYears"
              option-label="name"
              option-value="id"
              :placeholder="t('common.all')"
              show-clear
            />
          </div>
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
          </div>
          <div class="app-field journal-filters__action">
            <label class="app-field__label">{{ t('accounting.journal.apply_filters') }}</label>
            <Button :label="t('common.search')" icon="pi pi-search" @click="load" />
          </div>
        </div>
      </div>

      <DataTable
        :value="filtered"
        :loading="loading"
        class="app-data-table journal-table"
        paginator
        :rows="50"
        striped-rows
        size="small"
        row-hover
      >
        <Column field="date" :header="t('accounting.journal.date')" sortable />
        <Column field="entry_number" :header="t('accounting.journal.entry_number')" />
        <Column field="account_number" :header="t('accounting.journal.account')" />
        <Column field="label" :header="t('accounting.journal.label')" />
        <Column field="debit" :header="t('accounting.journal.debit')" class="app-money">
          <template #body="{ data }">{{ data.debit !== '0.00' ? data.debit : '' }}</template>
        </Column>
        <Column field="credit" :header="t('accounting.journal.credit')" class="app-money">
          <template #body="{ data }">{{ data.credit !== '0.00' ? data.credit : '' }}</template>
        </Column>
        <Column field="source_type" :header="t('accounting.journal.source')">
          <template #body="{ data }">
            {{ data.source_type ? t(`accounting.journal.sources.${data.source_type}`) : '' }}
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('accounting.journal.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <Dialog
      v-model:visible="showManualDialog"
      :header="t('accounting.journal.sources.manual')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('accounting.journal.title') }}</p>
          <p class="app-dialog-intro__text">{{ t('accounting.journal.manual_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('accounting.journal.manual_main_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('accounting.journal.manual_main_subtitle') }}</p>
          </div>
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('accounting.journal.date') }}</label>
              <InputText v-model="manualForm.date" type="date" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('accounting.journal.label') }}</label>
              <InputText v-model="manualForm.label" />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('invoices.total') }}</label>
              <InputText v-model="manualForm.amount" type="number" step="0.01" min="0" />
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('accounting.journal.manual_accounts_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('accounting.journal.manual_accounts_subtitle') }}</p>
          </div>
          <div class="app-form-grid">
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('accounting.journal.debit') }} — {{ t('accounting.journal.account') }}</label>
              <InputText v-model="manualForm.debit_account" :placeholder="t('accounting.accounts.number_placeholder')" />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('accounting.journal.credit') }} — {{ t('accounting.journal.account') }}</label>
              <InputText v-model="manualForm.credit_account" :placeholder="t('accounting.accounts.number_placeholder')" />
            </div>
          </div>
        </section>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="showManualDialog = false" />
        <Button :label="t('common.save')" icon="pi pi-check" :loading="saving" @click="saveManualEntry" />
      </template>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
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
  getExportCsvUrl,
  listFiscalYearsApi,
  type AccountingEntryRead,
  type EntrySourceType,
  type FiscalYearRead,
  type ManualEntryCreate,
} from '../api/accounting'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import { useTableFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const toast = useToast()

const entries = ref<AccountingEntryRead[]>([])
const { filterText, filtered } = useTableFilter(entries)
const fiscalYears = ref<FiscalYearRead[]>([])
const loading = ref(false)
const saving = ref(false)
const showManualDialog = ref(false)

const filters = ref({
  from_date: '',
  to_date: '',
  account_number: '',
  source_type: undefined as EntrySourceType | undefined,
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
  { label: t('accounting.journal.sources.gestion'), value: 'gestion' },
  { label: t('accounting.journal.sources.invoice'), value: 'invoice' },
  { label: t('accounting.journal.sources.payment'), value: 'payment' },
  { label: t('accounting.journal.sources.deposit'), value: 'deposit' },
  { label: t('accounting.journal.sources.salary'), value: 'salary' },
  { label: t('accounting.journal.sources.manual'), value: 'manual' },
  { label: t('accounting.journal.sources.cloture'), value: 'cloture' },
]

const summary = computed(() => {
  const visibleEntries = filtered.value
  const totalDebit = visibleEntries.reduce((sum, entry) => sum + parseFloat(entry.debit), 0)
  const totalCredit = visibleEntries.reduce((sum, entry) => sum + parseFloat(entry.credit), 0)
  const sources = new Set(visibleEntries.map((entry) => entry.source_type).filter(Boolean))
  const periodCaption = filters.value.from_date || filters.value.to_date
    ? `${filters.value.from_date || '...'} -> ${filters.value.to_date || '...'}`
    : t('accounting.journal.summary_period_all')

  return {
    entryCount: visibleEntries.length,
    totalDebit,
    totalCredit,
    sourceCount: sources.size,
    periodCaption,
  }
})

function formatAmount(value: number): string {
  return new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
}

async function load() {
  loading.value = true
  try {
    entries.value = await getJournalApi({
      from_date: filters.value.from_date || undefined,
      to_date: filters.value.to_date || undefined,
      account_number: filters.value.account_number || undefined,
      source_type: filters.value.source_type,
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

function downloadCsv() {
  const url = getExportCsvUrl('journal', {
    from_date: filters.value.from_date || undefined,
    to_date: filters.value.to_date || undefined,
    account_number: filters.value.account_number || undefined,
    fiscal_year_id: filters.value.fiscal_year_id,
  })
  window.open(url, '_blank')
}

onMounted(async () => {
  fiscalYears.value = await listFiscalYearsApi()
  await load()
})
</script>

<style scoped>
.journal-filters {
  align-items: end;
}

.journal-filters__action {
  justify-content: flex-end;
}

.journal-table :deep(.p-column-title) {
  white-space: nowrap;
}
</style>
