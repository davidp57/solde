<template>
  <nav class="nav-menu" :class="`nav-menu--${variant}`">
    <section v-for="section in menuSections" :key="section.key" class="nav-section">
      <h2 v-if="variant === 'full'" class="nav-section__title">{{ section.title }}</h2>
      <RouterLink
        v-for="item in section.items"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="nav-item--active"
        :title="variant === 'rail' ? item.label : undefined"
        :aria-label="item.label"
        @click="emit('navigate')"
      >
        <i :class="['pi', item.icon]" />
        <span class="nav-item__label">{{ item.label }}</span>
      </RouterLink>
    </section>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDarkMode } from '../composables/useDarkMode'
import { useNavigation } from '../composables/useNavigation'

withDefaults(defineProps<{ variant?: 'full' | 'rail' }>(), { variant: 'full' })
const emit = defineEmits<{ navigate: [] }>()

const { isDark } = useDarkMode()
const { menuSections } = useNavigation()

const activeItemBg = computed(() =>
  isDark.value ? 'rgba(52, 211, 153, 0.12)' : 'var(--p-primary-50)',
)
const activeItemColor = computed(() =>
  isDark.value ? 'var(--p-primary-300)' : 'var(--p-primary-color)',
)
const hoverBg = computed(() => (isDark.value ? 'var(--p-surface-800)' : 'var(--p-surface-100)'))
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

/* Rail (tablet): icon-only targets, no section labels, dividers between groups. */
.nav-menu--rail {
  align-items: center;
  gap: 0.5rem;
}

.nav-menu--rail .nav-section {
  width: 100%;
  align-items: center;
  gap: 0.25rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--app-surface-border);
}

.nav-menu--rail .nav-section:first-child {
  border-top: none;
  padding-top: 0;
}

.nav-menu--rail .nav-item {
  justify-content: center;
  width: 44px;
  height: 44px;
  margin: 0;
  padding: 0;
}

.nav-menu--rail .nav-item__label {
  /* Visually hidden but kept for screen readers; the title attr shows on hover. */
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.nav-menu--rail .nav-item .pi {
  font-size: 1.15rem;
}
</style>
