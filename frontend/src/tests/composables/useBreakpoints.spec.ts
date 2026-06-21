import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'
import { useBreakpoints } from '../../composables/useBreakpoints'

type Listener = (event: { matches: boolean }) => void

const realMatchMedia = window.matchMedia

/**
 * Installs a controllable matchMedia: the `max-width` query maps to "mobile",
 * the `min-width` query to "desktop". `set()` flips a query and notifies its
 * registered change listeners, emulating a viewport resize.
 */
function installMatchMedia(initial: { mobile: boolean; desktop: boolean }) {
  const state = { ...initial }
  const listeners: Record<'mobile' | 'desktop', Listener[]> = { mobile: [], desktop: [] }
  window.matchMedia = ((query: string) => {
    const key: 'mobile' | 'desktop' = query.includes('max-width') ? 'mobile' : 'desktop'
    return {
      get matches() {
        return state[key]
      },
      media: query,
      onchange: null,
      addEventListener: (_: string, cb: Listener) => listeners[key].push(cb),
      removeEventListener: (_: string, cb: Listener) => {
        listeners[key] = listeners[key].filter((l) => l !== cb)
      },
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    } as unknown as MediaQueryList
  }) as typeof window.matchMedia
  return {
    set(next: Partial<typeof state>) {
      for (const key of ['mobile', 'desktop'] as const) {
        if (next[key] !== undefined && next[key] !== state[key]) {
          state[key] = next[key] as boolean
          listeners[key].forEach((cb) => cb({ matches: state[key] }))
        }
      }
    },
  }
}

const Probe = defineComponent({
  setup: () => useBreakpoints(),
  template: '<div />',
})

afterEach(() => {
  window.matchMedia = realMatchMedia
})

describe('useBreakpoints', () => {
  it('reports desktop when the min-width query matches', () => {
    installMatchMedia({ mobile: false, desktop: true })
    const wrapper = mount(Probe)
    expect(wrapper.vm.isDesktop).toBe(true)
    expect(wrapper.vm.isTablet).toBe(false)
    expect(wrapper.vm.isMobile).toBe(false)
  })

  it('reports tablet when neither query matches', () => {
    installMatchMedia({ mobile: false, desktop: false })
    const wrapper = mount(Probe)
    expect(wrapper.vm.isTablet).toBe(true)
    expect(wrapper.vm.isMobile).toBe(false)
    expect(wrapper.vm.isDesktop).toBe(false)
  })

  it('reports mobile when the max-width query matches', () => {
    installMatchMedia({ mobile: true, desktop: false })
    const wrapper = mount(Probe)
    expect(wrapper.vm.isMobile).toBe(true)
    expect(wrapper.vm.isTablet).toBe(false)
  })

  it('reacts to a viewport change from desktop to mobile', async () => {
    const mm = installMatchMedia({ mobile: false, desktop: true })
    const wrapper = mount(Probe)
    expect(wrapper.vm.isDesktop).toBe(true)

    mm.set({ desktop: false, mobile: true })
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.isMobile).toBe(true)
    expect(wrapper.vm.isTablet).toBe(false)
    expect(wrapper.vm.isDesktop).toBe(false)
  })
})
