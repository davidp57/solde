import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'

export type NavItem = {
  to: string
  icon: string
  label: string
}

export type NavSection = {
  key: string
  title: string
  items: NavItem[]
}

// Routes promoted to the mobile bottom tab bar, in priority order. Only the
// ones the current user can reach are kept; the rest of the navigation stays
// available through the drawer (burger).
const BOTTOM_NAV_PRIORITY = ['/dashboard', '/invoices/client', '/bank', '/contacts', '/payments']

/**
 * Single source of truth for the application navigation, shared by the sidebar,
 * the tablet rail and the mobile bottom bar so the three stay in sync.
 */
export function useNavigation() {
  const { t } = useI18n()
  const auth = useAuthStore()

  const homeItems = computed<NavItem[]>(() => [
    { to: '/dashboard', icon: 'pi-home', label: t('nav.dashboard') },
    { to: '/aide', icon: 'pi-question-circle', label: t('nav.help') },
  ])

  const managementItems = computed<NavItem[]>(() => {
    if (!auth.canAccessManagement) return []
    return [
      { to: '/contacts', icon: 'pi-users', label: t('nav.contacts') },
      { to: '/invoices/client', icon: 'pi-file', label: t('nav.invoices_client') },
      { to: '/invoices/supplier', icon: 'pi-file-import', label: t('nav.invoices_supplier') },
      { to: '/payments', icon: 'pi-credit-card', label: t('nav.payments') },
      { to: '/bank', icon: 'pi-building-columns', label: t('nav.bank') },
      { to: '/cash', icon: 'pi-wallet', label: t('nav.cash') },
      { to: '/salaries', icon: 'pi-money-bill', label: t('nav.salaries') },
      { to: '/employees', icon: 'pi-id-card', label: t('nav.employees') },
    ]
  })

  const accountingItems = computed<NavItem[]>(() => {
    if (!auth.canAccessAccounting) return []
    return [
      { to: '/accounting/balance', icon: 'pi-chart-bar', label: t('nav.accounting_balance') },
      { to: '/accounting/journal', icon: 'pi-book', label: t('nav.accounting_journal') },
      { to: '/accounting/ledger', icon: 'pi-list', label: t('nav.accounting_ledger') },
      { to: '/accounting/bilan', icon: 'pi-chart-line', label: t('nav.accounting_bilan') },
      { to: '/accounting/resultat', icon: 'pi-chart-pie', label: t('nav.accounting_resultat') },
      {
        to: '/accounting/fiscal-years',
        icon: 'pi-calendar',
        label: t('nav.accounting_fiscal_years'),
      },
      { to: '/accounting/accounts', icon: 'pi-database', label: t('nav.accounting_accounts') },
      { to: '/accounting/rules', icon: 'pi-sliders-h', label: t('nav.accounting_rules') },
    ]
  })

  const administrationItems = computed<NavItem[]>(() => {
    if (!auth.canManageApplication) return []
    return [
      { to: '/users', icon: 'pi-users', label: t('nav.users') },
      { to: '/settings', icon: 'pi-cog', label: t('nav.settings') },
      { to: '/system', icon: 'pi-server', label: t('nav.system') },
      { to: '/import/excel', icon: 'pi-file-excel', label: t('nav.import_excel') },
      { to: '/import/history', icon: 'pi-history', label: t('nav.import_history') },
      { to: '/comments', icon: 'pi-comment', label: t('nav.comments') },
    ]
  })

  const menuSections = computed<NavSection[]>(() =>
    [
      { key: 'home', title: t('nav.section_home'), items: homeItems.value },
      { key: 'management', title: t('nav.section_management'), items: managementItems.value },
      { key: 'accounting', title: t('nav.section_accounting'), items: accountingItems.value },
      {
        key: 'administration',
        title: t('nav.section_administration'),
        items: administrationItems.value,
      },
    ].filter((section) => section.items.length > 0),
  )

  const allItems = computed<NavItem[]>(() => menuSections.value.flatMap((section) => section.items))

  // Four primary destinations for the mobile bottom bar: priority routes first,
  // then padded with whatever else the user can reach (the burger covers the rest).
  const bottomNavItems = computed<NavItem[]>(() => {
    const byRoute = new Map(allItems.value.map((item) => [item.to, item]))
    const picked: NavItem[] = []
    const seen = new Set<string>()
    const add = (item: NavItem): void => {
      if (seen.has(item.to)) return
      seen.add(item.to)
      picked.push(item)
    }
    for (const route of BOTTOM_NAV_PRIORITY) {
      const item = byRoute.get(route)
      if (item) add(item)
      if (picked.length === 4) return picked
    }
    for (const item of allItems.value) {
      if (item.to === '/aide') continue
      add(item)
      if (picked.length === 4) break
    }
    return picked
  })

  return { menuSections, allItems, bottomNavItems }
}
