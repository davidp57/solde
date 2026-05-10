import apiClient from './client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BackupDestination {
  id: number
  name: string
  type: 'local' | 'smb' | 'onedrive'
  enabled: boolean
  rclone_remote_name: string
  rclone_config: string | null
  target_path: string
  created_at: string
}

export interface BackupDestinationCreate {
  name: string
  type: 'local' | 'smb' | 'onedrive'
  enabled?: boolean
  rclone_remote_name: string
  rclone_config?: string | null
  target_path?: string
}

export interface BackupDestinationUpdate {
  name?: string
  type?: 'local' | 'smb' | 'onedrive'
  enabled?: boolean
  rclone_remote_name?: string
  rclone_config?: string | null
  target_path?: string
}

export interface BackupSchedule {
  enabled: boolean
  schedule_type: 'interval' | 'cron'
  interval_hours: number
  cron_expression: string | null
  include_uploads: boolean
  notify_on_failure: boolean
}

export interface BackupScheduleUpdate {
  enabled?: boolean
  schedule_type?: 'interval' | 'cron'
  interval_hours?: number
  cron_expression?: string | null
  include_uploads?: boolean
  notify_on_failure?: boolean
}

export interface BackupRunStatus {
  last_run_at: string | null
  last_run_status: 'success' | 'failure' | null
  destinations_results: Array<{
    destination_id: number
    destination_name: string
    success: boolean
    error: string | null
  }>
}

export interface BackupConnectionTestResult {
  success: boolean
  message: string
}

export interface BackupRestoreTestResult {
  ok: boolean
  integrity_check: string
  tables_found: string[]
  tables_missing: string[]
  error: string | null
}

export interface OneDriveOAuthStart {
  port: number
  auth_url: string
}

export interface OneDriveOAuthStatus {
  done: boolean
  token: string | null
}

// ---------------------------------------------------------------------------
// API calls — destinations
// ---------------------------------------------------------------------------

export async function listDestinations(): Promise<BackupDestination[]> {
  const { data } = await apiClient.get<BackupDestination[]>('/api/backup/destinations')
  return data
}

export async function createDestination(
  payload: BackupDestinationCreate,
): Promise<BackupDestination> {
  const { data } = await apiClient.post<BackupDestination>('/api/backup/destinations', payload)
  return data
}

export async function updateDestination(
  id: number,
  payload: BackupDestinationUpdate,
): Promise<BackupDestination> {
  const { data } = await apiClient.put<BackupDestination>(`/api/backup/destinations/${id}`, payload)
  return data
}

export async function deleteDestination(id: number): Promise<void> {
  await apiClient.delete(`/api/backup/destinations/${id}`)
}

export async function testDestination(id: number): Promise<BackupConnectionTestResult> {
  const { data } = await apiClient.post<BackupConnectionTestResult>(
    `/api/backup/destinations/${id}/test`,
  )
  return data
}

// ---------------------------------------------------------------------------
// API calls — schedule
// ---------------------------------------------------------------------------

export async function getSchedule(): Promise<BackupSchedule> {
  const { data } = await apiClient.get<BackupSchedule>('/api/backup/schedule')
  return data
}

export async function updateSchedule(payload: BackupScheduleUpdate): Promise<BackupSchedule> {
  const { data } = await apiClient.put<BackupSchedule>('/api/backup/schedule', payload)
  return data
}

// ---------------------------------------------------------------------------
// API calls — run + status
// ---------------------------------------------------------------------------

export async function triggerBackup(): Promise<void> {
  await apiClient.post('/api/backup/run')
}

export async function getBackupStatus(): Promise<BackupRunStatus> {
  const { data } = await apiClient.get<BackupRunStatus>('/api/backup/status')
  return data
}

// ---------------------------------------------------------------------------
// API calls — test-restore + restore
// ---------------------------------------------------------------------------

export async function testRestoreBackup(filename: string): Promise<BackupRestoreTestResult> {
  const { data } = await apiClient.post<BackupRestoreTestResult>(
    `/api/backup/backups/${encodeURIComponent(filename)}/test-restore`,
  )
  return data
}

export async function restoreBackup(
  filename: string,
  destinationId?: number,
): Promise<void> {
  const params = destinationId !== undefined ? { destination_id: destinationId } : {}
  await apiClient.post(`/api/backup/backups/${encodeURIComponent(filename)}/restore`, null, { params })
}

// ---------------------------------------------------------------------------
// API calls — OneDrive OAuth
// ---------------------------------------------------------------------------

export async function startOneDriveOAuth(): Promise<OneDriveOAuthStart> {
  const { data } = await apiClient.get<OneDriveOAuthStart>('/api/backup/oauth/onedrive/start')
  return data
}

export async function pollOneDriveOAuthStatus(): Promise<OneDriveOAuthStatus> {
  const { data } = await apiClient.get<OneDriveOAuthStatus>('/api/backup/oauth/onedrive/status')
  return data
}
