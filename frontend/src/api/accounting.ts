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
