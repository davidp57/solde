import apiClient from './client'

export type DepositType = 'cheques' | 'especes'
export type BankTransactionSource = 'manual' | 'import' | 'system_opening'
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
export type BankImportFormat = 'csv' | 'ofx' | 'qif'

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
}

export interface BankTransactionUpdate {
  reconciled?: boolean
  reconciled_with?: string | null
  reference?: string | null
  description?: string | null
}

export interface Deposit {
  id: number
  date: string
  type: DepositType
  total_amount: string
  bank_reference: string | null
  notes: string | null
  confirmed: boolean
  confirmed_date: string | null
  payment_ids: number[]
}

export interface DepositCreate {
  date: string
  type: DepositType
  payment_ids: number[]
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

export async function getBankBalance(): Promise<{ balance: string }> {
  const response = await apiClient.get<{ balance: string }>('/api/bank/balance')
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
  skip?: number
  limit?: number
}): Promise<BankTransaction[]> {
  const response = await apiClient.get<BankTransaction[]>('/api/bank/transactions', { params })
  return response.data
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

export async function importCsv(content: string): Promise<BankTransaction[]> {
  const response = await apiClient.post<BankTransaction[]>('/api/bank/transactions/import-csv', {
    content,
  })
  return response.data
}

export async function importOfx(content: string): Promise<BankTransaction[]> {
  const response = await apiClient.post<BankTransaction[]>('/api/bank/transactions/import-ofx', {
    content,
  })
  return response.data
}

export async function importQif(content: string): Promise<BankTransaction[]> {
  const response = await apiClient.post<BankTransaction[]>('/api/bank/transactions/import-qif', {
    content,
  })
  return response.data
}

export async function importBankStatement(
  format: BankImportFormat,
  content: string,
): Promise<BankTransaction[]> {
  if (format === 'ofx') {
    return importOfx(content)
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

export async function confirmDeposit(id: number): Promise<Deposit> {
  const response = await apiClient.post<Deposit>(`/api/bank/deposits/${id}/confirm`)
  return response.data
}

export async function createDeposit(payload: DepositCreate): Promise<Deposit> {
  const response = await apiClient.post<Deposit>('/api/bank/deposits', payload)
  return response.data
}

export async function getDeposit(id: number): Promise<Deposit> {
  const response = await apiClient.get<Deposit>(`/api/bank/deposits/${id}`)
  return response.data
}
