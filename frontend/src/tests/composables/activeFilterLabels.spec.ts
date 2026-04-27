import { describe, expect, it } from 'vitest'
import {
  findSelectedFilterLabel,
  collectActiveFilterLabels,
} from '../../composables/activeFilterLabels'

describe('findSelectedFilterLabel', () => {
  const options = [
    { label: 'Draft', value: 'draft' },
    { label: 'Paid', value: 'paid' },
    { label: 'Overdue', value: 'overdue' },
  ] as const

  it('returns the label matching the given value', () => {
    expect(findSelectedFilterLabel(options, 'paid')).toBe('Paid')
  })

  it('returns undefined when value is null', () => {
    expect(findSelectedFilterLabel(options, null)).toBeUndefined()
  })

  it('returns undefined when value is undefined', () => {
    expect(findSelectedFilterLabel(options, undefined)).toBeUndefined()
  })

  it('returns stringified value when no option matches', () => {
    expect(findSelectedFilterLabel(options, 'unknown')).toBe('unknown')
  })

  it('works with numeric values', () => {
    const numericOptions = [
      { label: 'One', value: 1 },
      { label: 'Two', value: 2 },
    ]
    expect(findSelectedFilterLabel(numericOptions, 1)).toBe('One')
    expect(findSelectedFilterLabel(numericOptions, 99)).toBe('99')
  })
})

describe('collectActiveFilterLabels', () => {
  it('returns only non-empty string labels', () => {
    expect(collectActiveFilterLabels('Status: Draft', null, undefined, 'Year: 2025')).toEqual([
      'Status: Draft',
      'Year: 2025',
    ])
  })

  it('filters out false values', () => {
    expect(collectActiveFilterLabels(false, 'Active', false)).toEqual(['Active'])
  })

  it('returns empty array when all labels are falsy', () => {
    expect(collectActiveFilterLabels(null, undefined, false)).toEqual([])
  })

  it('filters out empty strings', () => {
    expect(collectActiveFilterLabels('', 'Label', '')).toEqual(['Label'])
  })

  it('returns empty array with no arguments', () => {
    expect(collectActiveFilterLabels()).toEqual([])
  })
})
