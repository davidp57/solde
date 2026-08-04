import { mount } from '@vue/test-utils'
import { defineComponent, nextTick, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (key: string) => key }) }))

const fetchBlob = vi.fn()
vi.mock('../../api/document', () => ({
  fetchDocumentBlobApi: (...args: unknown[]) => fetchBlob(...args),
  getDocumentDownloadUrl: (id: number) => `/api/documents/${id}/download`,
}))

// A real ref: the template unwraps refs automatically, a plain object stays truthy.
const isMobile = ref(false)
vi.mock('../../composables/useBreakpoints', () => ({
  useBreakpoints: () => ({ isMobile }),
}))

import DocumentPreviewDialog from '../../components/documents/DocumentPreviewDialog.vue'
import type { AppDocument } from '../../api/document'

const DialogStub = defineComponent({
  props: { visible: { type: Boolean, default: false } },
  template: '<div v-if="visible"><slot /><slot name="footer" /></div>',
})

const ButtonStub = defineComponent({
  props: { label: { type: String, default: '' } },
  emits: ['click'],
  template: '<button @click="$emit(\'click\')">{{ label }}</button>',
})

function doc(overrides: Partial<AppDocument>): AppDocument {
  return {
    id: 3,
    title: 'Rapport',
    filename: 'rapport.md',
    mime_type: 'text/markdown',
    size_bytes: 20,
    fiscal_year_id: null,
    fiscal_year_name: null,
    tags: [],
    notes: null,
    uploaded_by: null,
    uploaded_at: '2026-08-04T10:00:00',
    ...overrides,
  }
}

function mountDialog(document: AppDocument | null) {
  return mount(DocumentPreviewDialog, {
    props: { visible: true, document },
    global: { stubs: { Dialog: DialogStub, Button: ButtonStub } },
  })
}

async function settle() {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
  await nextTick()
}

describe('DocumentPreviewDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    isMobile.value = false
    globalThis.URL.createObjectURL = vi.fn(() => 'blob:preview')
    globalThis.URL.revokeObjectURL = vi.fn()
  })

  it('renders Markdown as HTML', async () => {
    fetchBlob.mockResolvedValue(new Blob(['# Clôture 2025\n\nDéficit constaté.']))

    const wrapper = mountDialog(doc({}))
    await settle()

    const rendered = wrapper.find('[data-testid="document-preview-markdown"]')
    expect(rendered.exists()).toBe(true)
    expect(rendered.html()).toContain('<h1')
    expect(rendered.text()).toContain('Clôture 2025')
  })

  it('strips scripts from an uploaded Markdown file', async () => {
    fetchBlob.mockResolvedValue(new Blob(['# Titre\n\n<script>alert(1)</script>\n']))

    const wrapper = mountDialog(doc({}))
    await settle()

    const html = wrapper.find('[data-testid="document-preview-markdown"]').html()
    expect(html).not.toContain('<script')
    expect(html).not.toContain('alert(1)')
  })

  it('shows plain text as-is, without interpreting it', async () => {
    fetchBlob.mockResolvedValue(new Blob(['ligne 1\n<b>pas du gras</b>']))

    const wrapper = mountDialog(doc({ filename: 'notes.txt', mime_type: 'text/plain' }))
    await settle()

    const pre = wrapper.find('[data-testid="document-preview-text"]')
    expect(pre.exists()).toBe(true)
    expect(pre.text()).toContain('<b>pas du gras</b>')
    expect(pre.html()).not.toContain('<b>pas du gras</b>')
  })

  it('embeds a PDF from an object URL', async () => {
    fetchBlob.mockResolvedValue(new Blob(['%PDF-1.7']))

    const wrapper = mountDialog(doc({ filename: 'bilan.pdf', mime_type: 'application/pdf' }))
    await settle()

    const embed = wrapper.find('[data-testid="document-preview-pdf"]')
    expect(embed.exists()).toBe(true)
    expect(embed.attributes('src')).toContain('blob:preview')
  })

  it('offers a tab instead of an embed on mobile', async () => {
    isMobile.value = true
    fetchBlob.mockResolvedValue(new Blob(['%PDF-1.7']))

    const wrapper = mountDialog(doc({ filename: 'bilan.pdf', mime_type: 'application/pdf' }))
    await settle()

    expect(wrapper.find('[data-testid="document-preview-pdf"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('documents.preview_open_tab')
  })

  it('never fetches a format it cannot render', async () => {
    const wrapper = mountDialog(doc({ filename: 'contrat.docx', mime_type: 'application/zip' }))
    await settle()

    expect(fetchBlob).not.toHaveBeenCalled()
    expect(wrapper.find('[data-testid="document-preview-unsupported"]').exists()).toBe(true)
  })

  it('reports a failed load instead of staying blank', async () => {
    fetchBlob.mockRejectedValue(new Error('boom'))

    const wrapper = mountDialog(doc({}))
    await settle()

    expect(wrapper.text()).toContain('documents.preview_failed')
  })

  it('releases the object URL when it closes', async () => {
    fetchBlob.mockResolvedValue(new Blob(['%PDF-1.7']))
    const wrapper = mountDialog(doc({ filename: 'bilan.pdf', mime_type: 'application/pdf' }))
    await settle()

    await wrapper.setProps({ visible: false })
    await settle()

    expect(globalThis.URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview')
  })
})
