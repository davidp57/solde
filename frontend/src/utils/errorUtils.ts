/**
 * Extracts a human-readable error detail string from an Axios-style error object.
 *
 * The FastAPI backend returns structured error responses with the shape:
 *   { response: { data: { detail: string | object } } }
 *
 * Falls back to a caller-provided translated message when the error has no
 * recognised shape.  The fallback is required so callers are forced to pass
 * an already-translated string and cannot accidentally embed hard-coded UI text.
 */
export function getErrorDetail(error: unknown, fallback: string): string {
  if (error !== null && typeof error === 'object' && 'response' in error) {
    const response = (error as { response?: unknown }).response
    if (response !== null && typeof response === 'object' && 'data' in response) {
      const data = (response as { data?: unknown }).data
      if (data !== null && typeof data === 'object' && 'detail' in data) {
        const detail = (data as { detail?: unknown }).detail
        if (typeof detail === 'string') return detail
        if (Array.isArray(detail) && detail.length > 0) {
          const first = detail[0]
          if (typeof first === 'object' && first !== null && 'msg' in first) {
            return String((first as { msg: unknown }).msg)
          }
          return String(first)
        }
        // The API returns { code, detail } for every structured error
        // (see backend/errors.py); without this the caller would show
        // "[object Object]" and the actual reason would be lost.
        if (detail !== null && typeof detail === 'object' && 'detail' in detail) {
          const inner = (detail as { detail?: unknown }).detail
          if (typeof inner === 'string') return inner
        }
        if (detail !== null && detail !== undefined) return String(detail)
      }
    }
  }
  return fallback
}
