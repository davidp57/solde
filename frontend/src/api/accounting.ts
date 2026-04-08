import apiClient from './client'

export type AccountType = 'actif' | 'passif' | 'charge' | 'produit'

export interface AccountingAccount {
  id: number
  number: string
  label: string
  type: AccountType
  parent_number: string | null
  description: string | null
  is_default: boolean
  is_active: boolean
}

export interface AccountingAccountCreate {
  number: string
  label: string
  type: AccountType
  parent_number?: string | null
  description?: string | null
}

export interface AccountingAccountUpdate {
  label?: string
  type?: AccountType
  parent_number?: string | null
  description?: string | null
  is_active?: boolean
}

export async function listAccountsApi(
  type?: AccountType,
  activeOnly = true,
): Promise<AccountingAccount[]> {
  const params = new URLSearchParams()
  if (type) params.set('type', type)
  params.set('active_only', String(activeOnly))
  const response = await apiClient.get<AccountingAccount[]>(
    `/api/accounting/accounts/?${params}`,
  )
  return response.data
}

export async function seedAccountsApi(): Promise<{ inserted: number }> {
  const response = await apiClient.post<{ inserted: number }>(
    '/api/accounting/accounts/seed',
  )
  return response.data
}

export async function createAccountApi(
  payload: AccountingAccountCreate,
): Promise<AccountingAccount> {
  const response = await apiClient.post<AccountingAccount>(
    '/api/accounting/accounts/',
    payload,
  )
  return response.data
}

export async function updateAccountApi(
  id: number,
  payload: AccountingAccountUpdate,
): Promise<AccountingAccount> {
  const response = await apiClient.put<AccountingAccount>(
    `/api/accounting/accounts/${id}`,
    payload,
  )
  return response.data
}

// -----------------------------------------------------------------------
// Journal / entries types & API
// -----------------------------------------------------------------------

export type EntrySourceType =
  | 'invoice'
  | 'payment'
  | 'deposit'
  | 'salary'
  | 'manual'
  | 'cloture'

export interface AccountingEntryRead {
  id: number
  entry_number: string
  date: string
  account_number: string
  label: string
  debit: string
  credit: string
  fiscal_year_id: number | null
  source_type: EntrySourceType | null
  source_id: number | null
  created_at: string
}

export interface BalanceRow {
  account_number: string
  account_label: string
  account_type: string
  total_debit: string
  total_credit: string
  solde: string
}

export interface LedgerEntry {
  id: number
  entry_number: string
  date: string
  label: string
  debit: string
  credit: string
  running_balance: string
}

export interface LedgerRead {
  account_number: string
  account_label: string
  entries: LedgerEntry[]
  opening_balance: string
  closing_balance: string
}

export interface ResultatRead {
  total_charges: string
  total_produits: string
  resultat: string
  charges: BalanceRow[]
  produits: BalanceRow[]
}

export interface ManualEntryCreate {
  date: string
  debit_account: string
  credit_account: string
  amount: string
  label: string
  fiscal_year_id?: number | null
}

export interface JournalFilters {
  from_date?: string
  to_date?: string
  account_number?: string
  source_type?: EntrySourceType
  fiscal_year_id?: number
  skip?: number
  limit?: number
}

export async function getJournalApi(filters: JournalFilters = {}): Promise<AccountingEntryRead[]> {
  const params = new URLSearchParams()
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.account_number) params.set('account_number', filters.account_number)
  if (filters.source_type) params.set('source_type', filters.source_type)
  if (filters.fiscal_year_id) params.set('fiscal_year_id', String(filters.fiscal_year_id))
  if (filters.skip != null) params.set('skip', String(filters.skip))
  if (filters.limit != null) params.set('limit', String(filters.limit))
  const response = await apiClient.get<AccountingEntryRead[]>(
    `/accounting/entries/journal?${params}`,
  )
  return response.data
}

export async function getBalanceApi(filters: {
  from_date?: string
  to_date?: string
  fiscal_year_id?: number
} = {}): Promise<BalanceRow[]> {
  const params = new URLSearchParams()
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.fiscal_year_id) params.set('fiscal_year_id', String(filters.fiscal_year_id))
  const response = await apiClient.get<BalanceRow[]>(`/accounting/entries/balance?${params}`)
  return response.data
}

export async function getLedgerApi(
  accountNumber: string,
  filters: { from_date?: string; to_date?: string; fiscal_year_id?: number } = {},
): Promise<LedgerRead> {
  const params = new URLSearchParams()
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.fiscal_year_id) params.set('fiscal_year_id', String(filters.fiscal_year_id))
  const response = await apiClient.get<LedgerRead>(
    `/accounting/entries/ledger/${accountNumber}?${params}`,
  )
  return response.data
}

export async function getResultatApi(fiscalYearId?: number): Promise<ResultatRead> {
  const params = fiscalYearId ? `?fiscal_year_id=${fiscalYearId}` : ''
  const response = await apiClient.get<ResultatRead>(`/accounting/entries/resultat${params}`)
  return response.data
}

export async function createManualEntryApi(
  payload: ManualEntryCreate,
): Promise<AccountingEntryRead[]> {
  const response = await apiClient.post<AccountingEntryRead[]>(
    '/accounting/entries/manual',
    payload,
  )
  return response.data
}

// -----------------------------------------------------------------------
// Fiscal year types & API
// -----------------------------------------------------------------------

export type FiscalYearStatus = 'open' | 'closing' | 'closed'

export interface FiscalYearRead {
  id: number
  name: string
  start_date: string
  end_date: string
  status: FiscalYearStatus
  created_at: string
}

export interface FiscalYearCreate {
  name: string
  start_date: string
  end_date: string
}

export async function listFiscalYearsApi(): Promise<FiscalYearRead[]> {
  const response = await apiClient.get<FiscalYearRead[]>('/accounting/fiscal-years/')
  return response.data
}

export async function getCurrentFiscalYearApi(): Promise<FiscalYearRead | null> {
  const response = await apiClient.get<FiscalYearRead | null>('/accounting/fiscal-years/current')
  return response.data
}

export async function createFiscalYearApi(payload: FiscalYearCreate): Promise<FiscalYearRead> {
  const response = await apiClient.post<FiscalYearRead>('/accounting/fiscal-years/', payload)
  return response.data
}

export async function closeFiscalYearApi(id: number): Promise<FiscalYearRead> {
  const response = await apiClient.post<FiscalYearRead>(`/accounting/fiscal-years/${id}/close`)
  return response.data
}

// -----------------------------------------------------------------------
// Accounting rules types & API
// -----------------------------------------------------------------------

export interface AccountingRuleEntrySchema {
  id: number
  account_number: string
  side: 'debit' | 'credit'
  description_template: string
}

export interface AccountingRuleRead {
  id: number
  name: string
  trigger_type: string
  is_active: boolean
  priority: number
  description: string | null
  entries: AccountingRuleEntrySchema[]
}

export interface AccountingRuleUpdate {
  name?: string
  is_active?: boolean
  priority?: number
  description?: string | null
}

export async function listRulesApi(): Promise<AccountingRuleRead[]> {
  const response = await apiClient.get<AccountingRuleRead[]>('/accounting/rules/')
  return response.data
}

export async function updateRuleApi(
  id: number,
  payload: AccountingRuleUpdate,
): Promise<AccountingRuleRead> {
  const response = await apiClient.put<AccountingRuleRead>(`/accounting/rules/${id}`, payload)
  return response.data
}

export async function seedRulesApi(): Promise<{ inserted: number }> {
  const response = await apiClient.post<{ inserted: number }>('/accounting/rules/seed')
  return response.data
}
