import apiClient from './client'

export interface AppComment {
  id: number
  user_id: number
  user_name: string
  content: string
  is_resolved: boolean
  created_at: string
}

export async function listCommentsApi(): Promise<AppComment[]> {
  const response = await apiClient.get<AppComment[]>('/api/comments/')
  return response.data
}

export async function createCommentApi(content: string): Promise<AppComment> {
  const response = await apiClient.post<AppComment>('/api/comments/', { content })
  return response.data
}

export async function toggleResolvedApi(id: number, is_resolved: boolean): Promise<AppComment> {
  const response = await apiClient.patch<AppComment>(`/api/comments/${id}`, { is_resolved })
  return response.data
}

export async function deleteCommentApi(id: number): Promise<void> {
  await apiClient.delete(`/api/comments/${id}`)
}
