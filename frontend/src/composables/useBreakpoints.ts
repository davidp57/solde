import { ref, onMounted, onUnmounted } from 'vue'

const MOBILE_BREAKPOINT = 767

/**
 * Returns a reactive `isMobile` ref that is true when the viewport width
 * is ≤ 767px. Uses matchMedia for efficient listening without polling.
 */
export function useBreakpoints() {
  const isMobile = ref(false)

  let mediaQuery: MediaQueryList | null = null

  function handleChange(event: MediaQueryListEvent) {
    isMobile.value = event.matches
  }

  onMounted(() => {
    mediaQuery = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`)
    isMobile.value = mediaQuery.matches
    mediaQuery.addEventListener('change', handleChange)
  })

  onUnmounted(() => {
    mediaQuery?.removeEventListener('change', handleChange)
  })

  return { isMobile }
}
