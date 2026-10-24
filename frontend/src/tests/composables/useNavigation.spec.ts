import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useNavigation } from '../../composables/useNavigation'
import { useAuthStore } from '../../stores/auth'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

const Probe = defineComponent({
  setup: () => useNavigation(),
  template: '<div />',
})

function mountWithRole(role: 'readonly' | 'secretaire' | 'tresorier' | 'admin') {
  const auth = useAuthStore()
  auth.user = {
    id: 1,
    username: role,
    email: `${role}@example.com`,
    role,
    is_active: true,
    must_change_password: false,
    created_at: '2025-01-01T00:00:00',
  }
  return mount(Probe)
}

describe('useNavigation — bottomNavItems', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('promotes the four priority destinations for a gestionnaire', () => {
    const wrapper = mountWithRole('secretaire')
    expect(wrapper.vm.bottomNavItems.map((i) => i.to)).toEqual([
      '/dashboard',
      '/invoices/client',
      '/bank',
      '/contacts',
    ])
  })

  it('falls back to what is reachable for a readonly user (help excluded)', () => {
    const wrapper = mountWithRole('readonly')
    // Documents are readable by every role, so they survive the fallback; help never does.
    expect(wrapper.vm.bottomNavItems.map((i) => i.to)).toEqual(['/dashboard', '/documents'])
  })

  it('never exceeds four items', () => {
    const wrapper = mountWithRole('admin')
    expect(wrapper.vm.bottomNavItems.length).toBeLessThanOrEqual(4)
  })
})
