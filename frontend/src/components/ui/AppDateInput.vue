<template>
  <InputText :model-value="draft" :placeholder="placeholder" @update:model-value="updateValue" />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'

import { formatDateInputDraft, normalizeDateInput } from '../../utils/format'

const props = defineProps<{
  modelValue?: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { t } = useI18n()
const placeholder = t('common.date_filter_placeholder')
const draft = ref(formatDateInputDraft(props.modelValue))

watch(
  () => props.modelValue,
  (value) => {
    draft.value = formatDateInputDraft(value)
  },
)

function updateValue(value?: string): void {
  draft.value = value ?? ''
  const normalizedValue = normalizeDateInput(draft.value)
  if (normalizedValue === undefined) {
    return
  }

  emit('update:modelValue', normalizedValue ?? '')
}
</script>
