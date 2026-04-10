<template>
  <div class="app-layout">
    <!-- Mobile topbar -->
    <div class="topbar">
      <Button
        icon="pi pi-bars"
        text
        class="topbar-menu-btn"
        :aria-label="t('nav.dashboard')"
        @click="sidebarVisible = true"
      />
      <span class="topbar-title">{{ t('app.name') }}</span>
      <div class="topbar-user">
        <span class="topbar-username">{{ auth.user?.username }}</span>
        <Button
          :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'"
          text
          rounded
          :aria-label="isDark ? t('auth.light_mode') : t('auth.dark_mode')"
          @click="toggleDark"
        />
        <Button
          icon="pi pi-sign-out"
          text
          rounded
          :aria-label="t('auth.logout')"
          @click="handleLogout"
        />
      </div>
    </div>

    <!-- Mobile sidebar drawer -->
    <Drawer v-model:visible="sidebarVisible" position="left" class="app-drawer">
      <template #header>
        <span class="drawer-title">{{ t('app.name') }}</span>
      </template>
      <NavMenu @navigate="sidebarVisible = false" />
    </Drawer>

    <!-- Desktop layout -->
    <div class="layout-body">
      <!-- Desktop sidebar -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <span class="sidebar-logo">⚖️</span>
          <span class="sidebar-title">{{ t('app.name') }}</span>
        </div>
        <NavMenu />
        <div class="sidebar-footer">
          <div class="sidebar-user">
            <span class="sidebar-username">{{ auth.user?.username }}</span>
            <span class="sidebar-role">{{ auth.user?.role ? t(`user.role.${auth.user.role}`) : '' }}</span>
          </div>
          <Button
            :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'"
            text
            rounded
            :aria-label="isDark ? t('auth.light_mode') : t('auth.dark_mode')"
            @click="toggleDark"
          />
          <Button
            icon="pi pi-sign-out"
            text
            rounded
            :aria-label="t('auth.logout')"
            @click="handleLogout"
          />
        </div>
      </aside>

      <!-- Main content -->
      <main class="main-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Drawer from 'primevue/drawer'
import { useAuthStore } from '../stores/auth'
import NavMenu from '../components/NavMenu.vue'
import { useDarkMode } from '../composables/useDarkMode'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const { isDark, toggle: toggleDark } = useDarkMode()

const sidebarVisible = ref(false)

async function handleLogout(): Promise<void> {
  auth.logout()
  await router.push('/login')
}
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Topbar (always visible on mobile, desktop fine too) */
.topbar {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  background: var(--p-surface-0);
  border-bottom: 1px solid var(--p-surface-200);
  gap: 0.75rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.topbar-menu-btn {
  flex-shrink: 0;
}

.topbar-title {
  font-weight: 700;
  font-size: 1.1rem;
  flex: 1;
}

.topbar-user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

.topbar-username {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  display: none;
}

.drawer-title {
  font-weight: 700;
  font-size: 1.1rem;
}

/* Layout body: sidebar + main */
.layout-body {
  display: flex;
  flex: 1;
}

/* Desktop sidebar */
.sidebar {
  display: none;
  flex-direction: column;
  width: 240px;
  flex-shrink: 0;
  background: var(--p-surface-0);
  border-right: 1px solid var(--p-surface-200);
  min-height: calc(100vh - 53px);
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1rem 1rem;
  border-bottom: 1px solid var(--p-surface-100);
}

.sidebar-logo {
  font-size: 1.5rem;
}

.sidebar-title {
  font-weight: 700;
  font-size: 1rem;
}

.sidebar-footer {
  margin-top: auto;
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--p-surface-100);
  gap: 0.5rem;
}

.sidebar-user {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sidebar-username {
  font-size: 0.875rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-role {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

/* Main content */
.main-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  background: var(--p-surface-50);
  min-height: calc(100vh - 53px);
}

/* Desktop breakpoint */
@media (min-width: 768px) {
  .topbar-menu-btn {
    display: none;
  }

  .topbar-username {
    display: inline;
  }

  .sidebar {
    display: flex;
  }
}
</style>
