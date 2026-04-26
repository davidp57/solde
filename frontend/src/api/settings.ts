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
  smtp_bcc: string | null
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
  smtp_bcc?: string | null
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

export async function createBackupApi(label?: string | null): Promise<Blob> {
  const response = await apiClient.post('/api/settings/backup', { label: label ?? null }, {
    responseType: 'blob',
  })
  return response.data as Blob
}

// ---------------------------------------------------------------------------
// System supervision (BIZ-108 / BIZ-109)
// ---------------------------------------------------------------------------

export interface SystemInfo {
  app_version: string
  db_size_bytes: number
  started_at: string
  log_file: string
}

export interface BackupFile {
  filename: string
  size_bytes: number
  created_at: string
  label: string | null
}

export interface LogEntry {
  timestamp: string
  level: string
  logger: string
  message: string
}

export interface AuditLogEntry {
  id: number
  action: string
  actor_id: number | null
  actor_username: string | null
  target_type: string | null
  target_id: number | null
  detail: Record<string, unknown> | null
  created_at: string
}

export async function getSystemInfoApi(): Promise<SystemInfo> {
  const response = await apiClient.get<SystemInfo>('/api/settings/system-info')
  return response.data
}

export async function listBackupsApi(): Promise<BackupFile[]> {
  const response = await apiClient.get<BackupFile[]>('/api/settings/backups')
  return response.data
}

export async function restoreBackupApi(filename: string): Promise<void> {
  await apiClient.post(`/api/settings/backups/${encodeURIComponent(filename)}/restore`)
}

export async function getLogsApi(levels?: string[]): Promise<LogEntry[]> {
  const params = levels && levels.length > 0 ? { levels } : {}
  const response = await apiClient.get<LogEntry[]>('/api/settings/logs', {
    params,
    paramsSerializer: (p) => {
      const searchParams = new URLSearchParams()
      Object.entries(p).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach((item) => searchParams.append(key, String(item)))
        } else if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      return searchParams.toString()
    },
  })
  return response.data
}

export async function getAuditLogsApi(): Promise<AuditLogEntry[]> {
  const response = await apiClient.get<AuditLogEntry[]>('/api/settings/audit-logs')
  return response.data
}

