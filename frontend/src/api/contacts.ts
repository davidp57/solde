import apiClient, { parseTotalCount } from './client'
import type { ContactType } from './types'

export interface ContactEmail {
  id: number
  contact_id: number
  email: string
  label: string | null
  sort_order: number
}

export interface ContactEmailCreate {
  email: string
  label?: string | null
  sort_order?: number
}

export interface Contact {
  id: number
  type: ContactType
  nom: string
  prenom: string | null
  email: string | null
  telephone: string | null
  adresse: string | null
  notes: string | null
  is_active: boolean
  blocked: boolean
  contract_type: 'cdi' | 'cdd' | null
  base_gross: number | null
  base_hours: number | null
  hourly_rate: number | null
  is_contractor: boolean
  child_first_name: string | null
  child_last_name: string | null
  other_parent_first_name: string | null
  other_parent_last_name: string | null
  created_at: string
  updated_at: string
  last_invoice_ref: string | null
  last_invoice_date: string | null
  emails: ContactEmail[]
}

export interface ContactCreate {
  type: ContactType
  nom: string
  prenom?: string | null
  email?: string | null
  telephone?: string | null
  adresse?: string | null
  notes?: string | null
  blocked?: boolean
  contract_type?: 'cdi' | 'cdd' | null
  base_gross?: number | null
  base_hours?: number | null
  hourly_rate?: number | null
  is_contractor?: boolean
  child_first_name?: string | null
  child_last_name?: string | null
  other_parent_first_name?: string | null
  other_parent_last_name?: string | null
  emails?: ContactEmailCreate[]
}

export interface ContactUpdate {
  type?: ContactType
  nom?: string
  prenom?: string | null
  email?: string | null
  telephone?: string | null
  adresse?: string | null
  notes?: string | null
  is_active?: boolean
  blocked?: boolean
  contract_type?: 'cdi' | 'cdd' | null
  base_gross?: number | null
  base_hours?: number | null
  hourly_rate?: number | null
  is_contractor?: boolean
  child_first_name?: string | null
  child_last_name?: string | null
  other_parent_first_name?: string | null
  other_parent_last_name?: string | null
  emails?: ContactEmailCreate[]
}

export interface ContactFilters {
  type?: ContactType
  search?: string
  active_only?: boolean
  skip?: number
  limit?: number
}

export async function listContactsApi(filters: ContactFilters = {}): Promise<Contact[]> {
  const params = new URLSearchParams()
  if (filters.type) params.set('type', filters.type)
  if (filters.search) params.set('search', filters.search)
  if (filters.active_only !== undefined) params.set('active_only', String(filters.active_only))
  if (filters.skip !== undefined) params.set('skip', String(filters.skip))
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  const response = await apiClient.get<Contact[]>(`/api/contacts/?${params}`)
  return response.data
}

export async function listContactsWithCountApi(
  filters: ContactFilters = {},
): Promise<{ items: Contact[]; total: number }> {
  const params = new URLSearchParams()
  if (filters.type) params.set('type', filters.type)
  if (filters.search) params.set('search', filters.search)
  if (filters.active_only !== undefined) params.set('active_only', String(filters.active_only))
  if (filters.skip !== undefined) params.set('skip', String(filters.skip))
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  const response = await apiClient.get<Contact[]>(`/api/contacts/?${params}`)
  return { items: response.data, total: parseTotalCount(response.headers as Record<string, string>) }
}

export async function getContactApi(id: number): Promise<Contact> {
  const response = await apiClient.get<Contact>(`/api/contacts/${id}`)
  return response.data
}

export async function createContactApi(payload: ContactCreate): Promise<Contact> {
  const response = await apiClient.post<Contact>('/api/contacts/', payload)
  return response.data
}

export async function updateContactApi(id: number, payload: ContactUpdate): Promise<Contact> {
  const response = await apiClient.put<Contact>(`/api/contacts/${id}`, payload)
  return response.data
}

export async function deleteContactApi(id: number): Promise<void> {
  await apiClient.delete(`/api/contacts/${id}`)
}

export interface ContactEmailImportRow {
  nom: string
  email: string
}

export interface ContactEmailImportResult {
  rows_processed: number
  updated: number
  not_found: number
  already_has_email: number
  updated_indices: number[]
  not_found_indices: number[]
  already_has_email_indices: number[]
}

export async function importContactEmailsApi(rows: ContactEmailImportRow[]): Promise<ContactEmailImportResult> {
  const response = await apiClient.post<ContactEmailImportResult>('/api/contacts/import-emails', rows)
  return response.data
}

export interface MergeContactResult {
  target_id: number
  invoices_reassigned: number
  payments_reassigned: number
  cash_entries_reassigned: number
  salaries_reassigned: number
}

export async function mergeContactApi(sourceId: number, targetId: number): Promise<MergeContactResult> {
  const response = await apiClient.post<MergeContactResult>(
    `/api/contacts/${sourceId}/merge`,
    null,
    { params: { target_id: targetId } },
  )
  return response.data
}

// --- Member mailing (Lot ML) ---

export interface ActiveClient {
  id: number
  nom: string
  prenom: string | null
  email: string | null
  last_activity: string | null
}

export interface MemberMailingFailure {
  contact_id: number
  error: string
}

export interface MemberMailingResult {
  sent: number
  failed: MemberMailingFailure[]
}

export async function listActiveClientsApi(months: number): Promise<ActiveClient[]> {
  const response = await apiClient.get<ActiveClient[]>(
    `/api/contacts/active-clients?months=${months}`,
  )
  return response.data
}

export async function sendMemberMailingApi(payload: {
  contact_ids: number[]
  subject: string
  body: string
}): Promise<MemberMailingResult> {
  const response = await apiClient.post<MemberMailingResult>('/api/contacts/mailing', payload)
  return response.data
}
