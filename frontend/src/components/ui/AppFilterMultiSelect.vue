<template>
  <div class="app-filter-multiselect" @click.stop @mousedown.stop @keydown.stop>
    <MultiSelect
      :model-value="modelValue"
      :options="options"
      :option-label="optionLabel"
      :option-value="optionValue"
      :placeholder="placeholder"
      :display="display"
      :show-clear="showClear"
      append-to="self"
      @update:model-value="updateValue"
    />
  </div>
</template>

<script setup lang="ts">
import MultiSelect from 'primevue/multiselect'

const props = defineProps<{
  modelValue?: unknown
  options: unknown[]
  optionLabel?: string
  optionValue?: string
  placeholder?: string
  display?: 'comma' | 'chip'
  showClear?: boolean
  filterCallback?: () => void
}>()

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
}>()

function updateValue(value: unknown): void {
  emit('update:modelValue', value)
  props.filterCallback?.()
}
</script>

<style scoped>
.app-filter-multiselect {
  width: 100%;
}

.app-filter-multiselect :deep(.p-multiselect) {
  width: 100%;
}

.app-filter-multiselect :deep(.p-multiselect-overlay) {
  position: static;
}
</style>
