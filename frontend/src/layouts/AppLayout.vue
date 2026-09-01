<template>
  <div class="app-layout">
    <!-- Topbar (mobile + tablet; condensed) -->
    <div class="topbar">
      <Button
        icon="pi pi-bars"
        text
        class="topbar-menu-btn"
        :aria-label="t('nav.open_menu')"
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
        <Button
          v-if="auth.canAccessAccounting"
          icon="pi pi-check-square"
          text
          rounded
          :badge="checklistBadge"
          :aria-label="t('checklist.title')"
          :title="t('checklist.title')"
          @click="openChecklist"
        />
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

    <!-- Mobile sidebar drawer (full navigation) -->
    <Drawer v-model:visible="sidebarVisible" position="left" class="app-drawer">
      <template #header>
        <span class="drawer-title">{{ t('app.name') }}</span>
      </template>
      <NavMenu @navigate="sidebarVisible = false" />
    </Drawer>

    <!-- Layout body: sidebar / rail + main -->
    <div class="layout-body">
      <!-- Desktop sidebar (≥1200px) -->
      <aside class="sidebar">
        <NavMenu />
        <div class="sidebar-footer">
          <Button
            v-if="auth.canAccessAccounting"
            icon="pi pi-check-square"
            text
            rounded
            :badge="checklistBadge"
            :aria-label="t('checklist.title')"
            :title="t('checklist.title')"
            @click="openChecklist"
          />
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

      <!-- Tablet icon rail (768–1199px) -->
      <aside class="rail">
        <NavMenu variant="rail" />
        <div class="rail-footer">
          <Button
            v-if="auth.canAccessAccounting"
            icon="pi pi-check-square"
            text
            rounded
            :badge="checklistBadge"
            :aria-label="t('checklist.title')"
            :title="t('checklist.title')"
            @click="openChecklist"
          />
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
        <div class="main-inner">
          <RouterView />
        </div>
      </main>
    </div>

    <!-- Mobile bottom tab bar (primary destinations; drawer covers the rest).
         Hidden when there is only one reachable item (e.g. a readonly user) — a
         lone full-width tab adds no value. -->
    <nav v-if="bottomNavItems.length > 1" class="bottom-nav" :aria-label="t('nav.open_menu')">
      <RouterLink
        v-for="item in bottomNavItems"
        :key="item.to"
        :to="item.to"
        class="bottom-nav__item"
        active-class="bottom-nav__item--active"
      >
        <i :class="['pi', item.icon]" />
        <span class="bottom-nav__label">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <!-- Monthly bookkeeping checklist (reachable from every screen) -->
    <ChecklistDialog v-if="auth.canAccessAccounting" />

    <!-- Chat sidebar (floating, authenticated pages only) -->
    <ChatSidebar />

    <!-- Chat toggle button (visible when chat is enabled) -->
    <Button
      v-if="chatStore.isEnabled"
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
import { useChecklistStore } from '../stores/checklist'
import NavMenu from '../components/NavMenu.vue'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChecklistDialog from '../components/checklist/ChecklistDialog.vue'
import { useDarkMode } from '../composables/useDarkMode'
import { useNavigation } from '../composables/useNavigation'
const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const fiscalYearStore = useFiscalYearStore()
const { isDark, toggle: toggleDark } = useDarkMode()
const { bottomNavItems } = useNavigation()

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
const hoverBg = computed(() => (isDark.value ? 'var(--p-surface-800)' : 'var(--p-surface-100)'))

async function handleLogout(): Promise<void> {
  auth.logout({ preventDevAutoLogin: true })
  await router.push('/login')
}

const chatStore = useChatStore()
const checklistStore = useChecklistStore()

// Progress on the button itself, so the session is visible without opening it.
const checklistBadge = computed(() =>
  checklistStore.isOpen ? `${checklistStore.checkedCount}/${checklistStore.totalCount}` : undefined,
)

function openChecklist(): void {
  checklistStore.dialogVisible = true
}

onMounted(() => {
  if (auth.canAccessManagement) {
    void fiscalYearStore.initialize()
  }
  void chatStore.loadConfig()
  if (auth.canAccessAccounting) {
    void checklistStore.load()
  }
})
</script>

<style scoped>
.app-layout {
  /* Single source for the chrome dimensions the sticky panes depend on. */
  --app-topbar-height: 53px;
  --app-bottom-nav-height: 60px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Topbar */
.topbar {
  display: flex;
  align-items: center;
  height: var(--app-topbar-height);
  box-sizing: border-box;
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

/* Layout body: sidebar/rail + main */
.layout-body {
  display: flex;
  flex: 1;
  min-height: calc(100vh - var(--app-topbar-height));
}

/* Desktop sidebar + tablet rail share the chrome look but differ in width. */
.sidebar,
.rail {
  display: none;
  flex-direction: column;
  flex-shrink: 0;
  background: v-bind(panelBg);
  border-right: 1px solid v-bind(borderColor);
  height: calc(100vh - var(--app-topbar-height));
  overflow: hidden;
}

.sidebar {
  width: 240px;
}

.rail {
  width: 72px;
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

.rail-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 0;
  border-top: 1px solid v-bind(borderColor);
  gap: 0.25rem;
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
  min-height: calc(100vh - var(--app-topbar-height));
  min-width: 0;
}

.main-inner {
  min-width: 0;
}

/* Mobile bottom tab bar */
.bottom-nav {
  display: flex;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 200;
  background: v-bind(panelBg);
  border-top: 1px solid v-bind(borderColor);
  padding: 0.25rem 0.25rem calc(0.25rem + env(safe-area-inset-bottom, 0px));
}

.bottom-nav__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.15rem;
  min-height: 52px;
  padding: 0.25rem;
  text-decoration: none;
  color: var(--p-text-muted-color);
  border-radius: 0.5rem;
}

.bottom-nav__item .pi {
  font-size: 1.2rem;
}

.bottom-nav__label {
  font-size: 0.66rem;
  font-weight: 600;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bottom-nav__item--active {
  color: var(--p-primary-color);
}

/* Keep content clear of the fixed bottom bar on mobile. */
.main-content {
  padding-bottom: calc(var(--app-page-padding) + var(--app-bottom-nav-height));
}

/* Tablet: show the icon rail, hide the burger + bottom bar. */
@media (min-width: 768px) {
  .topbar-menu-btn {
    display: none;
  }

  .topbar-username {
    display: inline;
  }

  .rail {
    display: flex;
    position: sticky;
    top: var(--app-topbar-height);
  }

  .bottom-nav {
    display: none;
  }

  .main-content {
    padding-bottom: var(--app-page-padding);
  }
}

/* Desktop: full sidebar instead of the rail, centered content. */
@media (min-width: 1200px) {
  .rail {
    display: none;
  }

  .sidebar {
    display: flex;
    position: sticky;
    top: var(--app-topbar-height);
  }

  /* Allow wide pages (.app-page--wide) to reach their 1640px cap. Each
     .app-page sets its own width (1320 normal / 1640 wide) and centers itself,
     so this only needs to stop being the bottleneck — not clamp to 1320. */
  .main-inner {
    max-width: var(--app-page-wide-max-width);
    margin: 0 auto;
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

/* Chat FAB — lifted above the bottom bar on mobile. */
.chat-fab {
  position: fixed;
  bottom: calc(1.5rem + var(--app-bottom-nav-height));
  right: 1.5rem;
  z-index: 999;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

@media (min-width: 768px) {
  .chat-fab {
    bottom: 1.5rem;
  }
}
</style>
