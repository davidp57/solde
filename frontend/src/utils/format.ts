function parseDateLike(value: string | Date | null | undefined): Date | null {
  if (!value) return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  const trimmed = value.trim()
  if (!trimmed) return null

  const plainDateMatch = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (plainDateMatch) {
    const [, year, month, day] = plainDateMatch
    return new Date(Number(year), Number(month) - 1, Number(day))
  }

  const plainDateTimeMatch = trimmed.match(
    /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$/,
  )
  if (plainDateTimeMatch) {
    const [, year, month, day, hour, minute, second] = plainDateTimeMatch
    return new Date(
      Number(year),
      Number(month) - 1,
      Number(day),
      Number(hour),
      Number(minute),
      Number(second ?? '0'),
    )
  }

  const parsed = new Date(trimmed)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function isValidDateParts(year: string, month: string, day: string): boolean {
  const parsedYear = Number.parseInt(year, 10)
  const parsedMonth = Number.parseInt(month, 10)
  const parsedDay = Number.parseInt(day, 10)

  if (
    Number.isNaN(parsedYear) ||
    Number.isNaN(parsedMonth) ||
    Number.isNaN(parsedDay) ||
    parsedMonth < 1 ||
    parsedMonth > 12 ||
    parsedDay < 1 ||
    parsedDay > 31
  ) {
    return false
  }

  const candidate = new Date(`${year}-${month}-${day}T00:00:00`)
  return (
    candidate.getFullYear() === parsedYear &&
    candidate.getMonth() === parsedMonth - 1 &&
    candidate.getDate() === parsedDay
  )
}

function parseMonthLike(value: string | Date | null | undefined): Date | null {
  if (!value) return null

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : new Date(value.getFullYear(), value.getMonth(), 1)
  }

  const trimmed = value.trim()
  if (!trimmed) return null

  const plainMonthMatch = trimmed.match(/^(\d{4})-(\d{2})$/)
  if (plainMonthMatch) {
    const [, year, month] = plainMonthMatch
    const parsedMonth = Number(month)
    if (parsedMonth < 1 || parsedMonth > 12) return null
    return new Date(Number(year), parsedMonth - 1, 1)
  }

  const parsed = parseDateLike(trimmed)
  return parsed ? new Date(parsed.getFullYear(), parsed.getMonth(), 1) : null
}

export function formatDisplayDate(value: string | Date | null | undefined): string {
  const parsed = parseDateLike(value)
  if (!parsed) return typeof value === 'string' ? value : ''
  return new Intl.DateTimeFormat('fr-FR').format(parsed)
}

export function normalizeDateInput(value: string): string | null | undefined {
  const trimmedValue = value.trim()
  if (trimmedValue.length === 0) {
    return null
  }

  const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmedValue)
  if (isoMatch) {
    const [, year, month, day] = isoMatch
    if (!year || !month || !day) {
      return undefined
    }
    return isValidDateParts(year, month, day) ? `${year}-${month}-${day}` : undefined
  }

  const frMatch = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(trimmedValue)
  if (frMatch) {
    const [, day, month, year] = frMatch
    if (!year || !month || !day) {
      return undefined
    }
    return isValidDateParts(year, month, day) ? `${year}-${month}-${day}` : undefined
  }

  return undefined
}

export function formatDateInputDraft(value: string | null | undefined): string {
  if (!value) return ''
  const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!isoMatch) return value
  const [, year, month, day] = isoMatch
  return `${day}/${month}/${year}`
}

export function formatDisplayDateTime(value: string | Date | null | undefined): string {
  const parsed = parseDateLike(value)
  if (!parsed) return typeof value === 'string' ? value : ''
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(parsed)
}

export function formatDisplayMonth(value: string | Date | null | undefined): string {
  const parsed = parseMonthLike(value)
  if (!parsed) return typeof value === 'string' ? value : ''
  return new Intl.DateTimeFormat('fr-FR', {
    month: 'long',
    year: 'numeric',
  }).format(parsed)
}
