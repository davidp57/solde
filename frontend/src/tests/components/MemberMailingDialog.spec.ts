import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))
vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

const mockList = vi.fn()
const mockSend = vi.fn()
vi.mock('@/api/contacts', () => ({
  listActiveClientsApi: (m: number) => mockList(m),
  sendMemberMailingApi: (p: unknown) => mockSend(p),
}))

import MemberMailingDialog from '../../components/contacts/MemberMailingDialog.vue'

const ButtonStub = defineComponent({
  props: ['label', 'disabled', 'loading'],
  emits: ['click'],
  setup(props, { attrs, emit }) {
    return () =>
      h(
        'button',
        { 'data-testid': attrs['data-testid'], disabled: props.disabled, onClick: () => emit('click') },
        props.label,
      )
  },
})
const InputStub = defineComponent({
  props: ['modelValue'],
  emits: ['update:modelValue'],
  setup(props, { attrs, emit }) {
    return () =>
      h('input', {
        'data-testid': attrs['data-testid'],
        value: props.modelValue,
        onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLInputElement).value),
      })
  },
})
const Passthrough = defineComponent({
  setup(_props, { slots }) {
    return () => h('div', slots.default?.())
  },
})

const stubs = {
  Dialog: Passthrough,
  DataTable: Passthrough,
  Column: true,
  Button: ButtonStub,
  InputNumber: InputStub,
  InputText: InputStub,
  Textarea: InputStub,
}

async function flush(): Promise<void> {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
}

describe('MemberMailingDialog', () => {
  it('walks period → selection → compose → send', async () => {
    mockList.mockResolvedValue([
      { id: 1, nom: 'A', prenom: null, email: 'a@x.org', last_activity: '2026-06-01' },
      { id: 2, nom: 'B', prenom: null, email: 'b@x.org', last_activity: '2026-06-02' },
    ])
    mockSend.mockResolvedValue({ sent: 2, failed: [] })

    const wrapper = mount(MemberMailingDialog, { props: { visible: true }, global: { stubs } })

    // Step 1 → load recipients (default 6 months)
    await wrapper.get('[data-testid="mm-load"]').trigger('click')
    await flush()
    expect(mockList).toHaveBeenCalledWith(6)

    // Step 2 → all preselected → go to compose
    await wrapper.get('[data-testid="mm-to-compose"]').trigger('click')
    await nextTick()

    // Step 3 → compose + send
    await wrapper.get('[data-testid="mm-subject"]').setValue('Bonjour')
    await wrapper.get('[data-testid="mm-body"]').setValue('Message')
    await wrapper.get('[data-testid="mm-send"]').trigger('click')
    await flush()

    expect(mockSend).toHaveBeenCalledWith({
      contact_ids: [1, 2],
      subject: 'Bonjour',
      body: 'Message',
    })
    expect(wrapper.emitted('sent')).toBeTruthy()
    expect(wrapper.emitted('update:visible')?.at(-1)).toEqual([false])
  })

  it('does not send when no recipient is selected (Next disabled)', async () => {
    mockList.mockResolvedValue([])
    mockSend.mockClear()
    const wrapper = mount(MemberMailingDialog, { props: { visible: true }, global: { stubs } })

    await wrapper.get('[data-testid="mm-load"]').trigger('click')
    await flush()
    // 0 recipients → Next is disabled
    expect(wrapper.get('[data-testid="mm-to-compose"]').attributes('disabled')).toBeDefined()
  })
})
