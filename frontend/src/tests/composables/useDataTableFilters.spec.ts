import { ref } from 'vue'
import { describe, expect, it } from 'vitest'

import {
  equalsFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../../composables/useDataTableFilters'

describe('useDataTableFilters', () => {
  it('tracks active filters and resets them to the initial state', () => {
    const items = ref([
      { id: 1, name: 'Alice', status: 'paid' },
      { id: 2, name: 'Bob', status: 'draft' },
    ])

    const {
      filters,
      globalFilter,
      displayedRows,
      activeColumnFilterCount,
      hasActiveFilters,
      resetFilters,
      syncDisplayedRows,
    } = useDataTableFilters(items, {
      global: textFilter(''),
      name: textFilter(),
      status: equalsFilter(null),
    })

    expect(displayedRows.value).toHaveLength(2)
    expect(activeColumnFilterCount.value).toBe(0)
    expect(hasActiveFilters.value).toBe(false)

    globalFilter.value = 'alice'
    expect(filters.value.status).toBeDefined()
    expect(filters.value.name).toBeDefined()
    filters.value.status!.value = 'paid'

    expect(activeColumnFilterCount.value).toBe(1)
    expect(hasActiveFilters.value).toBe(true)

    const firstItem = items.value[0]
    expect(firstItem).toBeDefined()
    syncDisplayedRows([firstItem!])
    expect(displayedRows.value).toEqual([firstItem!])

    resetFilters()

    expect(globalFilter.value).toBe('')
    expect(filters.value.name!.value).toBeNull()
    expect(filters.value.status!.value).toBeNull()
    expect(activeColumnFilterCount.value).toBe(0)
    expect(hasActiveFilters.value).toBe(false)
  })

  it('treats empty array-based filters as inactive and populated ones as active', () => {
    const items = ref([{ id: 1 }, { id: 2 }])

    const { filters, activeColumnFilterCount, hasActiveFilters, resetFilters } =
      useDataTableFilters(items, {
        global: textFilter(''),
        status: inFilter([]),
        amount: numericRangeFilter(null),
      })

    expect(activeColumnFilterCount.value).toBe(0)
    expect(filters.value.status).toBeDefined()
    expect(filters.value.amount).toBeDefined()

    filters.value.status!.value = ['paid']
    filters.value.amount!.value = [null, 250]

    expect(activeColumnFilterCount.value).toBe(2)
    expect(hasActiveFilters.value).toBe(true)

    resetFilters()

    expect(activeColumnFilterCount.value).toBe(0)
    expect(hasActiveFilters.value).toBe(false)
  })
})
