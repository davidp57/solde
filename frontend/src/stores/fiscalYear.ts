import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import {
  getCurrentFiscalYearApi,
  listFiscalYearsApi,
  type FiscalYearRead,
} from '../api/accounting'

const STORAGE_KEY = 'selected_fiscal_year_id'
const STORAGE_SOURCE_KEY = 'selected_fiscal_year_source'
const USER_SELECTION_SOURCE = 'user'

export const useFiscalYearStore = defineStore('fiscalYear', () => {
  const fiscalYears = ref<FiscalYearRead[]>([])
  const selectedFiscalYearId = ref<number | undefined>()
  const loading = ref(false)
  const initialized = ref(false)
  let initPromise: Promise<void> | null = null

  const selectedFiscalYear = computed(() =>
    fiscalYears.value.find((fiscalYear) => fiscalYear.id === selectedFiscalYearId.value),
  )

  function persistSelection(id: number | undefined): void {
    if (id === undefined) {
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem(STORAGE_SOURCE_KEY)
      return
    }
    localStorage.setItem(STORAGE_KEY, String(id))
    localStorage.setItem(STORAGE_SOURCE_KEY, USER_SELECTION_SOURCE)
  }

  function restoreStoredSelection(): number | undefined {
    if (localStorage.getItem(STORAGE_SOURCE_KEY) !== USER_SELECTION_SOURCE) {
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem(STORAGE_SOURCE_KEY)
      return undefined
    }
    const rawValue = localStorage.getItem(STORAGE_KEY)
    if (!rawValue) return undefined
    const parsedValue = Number(rawValue)
    return Number.isInteger(parsedValue) ? parsedValue : undefined
  }

  function setSelectedFiscalYear(id: number | undefined): void {
    selectedFiscalYearId.value = id
    persistSelection(id)
  }

  async function initialize(force = false): Promise<void> {
    if (!force && initialized.value) return
    if (force) {
      initialized.value = false
      initPromise = null
    }
    if (initPromise) return initPromise

    initPromise = (async () => {
      loading.value = true
      try {
        const storedSelection = restoreStoredSelection()
        const [years, currentFiscalYear] = await Promise.all([
          listFiscalYearsApi(),
          getCurrentFiscalYearApi(),
        ])
        fiscalYears.value = years

        const validSelection = [
          selectedFiscalYearId.value,
          storedSelection,
          currentFiscalYear?.id,
          years.find((fiscalYear) => fiscalYear.status === 'open')?.id,
          years[0]?.id,
        ].find(
          (candidateId) =>
            candidateId !== undefined
            && years.some((fiscalYear) => fiscalYear.id === candidateId),
        )

        selectedFiscalYearId.value = validSelection
        initialized.value = true
      } finally {
        loading.value = false
        initPromise = null
      }
    })()

    return initPromise
  }

  return {
    fiscalYears,
    selectedFiscalYearId,
    selectedFiscalYear,
    loading,
    initialized,
    initialize,
    refresh: () => initialize(true),
    setSelectedFiscalYear,
  }
})