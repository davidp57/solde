import apiClient from './client'

export type AccountType = 'actif' | 'passif' | 'charge' | 'produit'

export interface AccountingAccount {
  id: number
  number: string
  label: string
  type: AccountType
  parent_number: string | null
  description: string | null
  is_default: boolean
  is_active: boolean
}

export interface AccountingAccountCreate {
  number: string
  label: string
  type: AccountType
  parent_number?: string | null
  description?: string | null
}

export interface AccountingAccountUpdate {
  label?: string
  type?: AccountType
  parent_number?: string | null
  description?: string | null
  is_active?: boolean
}

export async function listAccountsApi(
  type?: AccountType,
  activeOnly = true,
): Promise<AccountingAccount[]> {
  const params = new URLSearchParams()
  if (type) params.set('type', type)
  params.set('active_only', String(activeOnly))
  const response = await apiClient.get<AccountingAccount[]>(`/api/accounting/accounts/?${params}`)
  return response.data
}

export async function seedAccountsApi(): Promise<{ inserted: number }> {
  const response = await apiClient.post<{ inserted: number }>('/api/accounting/accounts/seed')
  return response.data
}

export async function createAccountApi(
  payload: AccountingAccountCreate,
): Promise<AccountingAccount> {
  const response = await apiClient.post<AccountingAccount>('/api/accounting/accounts/', payload)
  return response.data
}

export async function updateAccountApi(
  id: number,
  payload: AccountingAccountUpdate,
): Promise<AccountingAccount> {
  const response = await apiClient.put<AccountingAccount>(`/api/accounting/accounts/${id}`, payload)
  return response.data
}

// -----------------------------------------------------------------------
// Journal / entries types & API
// -----------------------------------------------------------------------

export type EntrySourceType =
  | 'gestion'
  | 'invoice'
  | 'payment'
  | 'deposit'
  | 'salary'
  | 'gestion'
  | 'manual'
  | 'cloture'

export interface AccountingEntryRead {
  id: number
  entry_number: string
  group_key: string
  date: string
  account_number: string
  account_label: string | null
  label: string
  debit: string
  credit: string
  fiscal_year_id: number | null
  source_type: EntrySourceType | null
  source_id: number | null
  source_reference: string | null
  source_contact_name: string | null
  source_invoice_id: number | null
  source_invoice_type: string | null
  source_invoice_number: string | null
  editable: boolean
  counterpart_entry_id: number | null
  counterpart_account_number: string | null
  counterpart_account_label: string | null
  created_at: string
}

export interface AccountingEntryGroupRead {
  group_key: string
  date: string
  label: string
  fiscal_year_id: number | null
  source_type: EntrySourceType | null
  source_id: number | null
  source_reference: string | null
  source_contact_name: string | null
  source_invoice_id: number | null
  source_invoice_type: string | null
  source_invoice_number: string | null
  line_count: number
  total_debit: string
  total_credit: string
  account_numbers: string[]
  editable: boolean
  lines: AccountingEntryRead[]
}

export interface BalanceRow {
  account_number: string
  account_label: string
  account_type: string
  total_debit: string
  total_credit: string
  solde: string
}

export interface LedgerEntry {
  id: number
  entry_number: string
  date: string
  label: string
  debit: string
  credit: string
  running_balance: string
}

export interface LedgerRead {
  account_number: string
  account_label: string
  entries: LedgerEntry[]
  opening_balance: string
  closing_balance: string
}

export interface ResultatRead {
  total_charges: string
  total_produits: string
  resultat: string
  charges: BalanceRow[]
  produits: BalanceRow[]
}

export interface ManualEntryCreate {
  date: string
  debit_account: string
  credit_account: string
  amount: string
  label: string
  fiscal_year_id?: number | null
}

export interface ManualEntryUpdate extends ManualEntryCreate {
  counterpart_entry_id: number
}

export interface JournalFilters {
  from_date?: string
  to_date?: string
  account_number?: string
  source_type?: EntrySourceType
  fiscal_year_id?: number
  skip?: number
  limit?: number
}

export async function getJournalApi(filters: JournalFilters = {}): Promise<AccountingEntryRead[]> {
  const params = new URLSearchParams()
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.account_number) params.set('account_number', filters.account_number)
  if (filters.source_type) params.set('source_type', filters.source_type)
  if (filters.fiscal_year_id) params.set('fiscal_year_id', String(filters.fiscal_year_id))
  if (filters.skip != null) params.set('skip', String(filters.skip))
  if (filters.limit != null) params.set('limit', String(filters.limit))
  const response = await apiClient.get<AccountingEntryRead[]>(
    `/api/accounting/entries/journal?${params}`,
  )
  return response.data
}

export async function getJournalGroupsApi(
  filters: JournalFilters = {},
): Promise<AccountingEntryGroupRead[]> {
  const params = new URLSearchParams()
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.account_number) params.set('account_number', filters.account_number)
  if (filters.source_type) params.set('source_type', filters.source_type)
  if (filters.fiscal_year_id) params.set('fiscal_year_id', String(filters.fiscal_year_id))
  if (filters.skip != null) params.set('skip', String(filters.skip))
  if (filters.limit != null) params.set('limit', String(filters.limit))
  const response = await apiClient.get<AccountingEntryGroupRead[]>(
    `/api/accounting/entries/journal-grouped?${params}`,
  )
  return response.data
}

export async function getBalanceApi(
  filters: {
    from_date?: string
    to_date?: string
    fiscal_year_id?: number
  } = {},
): Promise<BalanceRow[]> {
  const params = new URLSearchParams()
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.fiscal_year_id) params.set('fiscal_year_id', String(filters.fiscal_year_id))
  const response = await apiClient.get<BalanceRow[]>(`/api/accounting/entries/balance?${params}`)
  return response.data
}

export async function getLedgerApi(
  accountNumber: string,
  filters: { from_date?: string; to_date?: string; fiscal_year_id?: number } = {},
): Promise<LedgerRead> {
  const params = new URLSearchParams()
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.fiscal_year_id) params.set('fiscal_year_id', String(filters.fiscal_year_id))
  const response = await apiClient.get<LedgerRead>(
    `/api/accounting/entries/ledger/${accountNumber}?${params}`,
  )
  return response.data
}

export async function getResultatApi(fiscalYearId?: number): Promise<ResultatRead> {
  const params = fiscalYearId ? `?fiscal_year_id=${fiscalYearId}` : ''
  const response = await apiClient.get<ResultatRead>(`/api/accounting/entries/resultat${params}`)
  return response.data
}

export async function createManualEntryApi(
  payload: ManualEntryCreate,
): Promise<AccountingEntryRead[]> {
  const response = await apiClient.post<AccountingEntryRead[]>(
    '/api/accounting/entries/manual',
    payload,
  )
  return response.data
}

export async function updateManualEntryApi(
  entryId: number,
  payload: ManualEntryUpdate,
): Promise<AccountingEntryRead[]> {
  const response = await apiClient.put<AccountingEntryRead[]>(
    `/api/accounting/entries/manual/${entryId}`,
    payload,
  )
  return response.data
}

// -----------------------------------------------------------------------
// Fiscal year types & API
// -----------------------------------------------------------------------

export type FiscalYearStatus = 'open' | 'closing' | 'closed'

export interface FiscalYearRead {
  id: number
  name: string
  start_date: string
  end_date: string
  status: FiscalYearStatus
  created_at: string
}

export interface FiscalYearCreate {
  name: string
  start_date: string
  end_date: string
}

export async function listFiscalYearsApi(): Promise<FiscalYearRead[]> {
  const response = await apiClient.get<FiscalYearRead[]>('/api/accounting/fiscal-years/')
  return response.data
}

export async function getCurrentFiscalYearApi(): Promise<FiscalYearRead | null> {
  const response = await apiClient.get<FiscalYearRead | null>(
    '/api/accounting/fiscal-years/current',
  )
  return response.data
}

export async function createFiscalYearApi(payload: FiscalYearCreate): Promise<FiscalYearRead> {
  const response = await apiClient.post<FiscalYearRead>('/api/accounting/fiscal-years/', payload)
  return response.data
}

export async function closeFiscalYearApi(id: number): Promise<FiscalYearRead> {
  const response = await apiClient.post<FiscalYearRead>(`/api/accounting/fiscal-years/${id}/close`)
  return response.data
}

export async function closeFiscalYearAdministrativeApi(id: number): Promise<FiscalYearRead> {
  const response = await apiClient.post<FiscalYearRead>(
    `/api/accounting/fiscal-years/${id}/close-administrative`,
  )
  return response.data
}

// -----------------------------------------------------------------------
// Accounting rules types & API
// -----------------------------------------------------------------------

export interface AccountingRuleEntrySchema {
  id: number
  account_number: string
  side: 'debit' | 'credit'
  description_template: string
}

export interface AccountingRuleRead {
  id: number
  name: string
  trigger_type: string
  is_active: boolean
  priority: number
  description: string | null
  entries: AccountingRuleEntrySchema[]
}

export interface AccountingRuleUpdate {
  name?: string
  is_active?: boolean
  priority?: number
  description?: string | null
}

export async function listRulesApi(): Promise<AccountingRuleRead[]> {
  const response = await apiClient.get<AccountingRuleRead[]>('/api/accounting/rules/')
  return response.data
}

export async function updateRuleApi(
  id: number,
  payload: AccountingRuleUpdate,
): Promise<AccountingRuleRead> {
  const response = await apiClient.put<AccountingRuleRead>(`/api/accounting/rules/${id}`, payload)
  return response.data
}

export async function seedRulesApi(): Promise<{ inserted: number }> {
  const response = await apiClient.post<{ inserted: number }>('/api/accounting/rules/seed')
  return response.data
}

// -----------------------------------------------------------------------
// Salary types & API
// -----------------------------------------------------------------------

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

function parseSalaryNumericValue(value: unknown): number {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : 0
  }
  if (typeof value === 'string') {
    const parsedValue = Number.parseFloat(value)
    return Number.isFinite(parsedValue) ? parsedValue : 0
  }
  return 0
}

function normalizeSalaryRead(salary: SalaryRead): SalaryRead {
  return {
    ...salary,
    hours: parseSalaryNumericValue(salary.hours),
    gross: parseSalaryNumericValue(salary.gross),
    employee_charges: parseSalaryNumericValue(salary.employee_charges),
    employer_charges: parseSalaryNumericValue(salary.employer_charges),
    tax: parseSalaryNumericValue(salary.tax),
    net_pay: parseSalaryNumericValue(salary.net_pay),
    total_cost: parseSalaryNumericValue(salary.total_cost),
  }
}

function normalizeSalarySummaryRow(row: SalarySummaryRow): SalarySummaryRow {
  return {
    ...row,
    total_gross: parseSalaryNumericValue(row.total_gross),
    total_employer_charges: parseSalaryNumericValue(row.total_employer_charges),
    total_net_pay: parseSalaryNumericValue(row.total_net_pay),
    total_cost: parseSalaryNumericValue(row.total_cost),
  }
}

export async function listSalariesApi(params?: {
  employee_id?: number
  month?: string
  from_month?: string
  to_month?: string
  skip?: number
  limit?: number
}): Promise<SalaryRead[]> {
  const response = await apiClient.get<SalaryRead[]>('/api/salaries/', { params })
  return response.data.map(normalizeSalaryRead)
}

export async function getSalarySummaryApi(params?: {
  from_month?: string
  to_month?: string
}): Promise<SalarySummaryRow[]> {
  const response = await apiClient.get<SalarySummaryRow[]>('/api/salaries/summary', { params })
  return response.data.map(normalizeSalarySummaryRow)
}

export async function createSalaryApi(payload: SalaryCreate): Promise<SalaryRead> {
  const response = await apiClient.post<SalaryRead>('/api/salaries/', payload)
  return normalizeSalaryRead(response.data)
}

export async function updateSalaryApi(id: number, payload: SalaryUpdate): Promise<SalaryRead> {
  const response = await apiClient.put<SalaryRead>(`/api/salaries/${id}`, payload)
  return normalizeSalaryRead(response.data)
}

export async function deleteSalaryApi(id: number): Promise<void> {
  await apiClient.delete(`/api/salaries/${id}`)
}

// -----------------------------------------------------------------------
// Dashboard types & API
// -----------------------------------------------------------------------

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

export async function getDashboardApi(): Promise<DashboardKPIs> {
  const response = await apiClient.get<DashboardKPIs>('/api/dashboard/')
  return response.data
}

export async function getMonthlyChartApi(year: number): Promise<MonthlyChartRow[]> {
  const response = await apiClient.get<MonthlyChartRow[]>('/api/dashboard/chart/monthly', {
    params: { year },
  })
  return response.data
}

// -----------------------------------------------------------------------
// Import Excel
// -----------------------------------------------------------------------

export interface ImportResult {
  contacts_created: number
  invoices_created: number
  payments_created: number
  salaries_created: number
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

export interface TestImportShortcut {
  alias: string
  label: string
  import_type: 'gestion' | 'comptabilite'
  order: number
  available: boolean
  file_name: string | null
  message: string | null
}

export async function importGestionFileApi(file: File): Promise<ImportResult> {
  const form = new FormData()
  form.append('file', file)
  const response = await apiClient.post<ImportResult>('/api/import/excel/gestion', form, {
    timeout: 120000,
  })
  return response.data
}

export async function importComptabiliteFileApi(file: File): Promise<ImportResult> {
  const form = new FormData()
  form.append('file', file)
  const response = await apiClient.post<ImportResult>('/api/import/excel/comptabilite', form, {
    timeout: 120000,
  })
  return response.data
}

export async function listTestImportShortcutsApi(): Promise<TestImportShortcut[]> {
  const response = await apiClient.get<TestImportShortcut[]>('/api/import/excel/test-shortcuts')
  return response.data
}

export async function importTestShortcutApi(alias: string): Promise<ImportResult> {
  const response = await apiClient.post<ImportResult>(`/api/import/excel/test-shortcuts/${alias}`)
  return response.data
}

// -----------------------------------------------------------------------
// Fiscal year — pre-close checks & open-next
// -----------------------------------------------------------------------

export async function getFiscalYearPreCloseChecksApi(id: number): Promise<string[]> {
  const response = await apiClient.get<string[]>(
    `/api/accounting/fiscal-years/${id}/pre-close-checks`,
  )
  return response.data
}

export async function openNextFiscalYearApi(
  id: number,
  payload: FiscalYearCreate,
): Promise<FiscalYearRead> {
  const response = await apiClient.post<FiscalYearRead>(
    `/api/accounting/fiscal-years/${id}/open-next`,
    payload,
  )
  return response.data
}

// -----------------------------------------------------------------------
// Bilan (balance sheet) — actif / passif
// -----------------------------------------------------------------------

export interface BilanSection {
  account_number: string
  account_label: string
  solde: string
}

export interface BilanRead {
  actif: BilanSection[]
  passif: BilanSection[]
  total_actif: string
  total_passif: string
  resultat: string
}

export async function getBilanApi(fiscalYearId?: number): Promise<BilanRead> {
  const params = fiscalYearId ? `?fiscal_year_id=${fiscalYearId}` : ''
  const response = await apiClient.get<BilanRead>(`/api/accounting/entries/bilan${params}`)
  return response.data
}

export function getExportCsvUrl(
  type: 'journal' | 'balance' | 'resultat' | 'bilan',
  params: Record<string, string | number | undefined> = {},
): string {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v != null) sp.set(k, String(v))
  }
  const qs = sp.toString() ? `?${sp}` : ''
  return `/api/accounting/entries/${type}/export/csv${qs}`
}

// -----------------------------------------------------------------------
// Contact history & créances douteuses
// -----------------------------------------------------------------------

export interface ContactInvoiceSummary {
  id: number
  number: string
  type: string
  date: string
  due_date: string | null
  status: string
  total_amount: string
  paid_amount: string
  balance_due: string
}

export interface ContactPaymentSummary {
  id: number
  date: string
  amount: string
  method: string
  invoice_number: string | null
}

export interface ContactHistory {
  contact: Record<string, unknown>
  invoices: ContactInvoiceSummary[]
  payments: ContactPaymentSummary[]
  total_invoiced: string
  total_paid: string
  total_due: string
}

export async function getContactHistoryApi(contactId: number): Promise<ContactHistory> {
  const response = await apiClient.get<ContactHistory>(`/api/contacts/${contactId}/history`)
  return response.data
}

export async function markCreanceDouteuse(contactId: number): Promise<{
  debit_entry_id: number
  credit_entry_id: number
  account_douteux: string
  account_client: string
  amount: string
}> {
  const response = await apiClient.post(`/api/contacts/${contactId}/mark-douteux`)
  return response.data
}

// -----------------------------------------------------------------------
// Rule preview
// -----------------------------------------------------------------------

export interface RulePreviewEntry {
  account_number: string
  label: string
  debit: string
  credit: string
}

export async function previewRuleApi(
  ruleId: number,
  amount: string,
  label: string,
): Promise<RulePreviewEntry[]> {
  const response = await apiClient.post<RulePreviewEntry[]>(
    `/api/accounting/rules/${ruleId}/preview`,
    { amount, label },
  )
  return response.data
}

// -----------------------------------------------------------------------
// Import Excel — preview mode
// -----------------------------------------------------------------------

export type PreviewSheetStatus = 'recognized' | 'ignored' | 'unsupported' | 'empty'

export interface PreviewSheetResult {
  name: string
  kind: string
  status: PreviewSheetStatus
  header_row: number | null
  rows: number
  source_rows?: number
  detected_columns: string[]
  missing_columns: string[]
  ignored_rows: number
  policy_ignored_rows?: number
  blocked_rows: number
  initial_blocked_rows?: number
  sample_rows: Record<string, string>[]
  warnings: string[]
  errors: string[]
  warning_details: ImportIssueDetail[]
  error_details: ImportIssueDetail[]
}

export interface PreviewComparisonDomain {
  kind: string
  file_rows: number
  already_in_solde: number
  missing_in_solde: number
  extra_in_solde: number
  ignored_by_policy: number
  blocked: number
}

export interface PreviewComparisonSummary {
  mode: 'gestion-excel-to-solde'
  direction: 'excel-to-solde'
  domains: PreviewComparisonDomain[]
  totals: {
    file_rows: number
    already_in_solde: number
    missing_in_solde: number
    extra_in_solde: number
    ignored_by_policy: number
    blocked: number
  }
}

export interface PreviewResult {
  sheets: PreviewSheetResult[]
  estimated_contacts: number
  estimated_invoices: number
  estimated_payments: number
  estimated_salaries: number
  estimated_entries: number
  errors: string[]
  warnings: string[]
  error_details: ImportIssueDetail[]
  warning_details: ImportIssueDetail[]
  can_import: boolean
  sample_rows: Record<string, unknown>[]
  comparison?: PreviewComparisonSummary
}

export async function previewGestionFileApi(file: File): Promise<PreviewResult> {
  const form = new FormData()
  form.append('file', file)
  const response = await apiClient.post<PreviewResult>('/api/import/excel/gestion/preview', form, {
    timeout: 60000,
  })
  return response.data
}

export async function previewComptabiliteFileApi(file: File): Promise<PreviewResult> {
  const form = new FormData()
  form.append('file', file)
  const response = await apiClient.post<PreviewResult>(
    '/api/import/excel/comptabilite/preview',
    form,
    {
      timeout: 60000,
    },
  )
  return response.data
}

// -----------------------------------------------------------------------
// Bank — OFX / QIF import
// -----------------------------------------------------------------------

export async function importOFXApi(content: string) {
  const response = await apiClient.post('/api/bank/transactions/import-ofx', { content })
  return response.data
}

export async function importQIFApi(content: string) {
  const response = await apiClient.post('/api/bank/transactions/import-qif', { content })
  return response.data
}
