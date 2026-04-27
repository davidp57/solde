<template>
  <div class="app-range-filter">
    <InputText
      :model-value="startDraft"
      :placeholder="placeholder"
      @update:model-value="updateStart"
    />
    <InputText :model-value="endDraft" :placeholder="placeholder" @update:model-value="updateEnd" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'

import { formatDateInputDraft, normalizeDateInput } from '../../utils/format'

const props = defineProps<{
  modelValue?: [string | null, string | null] | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: [string | null, string | null] | null]
}>()

const { t } = useI18n()
const placeholder = t('common.date_filter_placeholder')
const startDraft = ref(formatDateInputDraft(props.modelValue?.[0]))
const endDraft = ref(formatDateInputDraft(props.modelValue?.[1]))

watch(
  () => props.modelValue,
  (value) => {
    startDraft.value = formatDateInputDraft(value?.[0])
    endDraft.value = formatDateInputDraft(value?.[1])
  },
)

function emitRange(start: string, end: string): void {
  const normalizedStart = normalizeDateInput(start)
  const normalizedEnd = normalizeDateInput(end)

  if (normalizedStart === undefined || normalizedEnd === undefined) {
    return
  }

  emit(
    'update:modelValue',
    normalizedStart || normalizedEnd ? [normalizedStart ?? null, normalizedEnd ?? null] : null,
  )
}

function updateStart(value?: string): void {
  startDraft.value = value ?? ''
  emitRange(startDraft.value, endDraft.value)
}

function updateEnd(value?: string): void {
  endDraft.value = value ?? ''
  emitRange(startDraft.value, endDraft.value)
}
</script>

<style scoped>
.app-range-filter {
  display: grid;
  gap: 0.5rem;
}
</style>
