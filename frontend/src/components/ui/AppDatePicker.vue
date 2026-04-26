<template>
  <div class="app-date-picker" :class="[wrapperClass, { 'app-date-picker--clearable': showClear }]">
    <input
      type="date"
      class="p-inputtext app-date-picker__input"
      :id="id"
      :required="required"
      :disabled="disabled"
      :value="inputValue"
      @change="onInput"
    />
    <button
      v-if="showClear && modelValue != null"
      type="button"
      class="app-date-picker__clear"
      tabindex="-1"
      @click.prevent="emit('update:modelValue', null)"
    >
      <i class="pi pi-times-circle" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps<{
  modelValue: Date | null
  required?: boolean
  disabled?: boolean
  id?: string
  showClear?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Date | null]
}>()

const attrs = useAttrs()

// Forward only layout-related attrs (class, style) to the wrapper div
const wrapperClass = computed(() => attrs.class as string | undefined)

const inputValue = computed(() => {
  if (!props.modelValue) return ''
  const d = props.modelValue
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
})

function onInput(event: Event): void {
  const value = (event.target as HTMLInputElement).value
  if (!value) {
    emit('update:modelValue', null)
    return
  }
  const [yearStr, monthStr, dayStr] = value.split('-')
  const year = parseInt(yearStr ?? '1970', 10)
  const month = parseInt(monthStr ?? '1', 10)
  const day = parseInt(dayStr ?? '1', 10)
  // Use noon (12:00) to be safe against DST shifts at midnight
  emit('update:modelValue', new Date(year, month - 1, day, 12))
}
</script>

<style scoped>
.app-date-picker {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.app-date-picker.w-full {
  width: 100%;
}

.app-date-picker__input {
  width: 100%;
  /* Ensure the native date picker icon is always visible */
  padding-right: 0.5rem;
}

.app-date-picker--clearable .app-date-picker__input {
  padding-right: 2rem;
}

.app-date-picker__clear {
  position: absolute;
  right: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--p-inputtext-placeholder-color, #6b7280);
  padding: 0;
  font-size: 0.75rem;
  line-height: 1;
}

.app-date-picker__clear:hover {
  color: var(--p-text-color, #374151);
}
</style>
