<template>
  <div
    class="app-date-picker p-inputtext"
    :class="wrapperClass"
    @click.self="dayRef?.focus()"
  >
    <input
      :id="id"
      ref="dayRef"
      v-model="dayStr"
      type="text"
      inputmode="numeric"
      class="app-date-picker__seg"
      maxlength="2"
      placeholder="JJ"
      :required="required"
      :disabled="disabled"
      @input="onDayInput"
      @keydown="onDayKeydown"
    />
    <span class="app-date-picker__sep">/</span>
    <input
      ref="monthRef"
      v-model="monthStr"
      type="text"
      inputmode="numeric"
      class="app-date-picker__seg"
      maxlength="2"
      placeholder="MM"
      :disabled="disabled"
      @input="onMonthInput"
      @keydown="onMonthKeydown"
    />
    <span class="app-date-picker__sep">/</span>
    <input
      ref="yearRef"
      v-model="yearStr"
      type="text"
      inputmode="numeric"
      class="app-date-picker__seg app-date-picker__seg--year"
      maxlength="4"
      placeholder="AAAA"
      :disabled="disabled"
      @input="onYearInput"
      @keydown="onYearKeydown"
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
import { computed, ref, useAttrs, watch } from 'vue'

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
const wrapperClass = computed(() => attrs.class as string | undefined)

const dayRef = ref<HTMLInputElement | null>(null)
const monthRef = ref<HTMLInputElement | null>(null)
const yearRef = ref<HTMLInputElement | null>(null)

const dayStr = ref('')
const monthStr = ref('')
const yearStr = ref('')

// Sync from modelValue to strings without triggering re-emit
watch(
  () => props.modelValue,
  (d) => {
    if (!d) {
      dayStr.value = ''
      monthStr.value = ''
      yearStr.value = ''
    } else {
      const dd = String(d.getDate()).padStart(2, '0')
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const yyyy = String(d.getFullYear())
      if (dayStr.value !== dd) dayStr.value = dd
      if (monthStr.value !== mm) monthStr.value = mm
      if (yearStr.value !== yyyy) yearStr.value = yyyy
    }
  },
  { immediate: true },
)

function tryEmit() {
  const d = parseInt(dayStr.value, 10)
  const m = parseInt(monthStr.value, 10)
  const y = parseInt(yearStr.value, 10)

  if (
    !isNaN(d) && d >= 1 && d <= 31 &&
    !isNaN(m) && m >= 1 && m <= 12 &&
    !isNaN(y) && y >= 1000 && y <= 9999
  ) {
    // Use noon (12:00) to avoid DST-related date shifts
    emit('update:modelValue', new Date(y, m - 1, d, 12))
  } else if (dayStr.value === '' && monthStr.value === '' && yearStr.value === '') {
    emit('update:modelValue', null)
  }
}

function onDayInput() {
  if (dayStr.value.length === 2) {
    monthRef.value?.focus()
    monthRef.value?.select()
  }
  tryEmit()
}

function onMonthInput() {
  if (monthStr.value.length === 2) {
    yearRef.value?.focus()
    yearRef.value?.select()
  }
  tryEmit()
}

function onYearInput() {
  tryEmit()
}

function onDayKeydown(e: KeyboardEvent) {
  const input = e.target as HTMLInputElement
  if (e.key === 'ArrowRight' && input.selectionStart === dayStr.value.length) {
    e.preventDefault()
    monthRef.value?.focus()
    monthRef.value?.setSelectionRange(0, 0)
  }
}

function onMonthKeydown(e: KeyboardEvent) {
  const input = e.target as HTMLInputElement
  if (e.key === 'Backspace' && monthStr.value === '') {
    e.preventDefault()
    dayRef.value?.focus()
    dayRef.value?.select()
  } else if (e.key === 'ArrowLeft' && input.selectionStart === 0) {
    e.preventDefault()
    dayRef.value?.focus()
    dayRef.value?.setSelectionRange(dayStr.value.length, dayStr.value.length)
  } else if (e.key === 'ArrowRight' && input.selectionStart === monthStr.value.length) {
    e.preventDefault()
    yearRef.value?.focus()
    yearRef.value?.setSelectionRange(0, 0)
  }
}

function onYearKeydown(e: KeyboardEvent) {
  const input = e.target as HTMLInputElement
  if (e.key === 'Backspace' && yearStr.value === '') {
    e.preventDefault()
    monthRef.value?.focus()
    monthRef.value?.select()
  } else if (e.key === 'ArrowLeft' && input.selectionStart === 0) {
    e.preventDefault()
    monthRef.value?.focus()
    monthRef.value?.setSelectionRange(monthStr.value.length, monthStr.value.length)
  }
}
</script>

<style scoped>
.app-date-picker {
  display: inline-flex !important;
  align-items: center;
  cursor: text;
}

.app-date-picker.w-full {
  width: 100%;
}

.app-date-picker__seg {
  border: none;
  outline: none;
  background: transparent;
  color: inherit;
  font: inherit;
  padding: 0;
  margin: 0;
  min-width: 0;
  text-align: center;
  width: 2ch;
}

.app-date-picker__seg--year {
  width: 4ch;
  text-align: left;
}

.app-date-picker__sep {
  padding: 0 1px;
  user-select: none;
  opacity: 0.5;
}

.app-date-picker__clear {
  margin-left: auto;
  padding-left: 0.35rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--p-inputtext-placeholder-color, #6b7280);
  font-size: 0.75rem;
  line-height: 1;
}

.app-date-picker__clear:hover {
  color: var(--p-text-color, #374151);
}
</style>
