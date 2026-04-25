import apiClient from './client'

export interface AppSettings {
  association_name: string
  association_address: string
  association_siret: string
  association_logo_path: string
  fiscal_year_start_month: number
  default_invoice_due_days: number | null
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
  default_invoice_due_days?: number | null
  smtp_host?: string | null
  smtp_port?: number
  smtp_user?: string | null
  smtp_password?: string | null
  smtp_from_email?: string | null
  smtp_use_tls?: boolean
}

export interface SystemOpening {
  configured: boolean
  date: string | null
  amount: string | null
  reference: string | null
}

export interface TreasurySystemOpening {
  default_date: string | null
  bank: SystemOpening
  cash: SystemOpening
}

export interface SystemOpeningUpdate {
  date: string
  amount: string
  reference?: string | null
}

export interface TreasurySystemOpeningUpdate {
  bank: SystemOpeningUpdate
  cash: SystemOpeningUpdate
}
export type SelectiveResetImportType = 'gestion' | 'comptabilite'

export interface SelectiveResetRequest {
  import_type: SelectiveResetImportType
  fiscal_year_id: number
}

export interface SelectiveResetPreview {
  import_type: SelectiveResetImportType
  fiscal_year_id: number
  fiscal_year_name: string
  fiscal_year_start_date: string
  fiscal_year_end_date: string
  matched_import_logs: number
  matched_import_runs: number
  root_objects: Record<string, number>
  derived_objects: Record<string, number>
  delete_plan: Record<string, number>
}

export async function getSettingsApi(): Promise<AppSettings> {
  const response = await apiClient.get<AppSettings>('/api/settings/')
  return response.data
}

export async function updateSettingsApi(payload: AppSettingsUpdate): Promise<AppSettings> {
  const response = await apiClient.put<AppSettings>('/api/settings/', payload)
  return response.data
}

export async function getSystemOpeningApi(): Promise<TreasurySystemOpening> {
  const response = await apiClient.get<TreasurySystemOpening>('/api/settings/system-opening')
  return response.data
}

export async function updateSystemOpeningApi(
  payload: TreasurySystemOpeningUpdate,
): Promise<TreasurySystemOpening> {
  const response = await apiClient.put<TreasurySystemOpening>(
    '/api/settings/system-opening',
    payload,
  )
  return response.data
}

export async function resetDbApi(): Promise<Record<string, number>> {
  const response = await apiClient.post<Record<string, number>>('/api/settings/reset-db')
  return response.data
}

export async function previewSelectiveResetApi(
  payload: SelectiveResetRequest,
): Promise<SelectiveResetPreview> {
  const response = await apiClient.post<SelectiveResetPreview>(
    '/api/settings/selective-reset/preview',
    payload,
  )
  return response.data
}

export async function applySelectiveResetApi(
  payload: SelectiveResetRequest,
): Promise<SelectiveResetPreview> {
  const response = await apiClient.post<SelectiveResetPreview>(
    '/api/settings/selective-reset/apply',
    payload,
  )
  return response.data
}

export async function bootstrapAccountingApi(): Promise<{
  accounts_inserted: number
  rules_inserted: number
  fiscal_years_created: number
}> {
  const response = await apiClient.post<{
    accounts_inserted: number
    rules_inserted: number
    fiscal_years_created: number
  }>('/api/settings/bootstrap-accounting')
  return response.data
}

export async function createBackupApi(): Promise<Blob> {
  const response = await apiClient.post('/api/settings/backup', null, {
    responseType: 'blob',
  })
  return response.data as Blob
}
