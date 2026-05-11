<template>
  <div ref="containerRef" class="docx-preview-container" />
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import { renderAsync } from 'docx-preview'

const props = defineProps<{
  blob: Blob | null
}>()

const containerRef = ref<HTMLElement | null>(null)
let abortController: AbortController | null = null

async function render(blob: Blob): Promise<void> {
  if (!containerRef.value) return
  abortController?.abort()
  abortController = new AbortController()
  containerRef.value.innerHTML = ''
  await renderAsync(blob, containerRef.value, undefined, {
    className: 'docx-preview',
    inWrapper: false,
    ignoreWidth: true,
    ignoreHeight: true,
    ignoreFonts: false,
    breakPages: true,
    useBase64URL: true,
    renderChanges: false,
    renderComments: false,
  })
}

watch(
  () => props.blob,
  (blob) => {
    if (blob) render(blob)
    else if (containerRef.value) containerRef.value.innerHTML = ''
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  abortController?.abort()
})
</script>

<style scoped>
.docx-preview-container {
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  max-height: 520px;
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-surface-radius-sm);
  background: #fff;
  padding: 0.5rem;
}
</style>
