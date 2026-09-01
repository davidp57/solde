import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const getCurrentChecklist = vi.fn()
const openChecklistSession = vi.fn()
const setChecklistStep = vi.fn()
const closeChecklistSession = vi.fn()

vi.mock('@/api/checklist', () => ({
  getCurrentChecklist: (...args: unknown[]) => getCurrentChecklist(...args),
  openChecklistSession: (...args: unknown[]) => openChecklistSession(...args),
  setChecklistStep: (...args: unknown[]) => setChecklistStep(...args),
  closeChecklistSession: (...args: unknown[]) => closeChecklistSession(...args),
}))

import { useChecklistStore } from '../../stores/checklist'

function step(key: string, overrides: Record<string, unknown> = {}) {
  return {
    key,
    block: 'statement',
    external: false,
    signal: null,
    route: null,
    checked: false,
    checked_by: null,
    checked_at: null,
    carried_over: false,
    ...overrides,
  }
}

function detail(steps: ReturnType<typeof step>[]) {
  return {
    session: {
      id: 1,
      period_type: 'monthly',
      period: '2026-09',
      status: 'open',
      opened_at: '2026-09-30T10:00:00',
      opened_by: 'zip',
      closed_at: null,
      closed_by: null,
    },
    steps,
    signals: {},
  }
}

describe('checklist store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('reports no open session when there is none', async () => {
    getCurrentChecklist.mockResolvedValue({
      detail: null,
      suggested_period: '2026-09',
      checked_count: 0,
      total_count: 17,
    })
    const store = useChecklistStore()

    await store.load()

    expect(store.isOpen).toBe(false)
    expect(store.suggestedPeriod).toBe('2026-09')
    // The header still knows how long the checklist is, to offer starting one.
    expect(store.totalCount).toBe(17)
  })

  it('counts the ticked steps', async () => {
    getCurrentChecklist.mockResolvedValue({
      detail: detail([step('a', { checked: true }), step('b'), step('c', { checked: true })]),
      suggested_period: '2026-09',
      checked_count: 2,
      total_count: 3,
    })
    const store = useChecklistStore()

    await store.load()

    expect(store.isOpen).toBe(true)
    expect(store.checkedCount).toBe(2)
  })

  it('surfaces only the steps still late', async () => {
    getCurrentChecklist.mockResolvedValue({
      detail: detail([
        step('late_and_done', { carried_over: true, checked: true }),
        step('late', { carried_over: true }),
        step('plain'),
      ]),
      suggested_period: '2026-09',
      checked_count: 1,
      total_count: 3,
    })
    const store = useChecklistStore()

    await store.load()

    expect(store.lateSteps.map((s) => s.key)).toEqual(['late'])
  })

  it('applies the session returned when a step is ticked', async () => {
    getCurrentChecklist.mockResolvedValue({
      detail: detail([step('reconcile')]),
      suggested_period: '2026-09',
      checked_count: 0,
      total_count: 1,
    })
    setChecklistStep.mockResolvedValue(detail([step('reconcile', { checked: true })]))
    const store = useChecklistStore()
    await store.load()

    await store.toggle('reconcile', true)

    expect(setChecklistStep).toHaveBeenCalledWith(1, 'reconcile', true)
    expect(store.checkedCount).toBe(1)
  })

  it('does nothing when ticking without an open session', async () => {
    const store = useChecklistStore()

    await store.toggle('reconcile', true)

    expect(setChecklistStep).not.toHaveBeenCalled()
  })

  it('reloads after closing, since the session is gone', async () => {
    getCurrentChecklist
      .mockResolvedValueOnce({
        detail: detail([step('reconcile')]),
        suggested_period: '2026-09',
        checked_count: 0,
        total_count: 1,
      })
      .mockResolvedValueOnce({
        detail: null,
        suggested_period: '2026-10',
        checked_count: 0,
        total_count: 1,
      })
    closeChecklistSession.mockResolvedValue({})
    const store = useChecklistStore()
    await store.load()

    await store.close()

    expect(closeChecklistSession).toHaveBeenCalledWith(1)
    expect(store.isOpen).toBe(false)
    expect(store.suggestedPeriod).toBe('2026-10')
  })
})
