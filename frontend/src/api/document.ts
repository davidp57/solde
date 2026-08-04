import apiClient from './client'

export interface AppDocument {
  id: number
  title: string
  filename: string
  mime_type: string | null
  size_bytes: number
  fiscal_year_id: number | null
  fiscal_year_name: string | null
  tags: string[]
  notes: string | null
  uploaded_by: string | null
  uploaded_at: string
}

export interface DocumentTag {
  tag: string
  count: number
}

export interface DocumentUpdate {
  title?: string
  fiscal_year_id?: number | null
  tags?: string[]
  notes?: string | null
}

export interface DocumentListFilters {
  fiscal_year_id?: number | null
  without_fiscal_year?: boolean
  tag?: string | null
  search?: string | null
  limit?: number
  offset?: number
}

export async function listDocumentsApi(
  filters: DocumentListFilters = {},
): Promise<{ items: AppDocument[]; total: number }> {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== '' && value !== false) {
      params.set(key, String(value))
    }
  }
  const qs = params.toString() ? `?${params}` : ''
  const response = await apiClient.get<AppDocument[]>(`/api/documents/${qs}`)
  const total = Number(response.headers['x-total-count'] ?? response.data.length)
  return { items: response.data, total }
}

export async function listDocumentTagsApi(): Promise<DocumentTag[]> {
  const response = await apiClient.get<DocumentTag[]>('/api/documents/tags')
  return response.data
}

export async function uploadDocumentApi(payload: {
  file: File
  title: string
  fiscal_year_id?: number | null
  tags?: string[]
  notes?: string | null
}): Promise<AppDocument> {
  const form = new FormData()
  form.append('file', payload.file)
  form.append('title', payload.title)
  if (payload.fiscal_year_id != null) form.append('fiscal_year_id', String(payload.fiscal_year_id))
  if (payload.tags?.length) form.append('tags', payload.tags.join(','))
  if (payload.notes) form.append('notes', payload.notes)
  const response = await apiClient.post<AppDocument>('/api/documents/', form)
  return response.data
}

export async function updateDocumentApi(
  id: number,
  payload: DocumentUpdate,
): Promise<AppDocument> {
  const response = await apiClient.patch<AppDocument>(`/api/documents/${id}`, payload)
  return response.data
}

export async function deleteDocumentApi(id: number): Promise<void> {
  await apiClient.delete(`/api/documents/${id}`)
}

export function getDocumentDownloadUrl(id: number): string {
  return `/api/documents/${id}/download`
}
