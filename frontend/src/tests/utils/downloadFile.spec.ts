import { beforeEach, describe, expect, it, vi } from 'vitest'

const get = vi.fn()
vi.mock('../../api/client', () => ({ default: { get: (...args: unknown[]) => get(...args) } }))

import { downloadAuthenticatedFile } from '../../utils/downloadFile'

// Captured before any spy is installed, otherwise each test would wrap the previous
// spy and the calls would recurse.
const nativeCreateElement = document.createElement.bind(document)

describe('downloadAuthenticatedFile', () => {
  let clicked: { download: string; href: string } | null

  beforeEach(() => {
    vi.clearAllMocks()
    clicked = null
    globalThis.URL.createObjectURL = vi.fn(() => 'blob:fake')
    globalThis.URL.revokeObjectURL = vi.fn()
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      const element = nativeCreateElement(tag)
      if (tag === 'a') {
        element.click = () => {
          clicked = {
            download: (element as HTMLAnchorElement).download,
            href: (element as HTMLAnchorElement).href,
          }
        }
      }
      return element
    })
  })

  it('goes through the API client, so the access token travels with the request', async () => {
    get.mockResolvedValue({ data: new Blob(['x']), headers: {} })

    await downloadAuthenticatedFile('/api/documents/7/download', 'fallback.pdf')

    expect(get).toHaveBeenCalledWith('/api/documents/7/download', { responseType: 'blob' })
  })

  it('saves the file under the name the server chose', async () => {
    get.mockResolvedValue({
      data: new Blob(['x']),
      headers: { 'content-disposition': 'attachment; filename="bilan_2025.pdf"' },
    })

    await downloadAuthenticatedFile('/api/accounting/entries/bilan/export/pdf', 'bilan.pdf')

    expect(clicked?.download).toBe('bilan_2025.pdf')
  })

  it('decodes an RFC 5987 filename', async () => {
    get.mockResolvedValue({
      data: new Blob(['x']),
      headers: { 'content-disposition': "attachment; filename*=UTF-8''proc%C3%A8s-verbal.pdf" },
    })

    await downloadAuthenticatedFile('/api/documents/1/download', 'fallback.pdf')

    expect(clicked?.download).toBe('procès-verbal.pdf')
  })

  it('falls back to the caller name when the server sends no disposition', async () => {
    get.mockResolvedValue({ data: new Blob(['x']), headers: {} })

    await downloadAuthenticatedFile('/api/documents/1/download', 'statuts.pdf')

    expect(clicked?.download).toBe('statuts.pdf')
  })

  it('releases the object URL once the click is done', async () => {
    get.mockResolvedValue({ data: new Blob(['x']), headers: {} })

    await downloadAuthenticatedFile('/api/documents/1/download', 'x.pdf')

    expect(globalThis.URL.revokeObjectURL).toHaveBeenCalledWith('blob:fake')
  })
})
