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

export function formatDisplayDate(value: string | Date | null | undefined): string {
  const parsed = parseDateLike(value)
  if (!parsed) return typeof value === 'string' ? value : ''
  return new Intl.DateTimeFormat('fr-FR').format(parsed)
}

export function formatDisplayDateTime(value: string | Date | null | undefined): string {
  const parsed = parseDateLike(value)
  if (!parsed) return typeof value === 'string' ? value : ''
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(parsed)
}
