import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AppFilterSegments from '../../components/ui/AppFilterSegments.vue'

const segments = [
  { key: 'all', label: 'Toutes', count: 47 },
  { key: 'overdue', label: 'En retard', count: 3 },
  { key: 'unpaid', label: 'Impayées', count: 12 },
]

describe('AppFilterSegments', () => {
  it('renders one chip per segment with its count and marks the active one', () => {
    const wrapper = mount(AppFilterSegments, {
      props: { segments, modelValue: 'overdue' },
    })

    const chips = wrapper.findAll('.app-filter-segments__chip')
    expect(chips).toHaveLength(3)
    expect(wrapper.text()).toContain('Toutes')
    expect(wrapper.text()).toContain('47')

    const active = wrapper.find('.app-filter-segments__chip--active')
    expect(active.text()).toContain('En retard')
    expect(active.attributes('aria-pressed')).toBe('true')
  })

  it('emits update:modelValue with the segment key on click', async () => {
    const wrapper = mount(AppFilterSegments, {
      props: { segments, modelValue: 'all' },
    })

    await wrapper.findAll('.app-filter-segments__chip')[2].trigger('click')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['unpaid'])
  })
})
