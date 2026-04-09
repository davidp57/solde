import apiClient from './client'

export type DepositType = 'cheques' | 'especes'
export type BankTransactionSource = 'manual' | 'import'

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
  payment_ids: number[]
}

export interface DepositCreate {
  date: string
  type: DepositType
  payment_ids: number[]
  bank_reference?: string | null
  notes?: string | null
}

export async function getBankBalance(): Promise<{ balance: string }> {
  const response = await apiClient.get<{ balance: string }>('/api/bank/balance')
  return response.data
}

export async function listTransactions(params?: {
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

export async function listDeposits(params?: {
  skip?: number
  limit?: number
}): Promise<Deposit[]> {
  const response = await apiClient.get<Deposit[]>('/api/bank/deposits', { params })
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
