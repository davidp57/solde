<template>
  <AppPanel :title="t('system.audit_title')" :subtitle="t('system.audit_subtitle')">
    <div class="audit-toolbar">
      <InputText
        v-model="search"
        class="audit-search"
        :placeholder="t('system.audit_search')"
        :aria-label="t('system.audit_search')"
      />
      <Select
        v-model="area"
        :options="areaOptions"
        option-label="label"
        option-value="value"
        show-clear
        :placeholder="t('system.audit_area.all')"
        :aria-label="t('system.audit_filter_area')"
      />
      <label class="audit-date">
        <span>{{ t('system.audit_filter_from') }}</span>
        <AppDatePicker v-model="fromDate" show-clear />
      </label>
      <label class="audit-date">
        <span>{{ t('system.audit_filter_to') }}</span>
        <AppDatePicker v-model="toDate" show-clear />
      </label>
      <span class="audit-total">{{ t('system.audit_total', { n: total }) }}</span>
    </div>

    <DataTable
      :value="entries"
      size="small"
      striped-rows
      lazy
      paginator
      :rows="PAGE_SIZE"
      :first="first"
      :total-records="total"
      :loading="loading"
      data-key="id"
      @page="onPage"
    >
      <template #empty>{{ t('system.audit_empty') }}</template>
      <Column :header="t('system.col_timestamp')" style="white-space: nowrap">
        <template #body="{ data }">{{ formatDatetime(data.created_at) }}</template>
      </Column>
      <Column field="actor_username" :header="t('system.col_actor')" />
      <Column :header="t('system.col_action')" style="min-width: 14rem">
        <template #body="{ data }">{{ auditActionLabel(data.action) }}</template>
      </Column>
      <Column :header="t('system.col_target')" style="min-width: 16rem">
        <template #body="{ data }">
          <template v-if="data.target_type">
            <span v-if="data.target_label">{{ data.target_label }}</span>
            <span class="audit-target-ref">
              {{ data.target_type }}<template v-if="data.target_id"> #{{ data.target_id }}</template>
            </span>
          </template>
          <span v-else>—</span>
        </template>
      </Column>
      <Column :header="t('system.col_detail')" style="min-width: 16rem">
        <template #body="{ data }">
          <dl v-if="data.detail" class="audit-detail">
            <template v-for="item in formatAuditDetail(data.detail)" :key="item.label">
              <dt>{{ item.label }}</dt>
              <dd v-if="item.values.length === 1">{{ item.values[0] }}</dd>
              <dd v-else>
                <ul>
                  <li v-for="(value, index) in item.values" :key="index">{{ value }}</li>
                </ul>
              </dd>
            </template>
          </dl>
          <span v-else>—</span>
        </template>
      </Column>
    </DataTable>
  </AppPanel>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Column from 'primevue/column'
import DataTable, { type DataTablePageEvent } from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import { type AuditLogEntry, searchAuditLogsApi } from '@/api/settings'
import AppDatePicker from '@/components/ui/AppDatePicker.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import { auditActionLabel, formatAuditDetail, matchingActionCodes } from '@/utils/auditLog'
import { getErrorDetail } from '@/utils/errorUtils'

const PAGE_SIZE = 50
const SEARCH_DEBOUNCE_MS = 300
const AREAS = [
  'auth',
  'admin',
  'bank',
  'invoice',
  'payment',
  'cash',
  'salary',
  'contact',
  'document',
  'import',
  'checklist',
  'chat',
] as const

const { t } = useI18n()
const toast = useToast()

const entries = ref<AuditLogEntry[]>([])
const total = ref(0)
const first = ref(0)
const loading = ref(false)
const search = ref('')
const area = ref<string | null>(null)
const fromDate = ref<Date | null>(null)
const toDate = ref<Date | null>(null)

const areaOptions = computed(() =>
  AREAS.map((key) => ({ label: t(`system.audit_area.${key}`), value: `${key}.` })),
)

function normalizeUtcIsoString(iso: string): string {
  // SQLite returns naive UTC datetimes (no timezone suffix); append Z so JS interprets as UTC.
  return /Z$|[+-]\d{2}:\d{2}$/.test(iso) ? iso : `${iso}Z`
}

function formatDatetime(iso: string): string {
  return new Date(normalizeUtcIsoString(iso)).toLocaleString('fr-FR', {
    dateStyle: 'short',
    timeStyle: 'short',
  })
}

// The pickers give a local calendar day: the range runs from its first to its last
// second, sent in UTC like the stored timestamps.
function dayStart(day: Date): string {
  return new Date(day.getFullYear(), day.getMonth(), day.getDate()).toISOString()
}

function dayEnd(day: Date): string {
  return new Date(day.getFullYear(), day.getMonth(), day.getDate(), 23, 59, 59, 999).toISOString()
}

// Responses can come back out of order while typing: only the latest one is shown.
let requestSeq = 0

async function load(): Promise<void> {
  const seq = ++requestSeq
  loading.value = true
  const q = search.value.trim()
  try {
    const { items, total: count } = await searchAuditLogsApi({
      q: q || undefined,
      q_actions: q ? matchingActionCodes(q) : undefined,
      action: area.value || undefined,
      from_date: fromDate.value ? dayStart(fromDate.value) : undefined,
      to_date: toDate.value ? dayEnd(toDate.value) : undefined,
      skip: first.value,
      limit: PAGE_SIZE,
    })
    if (seq !== requestSeq) return
    entries.value = items
    total.value = count
  } catch (err: unknown) {
    if (seq !== requestSeq) return
    toast.add({ severity: 'error', summary: getErrorDetail(err, t('system.load_error')), life: 5000 })
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

function onPage(event: DataTablePageEvent): void {
  first.value = event.first
  void load()
}

function reloadFromFirstPage(): void {
  first.value = 0
  void load()
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(reloadFromFirstPage, SEARCH_DEBOUNCE_MS)
})
watch([area, fromDate, toDate], reloadFromFirstPage)

onMounted(load)
</script>

<style scoped>
.audit-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.audit-search {
  flex: 1 1 18rem;
  min-width: 0;
}

.audit-date {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.audit-total {
  margin-left: auto;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.audit-target-ref {
  display: block;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.audit-detail {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.1rem 0.6rem;
  margin: 0;
  font-size: 0.8rem;
}

.audit-detail dt {
  color: var(--p-text-muted-color);
}

.audit-detail dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.audit-detail ul {
  margin: 0;
  padding-left: 1rem;
}
</style>
