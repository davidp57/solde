<template>
  <Dialog
    :visible="visible"
    :header="t('bank.import_dialog_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="app-dialog-form bank-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('bank.import_statement') }}</p>
        <p class="app-dialog-intro__text">{{ t('bank.import_intro') }}</p>
      </section>
      <section class="app-dialog-section">
        <div class="app-form-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('bank.import_file_label') }}</label>
            <div class="bank-import-file-row">
              <Button
                :label="t('bank.import_pick_file')"
                icon="pi pi-paperclip"
                severity="secondary"
                outlined
                @click="fileInput?.click()"
              />
              <span class="bank-import-file-name">
                {{ fileName || t('bank.import_no_file') }}
              </span>
            </div>
            <input
              ref="fileInput"
              type="file"
              class="bank-import-file-input"
              accept=".csv,.ofx,.qfx,.qif,text/csv,text/plain,application/xml,text/xml"
              @change="onFileSelected"
            />
          </div>
          <div v-if="isOfxOrQif && !acctidFullyConfigured" class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('bank.import_default_account') }}</label>
            <Select
              v-model="defaultBankAccount"
              :options="[
                { label: t('bank.filter_account_courant'), value: 'courant' },
                { label: t('bank.filter_account_epargne'), value: 'epargne' },
              ]"
              option-label="label"
              option-value="value"
              class="w-full"
            />
            <small class="app-field__hint">{{ t('bank.import_default_account_help') }}</small>
          </div>
        </div>
      </section>
      <section v-if="duplicates.length" class="app-dialog-section">
        <h3 class="bank-import-dup__title">
          {{ t('bank.import_duplicates_title', { n: duplicates.length }) }}
        </h3>
        <p class="bank-import-dup__intro">{{ t('bank.import_duplicates_intro') }}</p>
        <div v-for="(pair, index) in duplicates" :key="pair.imported.id" class="bank-import-dup">
          <p class="bank-import-dup__caption">
            {{ t('bank.import_duplicates_pair', { n: index + 1 }) }}
          </p>
          <div
            v-for="side in ['imported', 'existing'] as const"
            :key="side"
            class="bank-import-dup__row"
          >
            <span class="bank-import-dup__badge">{{ t(`bank.import_duplicates_${side}`) }}</span>
            <span class="bank-import-dup__date">{{ formatDisplayDate(pair[side].date) }}</span>
            <span class="bank-import-dup__label">{{ pair[side].description }}</span>
            <span class="bank-import-dup__amount">{{ pair[side].amount }} €</span>
            <span class="bank-import-dup__source">
              {{ t(`bank.sources.${pair[side].source}`) }}
            </span>
            <Button
              :label="t('bank.delete_transaction')"
              icon="pi pi-trash"
              severity="danger"
              text
              size="small"
              :disabled="!canDeleteTransaction(pair[side]) || deletingId !== null"
              :loading="deletingId === pair[side].id"
              :title="
                canDeleteTransaction(pair[side])
                  ? undefined
                  : t('bank.import_duplicates_locked')
              "
              @click="dropDuplicate(pair.imported.id, pair[side].id)"
            />
          </div>
        </div>
      </section>
      <div class="app-form-actions">
        <Button
          :label="duplicates.length ? t('common.close') : t('common.cancel')"
          severity="secondary"
          text
          @click="close"
        />
        <Button
          v-if="!duplicates.length"
          :label="t('bank.import_statement')"
          icon="pi pi-upload"
          :loading="saving"
          @click="submit"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import {
  importBankStatement,
  deleteTransaction,
  canDeleteTransaction,
  type BankImportDuplicate,
  type BankImportFormat,
  type BankAccountType,
} from '@/api/bank'
import { getSettingsApi } from '@/api/settings'
import { formatDisplayDate } from '@/utils/format'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  'update:visible': [val: boolean]
  saved: []
}>()

const { t } = useI18n()
const toast = useToast()
const saving = ref(false)
const fileName = ref('')
const fileContent = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const defaultBankAccount = ref<BankAccountType>('courant')
const acctidFullyConfigured = ref(false)
// Probable duplicates reported by the last import: the dialog stays open on them so the
// user drops the redundant row while both are still side by side.
const duplicates = ref<BankImportDuplicate[]>([])
const deletingId = ref<number | null>(null)

watch(
  () => props.visible,
  async (open) => {
    if (!open) return
    try {
      const s = await getSettingsApi()
      acctidFullyConfigured.value =
        Boolean(s.bank_account_courant_acctid) && Boolean(s.bank_account_epargne_acctid)
    } catch {
      acctidFullyConfigured.value = false
    }
  },
)

const isOfxOrQif = computed(() => {
  if (!fileName.value) return false
  return detectFormat(fileName.value) !== 'csv'
})

function detectFormat(name: string): BankImportFormat {
  const lower = name.toLowerCase()
  if (lower.endsWith('.ofx') || lower.endsWith('.qfx')) return 'ofx'
  if (lower.endsWith('.qif')) return 'qif'
  return 'csv'
}

async function onFileSelected(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  fileName.value = file.name
  fileContent.value = await file.text()
  input.value = ''
}

function close(): void {
  duplicates.value = []
  emit('update:visible', false)
}

/** Drop one side of a reported pair; the pair then leaves the list, settled. */
async function dropDuplicate(pairId: number, txId: number): Promise<void> {
  deletingId.value = txId
  try {
    await deleteTransaction(txId)
    duplicates.value = duplicates.value.filter((pair) => pair.imported.id !== pairId)
    toast.add({ severity: 'success', summary: t('bank.transaction_deleted'), life: 2000 })
    emit('saved')
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    deletingId.value = null
  }
}

async function submit(): Promise<void> {
  if (!fileName.value || !fileContent.value.trim()) {
    toast.add({ severity: 'warn', summary: t('bank.import_file_required'), life: 3000 })
    return
  }
  saving.value = true
  try {
    const result = await importBankStatement(detectFormat(fileName.value), fileContent.value, defaultBankAccount.value)
    duplicates.value = result.duplicates
    // Keep the dialog open when there are duplicates to arbitrate; closing it would bury
    // the pairs in the statement, where the older of the two is easy to miss.
    if (!duplicates.value.length) emit('update:visible', false)
    fileName.value = ''
    fileContent.value = ''
    defaultBankAccount.value = 'courant'
    const base =
      result.skipped > 0
        ? t('bank.import_success_with_skipped', { n: result.created.length, s: result.skipped })
        : t('bank.import_success', { n: result.created.length })
    // Deposits already recorded in Solde are folded into the statement rather
    // than imported a second time — say so, the counts would look off otherwise.
    const withMerged =
      result.merged > 0 ? base + t('bank.import_merged_suffix', { m: result.merged }) : base
    const summary =
      duplicates.value.length > 0
        ? withMerged + t('bank.import_duplicates_suffix', { d: duplicates.value.length })
        : withMerged
    toast.add({
      severity: duplicates.value.length > 0 ? 'warn' : 'success',
      summary,
      life: 6000,
    })
    emit('saved')
  } catch (err: unknown) {
    const rawDetail =
      err &&
      typeof err === 'object' &&
      'response' in err
        ? (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
        : undefined
    const detail =
      typeof rawDetail === 'string'
        ? rawDetail
        : Array.isArray(rawDetail)
          ? rawDetail.map((d: unknown) => (typeof d === 'object' && d && 'msg' in d ? (d as { msg: string }).msg : String(d))).join(', ')
          : undefined
    toast.add({
      severity: 'error',
      summary: detail ? t('bank.import_error') : t('common.error.unknown'),
      detail: detail ?? undefined,
      life: 8000,
    })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.bank-import-file-row {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
}

.bank-import-file-name {
  color: var(--app-text-muted);
  font-size: 0.95rem;
}

.bank-import-file-input {
  display: none;
}

.bank-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.bank-import-dup__title {
  margin: 0 0 var(--app-space-2);
  font-size: 1rem;
}

.bank-import-dup__intro {
  margin: 0 0 var(--app-space-3);
  color: var(--app-text-muted);
  font-size: 0.9rem;
}

.bank-import-dup {
  padding: var(--app-space-3);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-sm, 6px);
}

.bank-import-dup + .bank-import-dup {
  margin-top: var(--app-space-3);
}

.bank-import-dup__caption {
  margin: 0 0 var(--app-space-2);
  color: var(--app-text-muted);
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.bank-import-dup__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--app-space-2);
}

.bank-import-dup__row + .bank-import-dup__row {
  margin-top: var(--app-space-2);
}

.bank-import-dup__badge {
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: var(--app-surface-2, rgba(127, 127, 127, 0.15));
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.bank-import-dup__label {
  flex: 1 1 12rem;
  min-width: 0;
  overflow-wrap: anywhere;
}

.bank-import-dup__amount {
  font-weight: 700;
  white-space: nowrap;
}

.bank-import-dup__source,
.bank-import-dup__date {
  color: var(--app-text-muted);
  font-size: 0.9rem;
  white-space: nowrap;
}
</style>
