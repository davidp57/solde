import { nextTick } from 'vue'
import { describe, expect, it, beforeEach } from 'vitest'
import { useDarkMode } from '../../composables/useDarkMode'

describe('useDarkMode', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark-mode')
    // Reset module-level state to false
    const { isDark } = useDarkMode()
    isDark.value = false
  })

  it('returns isDark as false by default', () => {
    const { isDark } = useDarkMode()
    expect(isDark.value).toBe(false)
  })

  it('toggle switches isDark from false to true and back', () => {
    const { isDark, toggle } = useDarkMode()

    toggle()
    expect(isDark.value).toBe(true)

    toggle()
    expect(isDark.value).toBe(false)
  })

  it('toggle adds and removes dark-mode class on documentElement', async () => {
    const { toggle } = useDarkMode()

    toggle()
    await nextTick()
    expect(document.documentElement.classList.contains('dark-mode')).toBe(true)

    toggle()
    await nextTick()
    expect(document.documentElement.classList.contains('dark-mode')).toBe(false)
  })

  it('persists dark mode preference to localStorage', async () => {
    const { toggle } = useDarkMode()

    toggle()
    await nextTick()
    expect(localStorage.getItem('solde-dark-mode')).toBe('true')

    toggle()
    await nextTick()
    expect(localStorage.getItem('solde-dark-mode')).toBe('false')
  })
})
