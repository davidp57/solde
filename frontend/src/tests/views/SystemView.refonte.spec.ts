import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

vi.mock('@/api/settings', () => ({
  getSystemInfoApi: vi.fn().mockResolvedValue({
    app_version: '1.7.5',
    db_size_bytes: 19_300_000,
    started_at: '2026-06-14T08:12:00',
  }),
  listBackupsApi: vi.fn().mockResolvedValue([]),
  getAuditLogsApi: vi.fn().mockResolvedValue([]),
  getLogsApi: vi.fn().mockResolvedValue([]),
  createBackupApi: vi.fn(),
  restoreBackupApi: vi.fn(),
}))

vi.mock('@/api/backup', () => ({
  testRestoreBackup: vi.fn(),
}))

vi.mock('@/api/payments', () => ({
  listPayments: vi.fn().mockResolvedValue([
    { id: 1, date: '2026-05-01', amount: '120.00', contact_name: 'Dupont', invoice_number: 'F-1', contact_id: 3 },
    { id: 2, date: '2026-05-02', amount: '80.00', contact_name: 'Martin', invoice_number: 'F-2', contact_id: 4 },
  ]),
  fixDepositDate: vi.fn(),
}))

const ContainerStub = defineComponent({
  setup(_props, { slots }) {
    return () => h('div', [slots.default?.(), slots.title?.()])
  },
})

const stubs = {
  AppPage: ContainerStub,
  AppPageHeader: ContainerStub,
  AppPanel: ContainerStub,
  SettingsBackupPanel: true,
  Dialog: true,
  DataTable: true,
  Column: true,
  Button: true,
  InputText: true,
  Message: true,
  MultiSelect: true,
  AppDatePicker: true,
  RouterLink: true,
  Tabs: true,
  TabList: true,
  Tab: true,
}

import SystemView from '../../views/SystemView.vue'

async function flush() {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
  await nextTick()
}

describe('SystemView — refonte', () => {
  it('shows the status banner and surfaces anomalies in a worklist', async () => {
    const wrapper = mount(SystemView, { global: { stubs } })
    await flush()

    expect(wrapper.text()).toContain('system.status_ok')
    expect(wrapper.text()).toContain('1.7.5')

    expect(wrapper.find('.app-worklist').exists()).toBe(true)
    expect(wrapper.text()).toContain('system.anomaly_cheques')
    // One anomaly type listed, with 2 affected payments shown as its value.
    expect(wrapper.find('.app-worklist__count').text()).toBe('1')
    expect(wrapper.find('.app-worklist__value').text()).toBe('2')
  })
})
