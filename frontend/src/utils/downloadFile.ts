import apiClient from '../api/client'

/**
 * Download a file from an authenticated API route.
 *
 * `window.open` cannot be used for these: the access token lives in memory and is
 * attached by the axios interceptor, so a browser-initiated request arrives without
 * credentials and the server answers 401. Fetching the blob through the client and
 * handing it to a temporary link keeps the token on the request.
 *
 * The filename comes from `Content-Disposition` when the server sends one, so the saved
 * file keeps the name the server chose (`bilan_2025.pdf`, the original upload name…).
 */
export async function downloadAuthenticatedFile(
  url: string,
  fallbackFilename: string,
): Promise<void> {
  const response = await apiClient.get(url, { responseType: 'blob' })
  const objectUrl = URL.createObjectURL(response.data as Blob)
  try {
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = filenameFromDisposition(response.headers) ?? fallbackFilename
    document.body.appendChild(link)
    link.click()
    link.remove()
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
}

function filenameFromDisposition(headers: unknown): string | null {
  const raw = (headers as Record<string, string> | undefined)?.['content-disposition']
  if (!raw) return null
  // RFC 5987 form first (filename*=UTF-8''…), then the plain quoted or bare form.
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(raw)
  if (encoded) {
    try {
      return decodeURIComponent(encoded[1])
    } catch {
      // Fall through to the plain form rather than failing the download.
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(raw)
  return plain ? plain[1].trim() : null
}
