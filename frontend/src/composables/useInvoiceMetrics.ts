import { computed, type Ref } from 'vue'
import type { Invoice } from '../api/invoices'
import { useFiscalYearStore } from '../stores/fiscalYear'

// ---------------------------------------------------------------------------
// Pure helpers — exported so callers can reuse without re-importing
// ---------------------------------------------------------------------------

export function remainingForInvoice(invoice: Invoice): number {
  return Math.max(0, parseFloat(invoice.total_amount) - parseFloat(invoice.paid_amount))
}

export function isOpenReceivableInvoice(invoice: Invoice): boolean {
  return invoice.status !== 'draft' && remainingForInvoice(invoice) > 0
}

export function isOverdueInvoice(invoice: Invoice): boolean {
  return Boolean(
    invoice.status !== 'draft' &&
      invoice.due_date &&
      remainingForInvoice(invoice) > 0 &&
      invoice.due_date < new Date().toISOString().slice(0, 10),
  )
}

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

/**
 * Computes receivable and portfolio metrics from reactive invoice lists.
 *
 * @param allInvoices  - All client invoices (unfiltered).
 * @param displayedInvoices - Currently visible invoices after DataTable filtering.
 */
export function useInvoiceMetrics(
  allInvoices: Readonly<Ref<Invoice[]>>,
  displayedInvoices: Readonly<Ref<Invoice[]>>,
) {
  const fiscalYearStore = useFiscalYearStore()

  const receivableMetrics = computed(() => {
    const openReceivables = allInvoices.value.filter(isOpenReceivableInvoice)
    const fiscalYear = fiscalYearStore.selectedFiscalYear
    const exerciseReceivables = fiscalYear
      ? openReceivables.filter(
          (invoice) =>
            invoice.date >= fiscalYear.start_date && invoice.date <= fiscalYear.end_date,
        )
      : openReceivables
    const historicalReceivables = fiscalYear
      ? openReceivables.filter((invoice) => invoice.date < fiscalYear.start_date)
      : []

    return {
      exerciseAmount: exerciseReceivables.reduce(
        (sum, invoice) => sum + remainingForInvoice(invoice),
        0,
      ),
      exerciseCount: exerciseReceivables.length,
      totalAmount: openReceivables.reduce(
        (sum, invoice) => sum + remainingForInvoice(invoice),
        0,
      ),
      totalCount: openReceivables.length,
      historicalAmount: historicalReceivables.reduce(
        (sum, invoice) => sum + remainingForInvoice(invoice),
        0,
      ),
      historicalCount: historicalReceivables.length,
    }
  })

  const portfolioMetrics = computed(() => {
    const visible = displayedInvoices.value
    const totalAmount = visible.reduce(
      (sum, invoice) => sum + parseFloat(invoice.total_amount),
      0,
    )
    const paidAmount = visible.reduce(
      (sum, invoice) => sum + parseFloat(invoice.paid_amount),
      0,
    )
    const overdueInvoices = visible.filter(isOverdueInvoice)
    const overdueAmount = overdueInvoices.reduce(
      (sum, invoice) => sum + remainingForInvoice(invoice),
      0,
    )
    const partialCount = visible.filter((invoice) => invoice.status === 'partial').length

    return {
      visibleCount: visible.length,
      totalAmount,
      paidAmount,
      overdueAmount,
      overdueCount: overdueInvoices.length,
      partialCount,
      averageAmount: visible.length > 0 ? totalAmount / visible.length : 0,
    }
  })

  return { receivableMetrics, portfolioMetrics }
}
