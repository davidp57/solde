import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  closeChecklistSession,
  getCurrentChecklist,
  openChecklistSession,
  setChecklistStep,
  type ChecklistSessionDetail,
} from '@/api/checklist'

/**
 * The monthly bookkeeping session.
 *
 * Shared between the header button — which shows the progress — and the dialog,
 * so ticking a step updates both without a second round trip.
 */
export const useChecklistStore = defineStore('checklist', () => {
  const detail = ref<ChecklistSessionDetail | null>(null)
  const suggestedPeriod = ref('')
  const totalCount = ref(0)
  const loading = ref(false)
  const dialogVisible = ref(false)

  const session = computed(() => detail.value?.session ?? null)
  const steps = computed(() => detail.value?.steps ?? [])
  const signals = computed(() => detail.value?.signals ?? {})
  const checkedCount = computed(() => steps.value.filter((s) => s.checked).length)
  const isOpen = computed(() => session.value?.status === 'open')
  /** Steps the previous session was closed without — shown as a banner when any.  */
  const lateSteps = computed(() => steps.value.filter((s) => s.carried_over && !s.checked))

  function apply(next: ChecklistSessionDetail): void {
    detail.value = next
    totalCount.value = next.steps.length
  }

  async function load(): Promise<void> {
    loading.value = true
    try {
      const current = await getCurrentChecklist()
      detail.value = current.detail
      suggestedPeriod.value = current.suggested_period
      totalCount.value = current.total_count
    } finally {
      loading.value = false
    }
  }

  async function start(period?: string): Promise<void> {
    apply(await openChecklistSession(period ?? suggestedPeriod.value))
  }

  async function toggle(stepKey: string, checked: boolean): Promise<void> {
    if (!session.value) return
    apply(await setChecklistStep(session.value.id, stepKey, checked))
  }

  async function close(): Promise<void> {
    if (!session.value) return
    await closeChecklistSession(session.value.id)
    await load()
  }

  return {
    detail,
    suggestedPeriod,
    totalCount,
    loading,
    dialogVisible,
    session,
    steps,
    signals,
    checkedCount,
    isOpen,
    lateSteps,
    load,
    start,
    toggle,
    close,
  }
})
