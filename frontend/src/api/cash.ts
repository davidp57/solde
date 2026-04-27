import apiClient from './client'

export type CashMovementType = 'in' | 'out'
export type CashEntrySource = 'manual' | 'deposit' | 'payment' | 'system_opening'

export interface LinkedAccountingEntry {
  id: number
  account_number: string
  label: string
  debit: string
  credit: string
}

export interface CashEntryConnections {
  can_delete: boolean
  blocking_reason: string | null
  accounting_entries: LinkedAccountingEntry[]
}

export interface CashEntry {
  id: number
  date: string
  amount: string
  type: CashMovementType
  contact_id: number | null
  payment_id: number | null
  reference: string | null
  description: string
  source: CashEntrySource
  balance_after: string
  is_system_opening: boolean
}

export interface CashEntryCreate {
  date: string
  amount: string
  type: CashMovementType
  contact_id?: number | null
  payment_id?: number | null
  reference?: string | null
  description?: string
}

export interface CashEntryUpdate {
  date?: string
  amount?: string
  type?: CashMovementType
  contact_id?: number | null
  payment_id?: number | null
  reference?: string | null
  description?: string | null
}

export interface CashCount {
  id: number
  date: string
  count_100: number
  count_50: number
  count_20: number
  count_10: number
  count_5: number
  count_2: number
  count_1: number
  count_cents_50: number
  count_cents_20: number
  count_cents_10: number
  count_cents_5: number
  count_cents_2: number
  count_cents_1: number
  total_counted: string
  balance_expected: string
  difference: string
  notes: string | null
}

export interface CashCountCreate {
  date: string
  count_100?: number
  count_50?: number
  count_20?: number
  count_10?: number
  count_5?: number
  count_2?: number
  count_1?: number
  count_cents_50?: number
  count_cents_20?: number
  count_cents_10?: number
  count_cents_5?: number
  count_cents_2?: number
  count_cents_1?: number
  notes?: string | null
}

export interface FundsChartRow {
  month: string
  balance: number
}

export async function getCashBalance(): Promise<{ balance: string }> {
  const response = await apiClient.get<{ balance: string }>('/api/cash/balance')
  return response.data
}

export async function getCashFundsChart(months = 6): Promise<FundsChartRow[]> {
  const response = await apiClient.get<FundsChartRow[]>('/api/cash/chart/funds', {
    params: { months },
  })
  return response.data
}

export async function listCashEntries(params?: {
  from_date?: string
  to_date?: string
  skip?: number
  limit?: number
}): Promise<CashEntry[]> {
  const response = await apiClient.get<CashEntry[]>('/api/cash/entries', { params })
  return response.data
}

export async function addCashEntry(payload: CashEntryCreate): Promise<CashEntry> {
  const response = await apiClient.post<CashEntry>('/api/cash/entries', payload)
  return response.data
}

export async function getCashEntry(id: number): Promise<CashEntry> {
  const response = await apiClient.get<CashEntry>(`/api/cash/entries/${id}`)
  return response.data
}

export async function updateCashEntry(id: number, payload: CashEntryUpdate): Promise<CashEntry> {
  const response = await apiClient.put<CashEntry>(`/api/cash/entries/${id}`, payload)
  return response.data
}

export async function deleteCashEntry(id: number): Promise<void> {
  await apiClient.delete(`/api/cash/entries/${id}`)
}

export async function getCashEntryConnections(id: number): Promise<CashEntryConnections> {
  const response = await apiClient.get<CashEntryConnections>(`/api/cash/entries/${id}/connections`)
  return response.data
}

export async function listCashCounts(params?: {
  from_date?: string
  to_date?: string
  skip?: number
  limit?: number
}): Promise<CashCount[]> {
  const response = await apiClient.get<CashCount[]>('/api/cash/counts', { params })
  return response.data
}

export async function addCashCount(payload: CashCountCreate): Promise<CashCount> {
  const response = await apiClient.post<CashCount>('/api/cash/counts', payload)
  return response.data
}
