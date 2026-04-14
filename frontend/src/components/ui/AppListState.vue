<template>
  <div class="app-list-state" :class="stateClass">
    <div class="app-list-state__header">
      <span class="app-chip">{{ countLabel }}</span>
      <p class="app-list-state__text">{{ statusLabel }}</p>
    </div>

    <div v-if="chips.length > 0" class="app-list-state__chips">
      <span v-for="chip in chips" :key="chip" class="app-list-state__chip">{{ chip }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = withDefaults(
  defineProps<{
    displayedCount: number
    totalCount?: number
    loading?: boolean
    searchText?: string
    activeFilters?: string[]
  }>(),
  {
    totalCount: undefined,
    loading: false,
    searchText: '',
    activeFilters: () => [],
  },
)

const { t } = useI18n()

const trimmedSearchText = computed(() => props.searchText.trim())
const normalizedTotalCount = computed(() => props.totalCount ?? props.displayedCount)
const hasActiveConstraints = computed(
  () => trimmedSearchText.value.length > 0 || props.activeFilters.length > 0,
)

const countLabel = computed(() => {
  if (normalizedTotalCount.value !== props.displayedCount) {
    return t('common.list.count_filtered', {
      shown: props.displayedCount,
      total: normalizedTotalCount.value,
    })
  }

  return t('common.list.count_total', { count: props.displayedCount })
})

const statusLabel = computed(() => {
  if (props.loading) return t('common.list.status.loading')
  if (props.displayedCount === 0) {
    return hasActiveConstraints.value
      ? t('common.list.status.filtered_empty')
      : t('common.list.status.empty')
  }

  return hasActiveConstraints.value
    ? t('common.list.status.filtered_scope')
    : t('common.list.status.full_scope')
})

const chips = computed(() => {
  const nextChips: string[] = []

  if (trimmedSearchText.value.length > 0) {
    nextChips.push(t('common.list.search_chip', { query: trimmedSearchText.value }))
  }

  for (const label of props.activeFilters) {
    nextChips.push(t('common.list.filter_chip', { label }))
  }

  return nextChips
})

const stateClass = computed(() => ({
  'app-list-state--loading': props.loading,
  'app-list-state--empty': !props.loading && props.displayedCount === 0,
}))
</script>
