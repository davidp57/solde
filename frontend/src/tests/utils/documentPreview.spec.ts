import { describe, expect, it } from 'vitest'

import { previewKind } from '../../utils/documentPreview'
import type { AppDocument } from '../../api/document'

function doc(overrides: Partial<AppDocument>): AppDocument {
  return {
    id: 1,
    title: 'Titre',
    filename: 'fichier.bin',
    mime_type: null,
    size_bytes: 10,
    fiscal_year_id: null,
    fiscal_year_name: null,
    tags: [],
    notes: null,
    uploaded_by: null,
    uploaded_at: '2026-08-04T10:00:00',
    ...overrides,
  }
}

describe('previewKind', () => {
  it('recognises a PDF', () => {
    expect(previewKind(doc({ mime_type: 'application/pdf', filename: 'bilan.pdf' }))).toBe('pdf')
  })

  it.each(['image/png', 'image/jpeg', 'image/webp'])('recognises %s as an image', (mime) => {
    expect(previewKind(doc({ mime_type: mime }))).toBe('image')
  })

  it('recognises Markdown by its type', () => {
    expect(previewKind(doc({ mime_type: 'text/markdown', filename: 'rapport.md' }))).toBe(
      'markdown',
    )
  })

  it('recognises Markdown by extension when the type says plain text', () => {
    // A .md uploaded before Markdown was accepted carries text/plain.
    expect(previewKind(doc({ mime_type: 'text/plain', filename: 'rapport.md' }))).toBe('markdown')
  })

  it.each([
    ['text/plain', 'notes.txt'],
    ['text/csv', 'releve.csv'],
    ['application/json', 'export.json'],
    ['application/xml', 'flux.xml'],
  ])('shows %s as text', (mime, filename) => {
    expect(previewKind(doc({ mime_type: mime, filename }))).toBe('text')
  })

  it.each([
    ['application/zip', 'contrat.docx'],
    ['application/vnd.ms-office', 'ancien.xls'],
  ])('leaves %s unsupported rather than showing a broken frame', (mime, filename) => {
    expect(previewKind(doc({ mime_type: mime, filename }))).toBe('unsupported')
  })

  it('handles a missing document and a missing type', () => {
    expect(previewKind(null)).toBe('unsupported')
    expect(previewKind(doc({ mime_type: null, filename: 'inconnu' }))).toBe('unsupported')
  })
})
