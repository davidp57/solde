/**
 * Centralized Markdown rendering with XSS sanitization.
 * Always use this helper instead of calling marked.parse directly before v-html injection.
 */
import { Marked } from 'marked'
import DOMPurify from 'dompurify'

/**
 * Convert a heading's raw Markdown text to a URL-friendly id.
 * Strips leading # markers, lowercases, removes non-alphanumeric chars
 * (keeping Unicode letters/digits and hyphens), collapses whitespace to a
 * single hyphen. Duplicate headings get a -1, -2 … suffix (GitHub style).
 */
function headingSlug(raw: string): string {
  return raw
    .replace(/^#{1,6}\s+/, '') // strip leading # markers
    .replace(/\s+$/, '')       // trim trailing whitespace / newline
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, '') // keep Unicode letters, digits, spaces, hyphens
    .trim()
    .replace(/\s+/g, '-')      // collapse whitespace runs to a single hyphen
}

/**
 * Parse Markdown and sanitize the resulting HTML to prevent XSS.
 * Headings get deterministic id attributes so in-page anchor links work.
 * Safe to use with v-html.
 */
export function renderMarkdown(text: string): string {
  const usedIds = new Map<string, number>()

  const instance = new Marked({
    renderer: {
      heading({ text: html, depth, raw }: { text: string; depth: number; raw: string }): string {
        const base = headingSlug(raw)
        const n = usedIds.get(base) ?? 0
        const id = n === 0 ? base : `${base}-${n}`
        usedIds.set(base, n + 1)
        return `<h${depth} id="${id}">${html}</h${depth}>\n`
      },
    },
  })

  const rawHtml = instance.parse(text, { async: false }) as string
  return DOMPurify.sanitize(rawHtml, { ADD_ATTR: ['id'] })
}
