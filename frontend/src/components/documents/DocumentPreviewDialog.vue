<template>
  <Dialog
    :visible="visible"
    :header="document?.title ?? ''"
    modal
    maximizable
    :style="{ width: '56rem' }"
    :breakpoints="{ '960px': '95vw' }"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="document-preview" data-testid="document-preview">
      <div v-if="loading" class="document-preview__center">
        <i class="pi pi-spin pi-spinner" style="font-size: 2rem" />
      </div>

      <div v-else-if="error" class="app-empty-state">
        <i class="pi pi-exclamation-triangle" />
        <span>{{ error }}</span>
      </div>

      <!-- Mobile browsers embed PDFs poorly; a real tab is more usable there. -->
      <Button
        v-else-if="kind === 'pdf' && isMobile"
        icon="pi pi-external-link"
        :label="t('documents.preview_open_tab')"
        severity="secondary"
        outlined
        @click="openInTab"
      />
      <embed
        v-else-if="kind === 'pdf'"
        :src="`${blobUrl}#toolbar=0&navpanes=0&view=FitH`"
        type="application/pdf"
        class="document-preview__embed"
        :title="document?.title"
        data-testid="document-preview-pdf"
      />

      <img
        v-else-if="kind === 'image'"
        :src="blobUrl ?? ''"
        :alt="document?.title"
        class="document-preview__image"
        data-testid="document-preview-image"
      />

      <!-- Rendered through the shared helper, which sanitises: the file comes from a user. -->
      <div
        v-else-if="kind === 'markdown'"
        class="document-preview__markdown markdown-body"
        data-testid="document-preview-markdown"
        v-html="renderedMarkdown"
      />

      <pre
        v-else-if="kind === 'text'"
        class="document-preview__text"
        data-testid="document-preview-text"
        >{{ textContent }}</pre
      >

      <div v-else class="app-empty-state" data-testid="document-preview-unsupported">
        <i class="pi pi-file" />
        <span>{{ t('documents.preview_unsupported') }}</span>
        <Button
          :label="t('documents.download')"
          icon="pi pi-download"
          severity="secondary"
          outlined
          @click="$emit('download')"
        />
      </div>
    </div>

    <template #footer>
      <span class="document-preview__filename">{{ document?.filename }}</span>
      <Button
        :label="t('documents.download')"
        icon="pi pi-download"
        severity="secondary"
        outlined
        @click="$emit('download')"
      />
      <Button :label="t('common.close')" text @click="$emit('update:visible', false)" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { fetchDocumentBlobApi, type AppDocument } from '../../api/document'
import { useBreakpoints } from '../../composables/useBreakpoints'
import { previewKind } from '../../utils/documentPreview'
import { renderMarkdown } from '../../utils/renderMarkdown'

const props = defineProps<{ visible: boolean; document: AppDocument | null }>()
defineEmits<{ 'update:visible': [boolean]; download: [] }>()

const { t } = useI18n()
const { isMobile } = useBreakpoints()

const loading = ref(false)
const error = ref<string | null>(null)
const blobUrl = ref<string | null>(null)
const textContent = ref('')

const kind = computed(() => previewKind(props.document))

const renderedMarkdown = computed(() =>
  kind.value === 'markdown' ? renderMarkdown(textContent.value) : '',
)

function releaseBlob(): void {
  if (blobUrl.value) {
    URL.revokeObjectURL(blobUrl.value)
    blobUrl.value = null
  }
}

function openInTab(): void {
  if (blobUrl.value) window.open(blobUrl.value, '_blank', 'noopener,noreferrer')
}

async function load(document: AppDocument): Promise<void> {
  loading.value = true
  error.value = null
  textContent.value = ''
  releaseBlob()
  try {
    const blob = await fetchDocumentBlobApi(document.id)
    if (kind.value === 'markdown' || kind.value === 'text') {
      textContent.value = await blob.text()
    } else if (kind.value !== 'unsupported') {
      blobUrl.value = URL.createObjectURL(blob)
    }
  } catch {
    error.value = t('documents.preview_failed')
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.visible, props.document?.id] as const,
  ([visible]) => {
    if (visible && props.document) {
      // Nothing to fetch for a format we cannot render anyway.
      if (previewKind(props.document) === 'unsupported') return
      void load(props.document)
    } else if (!visible) {
      releaseBlob()
      textContent.value = ''
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.document-preview {
  min-height: 24rem;
  display: flex;
  flex-direction: column;
}

.document-preview__center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.document-preview__embed {
  width: 100%;
  height: 70vh;
  border: 1px solid var(--p-content-border-color);
  border-radius: 4px;
}

.document-preview__image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  margin: 0 auto;
}

.document-preview__markdown {
  max-height: 70vh;
  overflow-y: auto;
  padding: 0.5rem 0.25rem;
  line-height: 1.6;
}

.document-preview__text {
  max-height: 70vh;
  overflow: auto;
  margin: 0;
  padding: 0.75rem;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 4px;
  font-size: 0.85rem;
  white-space: pre-wrap;
  word-break: break-word;
}

.document-preview__filename {
  margin-right: auto;
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
</style>
