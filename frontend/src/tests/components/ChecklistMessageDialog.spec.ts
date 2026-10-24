import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { defineComponent, h } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

const addChecklistMessage = vi.fn()
const deleteChecklistMessage = vi.fn()
const listMyChecklistMessages = vi.fn()

vi.mock('@/api/checklist', () => ({
  addChecklistMessage: (...args: unknown[]) => addChecklistMessage(...args),
  deleteChecklistMessage: (...args: unknown[]) => deleteChecklistMessage(...args),
  listMyChecklistMessages: (...args: unknown[]) => listMyChecklistMessages(...args),
  getCurrentChecklist: vi.fn(),
}))

import ChecklistMessageDialog from '../../components/checklist/ChecklistMessageDialog.vue'

const passthrough = defineComponent({
  setup(_props, { slots }) {
    return () => h('div', slots.default?.())
  },
})

const stubs = {
  Dialog: passthrough,
  Textarea: defineComponent({
    props: ['modelValue'],
    emits: ['update:modelValue'],
    setup(props, { emit }) {
      return () =>
        h('textarea', {
          value: props.modelValue,
          onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLTextAreaElement).value),
        })
    },
  }),
  Button: defineComponent({
    props: ['label', 'ariaLabel', 'type', 'disabled'],
    emits: ['click'],
    setup(props, { emit }) {
      return () =>
        h(
          'button',
          {
            type: props.type ?? 'button',
            disabled: props.disabled,
            'aria-label': props.ariaLabel,
            onClick: () => emit('click'),
          },
          props.label,
        )
    },
  }),
}

function message(id: number, content: string) {
  return {
    id,
    content,
    author: 'sec',
    created_at: '2026-10-20T10:00:00',
    checked: false,
    checked_by: null,
    checked_at: null,
    late: false,
  }
}

describe('ChecklistMessageDialog', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('lists the author’s waiting messages when opened', async () => {
    listMyChecklistMessages.mockResolvedValue([message(1, 'Facture EDF')])

    const wrapper = mount(ChecklistMessageDialog, { props: { visible: true }, global: { stubs } })
    await flushPromises()

    expect(wrapper.text()).toContain('Facture EDF')
  })

  it('sends the draft and adds it to the list', async () => {
    listMyChecklistMessages.mockResolvedValue([])
    addChecklistMessage.mockResolvedValue(message(2, 'Chèque Dupont'))
    const wrapper = mount(ChecklistMessageDialog, { props: { visible: true }, global: { stubs } })
    await flushPromises()

    await wrapper.find('textarea').setValue('Chèque Dupont')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(addChecklistMessage).toHaveBeenCalledWith('Chèque Dupont')
    expect(wrapper.text()).toContain('Chèque Dupont')
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('')
  })

  it('withdraws a message', async () => {
    listMyChecklistMessages.mockResolvedValue([message(3, 'À retirer')])
    deleteChecklistMessage.mockResolvedValue(undefined)
    const wrapper = mount(ChecklistMessageDialog, { props: { visible: true }, global: { stubs } })
    await flushPromises()

    await wrapper.find('button[aria-label="checklist.messages.withdraw"]').trigger('click')
    await flushPromises()

    expect(deleteChecklistMessage).toHaveBeenCalledWith(3)
    expect(wrapper.text()).not.toContain('À retirer')
  })
})
