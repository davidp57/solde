import apiClient from './client'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatConfig {
  enabled: boolean
}

export interface ChatLogEntry {
  id: number
  user_id: number | null
  asked_at: string
  question: string
  prompt_tokens: number | null
  completion_tokens: number | null
}

export async function getChatConfig(): Promise<ChatConfig> {
  const response = await apiClient.get<ChatConfig>('/api/chat/config')
  return response.data
}

export async function getChatLogs(params?: {
  page?: number
  page_size?: number
  user_id?: number
}): Promise<ChatLogEntry[]> {
  const response = await apiClient.get<ChatLogEntry[]>('/api/chat/logs', { params })
  return response.data
}

/**
 * Send messages to the AI chat endpoint and stream the response via SSE.
 * Returns an AsyncGenerator of text chunks. Caller is responsible for managing
 * abort via AbortController.
 */
export async function* streamChat(
  messages: ChatMessage[],
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const token = localStorage.getItem('access_token')
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ messages }),
    signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (raw === '[DONE]') return
        try {
          const parsed: unknown = JSON.parse(raw)
          if (
            parsed !== null &&
            typeof parsed === 'object' &&
            'text' in parsed &&
            typeof (parsed as { text: unknown }).text === 'string'
          ) {
            yield (parsed as { text: string }).text
          } else if (
            parsed !== null &&
            typeof parsed === 'object' &&
            'error' in parsed
          ) {
            throw new Error(String((parsed as { error: unknown }).error))
          }
        } catch (e) {
          if (e instanceof SyntaxError) continue
          throw e
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
