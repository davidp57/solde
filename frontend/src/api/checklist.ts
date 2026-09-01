import apiClient from './client'

export type ChecklistBlock =
  | 'carryover'
  | 'entry'
  | 'payroll'
  | 'bank_visit'
  | 'statement'
  | 'cash_and_deposits'
  | 'closing'

export interface ChecklistStep {
  key: string
  block: ChecklistBlock
  /** Done outside the application — nothing here can observe it. */
  external: boolean
  signal: string | null
  route: string | null
  checked: boolean
  checked_by: string | null
  checked_at: string | null
  /** Left unchecked when the previous session was closed. */
  carried_over: boolean
}

export interface ChecklistSession {
  id: number
  period_type: string
  period: string
  status: 'open' | 'closed'
  opened_at: string
  opened_by: string | null
  closed_at: string | null
  closed_by: string | null
}

/** Observed facts, keyed by signal name. Shown next to a step, never ticking it. */
export type ChecklistSignals = Record<string, Record<string, string | number | null>>

export interface ChecklistSessionDetail {
  session: ChecklistSession
  steps: ChecklistStep[]
  signals: ChecklistSignals
}

export interface ChecklistCurrent {
  detail: ChecklistSessionDetail | null
  suggested_period: string
  checked_count: number
  total_count: number
}

export async function getCurrentChecklist(): Promise<ChecklistCurrent> {
  const response = await apiClient.get<ChecklistCurrent>('/api/checklist/current')
  return response.data
}

export async function openChecklistSession(period?: string): Promise<ChecklistSessionDetail> {
  const response = await apiClient.post<ChecklistSessionDetail>('/api/checklist/sessions', {
    period: period ?? null,
  })
  return response.data
}

export async function setChecklistStep(
  sessionId: number,
  stepKey: string,
  checked: boolean,
): Promise<ChecklistSessionDetail> {
  const response = await apiClient.put<ChecklistSessionDetail>(
    `/api/checklist/sessions/${sessionId}/steps/${stepKey}`,
    { checked },
  )
  return response.data
}

export async function closeChecklistSession(sessionId: number): Promise<ChecklistSession> {
  const response = await apiClient.post<ChecklistSession>(
    `/api/checklist/sessions/${sessionId}/close`,
  )
  return response.data
}

export async function listChecklistSessions(): Promise<ChecklistSession[]> {
  const response = await apiClient.get<ChecklistSession[]>('/api/checklist/sessions')
  return response.data
}
