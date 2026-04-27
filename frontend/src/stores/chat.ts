import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { type ChatMessage, getChatConfig, streamChat } from '@/api/chat'
import i18n from '@/i18n'

export const useChatStore = defineStore('chat', () => {
  const isOpen = ref(false)
  const isEnabled = ref(false)
  const isStreaming = ref(false)
  const messages = ref<ChatMessage[]>([])
  const streamingText = ref('')
  let abortController: AbortController | null = null

  const hasMessages = computed(() => messages.value.length > 0)

  async function loadConfig(): Promise<void> {
    try {
      const config = await getChatConfig()
      isEnabled.value = config.enabled
    } catch {
      isEnabled.value = false
    }
  }

  function open(): void {
    isOpen.value = true
  }

  function close(): void {
    isOpen.value = false
  }

  function toggle(): void {
    isOpen.value = !isOpen.value
  }

  function clear(): void {
    if (isStreaming.value) abort()
    messages.value = []
    streamingText.value = ''
  }

  function abort(): void {
    abortController?.abort()
    abortController = null
    isStreaming.value = false
    if (streamingText.value) {
      messages.value.push({ role: 'assistant', content: streamingText.value })
      streamingText.value = ''
    }
  }

  async function send(userText: string): Promise<void> {
    if (isStreaming.value || !userText.trim()) return

    messages.value.push({ role: 'user', content: userText.trim() })
    streamingText.value = ''
    isStreaming.value = true
    abortController = new AbortController()

    try {
      const generator = streamChat([...messages.value], abortController.signal)
      for await (const chunk of generator) {
        streamingText.value += chunk
      }
      messages.value.push({ role: 'assistant', content: streamingText.value })
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return
      messages.value.push({
        role: 'assistant',
        content: `_${i18n.global.t('chat.error')}_`,
      })
    } finally {
      streamingText.value = ''
      isStreaming.value = false
      abortController = null
    }
  }

  return {
    isOpen,
    isEnabled,
    isStreaming,
    messages,
    streamingText,
    hasMessages,
    loadConfig,
    open,
    close,
    toggle,
    clear,
    send,
    abort,
  }
})
