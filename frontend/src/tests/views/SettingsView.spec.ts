import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

const getSettingsApi = vi.fn().mockResolvedValue({
  association_name: 'Asso',
  association_siret: '123',
  association_address: 'addr',
  payment_iban: null,
  payment_bic: null,
  payment_check_payee: null,
  bank_account_courant_acctid: null,
  bank_account_epargne_acctid: null,
  list_default_limit: 500,
  fiscal_year_start_month: 8,
  default_invoice_due_days: 30,
  client_invoice_seq_digits: 3,
  client_invoice_number_template: '{year}-{seq}',
  supplier_invoice_number_template: 'FF-%Y',
  cheque_number_template: '{date}.{seq}',
  default_price_cours: null,
  default_price_adhesion: null,
  default_price_autres: null,
  smtp_host: null,
  smtp_port: 587,
  smtp_user: null,
  smtp_from_email: null,
  smtp_use_tls: true,
  smtp_bcc: null,
  email_subject_template: null,
  email_body_template: null,
})
const updateSettingsApi = vi.fn().mockResolvedValue({})

vi.mock('@/api/settings', () => ({
  getSettingsApi: () => getSettingsApi(),
  updateSettingsApi: (p: unknown) => updateSettingsApi(p),
}))

const SlotStub = defineComponent({
  setup(_props, { slots }) {
    return () => h('div', [slots.default?.(), slots.control?.()])
  },
})

const stubs = {
  AppPage: SlotStub,
  AppPageHeader: SlotStub,
  AppPanel: SlotStub,
  AppSettingRow: SlotStub,
  Tabs: SlotStub,
  TabList: SlotStub,
  Tab: SlotStub,
  SettingsSaveBar: true,
  SettingsSystemOpeningPanel: true,
  SettingsChatPanel: true,
  SettingsDangerZonePanel: true,
  InputText: true,
  InputNumber: true,
  Textarea: true,
  Select: true,
  Password: true,
  ToggleSwitch: true,
  Tag: true,
  Message: true,
}

import SettingsView from '../../views/SettingsView.vue'

describe('SettingsView', () => {
  it('loads settings and renders the four tabs', async () => {
    const wrapper = mount(SettingsView, { global: { stubs } })
    await Promise.resolve()
    await nextTick()

    expect(getSettingsApi).toHaveBeenCalled()
    const text = wrapper.text()
    expect(text).toContain('settings.tab_organisation')
    expect(text).toContain('settings.tab_comptabilite')
    expect(text).toContain('settings.tab_communication')
    expect(text).toContain('settings.tab_danger')
  })
})
