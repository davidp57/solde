import apiClient, { parseTotalCount } from './client'

export type PaymentMethod = 'especes' | 'cheque' | 'virement'
export type PaymentInvoiceType = 'client' | 'fournisseur'

export interface Payment {
  id: number
  invoice_id: number
  invoice_number?: string | null
  invoice_type?: PaymentInvoiceType | null
  contact_id: number
  contact_name?: string | null
  amount: string
  date: string
  method: PaymentMethod
  cheque_number: string | null
  reference: string | null
  notes: string | null
  deposited: boolean
  in_deposit: boolean
  deposit_date: string | null
  created_at: string
}

export interface PaymentCreate {
  invoice_id: number
  contact_id: number
  amount: string
  date: string
  method: PaymentMethod
  cheque_number?: string | null
  reference?: string | null
  notes?: string | null
}

export interface PaymentUpdate {
  amount?: string
  date?: string
  method?: PaymentMethod
  cheque_number?: string | null
  reference?: string | null
  notes?: string | null
  deposited?: boolean
  deposit_date?: string | null
}

export interface PaymentListParams {
  invoice_id?: number
  invoice_type?: PaymentInvoiceType
  contact_id?: number
  from_date?: string
  to_date?: string
  undeposited_only?: boolean
  inconsistent_only?: boolean
  skip?: number
  limit?: number
}

export async function listPayments(params?: PaymentListParams): Promise<Payment[]> {
  const response = await apiClient.get<Payment[]>('/api/payments/', { params })
  return response.data
}

export async function listPaymentsWithCount(
  params?: PaymentListParams,
): Promise<{ items: Payment[]; total: number }> {
  const response = await apiClient.get<Payment[]>('/api/payments/', { params })
  return { items: response.data, total: parseTotalCount(response.headers as Record<string, string>) }
}

export async function createPayment(payload: PaymentCreate): Promise<Payment> {
  const response = await apiClient.post<Payment>('/api/payments/', payload)
  return response.data
}

export async function getPayment(id: number): Promise<Payment> {
  const response = await apiClient.get<Payment>(`/api/payments/${id}`)
  return response.data
}

export async function updatePayment(id: number, payload: PaymentUpdate): Promise<Payment> {
  const response = await apiClient.put<Payment>(`/api/payments/${id}`, payload)
  return response.data
}

export async function deletePayment(id: number): Promise<void> {
  await apiClient.delete(`/api/payments/${id}`)
}

export async function suggestChequeNumber(paymentDate?: string): Promise<string> {
  const params = paymentDate ? { payment_date: paymentDate } : {}
  const response = await apiClient.get<string>('/api/payments/suggest_cheque_number', { params })
  return response.data
}

export async function fixDepositDate(id: number, depositDate: string): Promise<Payment> {
  const response = await apiClient.post<Payment>(
    `/api/payments/${id}/fix-deposit-date`,
    null,
    { params: { deposit_date: depositDate } },
  )
  return response.data
}
