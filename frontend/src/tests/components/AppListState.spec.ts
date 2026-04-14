import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: Record<string, string | number>) => {
      switch (key) {
        case 'common.list.count_total':
          return `${params?.count} element(s)`
        case 'common.list.count_filtered':
          return `${params?.shown} sur ${params?.total}`
        case 'common.list.status.loading':
          return 'Chargement en cours'
        case 'common.list.status.empty':
          return 'Aucun element'
        case 'common.list.status.filtered_empty':
          return 'Aucun resultat'
        case 'common.list.status.filtered_scope':
          return 'Filtres actifs'
        case 'common.list.status.full_scope':
          return 'Perimetre complet'
        case 'common.list.search_chip':
          return `Recherche : ${params?.query}`
        case 'common.list.filter_chip':
          return `Filtre : ${params?.label}`
        default:
          return key
      }
    },
  }),
}))

import AppListState from '../../components/ui/AppListState.vue'

describe('AppListState', () => {
  it('renders filtered count and active chips', () => {
    const wrapper = mount(AppListState, {
      props: {
        displayedCount: 3,
        totalCount: 12,
        searchText: 'martin',
        activeFilters: ['Clients'],
      },
    })

    expect(wrapper.text()).toContain('3 sur 12')
    expect(wrapper.text()).toContain('Filtres actifs')
    expect(wrapper.text()).toContain('Recherche : martin')
    expect(wrapper.text()).toContain('Filtre : Clients')
  })

  it('renders loading state before data is available', () => {
    const wrapper = mount(AppListState, {
      props: {
        displayedCount: 0,
        loading: true,
      },
    })

    expect(wrapper.text()).toContain('0 element(s)')
    expect(wrapper.text()).toContain('Chargement en cours')
  })

  it('renders empty filtered state when no result matches active filters', () => {
    const wrapper = mount(AppListState, {
      props: {
        displayedCount: 0,
        totalCount: 8,
        searchText: 'dupont',
      },
    })

    expect(wrapper.text()).toContain('0 sur 8')
    expect(wrapper.text()).toContain('Aucun resultat')
  })

  it('announces state changes politely for assistive technologies', () => {
    const wrapper = mount(AppListState, {
      props: {
        displayedCount: 2,
      },
    })

    expect(wrapper.get('.app-list-state__text').attributes('aria-live')).toBe('polite')
  })
})
