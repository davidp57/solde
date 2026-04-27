<template>
  <AppPanel
    :title="t('import.test_shortcuts_title')"
    :subtitle="t('import.test_shortcuts_subtitle')"
    dense
  >
    <p class="import-action-hint">{{ t('import.test_shortcuts_hint') }}</p>
    <div class="import-shortcuts-actions">
      <Button
        :label="t('import.test_shortcuts_run_all')"
        icon="pi pi-play"
        severity="contrast"
        :disabled="!allAvailable || importing || runningAll"
        :loading="runningAll"
        @click="emit('run-all-shortcuts')"
      />
    </div>
    <div class="import-shortcuts-grid">
      <article
        v-for="shortcut in testShortcuts"
        :key="shortcut.alias"
        class="import-shortcut-card"
      >
        <div class="import-shortcut-card__body">
          <div>
            <h3 class="import-shortcut-card__title">{{ shortcut.label }}</h3>
            <p class="import-shortcut-card__meta">
              {{ shortcut.file_name ?? t('import.test_shortcuts_missing_file') }}
            </p>
          </div>
          <p v-if="shortcut.message" class="import-shortcut-card__message">
            {{ shortcut.message }}
          </p>
        </div>
        <Button
          :data-testid="`quick-import-${shortcut.alias}`"
          :label="t('import.test_shortcuts_run', { label: shortcut.label })"
          icon="pi pi-bolt"
          severity="contrast"
          outlined
          :disabled="!shortcut.available || importing"
          :loading="runningShortcutAlias === shortcut.alias"
          @click="emit('run-shortcut', shortcut.alias)"
        />
      </article>
    </div>
  </AppPanel>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import AppPanel from '../ui/AppPanel.vue'
import type { TestImportShortcut } from '@/api/accounting'

const props = defineProps<{
  testShortcuts: TestImportShortcut[]
  importing: boolean
  runningShortcutAlias: string | null
  runningAll: boolean
}>()

const emit = defineEmits<{
  'run-shortcut': [alias: string]
  'run-all-shortcuts': []
}>()

const allAvailable = computed(() => props.testShortcuts.every((s) => s.available))

const { t } = useI18n()
</script>
