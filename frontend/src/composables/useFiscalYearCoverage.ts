import { useFiscalYearStore } from '@/stores/fiscalYear'
import type { FiscalYearRead } from '@/api/accounting'

/** Format a Date or an ISO-ish string as YYYY-MM-DD, using local parts. */
function toIsoDay(value: Date | string): string | null {
  if (value instanceof Date) {
    if (Number.isNaN(value.getTime())) return null
    const month = String(value.getMonth() + 1).padStart(2, '0')
    const day = String(value.getDate()).padStart(2, '0')
    return `${value.getFullYear()}-${month}-${day}`
  }
  const trimmed = value.trim()
  return /^\d{4}-\d{2}-\d{2}/.test(trimmed) ? trimmed.slice(0, 10) : null
}

/**
 * Tell whether a date falls inside a declared fiscal year.
 *
 * An entry dated outside every fiscal year is saved with no year attached: it
 * then shows up in no screen filtered by year, and its accounting entry carries
 * no `fiscal_year_id`. Warning at entry time is cheaper than hunting for it
 * later — the store already holds the full list, so no extra request is needed.
 */
export function useFiscalYearCoverage() {
  const fiscalYearStore = useFiscalYearStore()

  function coveringFiscalYear(
    value: Date | string | null | undefined,
  ): FiscalYearRead | undefined {
    if (!value) return undefined
    const day = toIsoDay(value)
    if (day === null) return undefined
    return fiscalYearStore.fiscalYears.find(
      (fiscalYear) => fiscalYear.start_date <= day && day <= fiscalYear.end_date,
    )
  }

  /** False only when the date is valid, years are known, and none covers it. */
  function isDateOutsideFiscalYears(value: Date | string | null | undefined): boolean {
    if (!value || !fiscalYearStore.fiscalYears.length) return false
    if (toIsoDay(value) === null) return false
    return coveringFiscalYear(value) === undefined
  }

  return { coveringFiscalYear, isDateOutsideFiscalYears }
}
