import { ref, onMounted, onUnmounted } from 'vue'

// Keep these in sync with the layout breakpoints documented in the design
// handoff: mobile < 768, tablet 768–1199, desktop ≥ 1200.
const MOBILE_MAX = 767
const DESKTOP_MIN = 1200

/**
 * Reactive viewport flags driven by matchMedia (no polling):
 * - `isMobile`  — width ≤ 767px (phones; tables collapse to cards)
 * - `isTablet`  — 768–1199px (icon rail navigation)
 * - `isDesktop` — width ≥ 1200px (full sidebar)
 *
 * `isMobile` keeps its historical meaning so existing callers are unaffected.
 */
export function useBreakpoints() {
  const isMobile = ref(false)
  const isDesktop = ref(false)
  const isTablet = ref(false)

  let mobileMq: MediaQueryList | null = null
  let desktopMq: MediaQueryList | null = null

  function sync(): void {
    isMobile.value = mobileMq?.matches ?? false
    isDesktop.value = desktopMq?.matches ?? false
    isTablet.value = !isMobile.value && !isDesktop.value
  }

  onMounted(() => {
    mobileMq = window.matchMedia(`(max-width: ${MOBILE_MAX}px)`)
    desktopMq = window.matchMedia(`(min-width: ${DESKTOP_MIN}px)`)
    sync()
    mobileMq.addEventListener('change', sync)
    desktopMq.addEventListener('change', sync)
  })

  onUnmounted(() => {
    mobileMq?.removeEventListener('change', sync)
    desktopMq?.removeEventListener('change', sync)
  })

  return { isMobile, isTablet, isDesktop }
}
