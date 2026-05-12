/**
 * Store managing the per-view, per-session list limit toggle.
 *
 * - systemLimit: the default limit configured in app settings (0 = fetch up to API max).
 * - Per-view override stored in sessionStorage so it resets on tab/browser close.
 * - totalCounts: map of viewKey → total items available on the server (from X-Total-Count header).
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { getSettingsApi } from '../api/settings'

const SESSION_KEY_PREFIX = 'list_limit_disabled_'
const DEFAULT_FALLBACK_LIMIT = 500
const MAX_LIST_FETCH_LIMIT = 5000

export const useListLimitStore = defineStore('listLimit', () => {
  const systemLimit = ref<number>(DEFAULT_FALLBACK_LIMIT)
  const loaded = ref(false)

  // Map viewKey -> total count from server (populated after each list fetch)
  const totalCounts = ref<Record<string, number>>({})

  // Map viewKey -> boolean override read from sessionStorage
  const disabledViews = ref<Set<string>>(new Set())

  /** Load the system limit from settings (idempotent). */
  async function init(): Promise<void> {
    if (loaded.value) return
    try {
      const settings = await getSettingsApi()
      systemLimit.value = settings.list_default_limit
    } catch {
      // keep fallback
    }
    loaded.value = true
    // Restore session overrides from sessionStorage
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i)
      if (key?.startsWith(SESSION_KEY_PREFIX)) {
        const viewKey = key.slice(SESSION_KEY_PREFIX.length)
        disabledViews.value.add(viewKey)
      }
    }
  }

  /** Return the effective limit for a given view (0 means no limit applied). */
  function effectiveLimit(viewKey: string): number {
    if (disabledViews.value.has(viewKey)) return 0
    return systemLimit.value
  }

  /** Return the request limit sent to APIs, honoring the backend hard cap. */
  function requestLimit(viewKey: string): number {
    const limit = effectiveLimit(viewKey)
    return limit > 0 ? limit : MAX_LIST_FETCH_LIMIT
  }

  /** Whether the limit is currently disabled for this view. */
  function isDisabled(viewKey: string): boolean {
    return disabledViews.value.has(viewKey)
  }

  /** Disable the limit for a view (persist in sessionStorage). */
  function disableLimit(viewKey: string): void {
    disabledViews.value.add(viewKey)
    sessionStorage.setItem(`${SESSION_KEY_PREFIX}${viewKey}`, '1')
  }

  /** Re-enable the limit for a view. */
  function enableLimit(viewKey: string): void {
    disabledViews.value.delete(viewKey)
    sessionStorage.removeItem(`${SESSION_KEY_PREFIX}${viewKey}`)
  }

  /** Toggle the limit state for a view. */
  function toggleLimit(viewKey: string): void {
    if (isDisabled(viewKey)) {
      enableLimit(viewKey)
    } else {
      disableLimit(viewKey)
    }
  }

  /** Record the total count returned by the server for a view. */
  function setTotalCount(viewKey: string, count: number): void {
    totalCounts.value[viewKey] = count
  }

  /** Whether there are more items on the server than what was fetched for this view. */
  function hasMore(viewKey: string, fetchedCount: number): boolean {
    const total = totalCounts.value[viewKey]
    if (total === undefined) return false
    return total > fetchedCount
  }

  const isLimitActive = computed(() => systemLimit.value > 0)

  return {
    systemLimit,
    loaded,
    totalCounts,
    isLimitActive,
    init,
    effectiveLimit,
    requestLimit,
    isDisabled,
    disableLimit,
    enableLimit,
    toggleLimit,
    setTotalCount,
    hasMore,
  }
})
