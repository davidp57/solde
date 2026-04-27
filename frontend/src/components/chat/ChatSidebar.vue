<template>
  <Transition name="chat-slide">
    <aside v-if="store.isOpen" class="chat-sidebar">
      <header class="chat-sidebar__header">
        <span class="chat-sidebar__title">
          <i class="pi pi-sparkles" />
          {{ t('chat.title') }}
        </span>
        <div class="chat-sidebar__actions">
          <Button
            v-if="store.hasMessages"
            icon="pi pi-trash"
            size="small"
            severity="secondary"
            text
            :title="t('chat.clear')"
            @click="store.clear()"
          />
          <Button
            icon="pi pi-times"
            size="small"
            severity="secondary"
            text
            :title="t('nav.chat_close')"
            @click="store.close()"
          />
        </div>
      </header>

      <div v-if="!store.isEnabled" class="chat-sidebar__disabled">
        <i class="pi pi-lock" />
        <p>{{ t('chat.disabled') }}</p>
      </div>

      <template v-else>
        <div ref="messagesEl" class="chat-sidebar__messages">
          <div v-if="!store.hasMessages && !store.isStreaming" class="chat-sidebar__empty">
            <i class="pi pi-sparkles chat-sidebar__empty-icon" />
            <p>{{ t('chat.placeholder') }}</p>
          </div>

          <ChatMessage
            v-for="(msg, i) in store.messages"
            :key="i"
            :message="msg"
          />

          <div v-if="store.isStreaming" class="chat-message chat-message--assistant">
            <div class="chat-message__bubble">
              <!-- eslint-disable-next-line vue/no-v-html -->
              <span v-if="store.streamingText" v-html="renderedStreamingText" />
              <span v-else class="chat-sidebar__thinking">{{ t('chat.thinking') }}</span>
            </div>
          </div>
        </div>

        <form class="chat-sidebar__input" @submit.prevent="submit">
          <Textarea
            v-model="inputText"
            :placeholder="t('chat.placeholder')"
            :disabled="store.isStreaming"
            rows="2"
            auto-resize
            class="chat-sidebar__textarea"
            @keydown.enter.exact.prevent="submit"
          />
          <Button
            v-if="store.isStreaming"
            icon="pi pi-stop"
            severity="secondary"
            :title="t('common.cancel')"
            @click="store.abort()"
          />
          <Button
            v-else
            type="submit"
            icon="pi pi-send"
            :disabled="!inputText.trim()"
            :title="t('chat.send')"
          />
        </form>
      </template>
    </aside>
  </Transition>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { marked } from 'marked'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import { useChatStore } from '@/stores/chat'
import ChatMessage from './ChatMessage.vue'

const { t } = useI18n()
const store = useChatStore()
const inputText = ref('')
const messagesEl = ref<HTMLElement | null>(null)

const renderedStreamingText = computed(() => {
  const result = marked.parse(store.streamingText, { async: false })
  return result as string
})

function submit(): void {
  const text = inputText.value.trim()
  if (!text || store.isStreaming) return
  inputText.value = ''
  void store.send(text)
}

watch(
  [() => store.messages.length, () => store.streamingText],
  async () => {
    await nextTick()
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  },
)
</script>

<style scoped>
.chat-sidebar {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 380px;
  max-width: 95vw;
  display: flex;
  flex-direction: column;
  background: var(--p-surface-0);
  border-left: 1px solid var(--p-surface-200);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.chat-sidebar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--app-space-4);
  border-bottom: 1px solid var(--p-surface-200);
  gap: var(--app-space-3);
}

.chat-sidebar__title {
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: var(--app-space-2);
  color: var(--app-text-primary);
}

.chat-sidebar__actions {
  display: flex;
  gap: var(--app-space-1);
}

.chat-sidebar__disabled {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--app-space-3);
  padding: var(--app-space-6);
  color: var(--app-text-muted);
  text-align: center;
}

.chat-sidebar__disabled .pi {
  font-size: 2rem;
}

.chat-sidebar__messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--app-space-4);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.chat-sidebar__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--app-space-3);
  color: var(--app-text-muted);
  text-align: center;
  padding: var(--app-space-6);
}

.chat-sidebar__empty-icon {
  font-size: 2.5rem;
  opacity: 0.4;
}

.chat-sidebar__thinking {
  animation: pulse 1.4s ease-in-out infinite;
  color: var(--app-text-muted);
  font-style: italic;
}

.chat-message {
  display: flex;
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
  background: var(--p-surface-100);
  color: var(--app-text-primary);
}

.chat-sidebar__input {
  display: flex;
  align-items: flex-end;
  gap: var(--app-space-2);
  padding: var(--app-space-3) var(--app-space-4);
  border-top: 1px solid var(--p-surface-200);
}

.chat-sidebar__textarea {
  flex: 1;
  resize: none;
}

/* Transition */
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: transform 0.25s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  transform: translateX(100%);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
