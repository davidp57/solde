export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export type UserRole = 'readonly' | 'secretaire' | 'tresorier' | 'admin'

export interface UserRead {
  id: number
  username: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export type ContactType = 'client' | 'fournisseur' | 'les_deux'

// ---------------------------------------------------------------------------
// Salary
// ---------------------------------------------------------------------------

export interface SalaryRead {
  id: number
  employee_id: number
  employee_name: string
  month: string
  hours: number
  gross: number
  employee_charges: number
  employer_charges: number
  tax: number
  net_pay: number
  total_cost: number
  notes: string | null
  created_at: string
}

export interface SalaryCreate {
  employee_id: number
  month: string
  hours: number
  gross: number
  employee_charges: number
  employer_charges: number
  tax: number
  net_pay: number
  notes?: string | null
}

export type SalaryUpdate = Partial<SalaryCreate>

export interface SalarySummaryRow {
  month: string
  count: number
  total_gross: number
  total_employer_charges: number
  total_net_pay: number
  total_cost: number
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export interface DashboardAlert {
  type: string
  message: string
}

export interface DashboardKPIs {
  bank_balance: number | null
  cash_balance: number | null
  unpaid_count: number
  unpaid_total: number
  overdue_count: number
  overdue_total: number
  undeposited_count: number
  current_fy_name: string | null
  current_resultat: number | null
  alerts: DashboardAlert[]
}

export interface MonthlyChartRow {
  month: string
  charges: number
  produits: number
}

// ---------------------------------------------------------------------------
// Import
// ---------------------------------------------------------------------------

export interface ImportResult {
  contacts_created: number
  invoices_created: number
  payments_created: number
  entries_created: number
  cash_created: number
  bank_created: number
  skipped: number
  ignored_rows: number
  blocked_rows: number
  errors: string[]
  warnings: string[]
  error_details: ImportIssueDetail[]
  warning_details: ImportIssueDetail[]
  sheets: ImportSheetResult[]
}

export interface ImportIssueDetail {
  severity: 'warning' | 'error'
  sheet_name: string | null
  kind: string | null
  row_number: number | null
  message: string
  display_message: string
}

export interface ImportSheetResult {
  name: string
  kind: string
  imported_rows: number
  ignored_rows: number
  blocked_rows: number
  warnings: string[]
  errors: string[]
  warning_details: ImportIssueDetail[]
  error_details: ImportIssueDetail[]
}

// ---------------------------------------------------------------------------
// Contact (extended)
// ---------------------------------------------------------------------------

export interface ContactRead {
  id: number
  type: ContactType
  nom: string
  prenom: string | null
  email: string | null
  telephone: string | null
  adresse: string | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}
