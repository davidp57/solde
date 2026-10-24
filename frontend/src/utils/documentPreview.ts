import type { AppDocument } from '../api/document'

export type PreviewKind = 'pdf' | 'image' | 'markdown' | 'text' | 'unsupported'

/**
 * Decide how a document can be shown in the browser.
 *
 * The MIME type recorded at upload comes first; the extension only settles what the
 * type cannot, since Markdown and plain text share `text/*` and a `.md` uploaded
 * before Markdown was recognised carries `text/plain`.
 *
 * Office documents (Word, Excel) land on `unsupported`: a browser cannot render them
 * without a conversion library, and pretending otherwise would show a broken frame
 * instead of a clear download prompt.
 */
export function previewKind(document: AppDocument | null): PreviewKind {
  if (!document) return 'unsupported'

  const mime = (document.mime_type ?? '').toLowerCase()
  if (mime === 'application/pdf') return 'pdf'
  if (mime.startsWith('image/')) return 'image'

  const extension = document.filename.toLowerCase().split('.').pop() ?? ''
  if (extension === 'md' || extension === 'markdown' || mime === 'text/markdown') {
    return 'markdown'
  }
  if (mime.startsWith('text/') || mime === 'application/json' || mime === 'application/xml') {
    return 'text'
  }
  return 'unsupported'
}
