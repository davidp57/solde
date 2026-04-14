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

const props = defineProps<{
  modelValue?: [string | null, string | null] | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: [string | null, string | null] | null]
}>()

const { t } = useI18n()
const placeholder = t('common.date_filter_placeholder')
const startDraft = ref(props.modelValue?.[0] ?? '')
const endDraft = ref(props.modelValue?.[1] ?? '')

watch(
  () => props.modelValue,
  (value) => {
    startDraft.value = value?.[0] ?? ''
    endDraft.value = value?.[1] ?? ''
  },
)

function normalizeDate(value: string): string | null | undefined {
  const trimmedValue = value.trim()
  if (trimmedValue.length === 0) {
    return null
  }

  const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmedValue)
  if (isoMatch) {
    const year = isoMatch[1]
    const month = isoMatch[2]
    const day = isoMatch[3]
    if (!year || !month || !day) {
      return undefined
    }
    return isValidDateParts(year, month, day) ? `${year}-${month}-${day}` : undefined
  }

  const frMatch = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(trimmedValue)
  if (frMatch) {
    const day = frMatch[1]
    const month = frMatch[2]
    const year = frMatch[3]
    if (!year || !month || !day) {
      return undefined
    }
    return isValidDateParts(year, month, day) ? `${year}-${month}-${day}` : undefined
  }

  return undefined
}

function isValidDateParts(year: string, month: string, day: string): boolean {
  const parsedYear = Number.parseInt(year, 10)
  const parsedMonth = Number.parseInt(month, 10)
  const parsedDay = Number.parseInt(day, 10)

  if (
    Number.isNaN(parsedYear) ||
    Number.isNaN(parsedMonth) ||
    Number.isNaN(parsedDay) ||
    parsedMonth < 1 ||
    parsedMonth > 12 ||
    parsedDay < 1 ||
    parsedDay > 31
  ) {
    return false
  }

  const candidate = new Date(`${year}-${month}-${day}T00:00:00`)
  return (
    candidate.getFullYear() === parsedYear &&
    candidate.getMonth() === parsedMonth - 1 &&
    candidate.getDate() === parsedDay
  )
}

function emitRange(start: string, end: string): void {
  const normalizedStart = normalizeDate(start)
  const normalizedEnd = normalizeDate(end)

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
