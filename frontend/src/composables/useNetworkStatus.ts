import { ref, readonly } from 'vue'

const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)

if (typeof window !== 'undefined') {
  window.addEventListener('offline', () => {
    isOffline.value = true
  })
  window.addEventListener('online', () => {
    isOffline.value = false
  })
}

/** Called from the Axios response interceptor when a network-level error is detected. */
export function markNetworkError(): void {
  isOffline.value = true
}

export function useNetworkStatus(): { isOffline: Readonly<typeof isOffline> } {
  return { isOffline: readonly(isOffline) }
}
