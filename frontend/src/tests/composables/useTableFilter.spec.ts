import { ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { applyFilter, useTableFilter } from '../../composables/useTableFilter'

describe('applyFilter', () => {
  const items = [
    { id: 1, name: 'Alice', city: 'Paris' },
    { id: 2, name: 'Bob', city: 'Lyon' },
    { id: 3, name: 'Charlie', city: 'Paris' },
  ]

  it('returns all items when query is empty', () => {
    expect(applyFilter(items, '')).toEqual(items)
    expect(applyFilter(items, '   ')).toEqual(items)
  })

  it('filters items by matching any field value (case-insensitive)', () => {
    expect(applyFilter(items, 'alice')).toEqual([items[0]])
    expect(applyFilter(items, 'PARIS')).toEqual([items[0], items[2]])
  })

  it('matches numeric fields converted to string', () => {
    expect(applyFilter(items, '2')).toEqual([items[1]])
  })

  it('returns empty array when no match', () => {
    expect(applyFilter(items, 'Marseille')).toEqual([])
  })

  it('handles items with null or undefined values gracefully', () => {
    const mixed = [
      { id: 1, name: null },
      { id: 2, name: undefined },
      { id: 3, name: 'Test' },
    ]
    expect(applyFilter(mixed, 'test')).toEqual([mixed[2]])
  })
})

describe('useTableFilter', () => {
  it('returns all items when filterText is empty', () => {
    const items = ref([{ name: 'Alice' }, { name: 'Bob' }])
    const { filtered, filterText } = useTableFilter(items)

    expect(filterText.value).toBe('')
    expect(filtered.value).toEqual(items.value)
  })

  it('reactively filters items when filterText changes', () => {
    const items = ref([
      { name: 'Alice', role: 'admin' },
      { name: 'Bob', role: 'user' },
    ])
    const { filtered, filterText } = useTableFilter(items)

    filterText.value = 'bob'
    expect(filtered.value).toHaveLength(1)
    expect(filtered.value[0]).toEqual({ name: 'Bob', role: 'user' })
  })

  it('reacts to source array changes', () => {
    const items = ref([{ name: 'Alice' }])
    const { filtered, filterText } = useTableFilter(items)

    filterText.value = 'bob'
    expect(filtered.value).toHaveLength(0)

    items.value = [{ name: 'Alice' }, { name: 'Bob' }]
    expect(filtered.value).toHaveLength(1)
  })
})
