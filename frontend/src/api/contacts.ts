import apiClient from './client'
import type { ContactType } from './types'

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
  contract_type: 'cdi' | 'cdd' | null
  base_gross: number | null
  base_hours: number | null
  hourly_rate: number | null
  is_contractor: boolean
  created_at: string
  updated_at: string
  last_invoice_ref: string | null
  last_invoice_date: string | null
}

export interface ContactCreate {
  type: ContactType
  nom: string
  prenom?: string | null
  email?: string | null
  telephone?: string | null
  adresse?: string | null
  notes?: string | null
  contract_type?: 'cdi' | 'cdd' | null
  base_gross?: number | null
  base_hours?: number | null
  hourly_rate?: number | null
  is_contractor?: boolean
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
  contract_type?: 'cdi' | 'cdd' | null
  base_gross?: number | null
  base_hours?: number | null
  hourly_rate?: number | null
  is_contractor?: boolean
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
