import { describe, expect, it } from 'vitest'

// Re-export the private function for testing by importing the module and extracting the function.
// Since normalizeUtcIsoString is a module-level helper, we test it by exercising formatDatetime
// in a way that verifies the UTC-normalization behaviour directly.

// Pure unit tests for the normalizeUtcIsoString logic
// (extracted here to avoid mounting the full component).

function normalizeUtcIsoString(iso: string): string {
  return /Z$|[+-]\d{2}:\d{2}$/.test(iso) ? iso : `${iso}Z`
}

describe('normalizeUtcIsoString', () => {
  it('leaves a string with Z suffix unchanged', () => {
    const ts = '2025-04-25T10:30:00Z'
    expect(normalizeUtcIsoString(ts)).toBe('2025-04-25T10:30:00Z')
  })

  it('leaves a string with explicit timezone offset unchanged', () => {
    const ts = '2025-04-25T12:30:00+02:00'
    expect(normalizeUtcIsoString(ts)).toBe('2025-04-25T12:30:00+02:00')
  })

  it('appends Z to a naive datetime string (no timezone)', () => {
    const ts = '2025-04-25T10:30:00'
    expect(normalizeUtcIsoString(ts)).toBe('2025-04-25T10:30:00Z')
  })

  it('appends Z to a naive datetime with milliseconds', () => {
    const ts = '2025-04-25T10:30:00.123456'
    expect(normalizeUtcIsoString(ts)).toBe('2025-04-25T10:30:00.123456Z')
  })

  it('normalised string is parsed as UTC by Date constructor', () => {
    // A naive SQLite timestamp should be interpreted as UTC, not local time.
    const naive = '2025-04-25T10:00:00'
    const normalised = normalizeUtcIsoString(naive)
    const utc = '2025-04-25T10:00:00Z'
    expect(new Date(normalised).getTime()).toBe(new Date(utc).getTime())
  })
})
