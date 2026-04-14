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
      <AppStatCard :label="t('cash.balance')" :value="formatAmount(balance)" />
      <AppStatCard
        :label="t('cash.journal')"
        :value="filteredEntries.length"
        :caption="`${entries.length} total`"
      />
      <AppStatCard :label="t('cash.counts_title')" :value="filteredCounts.length" tone="warn" />
    </section>

    <AppPanel :title="t('cash.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
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
              :value="filteredEntries"
              :loading="loadingEntries"
              class="app-data-table"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              data-key="id"
              size="small"
              row-hover
            >
              <Column field="date" :header="t('cash.entry_date')" sortable>
                <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
              </Column>
              <Column field="type" :header="t('cash.entry_type')">
                <template #body="{ data }">
                  <Tag
                    :value="t(`cash.movements.${data.type}`)"
                    :severity="data.type === 'in' ? 'success' : 'danger'"
                  />
                </template>
              </Column>
              <Column field="amount" :header="t('cash.entry_amount')" class="app-money">
                <template #body="{ data }">
                  <span :class="data.type === 'out' ? 'cash-negative' : 'cash-positive'">
                    {{ data.type === 'out' ? '-' : '+' }}{{ formatAmount(data.amount) }}
                  </span>
                </template>
              </Column>
              <Column field="reference" :header="t('cash.entry_reference')" />
              <Column field="description" :header="t('cash.entry_description')" />
              <Column field="balance_after" :header="t('cash.balance_after')">
                <template #body="{ data }">
                  {{ formatAmount(data.balance_after) }}
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
                <div class="app-empty-state">{{ t('accounting.balance.empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>

          <TabPanel value="counts">
            <DataTable
              :value="filteredCounts"
              :loading="loadingCounts"
              class="app-data-table"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              data-key="id"
              size="small"
              row-hover
            >
              <Column field="date" :header="t('cash.count_date')" sortable>
                <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
              </Column>
              <Column field="total_counted" :header="t('cash.count_total')" class="app-money">
                <template #body="{ data }">{{ formatAmount(data.total_counted) }}</template>
              </Column>
              <Column field="balance_expected" :header="t('cash.count_expected')" class="app-money">
                <template #body="{ data }">{{ formatAmount(data.balance_expected) }}</template>
              </Column>
              <Column field="difference" :header="t('cash.count_diff')" class="app-money">
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
              </Column>
              <Column field="notes" :header="t('cash.count_notes')" />
              <template #empty>
                <div class="app-empty-state">{{ t('accounting.balance.empty') }}</div>
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
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
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
import { useTableFilter, applyFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const toast = useToast()

const balance = ref('0')
const entries = ref<CashEntry[]>([])
const { filterText, filtered: filteredEntries } = useTableFilter(entries)
const counts = ref<CashCount[]>([])
const filteredCounts = computed(() => applyFilter(counts.value, filterText.value))
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
    const [b, e, c] = await Promise.all([getCashBalance(), listCashEntries(), listCashCounts()])
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

onMounted(loadAll)
</script>

<style scoped>
.cash-journal__actions {
  width: 8rem;
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
