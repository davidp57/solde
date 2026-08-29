import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => ({
    fiscalYears: [
      {
        id: 1,
        name: 'Exercice 2025',
        start_date: '2025-01-01',
        end_date: '2025-12-31',
        status: 'open',
      },
    ],
  }),
}))

vi.mock('../../api/payments', () => ({
  createPayment: vi.fn().mockResolvedValue({ id: 1 }),
  suggestChequeNumber: vi.fn().mockResolvedValue('12345'),
}))

vi.mock('../../api/cash', () => ({
  getCashBalance: vi.fn().mockResolvedValue({ balance: '120.00' }),
}))

const stubs = {
  Dialog: defineComponent({
    props: ['visible'],
    setup(_props, { slots }) {
      return () => h('div', slots.default?.())
    },
  }),
  Button: defineComponent({
    props: ['label', 'loading', 'type'],
    emits: ['click'],
    setup(props, { emit }) {
      return () => h('button', { type: props.type, onClick: () => emit('click') }, props.label)
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
  InputText: defineComponent({
    props: ['modelValue'],
    emits: ['update:modelValue'],
    setup(props) {
      return () => h('input', { value: props.modelValue })
    },
  }),
  InputNumber: defineComponent({
    props: ['modelValue'],
    emits: ['update:modelValue'],
    setup(props) {
      return () => h('input', { type: 'number', value: props.modelValue })
    },
  }),
  Textarea: defineComponent({
    props: ['modelValue'],
    emits: ['update:modelValue'],
    setup() {
      return () => h('textarea')
    },
  }),
  AppDatePicker: defineComponent({
    props: ['modelValue'],
    emits: ['update:modelValue'],
    setup() {
      return () => h('div')
    },
  }),
}

import { createPayment } from '../../api/payments'
import InvoicePaymentDialog from '../../components/invoices/InvoicePaymentDialog.vue'

function makeInvoice(overrides: Record<string, unknown> = {}) {
  return {
    id: 42,
    number: 'F-2026-0001',
    type: 'client',
    contact_id: 7,
    date: '2026-06-01',
    due_date: null,
    label: null,
    description: null,
    reference: null,
    total_amount: '100.00',
    paid_amount: '0.00',
    status: 'sent',
    pdf_path: null,
    file_path: null,
    created_at: '',
    updated_at: '',
    lines: [],
    ...overrides,
  }
}

describe('InvoicePaymentDialog', () => {
  it('records a payment and emits paid on a valid submit', async () => {
    const invoice = makeInvoice()
    const wrapper = mount(InvoicePaymentDialog, {
      props: { visible: false, invoice },
      global: { stubs },
    })

    // Opening the dialog initialises the form (amount = remaining) and suggests a cheque number.
    await wrapper.setProps({ visible: true })
    await flushPromises()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createPayment).toHaveBeenCalledTimes(1)
    expect(createPayment).toHaveBeenCalledWith(
      expect.objectContaining({ invoice_id: 42, contact_id: 7, amount: '100.00' }),
    )
    expect(wrapper.emitted('paid')?.[0]).toEqual([42])
    expect(wrapper.emitted('update:visible')?.at(-1)).toEqual([false])
  })

  it('clears the amount when the method switches to cash, and refuses an empty submit', async () => {
    vi.mocked(createPayment).mockClear()
    const wrapper = mount(InvoicePaymentDialog, {
      props: { visible: false, invoice: makeInvoice({ total_amount: '310.00' }) },
      global: { stubs },
    })
    await wrapper.setProps({ visible: true })
    await flushPromises()

    // Cheque is the default: the balance is still proposed.
    expect((wrapper.find('input[type="number"]').element as HTMLInputElement).value).toBe('310')

    await wrapper.find('select').setValue('especes')
    await flushPromises()

    expect((wrapper.find('input[type="number"]').element as HTMLInputElement).value).toBe('')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createPayment).not.toHaveBeenCalled()
  })

  it('reports the remaining amount on demand for a cash payment', async () => {
    vi.mocked(createPayment).mockClear()
    const wrapper = mount(InvoicePaymentDialog, {
      props: { visible: false, invoice: makeInvoice({ total_amount: '270.00' }) },
      global: { stubs },
    })
    await wrapper.setProps({ visible: true })
    await flushPromises()
    await wrapper.find('select').setValue('especes')
    await flushPromises()

    const applyButton = wrapper
      .findAll('button')
      .find((button) => button.text() === 'payments.apply_remaining')
    expect(applyButton).toBeDefined()

    await applyButton!.trigger('click')
    await flushPromises()

    expect((wrapper.find('input[type="number"]').element as HTMLInputElement).value).toBe('270')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createPayment).toHaveBeenCalledWith(
      expect.objectContaining({ amount: '270.00', method: 'especes' }),
    )
  })

  it('keeps the cheque pre-fill untouched', async () => {
    const wrapper = mount(InvoicePaymentDialog, {
      props: { visible: false, invoice: makeInvoice({ total_amount: '310.00' }) },
      global: { stubs },
    })
    await wrapper.setProps({ visible: true })
    await flushPromises()

    expect(wrapper.text()).not.toContain('payments.apply_remaining')
    expect(wrapper.text()).not.toContain('payments.cash_amount_hint')
  })

  it('does not record a payment when the remaining amount is zero', async () => {
    vi.mocked(createPayment).mockClear()
    const invoice = makeInvoice({ total_amount: '100.00', paid_amount: '100.00' })
    const wrapper = mount(InvoicePaymentDialog, {
      props: { visible: false, invoice },
      global: { stubs },
    })

    await wrapper.setProps({ visible: true })
    await flushPromises()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createPayment).not.toHaveBeenCalled()
  })
})
