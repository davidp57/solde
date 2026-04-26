<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('system.title')"
      :subtitle="t('system.subtitle')"
    />

    <!-- État système -->
    <AppPanel :title="t('system.info_title')">
      <div v-if="systemInfo" class="system-info-grid">
        <div class="system-info-item">
          <span class="system-info-label">{{ t('system.version') }}</span>
          <span class="system-info-value">{{ systemInfo.app_version }}</span>
        </div>
        <div class="system-info-item">
          <span class="system-info-label">{{ t('system.db_size') }}</span>
          <span class="system-info-value">{{ formatBytes(systemInfo.db_size_bytes) }}</span>
        </div>
        <div class="system-info-item">
          <span class="system-info-label">{{ t('system.started_at') }}</span>
          <span class="system-info-value">{{ formatDatetime(systemInfo.started_at) }}</span>
        </div>
        <div class="system-info-item">
          <span class="system-info-label">Statut</span>
          <Tag :value="t('system.status_ok')" severity="success" icon="pi pi-check-circle" />
        </div>
      </div>
      <Message v-if="systemInfoError" severity="error">{{ t('system.load_error') }}</Message>
    </AppPanel>

    <!-- Sauvegardes -->
    <AppPanel :title="t('system.backup_title')" :subtitle="t('system.backup_subtitle')">
      <div class="backup-actions">
        <Button
          :label="t('system.backup_download')"
          icon="pi pi-download"
          severity="secondary"
          outlined
          :loading="backing"
          @click="downloadBackup"
        />
        <Message v-if="backupError" severity="error" :closable="true">
          {{ backupError }}
        </Message>
      </div>

      <div v-if="backupFiles.length > 0" class="backup-list">
        <h3 class="backup-list-title">{{ t('system.backup_list_title') }}</h3>
        <DataTable :value="backupFiles" size="small" striped-rows>
          <Column field="filename" :header="t('system.col_filename')" />
          <Column :header="t('system.col_size')">
            <template #body="{ data }">{{ formatBytes(data.size_bytes) }}</template>
          </Column>
          <Column :header="t('system.col_date')">
            <template #body="{ data }">{{ formatDatetime(data.created_at) }}</template>
          </Column>
        </DataTable>
      </div>
      <p v-else class="empty-message">{{ t('system.backup_empty') }}</p>
    </AppPanel>

    <!-- Journaux applicatifs -->
    <AppPanel :title="t('system.logs_title')">
      <div class="logs-toolbar">
        <MultiSelect
          v-model="selectedLevels"
          :options="levelOptions"
          :placeholder="t('system.logs_filter_level')"
          class="logs-level-filter"
          display="chip"
        />
        <InputText
          v-model="logSearch"
          :placeholder="t('system.logs_filter_search')"
          class="logs-search"
        />
        <Button
          :label="t('system.logs_scroll_bottom')"
          icon="pi pi-arrow-down"
          severity="secondary"
          outlined
          size="small"
          @click="scrollLogsBottom"
        />
      </div>
      <div ref="logsContainerRef" class="logs-container">
        <p v-if="filteredLogs.length === 0" class="empty-message">
          {{ t('system.logs_empty') }}
        </p>
        <div
          v-for="(entry, i) in filteredLogs"
          :key="i"
          :class="['log-line', `log-${entry.level.toLowerCase()}`]"
        >
          <span class="log-ts">{{ entry.timestamp }}</span>
          <span :class="['log-level', `log-level--${entry.level.toLowerCase()}`]">{{
            entry.level
          }}</span>
          <span class="log-logger">{{ entry.logger }}</span>
          <span class="log-msg">{{ entry.message }}</span>
        </div>
      </div>
    </AppPanel>

    <!-- Journal d'audit -->
    <AppPanel :title="t('system.audit_title')" :subtitle="t('system.audit_subtitle')">
      <p v-if="auditLogs.length === 0" class="empty-message">{{ t('system.audit_empty') }}</p>
      <DataTable v-else :value="auditLogs" size="small" striped-rows paginator :rows="50">
        <Column :header="t('system.col_timestamp')" style="white-space: nowrap">
          <template #body="{ data }">{{ formatDatetime(data.created_at) }}</template>
        </Column>
        <Column field="actor_username" :header="t('system.col_actor')" />
        <Column field="action" :header="t('system.col_action')" />
        <Column :header="t('system.col_target')">
          <template #body="{ data }">
            <span v-if="data.target_type">{{ data.target_type }} #{{ data.target_id }}</span>
            <span v-else>—</span>
          </template>
        </Column>
        <Column :header="t('system.col_detail')">
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
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import MultiSelect from 'primevue/multiselect'
import Tag from 'primevue/tag'
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
} from '@/api/settings'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'

const { t } = useI18n()

// --- State ---
const systemInfo = ref<SystemInfo | null>(null)
const systemInfoError = ref(false)
const backupFiles = ref<BackupFile[]>([])
const backing = ref(false)
const backupError = ref('')
const logs = ref<LogEntry[]>([])
const auditLogs = ref<AuditLogEntry[]>([])
const logSearch = ref('')
const selectedLevels = ref<string[]>([])
const logsContainerRef = ref<HTMLElement | null>(null)

const levelOptions = ['DEBUG', 'INFO', 'WARNING', 'ERROR']

// --- Computed ---
const filteredLogs = computed(() => {
  let result = logs.value
  if (selectedLevels.value.length > 0) {
    result = result.filter((l) => selectedLevels.value.includes(l.level))
  }
  if (logSearch.value.trim()) {
    const q = logSearch.value.trim().toLowerCase()
    result = result.filter(
      (l) => l.logger.toLowerCase().includes(q) || l.message.toLowerCase().includes(q),
    )
  }
  return result
})

// --- Methods ---
function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(2)} Mo`
}

function formatDatetime(iso: string): string {
  return new Date(iso).toLocaleString('fr-FR', {
    dateStyle: 'short',
    timeStyle: 'short',
  })
}

function scrollLogsBottom(): void {
  if (logsContainerRef.value) {
    logsContainerRef.value.scrollTop = logsContainerRef.value.scrollHeight
  }
}

async function downloadBackup(): Promise<void> {
  backing.value = true
  backupError.value = ''
  try {
    const blob = await createBackupApi()
    const url = URL.createObjectURL(blob)
    const filename = `solde_backup_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.db`
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    // Refresh backup list
    backupFiles.value = await listBackupsApi()
  } catch {
    backupError.value = t('system.backup_error')
  } finally {
    backing.value = false
  }
}

// --- Init ---
onMounted(async () => {
  await Promise.all([
    getSystemInfoApi()
      .then((d) => (systemInfo.value = d))
      .catch(() => (systemInfoError.value = true)),
    listBackupsApi()
      .then((d) => (backupFiles.value = d))
      .catch(() => {}),
    getLogsApi()
      .then((d) => (logs.value = d))
      .catch(() => {}),
    getAuditLogsApi()
      .then((d) => (auditLogs.value = d))
      .catch(() => {}),
  ])
})
</script>

<style scoped>
.system-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.system-info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.system-info-label {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.system-info-value {
  font-weight: 600;
}

.backup-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: flex-start;
}

.backup-list {
  margin-top: 1.5rem;
}

.backup-list-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
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
