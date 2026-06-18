<template>
  <Tag :value="label" :severity="severity" class="invoice-status-badge" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Tag from 'primevue/tag'
import type { InvoiceStatus } from '../../api/invoices'
import { invoiceStatusSeverity } from './invoiceStatus'

const props = defineProps<{
  status: InvoiceStatus | string
}>()

const { t } = useI18n()

const severity = computed(() => invoiceStatusSeverity(props.status))
const label = computed(() => t(`invoices.statuses.${props.status}`))
</script>
