<template>
  <AppPanel :title="t('settings.backup_title')" :subtitle="t('settings.backup_subtitle')">
    <!-- ── Planification ─────────────────────────────────────────────── -->
    <section class="backup-section">
      <h3 class="backup-section__title">{{ t('settings.backup_schedule_title') }}</h3>
      <div class="app-form-grid">
        <div class="settings-switch col-span-2">
          <ToggleSwitch id="backup_enabled" v-model="schedule.enabled" @change="saveSchedule" />
          <label for="backup_enabled" class="app-field__label">
            {{ t('settings.backup_enabled') }}
          </label>
        </div>

        <div class="app-field">
          <label class="app-field__label">{{ t('settings.backup_schedule_type') }}</label>
          <Select
            v-model="schedule.schedule_type"
            :options="scheduleTypeOptions"
            option-label="label"
            option-value="value"
            class="w-full"
            @change="saveSchedule"
          />
        </div>

        <div v-if="schedule.schedule_type === 'interval'" class="app-field">
          <label for="backup_interval_hours" class="app-field__label">
            {{ t('settings.backup_interval_hours') }}
          </label>
          <InputNumber
            id="backup_interval_hours"
            v-model="schedule.interval_hours"
            :min="1"
            :max="168"
            :use-grouping="false"
            class="w-full"
            @blur="saveSchedule"
          />
        </div>

        <div v-else-if="schedule.schedule_type === 'daily'" class="app-field">
          <label for="backup_daily_time" class="app-field__label">
            {{ t('settings.backup_daily_time') }}
          </label>
          <InputText
            id="backup_daily_time"
            v-model="schedule.daily_time"
            placeholder="02:00"
            class="w-full"
            @blur="saveSchedule"
          />
          <small class="app-field__help">{{ t('settings.backup_daily_time_help') }}</small>
        </div>

        <div v-else class="app-field">
          <label for="backup_cron" class="app-field__label">
            {{ t('settings.backup_cron_expression') }}
          </label>
          <InputText
            id="backup_cron"
            v-model="schedule.cron_expression"
            placeholder="0 2 * * *"
            class="w-full"
            @blur="saveSchedule"
          />
          <small class="app-field__help">{{ t('settings.backup_cron_help') }}</small>
        </div>

        <div class="settings-switch">
          <ToggleSwitch
            id="backup_include_uploads"
            v-model="schedule.include_uploads"
            @change="saveSchedule"
          />
          <label for="backup_include_uploads" class="app-field__label">
            {{ t('settings.backup_include_uploads') }}
          </label>
        </div>

        <div class="settings-switch">
          <ToggleSwitch
            id="backup_include_all_backups"
            v-model="schedule.include_all_backups"
            @change="saveSchedule"
          />
          <label for="backup_include_all_backups" class="app-field__label">
            {{ t('settings.backup_include_all_backups') }}
          </label>
        </div>

        <div class="settings-switch">
          <ToggleSwitch
            id="backup_notify_on_failure"
            v-model="schedule.notify_on_failure"
            @change="saveSchedule"
          />
          <label for="backup_notify_on_failure" class="app-field__label">
            {{ t('settings.backup_notify_on_failure') }}
          </label>
        </div>
      </div>
    </section>

    <!-- ── Statut dernier run ─────────────────────────────────────────── -->
    <section class="backup-section">
      <h3 class="backup-section__title">{{ t('settings.backup_status_title') }}</h3>
      <div class="backup-status">
        <span v-if="backupRunning" class="backup-running-indicator">
          <ProgressSpinner style="width: 1.1rem; height: 1.1rem" stroke-width="4" />
          {{ t('settings.backup_in_progress') }}
          <span v-if="runStatus.backup_progress > 0" class="backup-progress-pct">
            {{ runStatus.backup_progress }} %
          </span>
        </span>
        <template v-else>
          <span v-if="runStatus.last_run_at">
            {{ t('settings.backup_last_run') }} {{ formatDate(runStatus.last_run_at) }}
            <Tag
              :value="runStatus.last_run_status === 'success' ? t('settings.backup_success') : t('settings.backup_failure')"
              :severity="runStatus.last_run_status === 'success' ? 'success' : 'danger'"
              class="ml-2"
            />
            <span v-if="runStatus.last_run_status !== 'success' && runStatus.last_run_error" class="backup-status__error ml-2">
              {{ runStatus.last_run_error }}
            </span>
          </span>
          <span v-else class="text-color-secondary">{{ t('settings.backup_never_run') }}</span>
        </template>
        <Button
          :label="t('settings.backup_run_now')"
          icon="pi pi-play"
          severity="secondary"
          outlined
          :loading="runningNow"
          :disabled="backupRunning"
          class="ml-3"
          @click="runNow"
        />
        <Button
          icon="pi pi-refresh"
          severity="secondary"
          text
          :title="t('common.refresh')"
          class="ml-1"
          @click="loadStatus"
        />
      </div>
    </section>

    <!-- ── Destinations ──────────────────────────────────────────────── -->
    <section class="backup-section">
      <h3 class="backup-section__title">{{ t('settings.backup_destinations_title') }}</h3>

      <div class="dest-list">
        <div v-if="destinations.length === 0 && !loadingDests" class="dest-list__empty">
          {{ t('settings.backup_no_destinations') }}
        </div>
        <div v-for="dest in destinations" :key="dest.id" class="dest-row">
          <span class="dest-row__name">{{ dest.name }}</span>
          <Tag :value="dest.type" severity="secondary" class="dest-row__type" />
          <div class="dest-row__actions">
            <ToggleSwitch
              :model-value="dest.enabled"
              @update:model-value="(v) => toggleDestEnabled(dest, v)"
            />
            <Button
              icon="pi pi-wifi"
              :title="t('settings.backup_test_connection')"
              severity="secondary"
              text
              size="small"
              @click="testConnection(dest)"
            />
            <Button
              icon="pi pi-pencil"
              :title="t('common.edit')"
              severity="secondary"
              text
              size="small"
              @click="openEditDestDialog(dest)"
            />
            <Button
              icon="pi pi-trash"
              :title="t('common.delete')"
              severity="danger"
              text
              size="small"
              @click="confirmDeleteDest(dest)"
            />
          </div>
        </div>
        <button class="dest-row dest-row--add" @click="openAddDestDialog">
          <i class="pi pi-plus-circle" />
          <span>{{ t('settings.backup_add_destination') }}</span>
        </button>
      </div>
    </section>

  </AppPanel>

  <!-- ── Dialog ajouter / éditer destination ───────────────────────── -->
  <Dialog
    v-model:visible="showAddDestDialog"
    :header="editDestId ? t('settings.backup_edit_destination') : t('settings.backup_add_destination')"
    modal
    :style="{ width: '480px' }"
  >
    <div class="app-form-grid">
      <div class="app-field col-span-2">
        <label class="app-field__label">{{ t('common.name') }}</label>
        <InputText v-model="newDest.name" class="w-full" />
      </div>
      <div class="app-field col-span-2">
        <label class="app-field__label">{{ t('settings.backup_dest_type') }}</label>
        <Select
          v-model="newDest.type"
          :options="destTypeOptions"
          option-label="label"
          option-value="value"
          class="w-full"
        />
      </div>
      <div v-if="newDest.type !== 'onedrive'" class="app-field col-span-2">
        <label class="app-field__label">{{ t('settings.backup_target_path') }}</label>
        <InputText v-model="newDest.target_path" class="w-full" />
      </div>

      <!-- SMB-specific fields -->
      <template v-if="newDest.type === 'smb'">
        <div class="app-field">
          <label class="app-field__label">{{ t('settings.backup_smb_host') }}</label>
          <InputText v-model="smbForm.host" class="w-full" />
        </div>
        <div class="app-field">
          <label class="app-field__label">{{ t('settings.backup_smb_user') }}</label>
          <InputText v-model="smbForm.user" class="w-full" />
        </div>
        <div class="app-field col-span-2">
          <label class="app-field__label">{{ t('settings.backup_smb_password') }}</label>
          <Password v-model="smbForm.pass" :feedback="false" toggle-mask class="w-full" />
        </div>
      </template>

      <!-- OneDrive — Device Authorization Flow (headless, works in Docker) -->
      <template v-else-if="newDest.type === 'onedrive'">
        <div class="app-field col-span-2">
          <!-- Step 0: start button -->
          <template v-if="!oauthPolling && !oauthDone">
            <Message severity="info" :closable="false">
              {{ t('settings.backup_onedrive_device_info') }}
            </Message>
            <Button
              :label="t('settings.backup_onedrive_start_btn')"
              icon="pi pi-microsoft"
              class="mt-2"
              @click="startOneDriveAuth"
            />
            <small v-if="oauthError" class="app-field__help p-error mt-1">{{ oauthError }}</small>
          </template>

          <!-- Step 1: polling — show device code -->
          <template v-else-if="oauthPolling">
            <Message severity="info" :closable="false">
              {{ t('settings.backup_onedrive_device_waiting') }}
            </Message>
            <div class="onedrive-device-code">
              <span class="onedrive-device-code__label">{{ t('settings.backup_onedrive_user_code') }}</span>
              <code class="onedrive-device-code__code">{{ deviceUserCode }}</code>
            </div>
            <a :href="deviceVerificationUri" target="_blank" rel="noopener" class="onedrive-link">
              {{ deviceVerificationUri }}
            </a>
            <div class="onedrive-spinner">
              <ProgressSpinner style="width:24px;height:24px" stroke-width="4" />
              <span>{{ t('settings.backup_onedrive_polling') }}</span>
            </div>
          </template>

          <!-- Step 2: done -->
          <template v-else-if="oauthDone">
            <Tag severity="success" :value="t('settings.backup_onedrive_authorized')" icon="pi pi-check" />
            <Button
              :label="t('settings.backup_onedrive_restart')"
              severity="secondary"
              size="small"
              class="mt-2"
              @click="startOneDriveAuth"
            />
          </template>
        </div>

        <!-- Path selector — shown once authorized -->
        <div v-if="oauthDone" class="app-field col-span-2">
          <label class="app-field__label">{{ t('settings.backup_target_path') }}</label>
          <InputGroup>
            <InputText
              v-model="newDest.target_path"
              :placeholder="t('settings.backup_onedrive_path_placeholder')"
            />
            <Button
              icon="pi pi-folder-open"
              :title="t('settings.backup_browse_onedrive')"
              severity="secondary"
              outlined
              @click="openFolderBrowser"
            />
          </InputGroup>
        </div>
      </template>
    </div>

    <template #footer>
      <Button :label="t('common.cancel')" severity="secondary" @click="showAddDestDialog = false" />
      <Button
        :label="t('common.save')"
        icon="pi pi-check"
        :loading="savingDest"
        @click="editDestId ? saveEditDest() : saveNewDest()"
      />
    </template>
  </Dialog>

  <!-- ── OneDrive folder browser ─────────────────────────────────────── -->
  <Dialog
    v-model:visible="showFolderBrowser"
    :header="t('settings.backup_onedrive_browse_title')"
    modal
    :style="{ width: '460px' }"
  >
    <div class="folder-breadcrumb">
      <button
        v-for="(crumb, i) in folderBreadcrumb"
        :key="i"
        class="folder-breadcrumb__item"
        :class="{ 'folder-breadcrumb__item--last': i === folderBreadcrumb.length - 1 }"
        :disabled="i === folderBreadcrumb.length - 1"
        @click="navigateTo(i)"
      >
        {{ crumb.name }}<span v-if="i < folderBreadcrumb.length - 1" class="folder-breadcrumb__sep"> / </span>
      </button>
    </div>
    <div v-if="folderLoading" class="folder-loading">
      <ProgressSpinner style="width: 28px; height: 28px" stroke-width="4" />
    </div>
    <div v-else-if="folderError" class="p-error folder-error">{{ folderError }}</div>
    <div v-else class="folder-list">
      <button
        v-for="item in folderItems"
        :key="item.id"
        class="folder-item"
        @click="navigateInto(item)"
      >
        <i class="pi pi-folder folder-item__icon" />
        <span class="folder-item__name">{{ item.name }}</span>
        <i class="pi pi-chevron-right folder-item__arrow" />
      </button>
      <div v-if="folderItems.length === 0" class="folder-empty">
        {{ t('settings.backup_onedrive_no_subfolders') }}
      </div>
    </div>
    <template #footer>
      <Button :label="t('common.cancel')" severity="secondary" @click="showFolderBrowser = false" />
      <Button
        :label="t('settings.backup_onedrive_choose_folder')"
        icon="pi pi-check"
        @click="chooseCurrentFolder"
      />
    </template>
  </Dialog>

  <!-- ── Toasts ─────────────────────────────────────────────────────── -->
  <Toast />
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import InputGroup from 'primevue/inputgroup'
import Message from 'primevue/message'
import Password from 'primevue/password'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ConfirmDialog from 'primevue/confirmdialog'
import Toast from 'primevue/toast'
import ToggleSwitch from 'primevue/toggleswitch'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import {
  listDestinations,
  createDestination,
  updateDestination,
  deleteDestination,
  testDestination,
  getSchedule,
  updateSchedule,
  triggerBackup,
  getBackupStatus,
  startOneDriveOAuth,
  pollOneDriveOAuthStatus,
  type BackupDestination,
  type BackupSchedule,
  type BackupRunStatus,
} from '@/api/backup'
import AppPanel from '@/components/ui/AppPanel.vue'

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const destinations = ref<BackupDestination[]>([])
const loadingDests = ref(false)
const savingDest = ref(false)
const showAddDestDialog = ref(false)
const editDestId = ref<number | null>(null)
const runningNow = ref(false)
const backupRunning = ref(false)
let _pollTimer: ReturnType<typeof setInterval> | null = null

function _stopPolling() {
  backupRunning.value = false
  if (_pollTimer !== null) {
    clearInterval(_pollTimer)
    _pollTimer = null
  }
}
// OneDrive device authorization flow state
const oauthPolling = ref(false)
const oauthDone = ref(false)
const oauthToken = ref<string | null>(null)
const oauthError = ref('')
const deviceUserCode = ref('')
const deviceVerificationUri = ref('')
let _oauthPollTimer: ReturnType<typeof setTimeout> | null = null

async function startOneDriveAuth(): Promise<void> {
  oauthPolling.value = false
  oauthDone.value = false
  oauthToken.value = null
  oauthError.value = ''
  deviceUserCode.value = ''
  deviceVerificationUri.value = ''
  if (_oauthPollTimer !== null) clearTimeout(_oauthPollTimer)

  try {
    const data = await startOneDriveOAuth()
    deviceUserCode.value = data.user_code
    deviceVerificationUri.value = data.verification_uri
    oauthPolling.value = true
    schedulePoll()
  } catch (err: unknown) {
    // Extract the detail message from the API error response if available
    const apiMsg =
      err &&
      typeof err === 'object' &&
      'response' in err &&
      err.response &&
      typeof err.response === 'object' &&
      'data' in err.response &&
      err.response.data &&
      typeof err.response.data === 'object' &&
      'detail' in err.response.data &&
      typeof (err.response.data as { detail: unknown }).detail === 'string'
        ? (err.response.data as { detail: string }).detail
        : null
    oauthError.value = apiMsg ?? t('settings.backup_onedrive_start_error')
  }
}

function schedulePoll(): void {
  _oauthPollTimer = setTimeout(() => void pollOnce(), 3000)
}

async function pollOnce(): Promise<void> {
  if (!oauthPolling.value) return
  try {
    const status = await pollOneDriveOAuthStatus()
    if (status.done && status.token) {
      oauthToken.value = status.token
      oauthPolling.value = false
      oauthDone.value = true
      return
    }
    if (status.error) {
      oauthError.value = status.error
      oauthPolling.value = false
      return
    }
  } catch {
    // network hiccup — keep polling
  }
  if (oauthPolling.value) schedulePoll()
}

function resetOneDriveAuth(): void {
  if (_oauthPollTimer !== null) clearTimeout(_oauthPollTimer)
  oauthPolling.value = false
  oauthDone.value = false
  oauthToken.value = null
  oauthError.value = ''
  deviceUserCode.value = ''
  deviceVerificationUri.value = ''
}

const schedule = reactive<BackupSchedule>({
  enabled: false,
  schedule_type: 'interval',
  interval_hours: 24,
  cron_expression: null,
  daily_time: '02:00',
  include_uploads: true,
  include_all_backups: false,
  notify_on_failure: false,
})

const runStatus = reactive<BackupRunStatus>({
  last_run_at: null,
  last_run_status: null,
  last_run_error: null,
  is_running: false,
  backup_progress: 0,
  destinations_results: [],
})

const newDest = reactive({
  name: '',
  type: 'local' as 'local' | 'smb' | 'onedrive',
  target_path: '',
})

// Auto-generate a safe rclone remote name from the destination display name.
function generateRemoteName(name: string): string {
  return name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'remote'
}

// ---------------------------------------------------------------------------
// OneDrive folder browser
// ---------------------------------------------------------------------------
const showFolderBrowser = ref(false)
const folderLoading = ref(false)
const folderError = ref('')
const folderItems = ref<{ id: string; name: string }[]>([])
const folderBreadcrumb = ref<{ id: string | null; name: string }[]>([])

function extractAccessToken(): string | null {
  if (!oauthToken.value) return null
  try {
    const config = JSON.parse(oauthToken.value) as { token: string }
    const tok = JSON.parse(config.token) as { access_token: string }
    return tok.access_token
  } catch {
    return null
  }
}

async function fetchFolderChildren(itemId: string | null): Promise<void> {
  const accessToken = extractAccessToken()
  if (!accessToken) return
  folderLoading.value = true
  folderError.value = ''
  try {
    const base = 'https://graph.microsoft.com/v1.0/me/drive'
    const url = itemId
      ? `${base}/items/${itemId}/children?$select=id,name,folder`
      : `${base}/root/children?$select=id,name,folder`
    const resp = await fetch(url, { headers: { Authorization: `Bearer ${accessToken}` } })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = (await resp.json()) as { value: { id: string; name: string; folder?: unknown }[] }
    folderItems.value = data.value
      .filter((item) => item.folder !== undefined)
      .sort((a, b) => a.name.localeCompare(b.name))
  } catch {
    folderError.value = t('settings.backup_onedrive_browse_error')
  } finally {
    folderLoading.value = false
  }
}

async function openFolderBrowser(): Promise<void> {
  folderBreadcrumb.value = [{ id: null, name: 'OneDrive' }]
  await fetchFolderChildren(null)
  showFolderBrowser.value = true
}

async function navigateInto(item: { id: string; name: string }): Promise<void> {
  folderBreadcrumb.value.push(item)
  await fetchFolderChildren(item.id)
}

async function navigateTo(index: number): Promise<void> {
  folderBreadcrumb.value = folderBreadcrumb.value.slice(0, index + 1)
  await fetchFolderChildren(folderBreadcrumb.value[index].id)
}

function chooseCurrentFolder(): void {
  newDest.target_path = folderBreadcrumb.value
    .slice(1)
    .map((c) => c.name)
    .join('/')
  showFolderBrowser.value = false
}

const smbForm = reactive({ host: '', user: '', pass: '' })

// ---------------------------------------------------------------------------
// Options
// ---------------------------------------------------------------------------
const scheduleTypeOptions = [
  { label: t('settings.backup_schedule_interval'), value: 'interval' },
  { label: t('settings.backup_schedule_daily'), value: 'daily' },
  { label: t('settings.backup_schedule_cron'), value: 'cron' },
]

const destTypeOptions = [
  { label: t('settings.backup_dest_local'), value: 'local' },
  { label: 'SMB / NAS', value: 'smb' },
  { label: 'OneDrive', value: 'onedrive' },
]

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(async () => {
  await Promise.all([loadSchedule(), loadDestinations(), loadStatus()])
  // If a backup is already running (e.g. user navigated away and came back),
  // resume the polling so the spinner stays visible until it completes.
  if (runStatus.is_running && _pollTimer === null) {
    backupRunning.value = true
    _pollTimer = setInterval(async () => {
      await loadStatus()
      if (!runStatus.is_running) {
        _stopPolling()
        if (runStatus.last_run_status === 'success') {
          toast.add({ severity: 'success', summary: t('settings.backup_success'), life: 4000 })
        } else if (runStatus.last_run_status === 'failure') {
          toast.add({ severity: 'error', summary: t('settings.backup_failure'), detail: runStatus.last_run_error ?? '', life: 6000 })
        }
      }
    }, 3000)
  }
})

onUnmounted(() => _stopPolling())

// ---------------------------------------------------------------------------
// Schedule
// ---------------------------------------------------------------------------
async function loadSchedule() {
  try {
    const s = await getSchedule()
    Object.assign(schedule, s)
  } catch {
    // silently ignore on load
  }
}

async function saveSchedule() {
  try {
    const saved = await updateSchedule({ ...schedule })
    Object.assign(schedule, saved)
    toast.add({ severity: 'success', summary: t('common.saved'), life: 2000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), detail: t('common.save_failed'), life: 4000 })
  }
}

// ---------------------------------------------------------------------------
// Run now
// ---------------------------------------------------------------------------
async function runNow() {
  runningNow.value = true
  try {
    await triggerBackup()
    toast.add({ severity: 'info', summary: t('settings.backup_started'), life: 3000 })
    // Start polling until is_running becomes false (backup completed)
    backupRunning.value = true
    _pollTimer = setInterval(async () => {
      await loadStatus()
      if (!runStatus.is_running) {
        _stopPolling()
        if (runStatus.last_run_status === 'success') {
          toast.add({ severity: 'success', summary: t('settings.backup_success'), life: 4000 })
        } else {
          toast.add({ severity: 'error', summary: t('settings.backup_failure'), detail: runStatus.last_run_error ?? '', life: 6000 })
        }
      }
    }, 3000)
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    runningNow.value = false
  }
}

async function loadStatus() {
  try {
    const s = await getBackupStatus()
    Object.assign(runStatus, s)
  } catch {
    // silently ignore
  }
}

// ---------------------------------------------------------------------------
// Destinations
// ---------------------------------------------------------------------------
async function loadDestinations() {
  loadingDests.value = true
  try {
    destinations.value = await listDestinations()
  } finally {
    loadingDests.value = false
  }
}

async function toggleDestEnabled(dest: BackupDestination, v: boolean) {
  try {
    await updateDestination(dest.id, { enabled: v })
    dest.enabled = v
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  }
}

async function testConnection(dest: BackupDestination) {
  try {
    const result = await testDestination(dest.id)
    toast.add({
      severity: result.success ? 'success' : 'error',
      summary: result.success ? t('settings.backup_conn_ok') : t('settings.backup_conn_fail'),
      detail: result.message,
      life: 5000,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  }
}

function confirmDeleteDest(dest: BackupDestination) {
  confirm.require({
    message: t('settings.backup_confirm_delete_dest', { name: dest.name }),
    header: t('common.confirm'),
    icon: 'pi pi-trash',
    acceptSeverity: 'danger',
    accept: async () => {
      try {
        await deleteDestination(dest.id)
        destinations.value = destinations.value.filter((d) => d.id !== dest.id)
        toast.add({ severity: 'success', summary: t('common.deleted'), life: 2000 })
      } catch {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
      }
    },
  })
}

function openAddDestDialog() {
  editDestId.value = null
  newDest.name = ''
  newDest.type = 'local'
  newDest.target_path = ''
  smbForm.host = ''
  smbForm.user = ''
  smbForm.pass = ''
  resetOneDriveAuth()
  showAddDestDialog.value = true
}

function openEditDestDialog(dest: BackupDestination) {
  editDestId.value = dest.id
  newDest.name = dest.name
  newDest.type = dest.type
  newDest.target_path = dest.target_path
  smbForm.host = ''
  smbForm.user = ''
  smbForm.pass = ''
  resetOneDriveAuth()
  // If the destination already has an OneDrive token, reuse it so the path
  // field is immediately editable without forcing a new authorization.
  if (dest.type === 'onedrive' && dest.rclone_config) {
    oauthToken.value = dest.rclone_config
    oauthDone.value = true
  }
  showAddDestDialog.value = true
}

async function saveNewDest() {
  if (!newDest.name) {
    toast.add({ severity: 'warn', summary: t('common.required_fields'), life: 3000 })
    return
  }

  savingDest.value = true
  try {
    let rclone_config: string | null = null

    if (newDest.type === 'smb') {
      rclone_config = JSON.stringify({
        host: smbForm.host,
        user: smbForm.user,
        pass: smbForm.pass,
      })
    } else if (newDest.type === 'onedrive' && oauthToken.value) {
      rclone_config = oauthToken.value
    }

    const created = await createDestination({
      name: newDest.name,
      type: newDest.type,
      rclone_remote_name: generateRemoteName(newDest.name),
      target_path: newDest.target_path,
      rclone_config,
    })
    destinations.value.push(created)
    showAddDestDialog.value = false
    toast.add({ severity: 'success', summary: t('common.saved'), life: 2000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    savingDest.value = false
  }
}

async function saveEditDest() {
  if (!newDest.name) {
    toast.add({ severity: 'warn', summary: t('common.required_fields'), life: 3000 })
    return
  }

  savingDest.value = true
  try {
    let rclone_config: string | null = null
    if (newDest.type === 'smb' && smbForm.host) {
      rclone_config = JSON.stringify({ host: smbForm.host, user: smbForm.user, pass: smbForm.pass })
    } else if (newDest.type === 'onedrive' && oauthToken.value) {
      rclone_config = oauthToken.value
    }

    const updated = await updateDestination(editDestId.value!, {
      name: newDest.name,
      type: newDest.type,
      rclone_remote_name: generateRemoteName(newDest.name),
      target_path: newDest.target_path,
      ...(rclone_config !== null ? { rclone_config } : {}),
    })
    destinations.value = destinations.value.map((d) => (d.id === updated.id ? updated : d))
    showAddDestDialog.value = false
    toast.add({ severity: 'success', summary: t('common.saved'), life: 2000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    savingDest.value = false
  }
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------
function formatDate(iso: string): string {
  // The backend stores naive datetimes (local server time, TZ=Europe/Paris).
  // Treat the ISO string as local time directly — no Z suffix needed.
  return new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<style scoped>
.onedrive-device-code {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0.75rem 0;
}
.onedrive-device-code__label {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}
.onedrive-device-code__code {
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  background: var(--surface-ground);
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  padding: 0.3rem 0.75rem;
}
.onedrive-link {
  display: block;
  margin-bottom: 0.75rem;
  color: var(--primary-color);
  text-decoration: underline;
  font-size: 0.9rem;
}
.onedrive-spinner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}
.folder-breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  margin-bottom: 0.75rem;
  font-size: 0.85rem;
  color: var(--text-color-secondary);
}
.folder-breadcrumb__item {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--primary-color);
  font-size: inherit;
}
.folder-breadcrumb__item--last {
  color: var(--text-color);
  cursor: default;
  font-weight: 600;
}
.folder-breadcrumb__sep {
  color: var(--text-color-secondary);
  pointer-events: none;
}
.folder-loading {
  display: flex;
  justify-content: center;
  padding: 1.5rem 0;
}
.folder-error {
  padding: 0.5rem 0;
}
.folder-list {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  max-height: 320px;
  overflow-y: auto;
}
.folder-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.45rem 0.6rem;
  border: none;
  border-radius: 6px;
  background: none;
  cursor: pointer;
  text-align: left;
  transition: background 0.1s;
  width: 100%;
}
.folder-item:hover {
  background: var(--surface-hover);
}
.folder-item__icon {
  color: var(--p-yellow-500);
  font-size: 1rem;
  flex-shrink: 0;
}
.folder-item__name {
  flex: 1;
  font-size: 0.9rem;
}
.folder-item__arrow {
  color: var(--text-color-secondary);
  font-size: 0.75rem;
  flex-shrink: 0;
}
.folder-empty {
  color: var(--text-color-secondary);
  font-style: italic;
  font-size: 0.875rem;
  padding: 1rem 0.5rem;
}
.backup-section {
  margin-bottom: 2rem;
}
.backup-section__title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 1rem;
}
.backup-status {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.25rem;
}
.backup-running-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-style: italic;
  color: var(--text-color-secondary);
}
.backup-progress-pct {
  font-style: normal;
  font-weight: 600;
  color: var(--p-primary-color);
}

.backup-status__error {
  font-size: 0.8em;
  color: var(--p-red-500);
  word-break: break-all;
}

.dest-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.dest-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0.75rem;
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
  background: var(--surface-card);
}

.dest-row__name {
  flex: 1;
  font-weight: 500;
}

.dest-row__type {
  font-size: 0.8rem;
}

.dest-row__actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.dest-row--add {
  cursor: pointer;
  border-style: dashed;
  background: transparent;
  color: var(--text-color-secondary);
  font-size: 0.875rem;
  gap: 0.5rem;
  justify-content: flex-start;
  transition: color 0.15s, border-color 0.15s;
}

.dest-row--add:hover {
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.dest-list__empty {
  color: var(--text-color-secondary);
  font-style: italic;
  padding: 0.25rem 0;
}
</style>
