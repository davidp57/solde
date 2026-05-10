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
        <Button
          :label="t('settings.backup_run_now')"
          icon="pi pi-play"
          severity="secondary"
          outlined
          :loading="runningNow"
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
      <div class="app-field col-span-2">
        <label class="app-field__label">{{ t('settings.backup_rclone_remote_name') }}</label>
        <InputText v-model="newDest.rclone_remote_name" class="w-full" />
        <small class="app-field__help">{{ t('settings.backup_rclone_remote_help') }}</small>
      </div>
      <div class="app-field col-span-2">
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

  <!-- ── Toasts ─────────────────────────────────────────────────────── -->
  <Toast />
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
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
  include_uploads: true,
  notify_on_failure: false,
})

const runStatus = reactive<BackupRunStatus>({
  last_run_at: null,
  last_run_status: null,
  last_run_error: null,
  destinations_results: [],
})

const newDest = reactive({
  name: '',
  type: 'local' as 'local' | 'smb' | 'onedrive',
  rclone_remote_name: '',
  target_path: '',
})

const smbForm = reactive({ host: '', user: '', pass: '' })

// ---------------------------------------------------------------------------
// Options
// ---------------------------------------------------------------------------
const scheduleTypeOptions = [
  { label: t('settings.backup_schedule_interval'), value: 'interval' },
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
})

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
    setTimeout(loadStatus, 3000)
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
  newDest.rclone_remote_name = ''
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
  newDest.rclone_remote_name = dest.rclone_remote_name
  newDest.target_path = dest.target_path
  smbForm.host = ''
  smbForm.user = ''
  smbForm.pass = ''
  resetOneDriveAuth()
  showAddDestDialog.value = true
}

async function saveNewDest() {
  if (!newDest.name || !newDest.rclone_remote_name) {
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
      rclone_remote_name: newDest.rclone_remote_name,
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
  if (!newDest.name || !newDest.rclone_remote_name) {
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
      rclone_remote_name: newDest.rclone_remote_name,
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
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0.25rem;
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
