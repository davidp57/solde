<template>
  <AppPanel :title="t('settings.backup_title')" :subtitle="t('settings.backup_subtitle')">
    <div class="settings-backup">
      <Button
        :label="t('settings.backup_download')"
        icon="pi pi-download"
        severity="secondary"
        outlined
        :loading="backing"
        @click="downloadBackup"
      />
      <Message v-if="errorMessage" severity="error" class="mt-2" :closable="true">
        {{ errorMessage }}
      </Message>
    </div>
  </AppPanel>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { createBackupApi } from '@/api/settings'
import AppPanel from '@/components/ui/AppPanel.vue'

const { t } = useI18n()

const backing = ref(false)
const errorMessage = ref('')

async function downloadBackup(): Promise<void> {
  backing.value = true
  errorMessage.value = ''
  try {
    const blob = await createBackupApi()
    const url = URL.createObjectURL(blob)
    const filename = `solde_backup_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.db`
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    errorMessage.value = t('settings.backup_error')
  } finally {
    backing.value = false
  }
}
</script>

<style scoped>
.settings-backup {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: flex-start;
}
</style>
