import apiClient from './client'

export async function getManual(): Promise<string> {
  const response = await apiClient.get<string>('/api/help/manual', {
    responseType: 'text',
  })
  return response.data
}
