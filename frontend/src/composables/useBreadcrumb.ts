import { computed, type ComputedRef } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { MenuItem } from 'primevue/menuitem'

export function useBreadcrumb(): {
  home: MenuItem
  items: ComputedRef<MenuItem[]>
} {
  const route = useRoute()
  const { t } = useI18n()

  const home: MenuItem = { icon: 'pi pi-home', to: '/dashboard' }

  const items = computed<MenuItem[]>(() => {
    const { label, breadcrumbParent } = route.meta
    if (!label) return []
    // Dashboard is the home — no extra breadcrumb items needed
    if (route.name === 'dashboard') return []

    const result: MenuItem[] = []
    if (breadcrumbParent) {
      result.push({
        label: t(breadcrumbParent.labelKey),
        to: breadcrumbParent.to,
      })
    }
    result.push({ label: t(label) })
    return result
  })

  return { home, items }
}
