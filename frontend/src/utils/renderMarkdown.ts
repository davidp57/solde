/**
 * Centralized Markdown rendering with XSS sanitization.
 * Always use this helper instead of calling marked.parse directly before v-html injection.
 */
import { marked } from 'marked'
import DOMPurify from 'dompurify'

/**
 * Parse Markdown and sanitize the resulting HTML to prevent XSS.
 * Safe to use with v-html.
 */
export function renderMarkdown(text: string): string {
  const raw = marked.parse(text, { async: false }) as string
  return DOMPurify.sanitize(raw)
}
