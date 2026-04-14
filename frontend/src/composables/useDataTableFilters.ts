import { FilterMatchMode } from '@primevue/core/api'
import { computed, ref, watch, type Ref } from 'vue'

export interface TableFilterDefinition {
  value: unknown
  matchMode: string
}

export type TableFilters = Record<string, TableFilterDefinition>

function cloneFilterValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return [...value]
  }

  return value
}

function cloneFilters(filters: TableFilters): TableFilters {
  return Object.fromEntries(
    Object.entries(filters).map(([key, filter]) => [
      key,
      {
        ...filter,
        value: cloneFilterValue(filter.value),
      },
    ]),
  )
}

function hasFilterValue(value: unknown): boolean {
  if (value === null || value === undefined) return false
  if (typeof value === 'string') return value.trim().length > 0
  if (Array.isArray(value)) return value.some((item) => hasFilterValue(item))
  return true
}

export function textFilter(value: string | null = null): TableFilterDefinition {
  return { value, matchMode: FilterMatchMode.CONTAINS }
}

export function equalsFilter(value: unknown = null): TableFilterDefinition {
  return { value, matchMode: FilterMatchMode.EQUALS }
}

export function inFilter(value: unknown[] = []): TableFilterDefinition {
  return { value, matchMode: FilterMatchMode.IN }
}

export function dateFilter(value: string | null = null): TableFilterDefinition {
  return { value, matchMode: FilterMatchMode.EQUALS }
}

export function dateRangeFilter(
  value: [string | null, string | null] | null = null,
): TableFilterDefinition {
  return { value, matchMode: FilterMatchMode.BETWEEN }
}

export function numericFilter(value: number | null = null): TableFilterDefinition {
  return { value, matchMode: FilterMatchMode.EQUALS }
}

export function numericRangeFilter(
  value: [number | null, number | null] | null = null,
): TableFilterDefinition {
  return { value, matchMode: FilterMatchMode.BETWEEN }
}

export function useDataTableFilters<T>(items: Ref<T[]>, initialFilters: TableFilters) {
  const filters = ref<TableFilters>(cloneFilters(initialFilters))
  const displayedRows = ref<T[]>([])

  watch(
    items,
    (value) => {
      displayedRows.value = value
    },
    { immediate: true },
  )

  const globalFilter = computed<string>({
    get: () => String(filters.value.global?.value ?? ''),
    set: (value) => {
      if (filters.value.global) {
        filters.value.global.value = value
      }
    },
  })

  const activeColumnFilterCount = computed(
    () =>
      Object.entries(filters.value).filter(
        ([key, filter]) => key !== 'global' && hasFilterValue(filter.value),
      ).length,
  )

  const hasActiveFilters = computed(
    () => globalFilter.value.trim().length > 0 || activeColumnFilterCount.value > 0,
  )

  function resetFilters(): void {
    filters.value = cloneFilters(initialFilters)
  }

  function syncDisplayedRows(value: T[]): void {
    displayedRows.value = value
  }

  return {
    filters,
    globalFilter,
    displayedRows,
    activeColumnFilterCount,
    hasActiveFilters,
    resetFilters,
    syncDisplayedRows,
  }
}
