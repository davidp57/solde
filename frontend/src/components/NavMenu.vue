<template>
  <nav class="nav-menu">
    <RouterLink
      v-for="item in menuItems"
      :key="item.to"
      :to="item.to"
      class="nav-item"
      active-class="nav-item--active"
      @click="emit('navigate')"
    >
      <i :class="['pi', item.icon]" />
      <span>{{ item.label }}</span>
    </RouterLink>
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

const menuItems = computed(() => {
  const items = [
    { to: '/dashboard', icon: 'pi-home', label: t('nav.dashboard') },
    { to: '/contacts', icon: 'pi-users', label: t('nav.contacts') },
    { to: '/invoices/client', icon: 'pi-file', label: t('nav.invoices_client') },
    { to: '/invoices/supplier', icon: 'pi-file-import', label: t('nav.invoices_supplier') },
    { to: '/payments', icon: 'pi-credit-card', label: t('nav.payments') },
    { to: '/bank', icon: 'pi-building-columns', label: t('nav.bank') },
    { to: '/cash', icon: 'pi-wallet', label: t('nav.cash') },
    { to: '/accounting/journal', icon: 'pi-book', label: t('nav.accounting_journal') },
    { to: '/accounting/balance', icon: 'pi-chart-bar', label: t('nav.accounting_balance') },
    { to: '/accounting/ledger', icon: 'pi-list', label: t('nav.accounting_ledger') },
    { to: '/accounting/resultat', icon: 'pi-chart-pie', label: t('nav.accounting_resultat') },
    { to: '/accounting/bilan', icon: 'pi-chart-line', label: t('nav.accounting_bilan') },
    { to: '/accounting/accounts', icon: 'pi-database', label: t('nav.accounting_accounts') },
    { to: '/accounting/rules', icon: 'pi-sliders-h', label: t('nav.accounting_rules') },
    {
      to: '/accounting/fiscal-years',
      icon: 'pi-calendar',
      label: t('nav.accounting_fiscal_years'),
    },
    { to: '/salaries', icon: 'pi-id-card', label: t('nav.salaries') },
    { to: '/import/excel', icon: 'pi-file-excel', label: t('nav.import_excel') },
  ]

  if (auth.isAdmin) {
    items.push({ to: '/users', icon: 'pi-users', label: t('nav.users') })
    items.push({ to: '/settings', icon: 'pi-cog', label: t('nav.settings') })
  }

  return items
})
</script>

<style scoped>
.nav-menu {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0;
  flex: 1;
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
