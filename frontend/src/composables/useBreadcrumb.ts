import { computed, type ComputedRef } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { MenuItem } from 'primevue/menuitem'

export interface BreadcrumbHome {
  icon: string
  route: string
}

export function useBreadcrumb(): {
  home: BreadcrumbHome
  items: ComputedRef<MenuItem[]>
} {
  const route = useRoute()
  const { t } = useI18n()

  const home: BreadcrumbHome = { icon: 'pi pi-home', route: '/dashboard' }

  const items = computed<MenuItem[]>(() => {
    const { label, breadcrumbParent } = route.meta
    if (!label) return []
    // Dashboard is the home — no extra breadcrumb items needed
    if (route.name === 'dashboard') return []

    const result: MenuItem[] = []
    if (breadcrumbParent) {
      result.push({
        label: t(breadcrumbParent.labelKey),
        route: breadcrumbParent.to,
      })
    }
    result.push({ label: t(label) })
    return result
  })

  return { home, items }
}
