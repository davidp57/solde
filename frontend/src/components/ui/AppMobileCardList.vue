<template>
  <div class="app-mobile-card-list">
    <div
      v-for="(item, index) in items"
      :key="index"
      class="app-mobile-card"
    >
      <slot name="card" :item="item" :index="index" />
    </div>
    <div v-if="items.length === 0" class="app-mobile-card-list__empty">
      <slot name="empty">
        <span>{{ emptyMessage }}</span>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    items: unknown[]
    emptyMessage?: string
  }>(),
  {
    emptyMessage: 'Aucune donnée',
  },
)
</script>

<style scoped>
.app-mobile-card-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.app-mobile-card {
  background: var(--app-surface-bg);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--p-border-radius-md, 6px);
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.app-mobile-card-list__empty {
  text-align: center;
  color: var(--p-text-muted-color);
  padding: 2rem 1rem;
  font-size: 0.9rem;
}
</style>
