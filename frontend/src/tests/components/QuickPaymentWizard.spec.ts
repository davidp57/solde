import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h, ref } from 'vue'
import { describe, expect, it, vi, beforeEach } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => ({ fiscalYears: [] }),
}))

vi.mock('../../composables/useBreakpoints', () => ({
  useBreakpoints: () => ({ isMobile: ref(true) }),
}))

vi.mock('../../api/payments', () => ({
  createPayment: vi.fn().mockResolvedValue({ id: 1 }),
  suggestChequeNumber: vi.fn().mockResolvedValue('12345'),
}))

vi.mock('../../api/cash', () => ({
  getCashBalance: vi.fn().mockResolvedValue({ balance: '120.00' }),
}))

vi.mock('../../api/contacts', () => ({
  listContactsApi: vi.fn().mockResolvedValue([{ id: 7, nom: 'Dupont', prenom: 'Marie' }]),
}))

vi.mock('../../api/invoices', () => ({
  listInvoicesApi: vi.fn().mockResolvedValue([
    {
      id: 42,
      number: '2026-0135',
      type: 'client',
      contact_id: 7,
      date: '2026-08-01',
      due_date: '2026-08-31',
      total_amount: '310.00',
      paid_amount: '0.00',
      status: 'sent',
      lines: [],
    },
  ]),
}))

const stubs = {
  Dialog: defineComponent({
    props: ['visible'],
    setup(_props, { slots }) {
      return () => h('div', slots.default?.())
    },
  }),
  Button: defineComponent({
    props: ['label', 'loading', 'type', 'disabled'],
    emits: ['click'],
    setup(props, { emit }) {
      return () =>
        h(
          'button',
          { type: props.type, disabled: props.disabled, onClick: () => emit('click') },
          props.label,
        )
    },
  }),
  Select: defineComponent({
    props: ['modelValue', 'options'],
    emits: ['update:modelValue'],
    setup(props, { emit }) {
      return () =>
        h(
          'select',
          {
            value: props.modelValue,
            onChange: (event: Event) =>
              emit('update:modelValue', (event.target as HTMLSelectElement).value),
          },
          (props.options ?? []).map((option: { label: string; value: string }) =>
            h('option', { value: option.value }, option.label),
          ),
        )
    },
  }),
  InputNumber: defineComponent({
    props: ['modelValue'],
    emits: ['update:modelValue'],
    setup(props) {
      return () => h('input', { type: 'number', value: props.modelValue })
    },
  }),
  InputText: defineComponent({
    props: ['modelValue'],
    setup(props) {
      return () => h('input', { value: props.modelValue })
    },
  }),
  Textarea: defineComponent({
    setup() {
      return () => h('textarea')
    },
  }),
  DataTable: defineComponent({
    setup() {
      return () => h('div')
    },
  }),
  Column: defineComponent({
    setup() {
      return () => h('div')
    },
  }),
  AppDatePicker: defineComponent({
    props: ['modelValue'],
    setup() {
      return () => h('div')
    },
  }),
  AppFiscalYearDateWarning: defineComponent({
    props: ['date'],
    setup() {
      return () => h('div')
    },
  }),
  AppMobileCardList: defineComponent({
    props: ['items'],
    setup(props, { slots }) {
      return () =>
        h(
          'div',
          (props.items ?? []).map((item: unknown) => h('div', slots.card?.({ item }))),
        )
    },
  }),
}

import { createPayment } from '../../api/payments'
import QuickPaymentWizard from '../../components/QuickPaymentWizard.vue'

async function openOnPaymentStep() {
  const wrapper = mount(QuickPaymentWizard, {
    props: { visible: false },
    global: { stubs },
  })
  await wrapper.setProps({ visible: true })
  await flushPromises()

  const chooseButton = wrapper
    .findAll('button')
    .find((button) => button.text() === 'dashboard.payment_wizard.choose')
  await chooseButton!.trigger('click')
  await flushPromises()

  return wrapper
}

describe('QuickPaymentWizard', () => {
  beforeEach(() => {
    vi.mocked(createPayment).mockClear()
  })

  it('proposes the invoice balance for a cheque', async () => {
    const wrapper = await openOnPaymentStep()

    expect((wrapper.find('input[type="number"]').element as HTMLInputElement).value).toBe('310')
    expect(wrapper.text()).not.toContain('payments.cash_amount_hint')
  })

  it('clears the amount and blocks saving when the method switches to cash', async () => {
    const wrapper = await openOnPaymentStep()

    await wrapper.find('select').setValue('especes')
    await flushPromises()

    expect((wrapper.find('input[type="number"]').element as HTMLInputElement).value).toBe('')
    expect(wrapper.text()).toContain('payments.cash_amount_hint')

    const saveButton = wrapper.findAll('button').find((button) => button.text() === 'common.save')
    expect(saveButton!.attributes('disabled')).toBeDefined()

    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(createPayment).not.toHaveBeenCalled()
  })

  it('reports the balance on demand and records the payment', async () => {
    const wrapper = await openOnPaymentStep()
    await wrapper.find('select').setValue('especes')
    await flushPromises()

    const applyButton = wrapper
      .findAll('button')
      .find((button) => button.text() === 'payments.apply_remaining')
    await applyButton!.trigger('click')
    await flushPromises()

    expect((wrapper.find('input[type="number"]').element as HTMLInputElement).value).toBe('310')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createPayment).toHaveBeenCalledWith(
      expect.objectContaining({ invoice_id: 42, amount: '310.00', method: 'especes' }),
    )
  })
})
