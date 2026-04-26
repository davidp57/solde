import apiClient from './client'

export type InvoiceType = 'client' | 'fournisseur'
export type InvoiceLabel = 'cs' | 'a' | 'cs+a' | 'general'
export type InvoiceLineType = 'cours' | 'adhesion' | 'autres'
export type InvoiceStatus =
  | 'draft'
  | 'sent'
  | 'paid'
  | 'partial'
  | 'overdue'
  | 'disputed'
  | 'irrecoverable'

export interface InvoiceLine {
  id: number
  invoice_id: number
  description: string
  line_type: InvoiceLineType | null
  quantity: string
  unit_price: string
  amount: string
}

export interface InvoiceLineCreate {
  description: string
  line_type?: InvoiceLineType | null
  quantity?: string
  unit_price?: string
}

export interface Invoice {
  id: number
  number: string
  type: InvoiceType
  contact_id: number
  date: string
  due_date: string | null
  label: InvoiceLabel | null
  description: string | null
  reference: string | null
  total_amount: string
  paid_amount: string
  status: InvoiceStatus
  pdf_path: string | null
  file_path: string | null
  created_at: string
  updated_at: string
  lines: InvoiceLine[]
}

export interface InvoiceCreate {
  type: InvoiceType
  contact_id: number
  date: string
  due_date?: string | null
  label?: InvoiceLabel | null
  description?: string | null
  reference?: string | null
  lines?: InvoiceLineCreate[]
  total_amount?: string | null
}

export interface InvoiceUpdate {
  contact_id?: number
  date?: string
  due_date?: string | null
  label?: InvoiceLabel | null
  description?: string | null
  reference?: string | null
  lines?: InvoiceLineCreate[]
  total_amount?: string | null
}

export interface InvoiceFilters {
  invoice_type?: InvoiceType
  invoice_status?: InvoiceStatus
  contact_id?: number
  from_date?: string
  to_date?: string
  year?: number
  skip?: number
  limit?: number
}

export async function listInvoicesApi(filters: InvoiceFilters = {}): Promise<Invoice[]> {
  const params = new URLSearchParams()
  if (filters.invoice_type) params.set('invoice_type', filters.invoice_type)
  if (filters.invoice_status) params.set('invoice_status', filters.invoice_status)
  if (filters.contact_id !== undefined) params.set('contact_id', String(filters.contact_id))
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.year !== undefined) params.set('year', String(filters.year))
  if (filters.skip !== undefined) params.set('skip', String(filters.skip))
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  const response = await apiClient.get<Invoice[]>(`/api/invoices/?${params}`)
  return response.data
}

export async function getInvoiceApi(id: number): Promise<Invoice> {
  const response = await apiClient.get<Invoice>(`/api/invoices/${id}`)
  return response.data
}

export async function createInvoiceApi(data: InvoiceCreate): Promise<Invoice> {
  const response = await apiClient.post<Invoice>('/api/invoices/', data)
  return response.data
}

export async function updateInvoiceApi(id: number, data: InvoiceUpdate): Promise<Invoice> {
  const response = await apiClient.put<Invoice>(`/api/invoices/${id}`, data)
  return response.data
}

export async function updateInvoiceStatusApi(id: number, status: InvoiceStatus): Promise<Invoice> {
  const response = await apiClient.patch<Invoice>(`/api/invoices/${id}/status`, { status })
  return response.data
}

export async function duplicateInvoiceApi(id: number): Promise<Invoice> {
  const response = await apiClient.post<Invoice>(`/api/invoices/${id}/duplicate`)
  return response.data
}

export async function deleteInvoiceApi(id: number): Promise<void> {
  await apiClient.delete(`/api/invoices/${id}`)
}

export async function downloadInvoicePdfApi(id: number): Promise<Blob> {
  const response = await apiClient.get(`/api/invoices/${id}/pdf`, { responseType: 'blob' })
  return response.data
}

export async function sendInvoiceEmailApi(id: number): Promise<void> {
  await apiClient.post(`/api/invoices/${id}/send-email`)
}

export async function writeOffInvoiceApi(id: number): Promise<Invoice> {
  const response = await apiClient.post<Invoice>(`/api/invoices/${id}/write-off`)
  return response.data
}

export async function restoreFromWriteoffApi(id: number): Promise<Invoice> {
  const response = await apiClient.post<Invoice>(`/api/invoices/${id}/restore-from-writeoff`)
  return response.data
}

export async function uploadInvoiceFileApi(id: number, file: File): Promise<Invoice> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post<Invoice>(`/api/invoices/${id}/file`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}
