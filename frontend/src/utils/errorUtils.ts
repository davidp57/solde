import fr from '@/i18n/fr'

// The French messages are read directly rather than through the vue-i18n instance:
// this helper runs outside any component setup, and the app has a single complete
// locale. It also keeps the helper importable in tests that mock vue-i18n.
const apiErrorMessages: Record<string, string> = fr.api_errors

/**
 * Extracts a human-readable error detail string from an Axios-style error object.
 *
 * The FastAPI backend returns structured error responses with the shape:
 *   { response: { data: { detail: string | object } } }
 *
 * Resolution order:
 *   1. a structured `code` that has a French message under `api_errors.<CODE>`;
 *   2. a 403 without its own translation — the role does not allow the action;
 *   3. a request that never got a response — the server is unreachable;
 *   4. whatever text the server sent (string, validation array, `detail` or
 *      `message` of a structured body), so the actual reason is never lost;
 *   5. the caller-provided translated fallback.
 *
 * The fallback is required so callers are forced to pass an already-translated
 * string and cannot accidentally embed hard-coded UI text.
 */
export function getErrorDetail(error: unknown, fallback: string): string {
  if (error === null || typeof error !== 'object') return fallback

  const response = 'response' in error ? (error as { response?: unknown }).response : undefined
  if (response === null || typeof response !== 'object') {
    // Axios sets `request` and leaves `response` empty when the server never answered.
    if ('request' in error && (error as { request?: unknown }).request) {
      return fr.common.error.network
    }
    return fallback
  }

  const statusCode = (response as { status?: unknown }).status
  const data = 'data' in response ? (response as { data?: unknown }).data : undefined
  const detail =
    data !== null && typeof data === 'object' && 'detail' in data
      ? (data as { detail?: unknown }).detail
      : undefined

  if (detail !== null && typeof detail === 'object' && !Array.isArray(detail)) {
    const code = (detail as { code?: unknown }).code
    if (typeof code === 'string' && Object.hasOwn(apiErrorMessages, code)) {
      return apiErrorMessages[code] as string
    }
  }
  if (statusCode === 403) return fr.common.error.forbidden_action

  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (typeof first === 'object' && first !== null && 'msg' in first) {
      return String((first as { msg: unknown }).msg)
    }
    return String(first)
  }
  // The API returns { code, detail } for every structured error (see
  // backend/errors.py), and the auth routes { code, message }; without this the
  // caller would show "[object Object]" and the actual reason would be lost.
  if (detail !== null && typeof detail === 'object') {
    for (const key of ['detail', 'message'] as const) {
      const inner = (detail as Record<string, unknown>)[key]
      if (typeof inner === 'string') return inner
    }
  }
  if (detail !== null && detail !== undefined) return String(detail)
  return fallback
}
