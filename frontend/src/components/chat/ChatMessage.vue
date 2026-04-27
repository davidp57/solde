<template>
  <div
    class="chat-message"
    :class="message.role === 'user' ? 'chat-message--user' : 'chat-message--assistant'"
  >
    <div class="chat-message__bubble" v-html="renderedContent" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage } from '@/api/chat'
import { useDarkMode } from '@/composables/useDarkMode'
import { renderMarkdown } from '@/utils/renderMarkdown'

const props = defineProps<{
  message: ChatMessage
}>()

const { isDark } = useDarkMode()
const assistantBg = computed(() => isDark.value ? 'var(--p-surface-800)' : 'var(--p-surface-100)')

const renderedContent = computed(() => renderMarkdown(props.message.content))
</script>

<style scoped>
.chat-message {
  display: flex;
}

.chat-message--user {
  justify-content: flex-end;
}

.chat-message--assistant {
  justify-content: flex-start;
}

.chat-message__bubble {
  max-width: 85%;
  padding: var(--app-space-3) var(--app-space-4);
  border-radius: var(--app-radius-lg);
  font-size: 0.9rem;
  line-height: 1.55;
  word-break: break-word;
}

.chat-message--user .chat-message__bubble {
  background: var(--p-primary-500);
  color: #fff;
}

.chat-message--assistant .chat-message__bubble {
  background: v-bind(assistantBg);
  color: var(--app-text-primary);
}

:deep(p) {
  margin: 0 0 var(--app-space-2);
}

:deep(p:last-child) {
  margin-bottom: 0;
}

:deep(ul),
:deep(ol) {
  margin: var(--app-space-2) 0;
  padding-left: var(--app-space-4);
}

:deep(code) {
  background: var(--p-surface-200);
  padding: 0.1em 0.35em;
  border-radius: var(--app-radius-sm);
  font-size: 0.85em;
}

:deep(pre code) {
  background: transparent;
  padding: 0;
}

:deep(pre) {
  background: var(--p-surface-200);
  padding: var(--app-space-3);
  border-radius: var(--app-radius);
  overflow-x: auto;
  margin: var(--app-space-2) 0;
}
</style>
