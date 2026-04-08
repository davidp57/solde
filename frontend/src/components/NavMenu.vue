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

const emit = defineEmits<{ navigate: [] }>()
const { t } = useI18n()
const auth = useAuthStore()

const menuItems = computed(() => {
  const items = [
    { to: '/dashboard', icon: 'pi-home', label: t('nav.dashboard') },
    { to: '/contacts', icon: 'pi-users', label: t('nav.contacts') },
    { to: '/invoices', icon: 'pi-file', label: t('nav.invoices') },
    { to: '/payments', icon: 'pi-credit-card', label: t('nav.payments') },
    { to: '/bank', icon: 'pi-building-columns', label: t('nav.bank') },
    { to: '/cash', icon: 'pi-wallet', label: t('nav.cash') },
    { to: '/accounting', icon: 'pi-book', label: t('nav.accounting') },
    { to: '/accounting/accounts', icon: 'pi-list', label: t('nav.accounting_accounts') },
  ]

  if (auth.isAdmin) {
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
  background: var(--p-surface-100);
}

.nav-item--active {
  background: var(--p-primary-50);
  color: var(--p-primary-color);
  font-weight: 500;
}

.nav-item .pi {
  font-size: 1rem;
  flex-shrink: 0;
}
</style>
