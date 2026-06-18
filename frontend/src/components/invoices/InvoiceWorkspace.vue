<template>
  <AppPage :width="wide ? 'wide' : 'default'">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="title" :subtitle="subtitle">
      <template #actions>
        <slot name="header-actions">
          <Button :label="newLabel ?? t('invoices.new')" icon="pi pi-plus" @click="emit('new')" />
        </slot>
      </template>
    </AppPageHeader>

    <InvoiceTypeToggle :type="type" />

    <InvoiceFunnelHero
      :type="type"
      :total-invoiced="funnel.totalInvoiced"
      :collected="funnel.collected"
      :remaining="funnel.remaining"
      :overdue="funnel.overdue"
      :invoice-count="funnel.count"
    />

    <AppPanel :title="panelTitle" :subtitle="panelSubtitle">
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ filtersHint }}</p>
          <div class="app-toolbar__meta-actions">
            <AppListState
              :displayed-count="displayedCount"
              :total-count="totalCount"
              :loading="loading"
              :search-text="searchValue"
              :active-filters="activeFilters"
            />
            <Button
              v-if="hasActiveFilters"
              icon="pi pi-filter-slash"
              severity="secondary"
              text
              :title="t('common.reset_filters')"
              @click="emit('reset-filters')"
            />
            <Button
              icon="pi pi-file-excel"
              severity="secondary"
              text
              :title="t('common.export_excel')"
              @click="emit('export')"
            />
          </div>
        </div>

        <InvoiceFilterSegments
          :segments="segments"
          :model-value="activeSegment"
          :aria-label="segmentsLabel ?? t('invoices.filter_status')"
          @update:model-value="(key: string) => emit('segment-change', key)"
        />

        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText
              :model-value="searchValue"
              :placeholder="t('common.filter_placeholder')"
              @update:model-value="(value: string) => emit('update:searchValue', value ?? '')"
            />
          </div>
          <slot name="toolbar-extras" />
        </div>
      </div>

      <slot />
    </AppPanel>

    <slot name="dialogs" />
  </AppPage>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import AppPage from '../ui/AppPage.vue'
import AppPageHeader from '../ui/AppPageHeader.vue'
import AppPanel from '../ui/AppPanel.vue'
import AppListState from '../ui/AppListState.vue'
import InvoiceTypeToggle from './InvoiceTypeToggle.vue'
import InvoiceFunnelHero from './InvoiceFunnelHero.vue'
import InvoiceFilterSegments, { type InvoiceFilterSegment } from './InvoiceFilterSegments.vue'

export interface InvoiceFunnelMetrics {
  totalInvoiced: number
  collected: number
  remaining: number
  overdue: number
  count: number
}

withDefaults(
  defineProps<{
    type: 'client' | 'supplier'
    title: string
    subtitle: string
    panelTitle: string
    panelSubtitle: string
    filtersHint: string
    funnel: InvoiceFunnelMetrics
    segments: InvoiceFilterSegment[]
    activeSegment: string
    searchValue: string
    displayedCount: number
    totalCount: number
    loading?: boolean
    activeFilters?: string[]
    hasActiveFilters?: boolean
    wide?: boolean
    newLabel?: string
    segmentsLabel?: string
  }>(),
  {
    loading: false,
    activeFilters: () => [],
    hasActiveFilters: false,
    wide: false,
    newLabel: undefined,
    segmentsLabel: undefined,
  },
)

const emit = defineEmits<{
  new: []
  'segment-change': [key: string]
  'reset-filters': []
  export: []
  'update:searchValue': [value: string]
}>()

const { t } = useI18n()
</script>
