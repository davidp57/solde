import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import NavMenu from '@/components/NavMenu.vue'
import { useAuthStore } from '@/stores/auth'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('@/composables/useDarkMode', () => ({
  useDarkMode: () => ({
    isDark: { value: false },
  }),
}))

function mountNavMenu() {
  return mount(NavMenu, {
    global: {
      stubs: {
        RouterLink: {
          props: ['to'],
          template: '<a :href="to"><slot /></a>',
        },
      },
    },
  })
}

describe('NavMenu', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('shows only the management section for a gestionnaire', () => {
    const auth = useAuthStore()
    auth.user = {
      id: 1,
      username: 'gestionnaire',
      email: 'gestionnaire@example.com',
      role: 'secretaire',
      is_active: true,
      must_change_password: false,
      created_at: '2025-01-01T00:00:00',
    }

    const wrapper = mountNavMenu()
    const text = wrapper.text()
    const links = wrapper.findAll('a').map((link) => link.text())

    expect(text).toContain('nav.section_home')
    expect(text).toContain('nav.section_management')
    expect(text).toContain('nav.dashboard')
    expect(text).toContain('nav.bank')
    expect(text).not.toContain('nav.section_accounting')
    expect(text).not.toContain('nav.accounting_journal')
    expect(text).not.toContain('nav.section_administration')
    expect(links).toEqual([
      'nav.dashboard',
      'nav.contacts',
      'nav.invoices_client',
      'nav.invoices_supplier',
      'nav.payments',
      'nav.bank',
      'nav.cash',
    ])
  })

  it('shows management and accounting sections for a comptable', () => {
    const auth = useAuthStore()
    auth.user = {
      id: 2,
      username: 'comptable',
      email: 'comptable@example.com',
      role: 'tresorier',
      is_active: true,
      must_change_password: false,
      created_at: '2025-01-01T00:00:00',
    }

    const wrapper = mountNavMenu()
    const text = wrapper.text()
    const links = wrapper.findAll('a').map((link) => link.text())

    expect(text).toContain('nav.section_home')
    expect(text).toContain('nav.section_management')
    expect(text).toContain('nav.section_accounting')
    expect(text).toContain('nav.accounting_journal')
    expect(text).not.toContain('nav.section_administration')
    expect(links).toEqual([
      'nav.dashboard',
      'nav.contacts',
      'nav.invoices_client',
      'nav.invoices_supplier',
      'nav.payments',
      'nav.bank',
      'nav.cash',
      'nav.accounting_balance',
      'nav.accounting_journal',
      'nav.accounting_ledger',
      'nav.salaries',
      'nav.accounting_bilan',
      'nav.accounting_resultat',
      'nav.accounting_fiscal_years',
      'nav.accounting_accounts',
      'nav.accounting_rules',
    ])
  })

  it('shows imports only inside the administration section for an admin', () => {
    const auth = useAuthStore()
    auth.user = {
      id: 4,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      must_change_password: false,
      created_at: '2025-01-01T00:00:00',
    }

    const wrapper = mountNavMenu()
    const text = wrapper.text()
    const links = wrapper.findAll('a').map((link) => link.text())

    expect(text).toContain('nav.section_administration')
    expect(links).toContain('nav.import_excel')
    expect(links).toContain('nav.import_history')
    expect(links).toContain('nav.users')
    expect(links).toContain('nav.settings')
  })

  it('shows only the home section for a readonly user', () => {
    const auth = useAuthStore()
    auth.user = {
      id: 3,
      username: 'readonly',
      email: 'readonly@example.com',
      role: 'readonly',
      is_active: true,
      must_change_password: false,
      created_at: '2025-01-01T00:00:00',
    }

    const wrapper = mountNavMenu()
    const text = wrapper.text()
    const links = wrapper.findAll('a').map((link) => link.text())

    expect(text).toContain('nav.section_home')
    expect(text).toContain('nav.dashboard')
    expect(text).not.toContain('nav.section_management')
    expect(text).not.toContain('nav.section_accounting')
    expect(text).not.toContain('nav.section_administration')
    expect(links).toEqual(['nav.dashboard'])
  })
})
