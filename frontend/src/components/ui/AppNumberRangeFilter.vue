<template>
  <div class="app-range-filter">
    <InputNumber
      :model-value="minValue"
      mode="decimal"
      :min-fraction-digits="fractionDigits"
      :max-fraction-digits="fractionDigits"
      @update:model-value="updateMin"
    />
    <InputNumber
      :model-value="maxValue"
      mode="decimal"
      :min-fraction-digits="fractionDigits"
      :max-fraction-digits="fractionDigits"
      @update:model-value="updateMax"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import InputNumber from 'primevue/inputnumber'

const props = withDefaults(
  defineProps<{
    modelValue?: [number | null, number | null] | null
    fractionDigits?: number
  }>(),
  {
    fractionDigits: 2,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: [number | null, number | null] | null]
}>()

const minValue = computed(() => props.modelValue?.[0] ?? null)
const maxValue = computed(() => props.modelValue?.[1] ?? null)

function buildRange(
  min: number | null | undefined,
  max: number | null | undefined,
): [number | null, number | null] | null {
  const normalizedMin = typeof min === 'number' ? min : null
  const normalizedMax = typeof max === 'number' ? max : null

  return normalizedMin !== null || normalizedMax !== null ? [normalizedMin, normalizedMax] : null
}

function updateMin(value: number | null | undefined): void {
  emit('update:modelValue', buildRange(value, maxValue.value))
}

function updateMax(value: number | null | undefined): void {
  emit('update:modelValue', buildRange(minValue.value, value))
}
</script>

<style scoped>
.app-range-filter {
  display: grid;
  gap: 0.5rem;
}
</style>
