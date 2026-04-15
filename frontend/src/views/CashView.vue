<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="t('cash.title')">
      <template #actions>
        <Button
          :label="t('cash.new_count')"
          icon="pi pi-calculator"
          severity="secondary"
          @click="countDialogVisible = true"
        />
        <Button :label="t('cash.new_entry')" icon="pi pi-plus" @click="openCreateEntryDialog" />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('cash.current_balance')"
        :value="displayBalanceValue"
        :caption="currentBalanceCaption"
      />
      <AppStatCard
        :label="t('cash.period_variation')"
        :value="formatSignedAmount(displayedPeriodVariation)"
        :caption="periodVariationCaption"
        :tone="displayedPeriodVariationTone"
      />
      <AppStatCard
        :label="t('cash.journal')"
        :value="displayedEntries.length"
        :caption="t('cash.metrics.entries_total', { count: entries.length })"
      />
      <AppStatCard
        :label="t('cash.counts_title')"
        :value="displayedCounts.length"
        :caption="t('cash.metrics.counts_total', { count: counts.length })"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('cash.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="activeGlobalFilter" :placeholder="t('common.filter_placeholder')" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('common.reset_filters') }}</label>
            <Button
              icon="pi pi-filter-slash"
              severity="secondary"
              outlined
              :disabled="!activeHasFilters"
              @click="resetActiveFilters"
            />
          </div>
        </div>
      </div>

      <Tabs v-model:value="activeTab">
        <TabList>
          <Tab value="journal">{{ t('cash.journal') }}</Tab>
          <Tab value="counts">{{ t('cash.counts_title') }}</Tab>
        </TabList>

        <TabPanels>
          <TabPanel value="journal">
            <DataTable
              v-model:filters="entryTableFilters"
              :value="entryRows"
              :loading="loadingEntries"
              class="app-data-table"
              filter-display="menu"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              :global-filter-fields="[
                'date',
                'type_label',
                'origin_label',
                'amount',
                'reference',
                'description',
                'balance_after',
              ]"
              data-key="id"
              size="small"
              row-hover
              removable-sort
              @value-change="syncDisplayedEntries"
            >
              <Column
                field="date"
                :header="t('cash.entry_date')"
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
                field="type_label"
                :header="t('cash.entry_type')"
                sortable
                filter-field="type"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <div class="cash-entry-type">
                    <Tag
                      :value="t(`cash.movements.${data.type}`)"
                      :severity="data.type === 'in' ? 'success' : 'danger'"
                    />
                    <Tag
                      v-if="data.is_system_opening"
                      :value="t('cash.origins.system_opening')"
                      class="cash-entry-type__system-opening"
                      severity="info"
                    />
                  </div>
                </template>
                <template #filter="{ filterModel }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="movementTypes"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                  />
                </template>
              </Column>
              <Column
                field="amount_value"
                :header="t('cash.entry_amount')"
                class="app-money"
                sortable
                filter-field="amount_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <span :class="data.type === 'out' ? 'cash-negative' : 'cash-positive'">
                    {{ data.type === 'out' ? '-' : '+' }}{{ formatAmount(data.amount) }}
                  </span>
                </template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="reference"
                :header="t('cash.entry_reference')"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText v-model="filterModel.value" :placeholder="t('cash.entry_reference')" />
                </template>
              </Column>
              <Column
                field="description"
                :header="t('cash.entry_description')"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText
                    v-model="filterModel.value"
                    :placeholder="t('cash.entry_description')"
                  />
                </template>
              </Column>
              <Column
                field="balance_after_value"
                :header="t('cash.balance_after')"
                sortable
                filter-field="balance_after_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  {{ formatAmount(data.balance_after) }}
                </template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column :header="t('common.actions')" class="cash-journal__actions">
                <template #body="{ data }">
                  <div class="app-inline-actions">
                    <Button
                      data-testid="cash-detail-button"
                      icon="pi pi-eye"
                      size="small"
                      severity="secondary"
                      text
                      @click="openDetailDialog(data)"
                    />
                    <Button
                      data-testid="cash-edit-button"
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
                <div class="app-empty-state">{{ t('cash.journal_empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>

          <TabPanel value="counts">
            <DataTable
              v-model:filters="countTableFilters"
              :value="countRows"
              :loading="loadingCounts"
              class="app-data-table"
              filter-display="menu"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              :global-filter-fields="[
                'date',
                'total_counted',
                'balance_expected',
                'difference',
                'notes',
              ]"
              data-key="id"
              size="small"
              row-hover
              removable-sort
              @value-change="syncDisplayedCounts"
            >
              <Column
                field="date"
                :header="t('cash.count_date')"
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
                field="total_counted_value"
                :header="t('cash.count_total')"
                class="app-money"
                sortable
                filter-field="total_counted_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">{{ formatAmount(data.total_counted) }}</template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="balance_expected_value"
                :header="t('cash.count_expected')"
                class="app-money"
                sortable
                filter-field="balance_expected_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">{{ formatAmount(data.balance_expected) }}</template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="difference_value"
                :header="t('cash.count_diff')"
                class="app-money"
                sortable
                filter-field="difference_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <span
                    :class="
                      parseFloat(data.difference) < 0
                        ? 'cash-negative cash-emphasis'
                        : parseFloat(data.difference) > 0
                          ? 'cash-warn'
                          : 'cash-positive'
                    "
                  >
                    {{ formatAmount(data.difference) }}
                  </span>
                </template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="notes"
                :header="t('cash.count_notes')"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText v-model="filterModel.value" :placeholder="t('cash.count_notes')" />
                </template>
              </Column>
              <template #empty>
                <div class="app-empty-state">{{ t('cash.counts_empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </AppPanel>

    <Dialog
      v-model:visible="detailDialogVisible"
      :header="t('cash.entry_details')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div v-if="selectedEntry" class="app-dialog-form cash-detail">
        <div class="cash-detail__row">
          <span class="cash-detail__label">{{ t('cash.entry_date') }}</span>
          <span>{{ formatDisplayDate(selectedEntry.date) }}</span>
        </div>
        <div class="cash-detail__row">
          <span class="cash-detail__label">{{ t('cash.entry_type') }}</span>
          <span>{{ t(`cash.movements.${selectedEntry.type}`) }}</span>
        </div>
        <div v-if="selectedEntry.is_system_opening" class="cash-detail__row">
          <span class="cash-detail__label">{{ t('cash.entry_origin') }}</span>
          <Tag
            :value="t('cash.origins.system_opening')"
            class="cash-entry-type__system-opening"
            severity="info"
          />
        </div>
        <div class="cash-detail__row">
          <span class="cash-detail__label">{{ t('cash.entry_amount') }}</span>
          <span>{{ formatAmount(selectedEntry.amount) }}</span>
        </div>
        <div class="cash-detail__row">
          <span class="cash-detail__label">{{ t('cash.entry_reference') }}</span>
          <span>{{ selectedEntry.reference || '—' }}</span>
        </div>
        <div class="cash-detail__row">
          <span class="cash-detail__label">{{ t('cash.entry_description') }}</span>
          <span>{{ selectedEntry.description || '—' }}</span>
        </div>
        <div class="cash-detail__row">
          <span class="cash-detail__label">{{ t('cash.balance_after') }}</span>
          <span>{{ formatAmount(selectedEntry.balance_after) }}</span>
        </div>
      </div>
    </Dialog>

    <!-- New entry dialog -->
    <Dialog
      v-model:visible="entryDialogVisible"
      :header="editingEntry ? t('cash.edit_entry') : t('cash.new_entry')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <form class="app-dialog-form cash-form" @submit.prevent="submitEntry">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('cash.journal') }}</p>
          <p class="app-dialog-intro__text">{{ t('cash.entry_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('cash.entry_section_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('cash.entry_section_subtitle') }}</p>
          </div>
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('cash.entry_date') }}</label>
              <DatePicker v-model="entryForm.date" date-format="yy-mm-dd" show-icon />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('cash.entry_type') }}</label>
              <Select
                v-model="entryForm.type"
                :options="movementTypes"
                option-label="label"
                option-value="value"
              />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('cash.entry_amount') }}</label>
              <InputNumber
                v-model="entryForm.amount"
                mode="decimal"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
                :min="0.01"
              />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('cash.entry_reference') }}</label>
              <InputText v-model="entryForm.reference" data-testid="cash-reference-input" />
            </div>
            <div class="app-field app-field--span-2">
              <label class="app-field__label">{{ t('cash.entry_description') }}</label>
              <InputText v-model="entryForm.description" />
            </div>
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="entryDialogVisible = false"
          />
          <Button
            data-testid="cash-save-button"
            type="button"
            :label="t('common.save')"
            :loading="saving"
            @click="submitEntry"
          />
        </div>
      </form>
    </Dialog>

    <!-- New count dialog -->
    <Dialog
      v-model:visible="countDialogVisible"
      :header="t('cash.new_count')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <form class="app-dialog-form cash-form" @submit.prevent="submitCount">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('cash.counts_title') }}</p>
          <p class="app-dialog-intro__text">{{ t('cash.count_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('cash.count_section_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('cash.count_section_subtitle') }}</p>
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('cash.count_date') }}</label>
            <DatePicker v-model="countForm.date" date-format="yy-mm-dd" show-icon />
          </div>
          <div class="cash-denominations-grid">
            <template v-for="denom in denominations" :key="denom.field">
              <div class="app-field">
                <label class="app-field__label">{{ denom.label }}</label>
                <InputNumber
                  v-model="(countForm as unknown as Record<string, number>)[denom.field]"
                  :min="0"
                />
              </div>
            </template>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-field">
            <label class="app-field__label">{{ t('cash.count_notes') }}</label>
            <Textarea v-model="countForm.notes" rows="2" />
            <small class="app-dialog-note">{{ t('cash.count_notes_help') }}</small>
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="countDialogVisible = false"
          />
          <Button type="submit" :label="t('common.save')" :loading="saving" />
        </div>
      </form>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import { useFiscalYearStore } from '../stores/fiscalYear'
import {
  addCashCount,
  addCashEntry,
  getCashEntry,
  getCashBalance,
  listCashCounts,
  listCashEntries,
  type CashCount,
  type CashCountCreate,
  type CashEntry,
  updateCashEntry,
} from '@/api/cash'
import { formatDisplayDate } from '@/utils/format'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'

const { t } = useI18n()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()

const balance = ref('0')
const entries = ref<CashEntry[]>([])
const counts = ref<CashCount[]>([])
const loadingEntries = ref(false)
const loadingCounts = ref(false)
const activeTab = ref('journal')
const entryDialogVisible = ref(false)
const countDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const saving = ref(false)
const editingEntry = ref<CashEntry | null>(null)
const selectedEntry = ref<CashEntry | null>(null)

const movementTypes = [
  { label: t('cash.movements.in'), value: 'in' },
  { label: t('cash.movements.out'), value: 'out' },
]

const entryRows = computed(() =>
  entries.value.map((entry) => ({
    ...entry,
    type_label: t(`cash.movements.${entry.type}`),
    origin_label: entry.is_system_opening ? t('cash.origins.system_opening') : '',
    amount_value: parseFloat(entry.amount),
    balance_after_value: parseFloat(entry.balance_after),
  })),
)

const countRows = computed(() =>
  counts.value.map((count) => ({
    ...count,
    total_counted_value: parseFloat(count.total_counted),
    balance_expected_value: parseFloat(count.balance_expected),
    difference_value: parseFloat(count.difference),
  })),
)

const periodVariation = computed(() =>
  entries.value.reduce((total, entry) => {
    const amount = parseFloat(entry.amount)
    return total + (entry.type === 'out' ? -amount : amount)
  }, 0),
)

const displayedPeriodVariation = computed(() =>
  displayedEntries.value.reduce((total, entry) => {
    const amount = parseFloat(entry.amount)
    return total + (entry.type === 'out' ? -amount : amount)
  }, 0),
)

const selectedPeriodLabel = computed(
  () => fiscalYearStore.selectedFiscalYear?.name ?? t('app.all_fiscal_years'),
)

const periodVariationTone = computed(() => {
  if (periodVariation.value > 0) return 'success'
  if (periodVariation.value < 0) return 'danger'
  return 'warn'
})

const displayedPeriodVariationTone = computed(() => {
  if (displayedPeriodVariation.value > 0) return 'success'
  if (displayedPeriodVariation.value < 0) return 'danger'
  return 'warn'
})

const {
  filters: entryTableFilters,
  globalFilter: entryGlobalFilter,
  displayedRows: displayedEntries,
  hasActiveFilters: entryHasActiveFilters,
  resetFilters: resetEntryFilters,
  syncDisplayedRows: syncDisplayedEntries,
} = useDataTableFilters(entryRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  type: inFilter(),
  amount_value: numericRangeFilter(),
  reference: textFilter(),
  description: textFilter(),
  balance_after_value: numericRangeFilter(),
})

const {
  filters: countTableFilters,
  globalFilter: countGlobalFilter,
  displayedRows: displayedCounts,
  hasActiveFilters: countHasActiveFilters,
  resetFilters: resetCountFilters,
  syncDisplayedRows: syncDisplayedCounts,
} = useDataTableFilters(countRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  total_counted_value: numericRangeFilter(),
  balance_expected_value: numericRangeFilter(),
  difference_value: numericRangeFilter(),
  notes: textFilter(),
})

const activeGlobalFilter = computed({
  get: () => (activeTab.value === 'journal' ? entryGlobalFilter.value : countGlobalFilter.value),
  set: (value: string) => {
    if (activeTab.value === 'journal') {
      entryGlobalFilter.value = value
    } else {
      countGlobalFilter.value = value
    }
  },
})

const activeHasFilters = computed(() =>
  activeTab.value === 'journal' ? entryHasActiveFilters.value : countHasActiveFilters.value,
)

function pickLatestVisibleBalanceAfter(
  rows: Array<{ id: number; date: string; balance_after: string }>,
): string | null {
  if (rows.length === 0) {
    return null
  }

  const latestRow = rows.reduce((latest, current) => {
    if (current.date > latest.date) {
      return current
    }
    if (current.date === latest.date && current.id > latest.id) {
      return current
    }
    return latest
  })

  return latestRow.balance_after
}

const scopedBalance = computed(() => pickLatestVisibleBalanceAfter(displayedEntries.value))

const displayBalanceValue = computed(() =>
  formatAmount(scopedBalance.value ?? balance.value),
)

const currentBalanceCaption = computed(() =>
  entryHasActiveFilters.value || fiscalYearStore.selectedFiscalYear
    ? t('cash.metrics.visible_scope_caption')
    : t('cash.metrics.current_balance_caption'),
)

const periodVariationCaption = computed(() =>
  entryHasActiveFilters.value
    ? t('cash.metrics.visible_scope_caption')
    : t('cash.metrics.period_variation_caption', { period: selectedPeriodLabel.value }),
)

function resetActiveFilters() {
  if (activeTab.value === 'journal') {
    resetEntryFilters()
    return
  }

  resetCountFilters()
}

const denominations = [
  { field: 'count_100', label: '100 €' },
  { field: 'count_50', label: '50 €' },
  { field: 'count_20', label: '20 €' },
  { field: 'count_10', label: '10 €' },
  { field: 'count_5', label: '5 €' },
  { field: 'count_2', label: '2 €' },
  { field: 'count_1', label: '1 €' },
  { field: 'count_cents_50', label: '0,50 €' },
  { field: 'count_cents_20', label: '0,20 €' },
  { field: 'count_cents_10', label: '0,10 €' },
  { field: 'count_cents_5', label: '0,05 €' },
  { field: 'count_cents_2', label: '0,02 €' },
  { field: 'count_cents_1', label: '0,01 €' },
]

interface CashEntryFormState {
  date: Date
  type: 'in' | 'out'
  amount: number
  reference: string
  description: string
}

const entryForm = ref<CashEntryFormState>({
  date: new Date(),
  type: 'in',
  amount: 0,
  reference: '',
  description: '',
})

interface CashCountFormState extends Omit<CashCountCreate, 'date'> {
  date: Date | null
  count_100: number
  count_50: number
  count_20: number
  count_10: number
  count_5: number
  count_2: number
  count_1: number
  count_cents_50: number
  count_cents_20: number
  count_cents_10: number
  count_cents_5: number
  count_cents_2: number
  count_cents_1: number
  notes: string
}

const countForm = ref<CashCountFormState>({
  date: new Date(),
  count_100: 0,
  count_50: 0,
  count_20: 0,
  count_10: 0,
  count_5: 0,
  count_2: 0,
  count_1: 0,
  count_cents_50: 0,
  count_cents_20: 0,
  count_cents_10: 0,
  count_cents_5: 0,
  count_cents_2: 0,
  count_cents_1: 0,
  notes: '',
})

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function formatSignedAmount(value: number): string {
  if (value > 0) {
    return `+${formatAmount(value)}`
  }
  return formatAmount(value)
}

function toIsoDate(d: Date | string): string {
  if (typeof d === 'string') return d
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function fromIsoDate(value: string): Date {
  const [year = 1970, month = 1, day = 1] = value.split('-').map(Number)
  return new Date(year, month - 1, day, 12)
}

function normalizeOptionalField(value: string): string | null {
  const trimmedValue = value.trim()
  return trimmedValue.length > 0 ? trimmedValue : null
}

function resetEntryForm() {
  entryForm.value = {
    date: new Date(),
    type: 'in',
    amount: 0,
    reference: '',
    description: '',
  }
}

function openCreateEntryDialog() {
  editingEntry.value = null
  resetEntryForm()
  entryDialogVisible.value = true
}

async function openDetailDialog(entry: CashEntry) {
  selectedEntry.value = await getCashEntry(entry.id)
  detailDialogVisible.value = true
}

function openEditDialog(entry: CashEntry) {
  editingEntry.value = entry
  entryForm.value = {
    date: fromIsoDate(entry.date),
    type: entry.type,
    amount: parseFloat(entry.amount),
    reference: entry.reference ?? '',
    description: entry.description,
  }
  entryDialogVisible.value = true
}

async function loadAll() {
  loadingEntries.value = true
  loadingCounts.value = true
  try {
    const dateRange = {
      from_date: fiscalYearStore.selectedFiscalYear?.start_date,
      to_date: fiscalYearStore.selectedFiscalYear?.end_date,
    }
    const [b, e, c] = await Promise.all([
      getCashBalance(),
      listCashEntries(dateRange),
      listCashCounts(dateRange),
    ])
    balance.value = b.balance
    entries.value = e
    counts.value = c
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loadingEntries.value = false
    loadingCounts.value = false
  }
}

async function submitEntry() {
  saving.value = true
  try {
    if (editingEntry.value) {
      await updateCashEntry(editingEntry.value.id, {
        date: toIsoDate(entryForm.value.date as unknown as Date),
        type: entryForm.value.type,
        amount: String(entryForm.value.amount),
        reference: normalizeOptionalField(entryForm.value.reference),
        description: entryForm.value.description,
      })
      toast.add({ severity: 'success', summary: t('cash.entry_updated'), life: 3000 })
    } else {
      await addCashEntry({
        date: toIsoDate(entryForm.value.date as unknown as Date),
        type: entryForm.value.type,
        amount: String(entryForm.value.amount),
        reference: normalizeOptionalField(entryForm.value.reference),
        description: entryForm.value.description,
      })
    }
    entryDialogVisible.value = false
    editingEntry.value = null
    resetEntryForm()
    await loadAll()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

async function submitCount() {
  saving.value = true
  try {
    if (!countForm.value.date) return
    const payload: CashCountCreate = {
      ...countForm.value,
      date: toIsoDate(countForm.value.date),
      notes: countForm.value.notes || null,
    }
    await addCashCount(payload)
    countDialogVisible.value = false
    await loadAll()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void loadAll()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  await loadAll()
})
</script>

<style scoped>
.cash-journal__actions {
  width: 8rem;
}

.cash-entry-type {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--app-space-2);
}

.cash-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.cash-detail {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.cash-detail__row {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-3);
}

.cash-detail__label {
  font-weight: 700;
}

.cash-denominations-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--app-space-3);
}

.cash-positive {
  color: var(--p-green-600);
}

.cash-negative {
  color: var(--p-red-500);
}

.cash-warn {
  color: var(--p-orange-500);
}

.cash-emphasis {
  font-weight: 700;
}

:deep(.p-tabpanels) {
  padding-inline: 0;
  padding-bottom: 0;
}

@media (max-width: 767px) {
  .cash-denominations-grid {
    grid-template-columns: 1fr;
  }
}
</style>
