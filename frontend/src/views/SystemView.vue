<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('system.title')"
      :subtitle="t('system.subtitle')"
    />

    <Tabs v-model:value="activeSystemTab">
      <TabList>
        <Tab value="monitoring">{{ t('system.tab_monitoring') }}</Tab>
        <Tab value="backups">{{ t('system.tab_backups') }}</Tab>
      </TabList>
    </Tabs>

    <!-- System status banner -->
    <AppPanel v-show="activeSystemTab === 'monitoring'">
      <div v-if="systemInfo" class="system-status">
        <div class="system-status__state">
          <span class="system-status__icon"><i class="pi pi-check-circle" /></span>
          <div>
            <p class="system-status__title">{{ t('system.status_ok') }}</p>
            <p class="system-status__subtitle">{{ t('system.status_subtitle') }}</p>
          </div>
        </div>
        <dl class="system-status__facts">
          <div class="system-status__fact">
            <dt>{{ t('system.version') }}</dt>
            <dd>{{ systemInfo.app_version }}</dd>
          </div>
          <div class="system-status__fact">
            <dt>{{ t('system.db_size') }}</dt>
            <dd>{{ formatBytes(systemInfo.db_size_bytes) }}</dd>
          </div>
          <div class="system-status__fact">
            <dt>{{ t('system.started_at') }}</dt>
            <dd>{{ formatDatetime(systemInfo.started_at) }}</dd>
          </div>
        </dl>
      </div>
      <Message v-if="systemInfoError" severity="error">{{ t('system.load_error') }}</Message>
    </AppPanel>

    <!-- Anomalies banner -->
    <AppPanel
      v-show="activeSystemTab === 'monitoring' && inconsistentPayments.length > 0"
      class="system-anomaly"
    >
      <div class="system-anomaly__row">
        <span class="system-anomaly__icon"><i class="pi pi-exclamation-triangle" /></span>
        <div class="system-anomaly__copy">
          <p class="system-anomaly__title">{{ t('system.anomaly_cheques') }}</p>
          <p class="system-anomaly__sub">
            {{ t('system.anomaly_cheques_sub', { count: inconsistentPayments.length }) }}
          </p>
        </div>
        <Button
          :label="t('system.anomaly_fix')"
          icon="pi pi-arrow-right"
          icon-pos="right"
          severity="warn"
          @click="fixDialogVisible = true"
        />
      </div>
    </AppPanel>

    <!-- Automated backup -->
    <SettingsBackupPanel v-show="activeSystemTab === 'backups'" />

    <!-- Backups -->
    <AppPanel
      v-show="activeSystemTab === 'backups'"
      :title="t('system.backup_title')"
      :subtitle="t('system.backup_subtitle')"
    >
      <div class="backup-actions">
        <div class="backup-create-row">
          <InputText
            v-model="backupLabel"
            :placeholder="t('system.backup_label_placeholder')"
            class="backup-label-input"
            :maxlength="100"
          />
          <Button
            :label="t('system.backup_download')"
            icon="pi pi-download"
            severity="secondary"
            outlined
            :loading="backing"
            @click="downloadBackup"
          />
        </div>
        <Message v-if="backupError" severity="error" :closable="true">
          {{ backupError }}
        </Message>
      </div>

      <div v-if="backupFiles.length > 0" class="backup-list">
        <h3 class="backup-list-title">{{ t('system.backup_list_title') }}</h3>
        <DataTable :value="backupFiles" size="small" striped-rows>
          <Column field="filename" :header="t('system.col_filename')" />
          <Column :header="t('system.col_label')">
            <template #body="{ data }">{{ data.label || '—' }}</template>
          </Column>
          <Column :header="t('system.col_size')">
            <template #body="{ data }">{{ formatBytes(data.size_bytes) }}</template>
          </Column>
          <Column :header="t('system.col_date')">
            <template #body="{ data }">{{ formatDatetime(data.created_at) }}</template>
          </Column>
          <Column header="" style="width: 7rem">
            <template #body="{ data }">
              <Button
                icon="pi pi-shield"
                size="small"
                severity="secondary"
                text
                :title="t('system.validate_btn')"
                :loading="validatingFile === data.filename"
                @click="validateBackup(data)"
              />
              <Button
                icon="pi pi-history"
                size="small"
                severity="danger"
                text
                :title="t('system.restore_btn')"
                @click="selectRestoreTarget(data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
      <p v-else class="empty-message">{{ t('system.backup_empty') }}</p>
    </AppPanel>

    <!-- Restore (inline, isolated destructive panel) -->
    <AppPanel v-show="activeSystemTab === 'backups'" class="restore-panel">
      <div class="restore-panel__header">
        <span class="restore-panel__icon"><i class="pi pi-exclamation-triangle" /></span>
        <div>
          <p class="restore-panel__title">{{ t('system.restore_title') }}</p>
          <p class="restore-panel__sub">{{ t('system.restore_subtitle') }}</p>
        </div>
      </div>
      <p v-if="!restoreTarget" class="restore-panel__hint">{{ t('system.restore_select_hint') }}</p>
      <template v-else>
        <p class="restore-panel__instructions">
          {{ t('system.restore_instructions') }}
          <strong class="restore-panel__file">{{ restoreTarget.filename }}</strong>
        </p>
        <Message v-if="restoreError" severity="error" :closable="false">{{ restoreError }}</Message>
        <div class="restore-panel__action">
          <InputText
            v-model="restoreConfirmText"
            class="restore-panel__input"
            :placeholder="RESTORE_KEYWORD"
            autocomplete="off"
          />
          <Button
            :label="t('system.restore_proceed_btn')"
            icon="pi pi-history"
            severity="danger"
            :disabled="restoreConfirmText.trim().toUpperCase() !== RESTORE_KEYWORD || restoring"
            :loading="restoring"
            @click="executeRestore"
          />
        </div>
      </template>
    </AppPanel>

    <!-- Backup validation result -->
    <Dialog
      v-model:visible="validateDialogVisible"
      :header="t('system.backup_validate_title')"
      modal
      :style="{ width: '30rem' }"
    >
      <div v-if="validateResult" class="validate-result">
        <Message :severity="validateResult.ok ? 'success' : 'error'" :closable="false">
          {{ validateResult.ok ? t('system.backup_validate_ok') : t('system.backup_validate_fail') }}
        </Message>
        <div v-if="!validateResult.ok" class="validate-details">
          <p v-if="validateResult.error">{{ validateResult.error }}</p>
          <p v-else>
            <strong>{{ t('system.backup_validate_integrity') }}</strong> : {{ validateResult.integrity_check }}<br />
            <strong>{{ t('system.backup_validate_tables_missing') }}</strong> :
            {{ validateResult.tables_missing.length ? validateResult.tables_missing.join(', ') : '—' }}
          </p>
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.close')" @click="validateDialogVisible = false" />
      </template>
    </Dialog>

    <!-- Application logs -->
    <AppPanel v-show="activeSystemTab === 'monitoring'" :title="t('system.logs_title')">
      <template #actions>
        <div class="logs-chips">
          <button
            v-for="lvl in logLevelChips"
            :key="lvl.value"
            type="button"
            :class="[
              'logs-chip',
              `logs-chip--${lvl.value.toLowerCase()}`,
              { 'logs-chip--active': selectedLevels.includes(lvl.value) },
            ]"
            @click="toggleLevel(lvl.value)"
          >
            {{ lvl.label }}
          </button>
        </div>
      </template>
      <div ref="logsContainerRef" class="logs-container">
        <p v-if="logsLoading" class="empty-message">{{ t('common.loading') }}</p>
        <p v-else-if="logs.length === 0" class="empty-message">{{ t('system.logs_empty') }}</p>
        <div
          v-for="(entry, i) in logs"
          v-else
          :key="i"
          :class="['log-line', `log-${entry.level.toLowerCase()}`]"
        >
          <span class="log-ts">{{ entry.timestamp }}</span>
          <span :class="['log-level', `log-level--${entry.level.toLowerCase()}`]">{{ entry.level }}</span>
          <span class="log-logger">{{ entry.logger }}</span>
          <span class="log-msg">{{ entry.message }}</span>
        </div>
      </div>
    </AppPanel>

    <!-- Inconsistent cheque payments (admin) — opened from the anomalies banner -->
    <Dialog
      v-model:visible="fixDialogVisible"
      :header="t('system.inconsistent_payments_title')"
      modal
      :style="{ width: 'min(56rem, 96vw)' }"
    >
      <p class="restore-panel__instructions">{{ t('system.inconsistent_payments_subtitle') }}</p>
      <p v-if="inconsistentPayments.length === 0" class="empty-message">
        {{ t('system.inconsistent_payments_empty') }}
      </p>
      <DataTable v-else :value="inconsistentPayments" size="small" striped-rows>
        <Column :header="t('system.col_payment_date')" style="white-space: nowrap">
          <template #body="{ data }">{{ data.date }}</template>
        </Column>
        <Column :header="t('system.col_invoice')">
          <template #body="{ data }">{{ data.invoice_number ?? '—' }}</template>
        </Column>
        <Column :header="t('system.col_contact')">
          <template #body="{ data }">{{ data.contact_label }}</template>
        </Column>
        <Column :header="t('system.col_amount')" style="text-align: right">
          <template #body="{ data }">{{ formatAmount(data.amount) }}</template>
        </Column>
        <Column :header="t('system.col_deposit_date')" style="min-width: 12rem">
          <template #body="{ data }">
            <AppDatePicker v-model="data._fixDate" show-clear style="width: 10rem" />
          </template>
        </Column>
        <Column header="" style="width: 6rem">
          <template #body="{ data }">
            <Button
              :label="t('system.inconsistent_payments_fix')"
              size="small"
              severity="success"
              :disabled="!data._fixDate"
              :loading="data._fixing"
              @click="fixInconsistentPayment(data)"
            />
          </template>
        </Column>
      </DataTable>
    </Dialog>

    <!-- Audit log -->
    <AppPanel
      v-show="activeSystemTab === 'monitoring'"
      :title="t('system.audit_title')"
      :subtitle="t('system.audit_subtitle')"
    >
      <p v-if="auditLogs.length === 0" class="empty-message">{{ t('system.audit_empty') }}</p>
      <DataTable v-else :value="auditLogs" size="small" striped-rows paginator :rows="50">
        <Column :header="t('system.col_timestamp')" style="white-space: nowrap">
          <template #body="{ data }">{{ formatDatetime(data.created_at) }}</template>
        </Column>
        <Column field="actor_username" :header="t('system.col_actor')" />
        <Column :header="t('system.col_action')" style="min-width: 18rem">
          <template #body="{ data }">
            {{ tAuditAction(data.action) }}
          </template>
        </Column>
        <Column :header="t('system.col_target')">
          <template #body="{ data }">
            <span v-if="data.target_type">{{ data.target_type }} #{{ data.target_id }}</span>
            <span v-else>—</span>
          </template>
        </Column>
        <Column :header="t('system.col_detail')" style="font-size: 0.6em">
          <template #body="{ data }">
            <code v-if="data.detail" class="audit-detail">{{
              JSON.stringify(data.detail)
            }}</code>
            <span v-else>—</span>
          </template>
        </Column>
      </DataTable>
    </AppPanel>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import {
  type AuditLogEntry,
  type BackupFile,
  type LogEntry,
  type SystemInfo,
  createBackupApi,
  getAuditLogsApi,
  getLogsApi,
  getSystemInfoApi,
  listBackupsApi,
  restoreBackupApi,
} from '@/api/settings'
import { testRestoreBackup, type BackupRestoreTestResult } from '@/api/backup'
import { listPayments, fixDepositDate, type Payment } from '@/api/payments'
import AppDatePicker from '@/components/ui/AppDatePicker.vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import SettingsBackupPanel from '@/components/settings/SettingsBackupPanel.vue'
import AppPanel from '@/components/ui/AppPanel.vue'

const RESTORE_KEYWORD = 'RESTAURER'

const logLevelChips = [
  { label: 'INFO', value: 'INFO' },
  { label: 'WARN', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' },
]

const { t } = useI18n()
const toast = useToast()

// --- State ---
const activeSystemTab = ref<'monitoring' | 'backups'>('monitoring')
const systemInfo = ref<SystemInfo | null>(null)
const systemInfoError = ref(false)
const backupFiles = ref<BackupFile[]>([])
const backing = ref(false)
const backupError = ref('')
const backupLabel = ref('')

// --- Inconsistent payments state ---
type InconsistentRow = Payment & { contact_label: string; _fixDate: Date | null; _fixing: boolean }
const inconsistentPayments = ref<InconsistentRow[]>([])

// --- Restore state ---
const restoreTarget = ref<BackupFile | null>(null)
const restoring = ref(false)
const restoreError = ref('')
const restoreConfirmText = ref('')

// --- Fix anomalies dialog ---
const fixDialogVisible = ref(false)

// --- Validate state ---
const validatingFile = ref<string | null>(null)
const validateResult = ref<BackupRestoreTestResult | null>(null)
const validateDialogVisible = ref(false)
const logs = ref<LogEntry[]>([])
const logsLoading = ref(false)
const auditLogs = ref<AuditLogEntry[]>([])
const selectedLevels = ref<string[]>([])
const logsContainerRef = ref<HTMLElement | null>(null)

function toggleLevel(level: string): void {
  const idx = selectedLevels.value.indexOf(level)
  if (idx === -1) {
    selectedLevels.value = [...selectedLevels.value, level]
  } else {
    selectedLevels.value = selectedLevels.value.filter((l) => l !== level)
  }
}

// --- Methods ---
function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(2)} Mo`
}

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

function tAuditAction(action: string): string {
  // Use dot-path as fallback: if the key is not found, vue-i18n returns the key itself.
  const key = `system.action.${action}`
  const result = t(key)
  return result === key ? action : result
}

async function downloadBackup(): Promise<void> {
  backing.value = true
  backupError.value = ''
  try {
    const label = backupLabel.value.trim() || null
    const blob = await createBackupApi(label)
    const url = URL.createObjectURL(blob)
    const ts = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '').replace(/-/g, '')
    const filename = `solde_backup_${ts}.db`
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    backupLabel.value = ''
    // Refresh backup list
    backupFiles.value = await listBackupsApi()
  } catch (err: unknown) {
    // Extract the first Pydantic validation message if available, otherwise generic
    const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    if (Array.isArray(detail) && detail.length > 0 && detail[0]?.msg) {
      backupError.value = String(detail[0].msg).replace(/^Value error, /, '')
    } else if (typeof detail === 'string') {
      backupError.value = detail
    } else {
      backupError.value = t('system.backup_error')
    }
  } finally {
    backing.value = false
  }
}

async function validateBackup(file: BackupFile): Promise<void> {
  validatingFile.value = file.filename
  try {
    validateResult.value = await testRestoreBackup(file.filename)
    validateDialogVisible.value = true
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    validatingFile.value = null
  }
}

function selectRestoreTarget(file: BackupFile): void {
  restoreTarget.value = file
  restoreError.value = ''
  restoreConfirmText.value = ''
}

async function executeRestore(): Promise<void> {
  if (!restoreTarget.value) return
  restoring.value = true
  restoreError.value = ''
  try {
    await restoreBackupApi(restoreTarget.value.filename)
    // Poll /api/health until the restarted server responds
    await pollUntilHealthy()
    window.location.reload()
  } catch {
    restoreError.value = t('system.restore_error')
    restoring.value = false
  }
}

async function pollUntilHealthy(): Promise<void> {
  const delay = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

  // Phase 1 — wait for the server to go down (confirms restart started).
  // Allow up to 10 s; break as soon as a request fails.
  for (let i = 0; i < 10; i++) {
    await delay(1000)
    try {
      const res = await fetch('/api/health')
      if (!res.ok) break
    } catch {
      break // connection refused → server is down
    }
  }

  // Phase 2 — wait for the server to come back up (up to 60 s).
  for (let i = 0; i < 30; i++) {
    await delay(2000)
    try {
      const res = await fetch('/api/health')
      if (res.ok) return
    } catch {
      // not yet up — keep polling
    }
  }
  throw new Error('Server did not come back online within the expected time.')
}

async function loadInconsistentPayments(): Promise<void> {
  try {
    const raw = await listPayments({ inconsistent_only: true })
    inconsistentPayments.value = raw.map((p) => ({
      ...p,
      contact_label: p.contact_name ?? p.invoice_number ?? String(p.contact_id),
      _fixDate: null,
      _fixing: false,
    }))
  } catch {
    // silently ignore — non-critical section
  }
}

function toLocalDateString(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function fixInconsistentPayment(row: InconsistentRow): Promise<void> {
  if (!row._fixDate) return
  row._fixing = true
  try {
    await fixDepositDate(row.id, toLocalDateString(row._fixDate))
    inconsistentPayments.value = inconsistentPayments.value.filter((r) => r.id !== row.id)
    toast.add({ severity: 'success', summary: t('system.inconsistent_payments_fixed'), life: 3000 })
  } catch {
    row._fixing = false
    toast.add({ severity: 'error', summary: t('system.inconsistent_payments_fix_error'), life: 5000 })
  }
}

async function loadLogs(): Promise<void> {
  logsLoading.value = true
  try {
    logs.value = await getLogsApi(selectedLevels.value.length > 0 ? selectedLevels.value : undefined)
  } catch {
    // silently ignore — user can retry by toggling a level chip
  } finally {
    logsLoading.value = false
  }
}

watch(selectedLevels, () => {
  void loadLogs()
})

// --- Init ---
onMounted(async () => {
  await Promise.all([
    getSystemInfoApi()
      .then((d) => (systemInfo.value = d))
      .catch(() => (systemInfoError.value = true)),
    listBackupsApi()
      .then((d) => (backupFiles.value = d))
      .catch((e) => console.error('Failed to load backups', e)),
    getAuditLogsApi()
      .then((d) => (auditLogs.value = d))
      .catch((e) => console.error('Failed to load audit logs', e)),
    loadInconsistentPayments(),
    loadLogs(),
  ])
})
</script>

<style scoped>
.system-status {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-5);
}

.system-status__state {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
}

.system-status__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  font-size: 1.4rem;
  background: color-mix(in srgb, var(--p-green-500, #22c55e) 16%, transparent);
  color: var(--p-green-600, #16a34a);
}

.system-status__title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.system-status__subtitle {
  margin: 0.1rem 0 0;
  color: var(--p-text-muted-color);
  font-size: 0.88rem;
}

.system-status__facts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-6);
  margin: 0;
}

.system-status__fact {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.system-status__fact dt {
  font-size: 0.72rem;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.system-status__fact dd {
  margin: 0;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

/* Anomalies banner */
.system-anomaly {
  border-color: color-mix(in srgb, var(--p-amber-500, #f59e0b) 45%, var(--app-surface-border));
  background: color-mix(in srgb, var(--p-amber-500, #f59e0b) 10%, var(--app-surface-bg));
}

.system-anomaly__row {
  display: flex;
  align-items: center;
  gap: var(--app-space-4);
}

.system-anomaly__icon {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--p-amber-500, #f59e0b) 20%, transparent);
  color: var(--p-amber-600, #b45309);
  font-size: 1.1rem;
}

.system-anomaly__copy {
  flex: 1;
  min-width: 0;
}

.system-anomaly__title {
  margin: 0;
  font-weight: 800;
}

.system-anomaly__sub {
  margin: 0.1rem 0 0;
  color: var(--p-text-muted-color);
  font-size: 0.88rem;
}

/* Log level chips */
.logs-chips {
  display: inline-flex;
  gap: 0.4rem;
}

.logs-chip {
  border: 1px solid var(--app-surface-border);
  border-radius: 999px;
  padding: 0.2rem 0.7rem;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  cursor: pointer;
  background: transparent;
  color: var(--p-text-muted-color);
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.logs-chip--active.logs-chip--info {
  background: color-mix(in srgb, var(--p-blue-500, #3b82f6) 18%, transparent);
  border-color: var(--p-blue-500, #3b82f6);
  color: var(--p-blue-500, #60a5fa);
}

.logs-chip--active.logs-chip--warning {
  background: color-mix(in srgb, var(--p-amber-500, #f59e0b) 20%, transparent);
  border-color: var(--p-amber-500, #f59e0b);
  color: var(--p-amber-600, #f59e0b);
}

.logs-chip--active.logs-chip--error {
  background: color-mix(in srgb, var(--p-red-500, #ef4444) 18%, transparent);
  border-color: var(--p-red-500, #ef4444);
  color: var(--p-red-500, #f87171);
}

/* Inline restore panel (isolated destructive) */
.restore-panel {
  border-color: color-mix(in srgb, var(--p-red-500, #ef4444) 35%, var(--app-surface-border));
  background: color-mix(in srgb, var(--p-red-500, #ef4444) 8%, var(--app-surface-bg));
}

.restore-panel__header {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  margin-bottom: var(--app-space-3);
}

.restore-panel__icon {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--p-red-500, #ef4444) 16%, transparent);
  color: var(--p-red-500, #dc2626);
  font-size: 1.1rem;
}

.restore-panel__title {
  margin: 0;
  font-weight: 800;
  color: var(--p-red-500, #dc2626);
}

.restore-panel__sub {
  margin: 0.1rem 0 0;
  color: var(--p-text-muted-color);
  font-size: 0.88rem;
}

.restore-panel__hint {
  margin: 0;
  color: var(--p-text-muted-color);
  font-style: italic;
}

.restore-panel__instructions {
  margin: 0 0 var(--app-space-3);
}

.restore-panel__file {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.restore-panel__action {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-2);
  align-items: center;
}

.restore-panel__input {
  max-width: 16rem;
}

.backup-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: flex-start;
}

.backup-create-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.backup-label-input {
  min-width: 220px;
}

.restore-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.restore-filename {
  font-family: monospace;
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}

.restore-confirm-label {
  font-size: 0.85rem;
  font-weight: 600;
}

.restore-confirm-input {
  width: 100%;
}

.restore-file-details {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.backup-list {
  margin-top: 1.5rem;
}

.backup-list-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.logs-load-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.logs-count {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
}

.logs-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  align-items: center;
}

.logs-level-filter {
  width: 200px;
}

.logs-search {
  flex: 1;
  min-width: 160px;
}

.logs-container {
  max-height: 400px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 0.78rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: var(--p-border-radius-sm);
  padding: 0.5rem;
  background: var(--p-surface-950, #0a0a0a);
}

.log-line {
  display: flex;
  gap: 0.5rem;
  padding: 1px 0;
  line-height: 1.4;
}

.log-ts {
  color: var(--p-text-muted-color);
  flex-shrink: 0;
}

.log-level {
  flex-shrink: 0;
  width: 7ch;
  font-weight: 600;
}

.log-level--debug {
  color: #6b7280;
}
.log-level--info {
  color: #e5e7eb;
}
.log-level--warning {
  color: #f59e0b;
}
.log-level--error {
  color: #ef4444;
}

.log-logger {
  color: #60a5fa;
  flex-shrink: 0;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-msg {
  color: #d1d5db;
  word-break: break-all;
}

.empty-message {
  color: var(--p-text-muted-color);
  font-style: italic;
}

.audit-detail {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}
</style>
