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
      <div v-if="auth.canAccessManagement" class="topbar-context">
        <span class="topbar-context__label">{{ t('app.active_fiscal_year') }}</span>
        <Select
          v-model="selectedFiscalYearOptionId"
          :options="fiscalYearOptions"
          option-label="name"
          option-value="id"
          :placeholder="t('app.active_fiscal_year')"
          :loading="fiscalYearStore.loading"
          :disabled="fiscalYearStore.fiscalYears.length === 0"
          class="topbar-context__select"
        />
      </div>
      <div class="topbar-user">
        <RouterLink to="/profile" class="topbar-username">{{ displayedUsername }}</RouterLink>
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
        <NavMenu />
        <div class="sidebar-footer">
          <RouterLink to="/profile" class="sidebar-user">
            <span class="sidebar-username">{{ displayedUsername }}</span>
            <span class="sidebar-role">{{ displayedRoleLabel }}</span>
          </RouterLink>
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
        <span class="sidebar-version">v{{ appVersion }}</span>
      </aside>

      <!-- Main content -->
      <main class="main-content">
        <RouterView />
      </main>
    </div>

    <!-- Chat sidebar (floating, authenticated pages only) -->
    <ChatSidebar />

    <!-- Chat toggle button (always visible for authenticated users) -->
    <Button
      icon="pi pi-sparkles"
      class="chat-fab"
      rounded
      :severity="chatStore.isOpen ? 'secondary' : 'primary'"
      :title="chatStore.isOpen ? t('nav.chat_close') : t('nav.chat_open')"
      @click="chatStore.toggle()"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Drawer from 'primevue/drawer'
import Select from 'primevue/select'
import { useAuthStore } from '../stores/auth'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { useChatStore } from '../stores/chat'
import NavMenu from '../components/NavMenu.vue'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import { useDarkMode } from '../composables/useDarkMode'
const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const fiscalYearStore = useFiscalYearStore()
const { isDark, toggle: toggleDark } = useDarkMode()

const sidebarVisible = ref(false)
const appVersion = __APP_VERSION__
const displayedUsername = computed(() => auth.user?.username ?? t('auth.me'))
const displayedRoleLabel = computed(() =>
  auth.user?.role ? t(`user.role.${auth.user.role}`) : t('auth.session_active'),
)
const fiscalYearOptions = computed(() => [
  { id: null, name: t('app.all_fiscal_years') },
  ...fiscalYearStore.fiscalYears,
])
const selectedFiscalYearOptionId = computed<number | null>({
  get: () => fiscalYearStore.selectedFiscalYearId ?? null,
  set: (value: number | null) => fiscalYearStore.setSelectedFiscalYear(value ?? undefined),
})

// Reactive backgrounds for dark/light mode (v-bind in CSS)
const panelBg = computed(() => (isDark.value ? 'var(--p-surface-900)' : 'var(--p-surface-0)'))
const mainBg = computed(() => (isDark.value ? 'var(--p-surface-950)' : 'var(--p-surface-50)'))
const borderColor = computed(() => (isDark.value ? 'var(--p-surface-700)' : 'var(--p-surface-200)'))

async function handleLogout(): Promise<void> {
  auth.logout({ preventDevAutoLogin: true })
  await router.push('/login')
}

const chatStore = useChatStore()

onMounted(() => {
  if (auth.canAccessManagement) {
    void fiscalYearStore.initialize()
  }
  void chatStore.loadConfig()
})
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
  background: v-bind(panelBg);
  border-bottom: 1px solid v-bind(borderColor);
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

.topbar-context {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.topbar-context__label {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  white-space: nowrap;
}

.topbar-context__select {
  width: 11rem;
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
  min-height: calc(100vh - 53px);
}

/* Desktop sidebar */
.sidebar {
  display: none;
  flex-direction: column;
  width: 240px;
  flex-shrink: 0;
  background: v-bind(panelBg);
  border-right: 1px solid v-bind(borderColor);
  height: calc(100vh - 53px);
  overflow: hidden;
}

.sidebar-footer {
  margin-top: auto;
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-top: 1px solid v-bind(borderColor);
  gap: 0.5rem;
  flex-shrink: 0;
}

.sidebar-user {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  text-decoration: none;
  color: inherit;
  padding: 0.25rem 0.375rem;
  border-radius: 0.375rem;
  transition: background 0.15s;
}

.sidebar-user:hover {
  background: v-bind(hoverBg);
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

.sidebar-version {
  font-size: 0.7rem;
  color: var(--p-text-muted-color);
  padding: 0.25rem 1rem 0.5rem;
  display: block;
  opacity: 0.6;
}

/* Main content */
.main-content {
  flex: 1;
  padding: var(--app-page-padding);
  overflow-y: auto;
  background: v-bind(mainBg);
  min-height: calc(100vh - 53px);
  min-width: 0;
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
    position: sticky;
    top: 53px;
  }
}

@media (max-width: 767px) {
  .topbar-context__label {
    display: none;
  }

  .topbar-context__select {
    width: 8.5rem;
  }
}

/* Chat FAB */
.chat-fab {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 999;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}
</style>
