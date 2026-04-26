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
        :caption="t('accounting.journal.summary_search', { count: displayedGroups.length })"
        tone="success"
      />
      <AppStatCard
        :label="t('accounting.journal.summary_sources')"
        :value="summary.sourceCount"
        :caption="summary.periodCaption"
        tone="warn"
      />
    </section>

    <AppPanel
      :title="t('accounting.journal.workspace_title')"
      :subtitle="t('accounting.journal.workspace_subtitle')"
    >
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('accounting.journal.filters_hint') }}</p>
          <div class="app-toolbar__meta-actions">
            <span class="app-chip">{{
              t('accounting.journal.summary_search', { count: displayedGroups.length })
            }}</span>
            <Button
              :label="t('common.reset_filters')"
              icon="pi pi-filter-slash"
              severity="secondary"
              outlined
              :disabled="!hasAnyFilters"
              :title="t('common.reset_filters')"
              @click="resetAllFilters"
            />
          </div>
        </div>

        <div class="app-filter-grid journal-filters">
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_from') }}</label>
            <AppDateInput v-model="filters.from_date" @keydown.enter="load" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_to') }}</label>
            <AppDateInput v-model="filters.to_date" @keydown.enter="load" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_account') }}</label>
            <AppAccountSelect
              :model-value="filters.account_number || null"
              :accounts="journalAccounts"
              :placeholder="t('accounting.journal.account')"
              @update:model-value="onAccountFilterChange"
            />
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
              @update:modelValue="onSourceTypeChange"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_fiscal_year') }}</label>
            <Select
              v-model="selectedFiscalYearId"
              :options="fiscalYears"
              option-label="name"
              option-value="id"
              :placeholder="t('common.all')"
              @change="load"
            />
          </div>
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText
              v-model="globalFilter"
              :placeholder="t('common.filter_placeholder')"
              @keydown.enter="load"
            />
          </div>
          <div class="app-field journal-filters__action">
            <label class="app-field__label">{{ t('accounting.journal.apply_filters') }}</label>
            <Button :label="t('common.search')" icon="pi pi-search" @click="load" />
          </div>
        </div>
      </div>

      <AppTableSkeleton v-if="loading && !groups.length" :rows="8" :cols="5" />
      <DataTable
        v-else
        v-model:filters="tableFilters"
        :value="journalRows"
        :loading="loading"
        class="app-data-table journal-table"
        filter-display="menu"
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        striped-rows
        size="small"
        row-hover
        :global-filter-fields="[
          'date',
          'source_label',
          'reference_value',
          'contact_display',
          'label',
          'accounts_summary',
          'line_count',
          'total_debit',
          'total_credit',
        ]"
        removable-sort
        @value-change="syncDisplayedGroups"
      >
        <Column
          field="date"
          :header="t('accounting.journal.date')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
          <template #filter="{ filterModel }">
            <AppDateRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="source_label"
          :header="t('accounting.journal.source')"
          class="journal-table__source-column"
          sortable
          filter-field="source_type"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag
              v-if="data.source_type"
              :value="t(`accounting.journal.sources.${data.source_type}`)"
              :severity="sourceSeverity(data.source_type)"
            />
            <span v-else>{{ t('accounting.journal.sources.manual') }}</span>
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="sourceTypeOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              display="chip"
              show-clear
              :filter-callback="filterCallback"
            />
          </template>
        </Column>
        <Column
          field="reference_value"
          :header="t('accounting.journal.reference')"
          class="journal-table__reference-column"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <div class="journal-reference-cell">
              <Button
                v-if="canOpenInvoice(data)"
                data-testid="journal-open-invoice-button"
                :label="data.reference_value"
                link
                class="journal-reference-cell__link"
                @click="openInvoice(data)"
              />
              <span v-else>{{ data.reference_value }}</span>
              <small v-if="showInvoiceNumber(data)" class="journal-reference-cell__invoice-number">
                {{ data.source_invoice_number }}
              </small>
            </div>
          </template>
          <template #filter="{ filterModel }">
            <InputText
              v-model="filterModel.value"
              :placeholder="t('accounting.journal.reference')"
            />
          </template>
        </Column>
        <Column
          field="contact_display"
          :header="t('accounting.journal.contact')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            {{ data.source_contact_name || t('accounting.journal.no_contact') }}
          </template>
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('accounting.journal.contact')" />
          </template>
        </Column>
        <Column
          field="label"
          :header="t('accounting.journal.label')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('accounting.journal.label')" />
          </template>
        </Column>
        <Column
          field="accounts_summary"
          :header="t('accounting.journal.accounts')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <div class="journal-account-list">{{ data.accounts_summary }}</div>
          </template>
          <template #filter="{ filterModel }">
            <InputText
              v-model="filterModel.value"
              :placeholder="t('accounting.journal.accounts')"
            />
          </template>
        </Column>
        <Column
          field="line_count"
          :header="t('accounting.journal.lines_count')"
          class="journal-table__count-column"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="total_debit_value"
          :header="t('accounting.journal.debit')"
          class="app-money"
          sortable
          filter-field="total_debit_value"
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatEntryAmount(data.total_debit) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="total_credit_value"
          :header="t('accounting.journal.credit')"
          class="app-money"
          sortable
          filter-field="total_credit_value"
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatEntryAmount(data.total_credit) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column :header="t('common.actions')" class="journal-table__actions-column">
          <template #body="{ data }">
            <div class="app-inline-actions">
              <Button
                data-testid="journal-detail-button"
                icon="pi pi-eye"
                size="small"
                severity="secondary"
                text
                @click="openDetailDialog(data)"
              />
              <Button
                v-if="data.editable"
                data-testid="journal-edit-button"
                icon="pi pi-pencil"
                size="small"
                severity="secondary"
                text
                @click="openEditDialog(data)"
              />
            </div>
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('accounting.journal.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <Dialog
      v-model:visible="showManualDialog"
      :header="
        editingEntry
          ? t('accounting.journal.edit_manual_entry')
          : t('accounting.journal.new_manual_entry')
      "
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
            <h3 class="app-dialog-section__title">
              {{ t('accounting.journal.manual_main_title') }}
            </h3>
            <p class="app-dialog-section__copy">
              {{ t('accounting.journal.manual_main_subtitle') }}
            </p>
          </div>
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('accounting.journal.date') }}</label>
              <InputText v-model="manualForm.date" data-testid="journal-date-input" type="date" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('accounting.journal.label') }}</label>
              <InputText v-model="manualForm.label" data-testid="journal-label-input" />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('invoices.total') }}</label>
              <InputText
                v-model="manualForm.amount"
                data-testid="journal-amount-input"
                type="number"
                step="0.01"
                min="0"
              />
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">
              {{ t('accounting.journal.manual_accounts_title') }}
            </h3>
            <p class="app-dialog-section__copy">
              {{ t('accounting.journal.manual_accounts_subtitle') }}
            </p>
          </div>
          <div class="app-form-grid">
            <div class="app-field app-field--full">
              <label class="app-field__label"
                >{{ t('accounting.journal.debit') }} — {{ t('accounting.journal.account') }}</label
              >
              <InputText
                v-model="manualForm.debit_account"
                data-testid="journal-debit-account-input"
                :placeholder="t('accounting.accounts.number_placeholder')"
              />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label"
                >{{ t('accounting.journal.credit') }} — {{ t('accounting.journal.account') }}</label
              >
              <InputText
                v-model="manualForm.credit_account"
                data-testid="journal-credit-account-input"
                :placeholder="t('accounting.accounts.number_placeholder')"
              />
            </div>
          </div>
        </section>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="closeManualDialog" />
        <Button
          :label="t('common.save')"
          icon="pi pi-check"
          :loading="saving"
          @click="saveManualEntry"
        />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="showDetailDialog"
      :header="t('accounting.journal.entry_details')"
      modal
      class="app-dialog app-dialog--large"
    >
      <div v-if="selectedGroup" class="app-dialog-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('accounting.journal.source_details') }}</p>
          <p class="app-dialog-intro__text">{{ selectedGroup.label }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="journal-detail-grid">
            <div>
              <span class="journal-detail-grid__label">{{ t('accounting.journal.date') }}</span>
              <strong>{{ formatDisplayDate(selectedGroup.date) }}</strong>
            </div>
            <div>
              <span class="journal-detail-grid__label">{{ t('accounting.journal.source') }}</span>
              <strong>{{
                selectedGroup.source_type
                  ? t(`accounting.journal.sources.${selectedGroup.source_type}`)
                  : t('accounting.journal.sources.manual')
              }}</strong>
            </div>
            <div>
              <span class="journal-detail-grid__label">{{
                t('accounting.journal.reference')
              }}</span>
              <strong>{{ entryReference(selectedGroup) }}</strong>
            </div>
            <div>
              <span class="journal-detail-grid__label">{{ t('accounting.journal.contact') }}</span>
              <strong>{{
                selectedGroup.source_contact_name || t('accounting.journal.no_contact')
              }}</strong>
            </div>
            <div>
              <span class="journal-detail-grid__label">{{
                t('accounting.journal.lines_count')
              }}</span>
              <strong>{{ selectedGroup.line_count }}</strong>
            </div>
            <div>
              <span class="journal-detail-grid__label"
                >{{ t('accounting.journal.debit') }} / {{ t('accounting.journal.credit') }}</span
              >
              <strong
                >{{ formatEntryAmount(selectedGroup.total_debit) || '0,00' }} /
                {{ formatEntryAmount(selectedGroup.total_credit) || '0,00' }}</strong
              >
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('accounting.journal.entry_lines') }}</h3>
            <p class="app-dialog-section__copy">{{ accountsSummary(selectedGroup) }}</p>
          </div>
          <DataTable
            v-model:filters="lineTableFilters"
            :value="lineRows"
            class="app-data-table journal-lines-table"
            filter-display="menu"
            paginator
            :rows="20"
            :rows-per-page-options="[20, 50, 100, 500]"
            size="small"
            striped-rows
            :global-filter-fields="[
              'entry_number',
              'account_number',
              'account_label',
              'label',
              'debit_value',
              'credit_value',
            ]"
            removable-sort
          >
            <Column
              field="entry_number"
              :header="t('accounting.journal.entry_number')"
              sortable
              :show-filter-match-modes="false"
              :show-add-button="false"
            >
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  :placeholder="t('accounting.journal.entry_number')"
                />
              </template>
            </Column>
            <Column
              field="account_number"
              :header="t('accounting.journal.account')"
              sortable
              :show-filter-match-modes="false"
              :show-add-button="false"
            >
              <template #body="{ data }">
                <div class="journal-account-cell">
                  <strong>{{ data.account_number }}</strong>
                  <span>{{ data.account_label || data.account_number }}</span>
                </div>
              </template>
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  :placeholder="t('accounting.journal.account')"
                />
              </template>
            </Column>
            <Column
              field="label"
              :header="t('accounting.journal.label')"
              sortable
              :show-filter-match-modes="false"
              :show-add-button="false"
            >
              <template #filter="{ filterModel }">
                <InputText
                  v-model="filterModel.value"
                  :placeholder="t('accounting.journal.label')"
                />
              </template>
            </Column>
            <Column
              field="debit_value"
              :header="t('accounting.journal.debit')"
              class="app-money"
              sortable
              data-type="numeric"
              :show-filter-match-modes="false"
              :show-add-button="false"
            >
              <template #body="{ data }">{{ formatEntryAmount(data.debit) }}</template>
              <template #filter="{ filterModel }">
                <AppNumberRangeFilter v-model="filterModel.value" />
              </template>
            </Column>
            <Column
              field="credit_value"
              :header="t('accounting.journal.credit')"
              class="app-money"
              sortable
              data-type="numeric"
              :show-filter-match-modes="false"
              :show-add-button="false"
            >
              <template #body="{ data }">{{ formatEntryAmount(data.credit) }}</template>
              <template #filter="{ filterModel }">
                <AppNumberRangeFilter v-model="filterModel.value" />
              </template>
            </Column>
          </DataTable>
        </section>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="showDetailDialog = false" />
        <Button
          v-if="selectedGroup && selectedGroup.editable"
          :label="t('accounting.journal.edit_manual_entry')"
          icon="pi pi-pencil"
          severity="secondary"
          outlined
          @click="openEditDialog(selectedGroup)"
        />
        <Button
          v-if="selectedGroup && canOpenInvoice(selectedGroup)"
          :label="t('accounting.journal.open_invoice')"
          icon="pi pi-external-link"
          severity="secondary"
          outlined
          @click="openInvoice(selectedGroup)"
        />
      </template>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import {
  createManualEntryApi,
  getExportCsvUrl,
  getJournalGroupsApi,
  listAccountsApi,
  type AccountingAccount,
  type AccountingEntryGroupRead,
  type AccountingEntryRead,
  type EntrySourceType,
  type ManualEntryCreate,
  type ManualEntryUpdate,
  updateManualEntryApi,
} from '../api/accounting'
import AppPage from '../components/ui/AppPage.vue'
import AppDateInput from '../components/ui/AppDateInput.vue'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import AppAccountSelect from '../components/ui/AppAccountSelect.vue'
import AppTableSkeleton from '../components/ui/AppTableSkeleton.vue'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { formatDisplayDate } from '@/utils/format'

type JournalSourceInfo = Pick<
  AccountingEntryGroupRead,
  | 'source_reference'
  | 'source_invoice_number'
  | 'source_invoice_id'
  | 'source_invoice_type'
  | 'source_contact_name'
>

const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const fiscalYearStore = useFiscalYearStore()

const groups = ref<AccountingEntryGroupRead[]>([])
const journalAccounts = ref<AccountingAccount[]>([])
const fiscalYears = computed(() => fiscalYearStore.fiscalYears)
const selectedFiscalYearId = computed({
  get: () => fiscalYearStore.selectedFiscalYearId,
  set: (value: number | undefined) => fiscalYearStore.setSelectedFiscalYear(value),
})
const loading = ref(false)
const saving = ref(false)
const showManualDialog = ref(false)
const showDetailDialog = ref(false)
const selectedGroup = ref<AccountingEntryGroupRead | null>(null)
const editingEntry = ref<AccountingEntryRead | null>(null)
const lineRows = computed(() =>
  (selectedGroup.value?.lines ?? []).map((line) => ({
    ...line,
    debit_value: parseFloat(line.debit),
    credit_value: parseFloat(line.credit),
  })),
)

const filters = ref({
  from_date: '',
  to_date: '',
  account_number: '',
  source_type: undefined as EntrySourceType | undefined,
})

const journalRows = computed(() =>
  groups.value.map((group) => ({
    ...group,
    source_label: group.source_type
      ? t(`accounting.journal.sources.${group.source_type}`)
      : t('accounting.journal.sources.manual'),
    reference_value: entryReference(group),
    contact_display: group.source_contact_name || t('accounting.journal.no_contact'),
    accounts_summary: accountsSummary(group),
    total_debit_value: parseFloat(group.total_debit),
    total_credit_value: parseFloat(group.total_credit),
  })),
)

const {
  filters: tableFilters,
  globalFilter,
  displayedRows: displayedGroups,
  hasActiveFilters,
  resetFilters,
  syncDisplayedRows: syncDisplayedGroups,
} = useDataTableFilters(journalRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  source_type: inFilter(),
  reference_value: textFilter(),
  contact_display: textFilter(),
  label: textFilter(),
  accounts_summary: textFilter(),
  line_count: numericRangeFilter(),
  total_debit_value: numericRangeFilter(),
  total_credit_value: numericRangeFilter(),
})
const { filters: lineTableFilters } = useDataTableFilters(lineRows, {
  global: textFilter(''),
  entry_number: textFilter(),
  account_number: textFilter(),
  label: textFilter(),
  debit_value: numericRangeFilter(),
  credit_value: numericRangeFilter(),
})

const manualForm = ref<ManualEntryUpdate>({
  date: new Date().toISOString().substring(0, 10),
  debit_account: '',
  credit_account: '',
  amount: '',
  label: '',
  counterpart_entry_id: 0,
})

const sourceTypeOptions = [
  { label: t('accounting.journal.sources.gestion'), value: 'gestion' },
  { label: t('accounting.journal.sources.invoice'), value: 'invoice' },
  { label: t('accounting.journal.sources.payment'), value: 'payment' },
  { label: t('accounting.journal.sources.deposit'), value: 'deposit' },
  { label: t('accounting.journal.sources.salary'), value: 'salary' },
  { label: t('accounting.journal.sources.gestion'), value: 'gestion' },
  { label: t('accounting.journal.sources.manual'), value: 'manual' },
  { label: t('accounting.journal.sources.cloture'), value: 'cloture' },
]

const hasRemoteFilters = computed(
  () =>
    Boolean(
      filters.value.from_date ||
        filters.value.to_date ||
        filters.value.account_number ||
        filters.value.source_type ||
        selectedFiscalYearId.value,
    ),
)

const hasAnyFilters = computed(() => hasActiveFilters.value || hasRemoteFilters.value)

const summary = computed(() => {
  const visibleGroups = displayedGroups.value
  const totalDebit = visibleGroups.reduce((sum, group) => sum + parseFloat(group.total_debit), 0)
  const totalCredit = visibleGroups.reduce((sum, group) => sum + parseFloat(group.total_credit), 0)
  const sources = new Set(visibleGroups.map((group) => group.source_type).filter(Boolean))
  const periodCaption =
    filters.value.from_date || filters.value.to_date
      ? `${filters.value.from_date || '...'} -> ${filters.value.to_date || '...'}`
      : t('accounting.journal.summary_period_all')

  return {
    entryCount: visibleGroups.length,
    totalDebit,
    totalCredit,
    sourceCount: sources.size,
    periodCaption,
  }
})

function formatAmount(value: number): string {
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function formatEntryAmount(value: string): string {
  const numericValue = Number.parseFloat(value)
  return numericValue === 0 ? '' : formatAmount(numericValue)
}

function sourceSeverity(
  sourceType: EntrySourceType,
): 'info' | 'success' | 'warn' | 'contrast' | 'secondary' {
  const map: Record<EntrySourceType, 'info' | 'success' | 'warn' | 'contrast' | 'secondary'> = {
    invoice: 'info',
    payment: 'success',
    deposit: 'warn',
    salary: 'secondary',
    gestion: 'info',
    manual: 'contrast',
    cloture: 'warn',
  }
  return map[sourceType]
}

function entryReference(entry: JournalSourceInfo): string {
  return (
    entry.source_reference || entry.source_invoice_number || t('accounting.journal.no_reference')
  )
}

function showInvoiceNumber(entry: JournalSourceInfo): boolean {
  return Boolean(
    entry.source_invoice_number && entry.source_invoice_number !== entry.source_reference,
  )
}

function canOpenInvoice(entry: JournalSourceInfo): boolean {
  return Boolean(
    entry.source_invoice_id &&
    (entry.source_invoice_type === 'client' || entry.source_invoice_type === 'fournisseur'),
  )
}

function openInvoice(entry: JournalSourceInfo) {
  if (!canOpenInvoice(entry) || !entry.source_invoice_id) return
  void router.push({
    name: entry.source_invoice_type === 'client' ? 'invoices-client' : 'invoices-supplier',
    query: { invoiceId: String(entry.source_invoice_id) },
  })
}

function accountsSummary(group: AccountingEntryGroupRead): string {
  if (group.account_numbers.length <= 3) {
    return group.account_numbers.join(', ')
  }
  return `${group.account_numbers.slice(0, 3).join(', ')} +${group.account_numbers.length - 3}`
}

function onAccountFilterChange(value: string | null) {
  filters.value.account_number = value ?? ''
  void load()
}

function findEditableEntry(group: AccountingEntryGroupRead): AccountingEntryRead | null {
  return (
    group.lines.find((line) => line.editable && Number.parseFloat(line.debit) > 0) ||
    group.lines.find((line) => line.editable) ||
    null
  )
}

function resetManualForm() {
  manualForm.value = {
    date: new Date().toISOString().substring(0, 10),
    debit_account: '',
    credit_account: '',
    amount: '',
    label: '',
    counterpart_entry_id: 0,
  }
}

function closeManualDialog() {
  showManualDialog.value = false
  editingEntry.value = null
  resetManualForm()
}

function openDetailDialog(group: AccountingEntryGroupRead) {
  selectedGroup.value = group
  showDetailDialog.value = true
}

function openEditDialog(group: AccountingEntryGroupRead) {
  const entry = findEditableEntry(group)
  if (!entry || !entry.counterpart_entry_id || !entry.counterpart_account_number) return
  const debitAccount =
    Number.parseFloat(entry.debit) > 0 ? entry.account_number : entry.counterpart_account_number
  const creditAccount =
    Number.parseFloat(entry.credit) > 0 ? entry.account_number : entry.counterpart_account_number
  editingEntry.value = entry
  manualForm.value = {
    date: entry.date,
    debit_account: debitAccount,
    credit_account: creditAccount,
    amount: Number.parseFloat(entry.debit || '0') > 0 ? entry.debit : entry.credit,
    label: entry.label,
    fiscal_year_id: entry.fiscal_year_id,
    counterpart_entry_id: entry.counterpart_entry_id,
  }
  showDetailDialog.value = false
  showManualDialog.value = true
}

async function load() {
  loading.value = true
  try {
    groups.value = await getJournalGroupsApi({
      from_date: filters.value.from_date || undefined,
      to_date: filters.value.to_date || undefined,
      account_number: filters.value.account_number || undefined,
      source_type: filters.value.source_type,
      fiscal_year_id: selectedFiscalYearId.value,
    })
  } finally {
    loading.value = false
  }
}

function onSourceTypeChange(value: EntrySourceType | undefined) {
  filters.value.source_type = value
  void load()
}

function resetAllFilters() {
  filters.value = {
    from_date: '',
    to_date: '',
    account_number: '',
    source_type: undefined,
  }
  selectedFiscalYearId.value = undefined
  resetFilters()
  void load()
}

async function saveManualEntry() {
  saving.value = true
  try {
    if (editingEntry.value) {
      await updateManualEntryApi(editingEntry.value.id, manualForm.value)
      toast.add({
        severity: 'success',
        summary: t('accounting.journal.manual_updated'),
        life: 3000,
      })
    } else {
      const createPayload: ManualEntryCreate = {
        date: manualForm.value.date,
        debit_account: manualForm.value.debit_account,
        credit_account: manualForm.value.credit_account,
        amount: manualForm.value.amount,
        label: manualForm.value.label,
        fiscal_year_id: manualForm.value.fiscal_year_id,
      }
      await createManualEntryApi(createPayload)
      toast.add({ severity: 'success', summary: t('common.save'), life: 3000 })
    }
    closeManualDialog()
    await load()
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
    fiscal_year_id: selectedFiscalYearId.value,
  })
  window.open(url, '_blank')
}

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void load()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  const [, accts] = await Promise.all([load(), listAccountsApi(undefined, false)])
  journalAccounts.value = accts
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

.journal-table__actions-column {
  width: 6rem;
}

.journal-table__source-column {
  width: 8rem;
}

.journal-table__reference-column {
  min-width: 12rem;
}

.journal-table__count-column {
  width: 5rem;
}

.journal-account-cell {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.journal-account-list {
  line-height: 1.5;
}

.journal-reference-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
}

.journal-reference-cell__link {
  padding: 0;
}

.journal-reference-cell__invoice-number {
  color: var(--p-text-muted-color);
}

.journal-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--app-space-4);
}

.journal-detail-grid__label {
  display: block;
  margin-bottom: var(--app-space-1);
  color: var(--p-text-muted-color);
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.journal-lines-table {
  margin-top: var(--app-space-4);
}

@media (max-width: 767px) {
  .journal-detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
