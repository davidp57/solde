import { mount } from '@vue/test-utils'
import { h } from 'vue'
import { describe, expect, it } from 'vitest'

import AppSettingRow from '../../components/ui/AppSettingRow.vue'

describe('AppSettingRow', () => {
  it('renders label, description, warning and the control slot', () => {
    const wrapper = mount(AppSettingRow, {
      props: {
        label: 'Chiffres de la séquence',
        description: 'Nombre de chiffres du compteur',
        warning: 'Impacte la numérotation future',
        htmlFor: 'seq',
      },
      slots: { control: () => h('input', { id: 'seq', class: 'the-control' }) },
    })

    expect(wrapper.find('.app-setting-row__label').text()).toContain('Chiffres de la séquence')
    expect(wrapper.find('.app-setting-row__description').text()).toContain('compteur')
    expect(wrapper.find('.app-setting-row__warning').text()).toContain('numérotation future')
    expect(wrapper.find('.the-control').exists()).toBe(true)
    // label is associated with the control for accessibility
    expect(wrapper.find('label').attributes('for')).toBe('seq')
  })

  it('omits optional parts when not provided', () => {
    const wrapper = mount(AppSettingRow, {
      props: { label: 'Nom' },
      slots: { control: () => h('input') },
    })
    expect(wrapper.find('.app-setting-row__description').exists()).toBe(false)
    expect(wrapper.find('.app-setting-row__warning').exists()).toBe(false)
    // no htmlFor → plain span, no <label for>
    expect(wrapper.find('label').exists()).toBe(false)
  })
})
