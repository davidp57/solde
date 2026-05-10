import type { AxiosError } from 'axios'

/**
 * Structured API error payload returned by the backend.
 */
export interface ApiErrorDetail {
  code: string
  detail: string
}

/**
 * Extract the structured error code from an Axios error response.
 * Returns the `code` field if the response detail is a structured object,
 * or null if the error is not structured (e.g. validation errors, network errors).
 */
export function getApiErrorCode(error: unknown): string | null {
  const axiosErr = error as AxiosError<{ detail: ApiErrorDetail | string | unknown }>
  const detail = axiosErr?.response?.data?.detail
  if (detail && typeof detail === 'object' && 'code' in detail) {
    return (detail as ApiErrorDetail).code
  }
  return null
}

/**
 * Extract the human-readable detail message from a structured API error.
 * Falls back to the raw detail string if not structured.
 */
export function getApiErrorMessage(error: unknown): string | null {
  const axiosErr = error as AxiosError<{ detail: ApiErrorDetail | string | unknown }>
  const detail = axiosErr?.response?.data?.detail
  if (detail && typeof detail === 'object' && 'code' in detail) {
    return (detail as ApiErrorDetail).detail
  }
  if (typeof detail === 'string') {
    return detail
  }
  return null
}
