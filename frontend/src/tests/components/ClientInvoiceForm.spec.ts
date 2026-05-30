import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

vi.mock('../../api/invoices', () => ({
  createInvoiceApi: vi.fn(),
  updateInvoiceApi: vi.fn(),
  getNextClientInvoiceNumberApi: vi.fn().mockResolvedValue('2026-0001'),
}))

vi.mock('../../api/settings', () => ({
  getSettingsApi: vi.fn().mockResolvedValue({
    default_invoice_due_days: 30,
    default_price_cours: 25,
    default_price_adhesion: 10,
    default_price_autres: 0,
    client_invoice_seq_digits: 4,
    client_invoice_number_template: '{year}-{seq}',
  }),
}))

vi.mock('../../utils/contact', () => ({
  formatContactDisplayName: (c: { last_name: string }) => c.last_name,
}))

const stubs = {
  Button: defineComponent({ props: ['label', 'loading', 'disabled', 'severity', 'icon', 'size', 'text', 'outlined', 'type'], emits: ['click'], setup(_, { slots }) { return () => h('button', {}, slots.default?.()) } }),
  Select: defineComponent({ props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder'], emits: ['update:modelValue'], setup(props, { emit }) { return () => h('select', { onChange: (e: Event) => emit('update:modelValue', (e.target as HTMLSelectElement).value) }) } }),
  InputText: defineComponent({ props: ['modelValue'], emits: ['update:modelValue'], setup(props, { emit }) { return () => h('input', { value: props.modelValue, onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLInputElement).value) }) } }),
  AppDatePicker: defineComponent({ props: ['modelValue'], emits: ['update:modelValue'], setup() { return () => h('div') } }),
}

import ClientInvoiceForm from '../../components/ClientInvoiceForm.vue'

describe('ClientInvoiceForm — normalizeDecimalInput', () => {
  async function mountAndGetPriceInput() {
    const wrapper = mount(ClientInvoiceForm, {
      props: { invoice: null, contacts: [] },
      global: { stubs },
    })
    // Wait for onMounted (addLine + settings fetch)
    await nextTick()
    await nextTick()
    return wrapper
  }

  it('accepte un prix unitaire négatif (ligne de remise)', async () => {
    const wrapper = await mountAndGetPriceInput()
    const priceInput = wrapper.find('.invoice-form__price')
    expect(priceInput.exists()).toBe(true)

    await priceInput.setValue('-4')
    await priceInput.trigger('input')
    await nextTick()

    const grandTotal = wrapper.find('.invoice-form__grand-total')
    // quantity=1, unit_price=-4 → total=-4.00
    expect(grandTotal.text()).toContain('-4.00')
  })

  it("ne réinitialise pas le champ quand l'utilisateur tape uniquement '-'", async () => {
    const wrapper = await mountAndGetPriceInput()
    const priceInput = wrapper.find<HTMLInputElement>('.invoice-form__price')
    expect(priceInput.exists()).toBe(true)

    // Simulate typing just the minus sign (intermediate state)
    await priceInput.setValue('-')
    await priceInput.trigger('input')
    await nextTick()

    // The reactive value should NOT have been updated (still 0 or previous),
    // and the DOM input value must still show "-" (not been overwritten with "0")
    expect(priceInput.element.value).toBe('-')
  })

  it('empêche une quantité négative', async () => {
    const wrapper = await mountAndGetPriceInput()
    const qtyInput = wrapper.find('.invoice-form__quantity')
    expect(qtyInput.exists()).toBe(true)

    await qtyInput.setValue('-3')
    await qtyInput.trigger('input')
    await nextTick()

    // quantity clamped to 0 → total = 0
    const grandTotal = wrapper.find('.invoice-form__grand-total')
    expect(grandTotal.text()).toContain('0.00')
  })

  it('désactive la soumission si le total est négatif', async () => {
    const wrapper = await mountAndGetPriceInput()
    const priceInput = wrapper.find('.invoice-form__price')

    await priceInput.setValue('-100')
    await priceInput.trigger('input')
    await nextTick()

    const error = wrapper.find('.invoice-form__error')
    expect(error.exists()).toBe(true)
  })
})
