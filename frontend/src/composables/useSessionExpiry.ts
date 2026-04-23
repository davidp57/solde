import { ref, watch, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const WARNING_BEFORE_MS = 5 * 60 * 1000 // 5 minutes

function getTokenExpiry(token: string): number | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(atob((parts[1] ?? '').replace(/-/g, '+').replace(/_/g, '/')))
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

export function useSessionExpiry(): {
  isExpiringSoon: ReturnType<typeof ref<boolean>>
  dismissWarning: () => void
  extendSession: () => Promise<void>
} {
  const auth = useAuthStore()
  const isExpiringSoon = ref(false)
  let warningTimer: ReturnType<typeof setTimeout> | null = null
  let expiredTimer: ReturnType<typeof setTimeout> | null = null

  function clearTimers(): void {
    if (warningTimer !== null) {
      clearTimeout(warningTimer)
      warningTimer = null
    }
    if (expiredTimer !== null) {
      clearTimeout(expiredTimer)
      expiredTimer = null
    }
  }

  function schedule(token: string): void {
    clearTimers()
    const expMs = getTokenExpiry(token)
    if (expMs === null) return

    const now = Date.now()
    const warningAt = expMs - WARNING_BEFORE_MS
    const msUntilWarning = warningAt - now

    if (msUntilWarning > 0) {
      warningTimer = setTimeout(() => {
        isExpiringSoon.value = true
      }, msUntilWarning)
    } else if (expMs > now) {
      // Already inside the warning window
      isExpiringSoon.value = true
    }

    const msUntilExpiry = expMs - now
    if (msUntilExpiry > 0) {
      expiredTimer = setTimeout(() => {
        isExpiringSoon.value = false
      }, msUntilExpiry)
    }
  }

  watch(
    () => auth.accessToken,
    (token) => {
      isExpiringSoon.value = false
      if (token) {
        schedule(token)
      } else {
        clearTimers()
      }
    },
    { immediate: true },
  )

  onUnmounted(clearTimers)

  function dismissWarning(): void {
    isExpiringSoon.value = false
  }

  async function extendSession(): Promise<void> {
    const success = await auth.refreshAccessToken()
    if (success) {
      isExpiringSoon.value = false
    }
  }

  return { isExpiringSoon, dismissWarning, extendSession }
}
