<template>
  <Message
    v-if="isOutside"
    severity="warn"
    size="small"
    data-testid="fiscal-year-date-warning"
    class="app-fy-date-warning"
  >
    {{ t('fiscalYearGuard.date_outside') }}
  </Message>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Message from 'primevue/message'
import { useFiscalYearCoverage } from '@/composables/useFiscalYearCoverage'

const props = defineProps<{ date: Date | string | null | undefined }>()

const { t } = useI18n()
const { isDateOutsideFiscalYears } = useFiscalYearCoverage()

const isOutside = computed(() => isDateOutsideFiscalYears(props.date))
</script>

<style scoped>
.app-fy-date-warning {
  margin-top: var(--app-space-2);
}
</style>
