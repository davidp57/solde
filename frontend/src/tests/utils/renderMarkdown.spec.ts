import { describe, expect, it } from 'vitest'

import { renderMarkdown } from '../../utils/renderMarkdown'

// ---------------------------------------------------------------------------
// headingSlug behaviour (verified via generated id attributes in the HTML)
// ---------------------------------------------------------------------------

describe('renderMarkdown — heading id generation', () => {
  it('generates a lowercase hyphenated slug from an ASCII heading', () => {
    const html = renderMarkdown('## Hello World')
    expect(html).toContain('id="hello-world"')
  })

  it('keeps accented Unicode letters in the slug', () => {
    const html = renderMarkdown('## Guide par rôle')
    expect(html).toContain('id="guide-par-rôle"')
  })

  it('strips punctuation but keeps letters and hyphens', () => {
    const html = renderMarkdown('## « Je veux… »')
    expect(html).toContain('id="je-veux"')
  })

  it('collapses multiple spaces / mixed whitespace to a single hyphen', () => {
    const html = renderMarkdown('## Foo   Bar')
    expect(html).toContain('id="foo-bar"')
  })

  it('appends -1, -2 suffix for duplicate headings', () => {
    const md = '## Remises en banque\n\nsome text\n\n## Remises en banque\n\nmore text'
    const html = renderMarkdown(md)
    expect(html).toContain('id="remises-en-banque"')
    expect(html).toContain('id="remises-en-banque-1"')
  })

  it('counter resets between independent renderMarkdown calls', () => {
    const first = renderMarkdown('## Section A\n\n## Section A')
    const second = renderMarkdown('## Section A\n\n## Section A')
    // Both calls should produce the same ids independently
    expect(first).toBe(second)
  })
})

// ---------------------------------------------------------------------------
// XSS sanitization — id attributes must be preserved; scripts must be stripped
// ---------------------------------------------------------------------------

describe('renderMarkdown — XSS sanitization', () => {
  it('preserves id attributes on headings after sanitization', () => {
    const html = renderMarkdown('## Mon titre')
    expect(html).toContain('id="mon-titre"')
  })

  it('strips script tags', () => {
    const html = renderMarkdown('<script>alert(1)</script> safe text')
    expect(html).not.toContain('<script>')
    expect(html).toContain('safe text')
  })
})
