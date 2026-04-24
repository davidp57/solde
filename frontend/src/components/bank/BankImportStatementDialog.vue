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
        </div>
      </section>
      <div class="app-form-actions">
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          text
          @click="$emit('update:visible', false)"
        />
        <Button
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
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import { useToast } from 'primevue/usetoast'
import { importBankStatement, type BankImportFormat } from '@/api/bank'

defineProps<{ visible: boolean }>()
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

async function submit(): Promise<void> {
  if (!fileName.value || !fileContent.value.trim()) {
    toast.add({ severity: 'warn', summary: t('bank.import_file_required'), life: 3000 })
    return
  }
  saving.value = true
  try {
    const imported = await importBankStatement(detectFormat(fileName.value), fileContent.value)
    emit('update:visible', false)
    fileName.value = ''
    fileContent.value = ''
    toast.add({
      severity: 'success',
      summary: t('bank.import_success', { n: imported.length }),
      life: 3000,
    })
    emit('saved')
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
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
</style>
