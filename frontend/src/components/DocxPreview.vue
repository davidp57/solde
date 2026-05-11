<template>
  <div class="docx-preview-container">
    <div ref="containerRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { renderAsync } from 'docx-preview'

const props = defineProps<{
  blob: Blob | null
}>()

const containerRef = ref<HTMLElement | null>(null)

async function render(blob: Blob): Promise<void> {
  if (!containerRef.value) return
  containerRef.value.innerHTML = ''
  try {
    await renderAsync(blob, containerRef.value, undefined, {
      className: 'docx-preview',
      ignoreWidth: true,
      ignoreHeight: true,
      breakPages: true,
    })
  } catch (e) {
    console.error('DocxPreview render failed', e)
  }
}

onMounted(() => {
  if (props.blob) render(props.blob)
})

watch(
  () => props.blob,
  (blob) => {
    if (blob) render(blob)
    else if (containerRef.value) containerRef.value.innerHTML = ''
  },
)
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
