import apiClient, { parseTotalCount } from './client'

export type DepositType = 'cheques' | 'especes'
export type BankTransactionSource =
  | 'manual'
  | 'import'
  | 'import_excel'
  | 'import_csv'
  | 'import_ofx'
  | 'import_qif'
  | 'system_opening'
export type BankTransactionCategory =
  | 'uncategorized'
  | 'customer_payment'
  | 'cheque_deposit'
  | 'cash_deposit'
  | 'supplier_payment'
  | 'salary'
  | 'social_charge'
  | 'bank_fee'
  | 'internal_transfer'
  | 'grant'
  | 'sepa_debit'
  | 'other_credit'
  | 'other_debit'
  | 'no_entry'
export type BankImportFormat = 'csv' | 'ofx' | 'qif'
export type BankAccountType = 'courant' | 'epargne'

export interface BankTransaction {
  id: number
  date: string
  amount: string
  reference: string | null
  description: string
  balance_after: string
  reconciled: boolean
  reconciled_with: string | null
  source: BankTransactionSource
  detected_category: BankTransactionCategory
  bank_account: BankAccountType
  payment_id: number | null
  payment_ids: number[]
}

export interface BankTransactionClientPaymentAllocation {
  invoice_id: number
  amount: string
}

export interface BankTransactionClientPaymentLink {
  payment_id: number
}

export interface BankTransactionClientPaymentLinks {
  payment_ids: number[]
}

export interface BankTransactionCreate {
  date: string
  amount: string
  reference?: string | null
  description?: string
  balance_after?: string
  source?: BankTransactionSource
  bank_account?: BankAccountType
}

export interface BankTransactionUpdate {
  reconciled?: boolean
  reconciled_with?: string | null
  reference?: string | null
  description?: string | null
  detected_category?: BankTransactionCategory
  // Manual transactions only
  date?: string
  amount?: string
  bank_account?: BankAccountType
}

export interface Deposit {
  id: number
  date: string
  type: DepositType
  total_amount: string
  bank_reference: string | null
  notes: string | null
  denomination_details: string | null
  confirmed: boolean
  confirmed_date: string | null
  payment_ids: number[]
}

export interface DenominationLine {
  value: number
  count: number
}

export interface CashCountPrefill {
  date: string
  total_amount: number
  denominations: DenominationLine[]
}

export interface DepositCreate {
  date: string
  type: DepositType
  payment_ids?: number[]
  total_amount?: string | null
  denomination_details?: string | null
  bank_reference?: string | null
  notes?: string | null
}

export interface FundsChartRow {
  month: string
  current_account: number
  savings_account: number
  total: number
  balance: number
}

export interface BankBalance {
  balance: string
  balance_courant: string
  balance_epargne: string
}

export async function getBankBalance(): Promise<BankBalance> {
  const response = await apiClient.get<BankBalance>('/api/bank/balance')
  return response.data
}

export async function getBankFundsChart(months = 6): Promise<FundsChartRow[]> {
  const response = await apiClient.get<FundsChartRow[]>('/api/bank/chart/funds', {
    params: { months },
  })
  return response.data
}

export async function listTransactions(params?: {
  from_date?: string
  to_date?: string
  unreconciled_only?: boolean
  bank_account?: BankAccountType
  skip?: number
  limit?: number
}): Promise<BankTransaction[]> {
  const response = await apiClient.get<BankTransaction[]>('/api/bank/transactions', { params })
  return response.data
}

export async function listTransactionsWithCount(params?: {
  from_date?: string
  to_date?: string
  unreconciled_only?: boolean
  bank_account?: BankAccountType
  skip?: number
  limit?: number
}): Promise<{ items: BankTransaction[]; total: number }> {
  const response = await apiClient.get<BankTransaction[]>('/api/bank/transactions', { params })
  return { items: response.data, total: parseTotalCount(response.headers as Record<string, string>) }
}

export async function addTransaction(payload: BankTransactionCreate): Promise<BankTransaction> {
  const response = await apiClient.post<BankTransaction>('/api/bank/transactions', payload)
  return response.data
}

export async function updateTransaction(
  id: number,
  payload: BankTransactionUpdate,
): Promise<BankTransaction> {
  const response = await apiClient.put<BankTransaction>(`/api/bank/transactions/${id}`, payload)
  return response.data
}

export async function deleteTransaction(id: number): Promise<void> {
  await apiClient.delete(`/api/bank/transactions/${id}`)
}

export async function reconcileTransactionsBulk(ids: number[]): Promise<number> {
  const response = await apiClient.post<number>('/api/bank/transactions/reconcile-bulk', { ids })
  return response.data
}

export interface BankImportResult {
  created: BankTransaction[]
  skipped: number
  /** Statement rows folded into a deposit already recorded by Solde. */
  merged: number
}

export async function importCsv(content: string): Promise<BankImportResult> {
  const response = await apiClient.post<BankImportResult>('/api/bank/transactions/import-csv', {
    content,
  })
  return response.data
}

export async function importOfx(content: string, defaultBankAccount: BankAccountType = 'courant'): Promise<BankImportResult> {
  const response = await apiClient.post<BankImportResult>('/api/bank/transactions/import-ofx', {
    content,
    default_bank_account: defaultBankAccount,
  })
  return response.data
}

export async function importQif(content: string): Promise<BankImportResult> {
  const response = await apiClient.post<BankImportResult>('/api/bank/transactions/import-qif', {
    content,
  })
  return response.data
}

export async function importBankStatement(
  format: BankImportFormat,
  content: string,
  defaultBankAccount: BankAccountType = 'courant',
): Promise<BankImportResult> {
  if (format === 'ofx') {
    return importOfx(content, defaultBankAccount)
  }
  if (format === 'qif') {
    return importQif(content)
  }
  return importCsv(content)
}

export async function createClientPaymentFromTransaction(
  txId: number,
  invoiceId: number,
): Promise<BankTransaction> {
  const response = await apiClient.post<BankTransaction>(
    `/api/bank/transactions/${txId}/create-client-payment`,
    {
      invoice_id: invoiceId,
    },
  )
  return response.data
}

export async function createClientPaymentsFromTransaction(
  txId: number,
  allocations: BankTransactionClientPaymentAllocation[],
): Promise<BankTransaction> {
  const response = await apiClient.post<BankTransaction>(
    `/api/bank/transactions/${txId}/create-client-payments`,
    {
      allocations,
    },
  )
  return response.data
}

export async function createSupplierPaymentFromTransaction(
  txId: number,
  invoiceId: number,
): Promise<BankTransaction> {
  const response = await apiClient.post<BankTransaction>(
    `/api/bank/transactions/${txId}/create-supplier-payment`,
    {
      invoice_id: invoiceId,
    },
  )
  return response.data
}

export async function linkClientPaymentToTransaction(
  txId: number,
  paymentId: number,
): Promise<BankTransaction> {
  const response = await apiClient.post<BankTransaction>(
    `/api/bank/transactions/${txId}/link-client-payment`,
    {
      payment_id: paymentId,
    },
  )
  return response.data
}

export async function linkClientPaymentsToTransaction(
  txId: number,
  paymentIds: number[],
): Promise<BankTransaction> {
  const payload: BankTransactionClientPaymentLinks = {
    payment_ids: paymentIds,
  }
  const response = await apiClient.post<BankTransaction>(
    `/api/bank/transactions/${txId}/link-client-payments`,
    payload,
  )
  return response.data
}

export async function linkSupplierPaymentToTransaction(
  txId: number,
  paymentId: number,
): Promise<BankTransaction> {
  const response = await apiClient.post<BankTransaction>(
    `/api/bank/transactions/${txId}/link-supplier-payment`,
    {
      payment_id: paymentId,
    },
  )
  return response.data
}

export async function listDeposits(params?: {
  from_date?: string
  to_date?: string
  confirmed?: boolean
  skip?: number
  limit?: number
}): Promise<Deposit[]> {
  const response = await apiClient.get<Deposit[]>('/api/bank/deposits', { params })
  return response.data
}

export async function listDepositsWithCount(params?: {
  from_date?: string
  to_date?: string
  confirmed?: boolean
  skip?: number
  limit?: number
}): Promise<{ items: Deposit[]; total: number }> {
  const response = await apiClient.get<Deposit[]>('/api/bank/deposits', { params })
  return { items: response.data, total: parseTotalCount(response.headers as Record<string, string>) }
}

export async function confirmDeposit(id: number): Promise<Deposit> {
  const response = await apiClient.post<Deposit>(`/api/bank/deposits/${id}/confirm`)
  return response.data
}

export interface DepositUpdate {
  payment_ids?: number[]
  total_amount?: string | null
  denomination_details?: string | null
}

export async function updateDeposit(id: number, payload: DepositUpdate): Promise<Deposit> {
  const response = await apiClient.patch<Deposit>(`/api/bank/deposits/${id}`, payload)
  return response.data
}

export async function deleteDeposit(id: number): Promise<void> {
  await apiClient.delete(`/api/bank/deposits/${id}`)
}

export async function createDeposit(payload: DepositCreate): Promise<Deposit> {
  const response = await apiClient.post<Deposit>('/api/bank/deposits', payload)
  return response.data
}

export async function getDeposit(id: number): Promise<Deposit> {
  const response = await apiClient.get<Deposit>(`/api/bank/deposits/${id}`)
  return response.data
}
