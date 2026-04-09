import apiClient from './client'

export interface AppSettings {
  association_name: string
  association_address: string
  association_siret: string
  association_logo_path: string
  fiscal_year_start_month: number
  smtp_host: string | null
  smtp_port: number
  smtp_user: string | null
  smtp_from_email: string | null
  smtp_use_tls: boolean
}

export interface AppSettingsUpdate {
  association_name?: string
  association_address?: string
  association_siret?: string
  fiscal_year_start_month?: number
  smtp_host?: string | null
  smtp_port?: number
  smtp_user?: string | null
  smtp_password?: string | null
  smtp_from_email?: string | null
  smtp_use_tls?: boolean
}

export async function getSettingsApi(): Promise<AppSettings> {
  const response = await apiClient.get<AppSettings>('/api/settings/')
  return response.data
}

export async function updateSettingsApi(payload: AppSettingsUpdate): Promise<AppSettings> {
  const response = await apiClient.put<AppSettings>('/api/settings/', payload)
  return response.data
}

export async function resetDbApi(): Promise<Record<string, number>> {
  const response = await apiClient.post<Record<string, number>>('/api/settings/reset-db')
  return response.data
}
