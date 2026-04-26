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
    <span class="app-date-picker__spacer" />
    <button
      v-if="showClear && modelValue != null"
      type="button"
      class="app-date-picker__icon-btn"
      tabindex="-1"
      @click.prevent="emit('update:modelValue', null)"
    >
      <i class="pi pi-times-circle" />
    </button>
    <button
      v-if="!disabled"
      type="button"
      class="app-date-picker__icon-btn"
      tabindex="-1"
      @click="toggleCalendar"
    >
      <i class="pi pi-calendar" />
    </button>
    <Popover ref="popoverRef">
      <DatePicker
        :model-value="modelValue"
        inline
        @update:model-value="onCalendarSelect"
      />
    </Popover>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useAttrs, watch } from 'vue'
import DatePicker from 'primevue/datepicker'
import Popover from 'primevue/popover'

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
const popoverRef = ref()

const dayStr = ref('')
const monthStr = ref('')
const yearStr = ref('')

// Prevent the watch from overwriting in-progress user input after we emit
let suppressWatch = 0

watch(
  () => props.modelValue,
  (d) => {
    if (suppressWatch > 0) return
    if (!d) {
      dayStr.value = ''
      monthStr.value = ''
      yearStr.value = ''
    } else {
      dayStr.value = String(d.getDate()).padStart(2, '0')
      monthStr.value = String(d.getMonth() + 1).padStart(2, '0')
      yearStr.value = String(d.getFullYear())
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
    // Suppress the watch so it doesn't reformat the segment the user is currently editing
    suppressWatch++
    emit('update:modelValue', new Date(y, m - 1, d, 12))
    nextTick(() => { suppressWatch-- })
  } else if (dayStr.value === '' && monthStr.value === '' && yearStr.value === '') {
    suppressWatch++
    emit('update:modelValue', null)
    nextTick(() => { suppressWatch-- })
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

function toggleCalendar(e: MouseEvent) {
  popoverRef.value?.toggle(e)
}

function onCalendarSelect(date: unknown) {
  if (!date || !(date instanceof Date)) {
    emit('update:modelValue', null)
  } else {
    // Use noon to avoid DST shifts
    emit('update:modelValue', new Date(date.getFullYear(), date.getMonth(), date.getDate(), 12))
  }
  popoverRef.value?.hide()
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

.app-date-picker__spacer {
  flex: 1;
}

.app-date-picker__icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.2rem;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--p-inputtext-placeholder-color, #6b7280);
  font-size: 0.8rem;
  line-height: 1;
  flex-shrink: 0;
}

.app-date-picker__icon-btn:hover {
  color: var(--p-text-color, #374151);
}
</style>
