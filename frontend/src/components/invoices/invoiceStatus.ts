import type { InvoiceStatus } from '../../api/invoices'

// Single source of truth for invoice status → PrimeVue severity mapping.
// Previously duplicated verbatim across ClientInvoicesView, SupplierInvoicesView
// and ContactHistoryContent.
const STATUS_SEVERITY: Record<InvoiceStatus, string> = {
  draft: 'secondary',
  sent: 'info',
  paid: 'success',
  partial: 'warn',
  overdue: 'danger',
  disputed: 'danger',
  irrecoverable: 'secondary',
  archived: 'secondary',
}

export function invoiceStatusSeverity(status: string): string {
  return STATUS_SEVERITY[status as InvoiceStatus] ?? 'secondary'
}
