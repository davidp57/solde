import fr from '@/i18n/fr'

/**
 * Display helpers for the audit journal.
 *
 * Action names exist only in French, in the interface: the server stores codes such
 * as `bank.transaction.bulk_reconcile`. Searching "rapprochement" therefore needs the
 * interface to tell the server which codes that word designates (`matchingActionCodes`).
 */

type MessageTree = { [key: string]: string | MessageTree }

function flatten(tree: MessageTree, prefix = ''): Record<string, string> {
  const flat: Record<string, string> = {}
  for (const [key, value] of Object.entries(tree)) {
    const code = prefix ? `${prefix}.${key}` : key
    if (typeof value === 'string') flat[code] = value
    else Object.assign(flat, flatten(value, code))
  }
  return flat
}

/** French name of every audited action, keyed by its code. */
export const AUDIT_ACTION_LABELS: Readonly<Record<string, string>> = flatten(
  fr.system.action as MessageTree,
)

const DETAIL_LABELS: Readonly<Record<string, string>> = fr.system.audit_detail

const CATEGORY_LABELS: Readonly<Record<string, string>> = fr.bank.categories

/** Detail keys holding an amount, displayed as euros. */
const AMOUNT_KEYS = new Set(['amount', 'total', 'total_amount'])
/** Detail keys holding a bank category code. */
const CATEGORY_KEYS = new Set(['category'])
const ISO_DAY = /^(\d{4})-(\d{2})-(\d{2})$/

export function auditActionLabel(code: string): string {
  return Object.hasOwn(AUDIT_ACTION_LABELS, code) ? (AUDIT_ACTION_LABELS[code] as string) : code
}

function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
}

/** Codes of the actions whose French name contains *query* (accents and case ignored). */
export function matchingActionCodes(query: string): string[] {
  const needle = normalize(query.trim())
  if (!needle) return []
  return Object.entries(AUDIT_ACTION_LABELS)
    .filter(([, label]) => normalize(label).includes(needle))
    .map(([code]) => code)
}

export interface AuditDetailItem {
  label: string
  /** One value, or several for a list (the lines of a bulk reconciliation). */
  values: string[]
}

function formatAmount(value: unknown): string {
  const number = typeof value === 'number' ? value : Number.parseFloat(String(value))
  if (!Number.isFinite(number)) return String(value)
  return `${number.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`
}

function formatValue(key: string, value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? fr.common.yes : fr.common.no
  if (AMOUNT_KEYS.has(key)) return formatAmount(value)
  if (CATEGORY_KEYS.has(key) && typeof value === 'string' && Object.hasOwn(CATEGORY_LABELS, value)) {
    return CATEGORY_LABELS[value] as string
  }
  const day = typeof value === 'string' ? ISO_DAY.exec(value) : null
  if (day) return `${day[3]}/${day[2]}/${day[1]}`
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

/** Turn an entry's raw detail into labelled, formatted lines. */
export function formatAuditDetail(detail: Record<string, unknown> | null): AuditDetailItem[] {
  if (!detail) return []
  return Object.entries(detail).map(([key, value]) => ({
    label: Object.hasOwn(DETAIL_LABELS, key) ? (DETAIL_LABELS[key] as string) : key,
    values: Array.isArray(value)
      ? value.map((item) => formatValue(key, item))
      : [formatValue(key, value)],
  }))
}
