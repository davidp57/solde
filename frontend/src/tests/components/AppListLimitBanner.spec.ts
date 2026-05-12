import { mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const limitStoreMock = {
  totalCounts: reactive<Record<string, number>>({}),
  isDisabled: vi.fn(() => false),
  disableLimit: vi.fn(),
  enableLimit: vi.fn(),
}

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: Record<string, string | number>) => {
      switch (key) {
        case 'common.list_limit_active_warning':
          return `Limite à ${params?.limit} éléments active — ${params?.total} éléments disponibles sur le serveur.`
        case 'common.list_limit_disable':
          return 'Désactiver la limite'
        case 'common.list_limit_disabled_info':
          return 'Limite désactivée — tous les éléments sont chargés.'
        case 'common.list_limit_enable':
          return 'Réactiver la limite'
        default:
          return key
      }
    },
    n: (value: number) => String(value),
  }),
}))

vi.mock('../../stores/listLimit', () => ({
  useListLimitStore: () => limitStoreMock,
}))

import AppListLimitBanner from '../../components/ui/AppListLimitBanner.vue'

describe('AppListLimitBanner', () => {
  beforeEach(() => {
    limitStoreMock.totalCounts.invoices = 0
    limitStoreMock.isDisabled.mockReturnValue(false)
    vi.clearAllMocks()
  })

  it('does not warn when the server total stays below the configured limit', () => {
    limitStoreMock.totalCounts['invoices-client'] = 201

    const wrapper = mount(AppListLimitBanner, {
      props: {
        viewKey: 'invoices-client',
        fetchedCount: 22,
        limit: 500,
      },
      global: {
        stubs: {
          Message: { template: '<div><slot /></div>' },
        },
      },
    })

    expect(wrapper.text()).not.toContain('Limite à 500 éléments active')
    expect(wrapper.text()).not.toContain('201 éléments disponibles sur le serveur')
  })

  it('warns only when the fetched page reaches the configured limit and more items exist', () => {
    limitStoreMock.totalCounts['invoices-client'] = 1200

    const wrapper = mount(AppListLimitBanner, {
      props: {
        viewKey: 'invoices-client',
        fetchedCount: 500,
        limit: 500,
      },
      global: {
        stubs: {
          Message: { template: '<div><slot /></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('Limite à 500 éléments active')
    expect(wrapper.text()).toContain('1200 éléments disponibles sur le serveur')
  })
})
