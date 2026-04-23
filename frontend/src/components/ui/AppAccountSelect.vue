<template>
  <Select
    v-bind="$attrs"
    :model-value="modelValue"
    :options="accountOptions"
    option-label="displayLabel"
    option-value="number"
    :placeholder="placeholder"
    filter
    show-clear
    @update:model-value="emit('update:modelValue', $event ?? null)"
  >
    <template #option="{ option }">
      <div class="account-select-option">
        <span
          v-if="option.focusKey"
          class="account-select-dot"
          :class="`account-select-dot--${option.focusKey}`"
        />
        <span>{{ option.displayLabel }}</span>
      </div>
    </template>
    <template #value="{ value }">
      <div v-if="value !== null && value !== undefined && value !== ''" class="account-select-option">
        <span
          v-if="selectedFocusKey"
          class="account-select-dot"
          :class="`account-select-dot--${selectedFocusKey}`"
        />
        <span>{{ selectedDisplayLabel ?? value }}</span>
      </div>
    </template>
  </Select>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Select from 'primevue/select'
import type { AccountingAccount } from '@/api/accounting'
import {
  formatFocusedAccountLabel,
  getFocusAccountKey,
  type FocusAccountKey,
} from '@/utils/focusAccounts'

const props = withDefaults(
  defineProps<{
    modelValue: string | null
    accounts: AccountingAccount[]
    placeholder?: string
  }>(),
  {
    placeholder: undefined,
  },
)

const emit = defineEmits<{ 'update:modelValue': [value: string | null] }>()

const { t } = useI18n()

const accountOptions = computed(() =>
  props.accounts.map((a) => ({
    number: a.number,
    displayLabel: formatFocusedAccountLabel(a.number, a.label, t),
    focusKey: getFocusAccountKey(a.number),
  })),
)

const selectedFocusKey = computed<FocusAccountKey | null>(() => {
  if (!props.modelValue) return null
  return getFocusAccountKey(props.modelValue)
})

const selectedDisplayLabel = computed<string | null>(() => {
  if (!props.modelValue) return null
  const opt = accountOptions.value.find((o) => o.number === props.modelValue)
  return opt?.displayLabel ?? null
})
</script>
