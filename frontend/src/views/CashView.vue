<template>
  <div class="cash-view p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">{{ t('cash.title') }}</h2>
      <div class="flex gap-2">
        <Button :label="t('cash.new_count')" icon="pi pi-calculator" severity="secondary" @click="countDialogVisible = true" />
        <Button :label="t('cash.new_entry')" icon="pi pi-plus" @click="entryDialogVisible = true" />
      </div>
    </div>

    <!-- Balance card -->
    <div class="balance-card mb-6">
      <span class="label">{{ t('cash.balance') }}</span>
      <span class="amount">{{ formatAmount(balance) }}</span>
    </div>

    <!-- Tabs: journal / counts -->
    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="journal">{{ t('cash.journal') }}</Tab>
        <Tab value="counts">{{ t('cash.counts_title') }}</Tab>
      </TabList>

      <TabPanels>
        <TabPanel value="journal">
          <DataTable :value="entries" :loading="loadingEntries" striped-rows paginator :rows="20" data-key="id">
            <Column field="date" :header="t('cash.entry_date')" sortable />
            <Column field="type" :header="t('cash.entry_type')">
              <template #body="{ data }">
                <Tag
                  :value="t(`cash.movements.${data.type}`)"
                  :severity="data.type === 'in' ? 'success' : 'danger'"
                />
              </template>
            </Column>
            <Column field="amount" :header="t('cash.entry_amount')">
              <template #body="{ data }">
                <span :class="data.type === 'out' ? 'text-red-500' : 'text-green-600'">
                  {{ data.type === 'out' ? '-' : '+' }}{{ formatAmount(data.amount) }}
                </span>
              </template>
            </Column>
            <Column field="description" :header="t('cash.entry_description')" />
            <Column field="balance_after" :header="t('cash.balance_after')">
              <template #body="{ data }">
                {{ formatAmount(data.balance_after) }}
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <TabPanel value="counts">
          <DataTable :value="counts" :loading="loadingCounts" striped-rows paginator :rows="10" data-key="id">
            <Column field="date" :header="t('cash.count_date')" sortable />
            <Column field="total_counted" :header="t('cash.count_total')">
              <template #body="{ data }">{{ formatAmount(data.total_counted) }}</template>
            </Column>
            <Column field="balance_expected" :header="t('cash.count_expected')">
              <template #body="{ data }">{{ formatAmount(data.balance_expected) }}</template>
            </Column>
            <Column field="difference" :header="t('cash.count_diff')">
              <template #body="{ data }">
                <span :class="parseFloat(data.difference) < 0 ? 'text-red-500 font-semibold' : parseFloat(data.difference) > 0 ? 'text-orange-500' : 'text-green-600'">
                  {{ formatAmount(data.difference) }}
                </span>
              </template>
            </Column>
            <Column field="notes" :header="t('cash.count_notes')" />
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <!-- New entry dialog -->
    <Dialog v-model:visible="entryDialogVisible" :header="t('cash.new_entry')" modal :style="{ width: '420px' }">
      <form class="flex flex-col gap-3" @submit.prevent="submitEntry">
        <div class="flex flex-col gap-1">
          <label>{{ t('cash.entry_date') }}</label>
          <DatePicker v-model="entryForm.date" date-format="yy-mm-dd" show-icon />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('cash.entry_type') }}</label>
          <Select v-model="entryForm.type" :options="movementTypes" option-label="label" option-value="value" />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('cash.entry_amount') }}</label>
          <InputNumber v-model="entryForm.amount" mode="decimal" :min-fraction-digits="2" :max-fraction-digits="2" :min="0.01" />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('cash.entry_description') }}</label>
          <InputText v-model="entryForm.description" />
        </div>
        <div class="flex justify-end gap-2 mt-2">
          <Button :label="t('common.cancel')" severity="secondary" text @click="entryDialogVisible = false" />
          <Button type="submit" :label="t('common.save')" :loading="saving" />
        </div>
      </form>
    </Dialog>

    <!-- New count dialog -->
    <Dialog v-model:visible="countDialogVisible" :header="t('cash.new_count')" modal :style="{ width: '540px' }">
      <form class="flex flex-col gap-3" @submit.prevent="submitCount">
        <div class="flex flex-col gap-1">
          <label>{{ t('cash.count_date') }}</label>
          <DatePicker v-model="countForm.date" date-format="yy-mm-dd" show-icon />
        </div>
        <div class="grid grid-cols-2 gap-2">
          <template v-for="denom in denominations" :key="denom.field">
            <div class="flex flex-col gap-1">
              <label>{{ denom.label }}</label>
              <InputNumber v-model="(countForm as Record<string, number>)[denom.field]" :min="0" />
            </div>
          </template>
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('cash.count_notes') }}</label>
          <Textarea v-model="countForm.notes" rows="2" />
        </div>
        <div class="flex justify-end gap-2 mt-2">
          <Button :label="t('common.cancel')" severity="secondary" text @click="countDialogVisible = false" />
          <Button type="submit" :label="t('common.save')" :loading="saving" />
        </div>
      </form>
    </Dialog>
  </div>
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
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  addCashCount,
  addCashEntry,
  getCashBalance,
  listCashCounts,
  listCashEntries,
  type CashCount,
  type CashEntry,
} from '@/api/cash'

const { t } = useI18n()
const toast = useToast()

const balance = ref('0')
const entries = ref<CashEntry[]>([])
const counts = ref<CashCount[]>([])
const loadingEntries = ref(false)
const loadingCounts = ref(false)
const activeTab = ref('journal')
const entryDialogVisible = ref(false)
const countDialogVisible = ref(false)
const saving = ref(false)

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

const entryForm = ref({
  date: new Date(),
  type: 'in' as 'in' | 'out',
  amount: 0,
  description: '',
})

const countForm = ref<Record<string, number | string | null>>({
  date: new Date() as unknown as string,
  count_100: 0, count_50: 0, count_20: 0, count_10: 0, count_5: 0,
  count_2: 0, count_1: 0, count_cents_50: 0, count_cents_20: 0,
  count_cents_10: 0, count_cents_5: 0, count_cents_2: 0, count_cents_1: 0,
  notes: null,
})

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function toIsoDate(d: Date | string): string {
  if (typeof d === 'string') return d
  return d.toISOString().slice(0, 10)
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
    await addCashEntry({
      date: toIsoDate(entryForm.value.date as unknown as Date),
      type: entryForm.value.type,
      amount: String(entryForm.value.amount),
      description: entryForm.value.description,
    })
    entryDialogVisible.value = false
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
    const payload: Record<string, number | string | null> = { ...countForm.value }
    payload.date = toIsoDate(payload.date as unknown as Date)
    await addCashCount(payload as Parameters<typeof addCashCount>[0])
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
.balance-card {
  display: inline-flex;
  align-items: center;
  gap: 1rem;
  background: var(--p-surface-100);
  border-radius: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: 1px solid var(--p-surface-200);
}
.balance-card .label {
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
}
.balance-card .amount {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--p-primary-color);
}
</style>
