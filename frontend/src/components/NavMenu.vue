<template>
  <nav class="nav-menu">
    <section v-for="section in menuSections" :key="section.key" class="nav-section">
      <h2 class="nav-section__title">{{ section.title }}</h2>
      <RouterLink
        v-for="item in section.items"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="nav-item--active"
        @click="emit('navigate')"
      >
        <i :class="['pi', item.icon]" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </section>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { useDarkMode } from '../composables/useDarkMode'

const emit = defineEmits<{ navigate: [] }>()
const { t } = useI18n()
const auth = useAuthStore()
const { isDark } = useDarkMode()

const activeItemBg = computed(() =>
  isDark.value ? 'rgba(52, 211, 153, 0.12)' : 'var(--p-primary-50)',
)
const activeItemColor = computed(() =>
  isDark.value ? 'var(--p-primary-300)' : 'var(--p-primary-color)',
)
const hoverBg = computed(() => (isDark.value ? 'var(--p-surface-800)' : 'var(--p-surface-100)'))

type MenuItem = {
  to: string
  icon: string
  label: string
}

const homeItems = computed<MenuItem[]>(() => [
  { to: '/dashboard', icon: 'pi-home', label: t('nav.dashboard') },
])

const managementItems = computed<MenuItem[]>(() => {
  const items: MenuItem[] = []

  if (auth.canAccessManagement) {
    items.push(
      { to: '/contacts', icon: 'pi-users', label: t('nav.contacts') },
      { to: '/invoices/client', icon: 'pi-file', label: t('nav.invoices_client') },
      { to: '/invoices/supplier', icon: 'pi-file-import', label: t('nav.invoices_supplier') },
      { to: '/payments', icon: 'pi-credit-card', label: t('nav.payments') },
      { to: '/bank', icon: 'pi-building-columns', label: t('nav.bank') },
      { to: '/cash', icon: 'pi-wallet', label: t('nav.cash') },
      { to: '/salaries', icon: 'pi-money-bill', label: t('nav.salaries') },
    )
  }

  return items
})

const accountingItems = computed<MenuItem[]>(() => {
  if (!auth.canAccessAccounting) {
    return []
  }

  return [
    { to: '/accounting/balance', icon: 'pi-chart-bar', label: t('nav.accounting_balance') },
    { to: '/accounting/journal', icon: 'pi-book', label: t('nav.accounting_journal') },
    { to: '/accounting/ledger', icon: 'pi-list', label: t('nav.accounting_ledger') },
    { to: '/employees', icon: 'pi-id-card', label: t('nav.employees') },
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

const administrationItems = computed<MenuItem[]>(() => {
  if (!auth.canManageApplication) {
    return []
  }

  return [
    { to: '/users', icon: 'pi-users', label: t('nav.users') },
    { to: '/settings', icon: 'pi-cog', label: t('nav.settings') },
    { to: '/import/excel', icon: 'pi-file-excel', label: t('nav.import_excel') },
    { to: '/import/history', icon: 'pi-history', label: t('nav.import_history') },
  ]
})

const menuSections = computed(() => {
  const sections = [
    {
      key: 'home',
      title: t('nav.section_home'),
      items: homeItems.value,
    },
    {
      key: 'management',
      title: t('nav.section_management'),
      items: managementItems.value,
    },
    {
      key: 'accounting',
      title: t('nav.section_accounting'),
      items: accountingItems.value,
    },
    {
      key: 'administration',
      title: t('nav.section_administration'),
      items: administrationItems.value,
    },
  ]

  return sections.filter((section) => section.items.length > 0)
})
</script>

<style scoped>
.nav-menu {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0;
  flex: 1;
  gap: 0.75rem;
  min-height: 0;
  overflow-y: auto;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-section__title {
  margin: 0;
  padding: 0 1rem;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  color: var(--p-text-color);
  text-decoration: none;
  font-size: 0.9rem;
  border-radius: 0.375rem;
  margin: 0 0.5rem;
  transition: background 0.15s;
}

.nav-item:hover {
  background: v-bind(hoverBg);
}

.nav-item--active {
  background: v-bind(activeItemBg);
  color: v-bind(activeItemColor);
  font-weight: 500;
}

.nav-item .pi {
  font-size: 1rem;
  flex-shrink: 0;
}
</style>
