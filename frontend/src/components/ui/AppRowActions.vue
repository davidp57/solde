<template>
  <div class="app-row-actions">
    <Button
      v-if="primary"
      :label="primary.label"
      :icon="primary.icon"
      :severity="primary.severity"
      size="small"
      outlined
      class="app-row-actions__primary"
      @click="primary.command"
    />
    <template v-if="menuItems.length">
      <Button
        icon="pi pi-ellipsis-h"
        size="small"
        text
        severity="secondary"
        :aria-label="menuAriaLabel ?? primary?.label"
        aria-haspopup="true"
        @click="toggle"
      />
      <Menu ref="menuRef" :model="menuItems" popup />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'

export interface RowAction {
  key: string
  label: string
  icon: string
  severity?: string
  command: () => void
}

defineProps<{
  /** Optional: a row may have nothing but overflow items — a reconciled statement
   *  line, say, whose only actions are to undo the reconciliation or delete it. */
  primary?: RowAction
  menuItems: MenuItem[]
  menuAriaLabel?: string
}>()

const menuRef = ref<InstanceType<typeof Menu> | null>(null)

function toggle(event: Event): void {
  menuRef.value?.toggle(event)
}
</script>

<style scoped>
.app-row-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-1);
}

/* Keep the primary action close to the status badge scale (compact). */
.app-row-actions__primary {
  white-space: nowrap;
  font-size: 0.78rem;
  padding-block: 0.2rem;
  padding-inline: 0.55rem;
  gap: 0.3rem;
}

.app-row-actions__primary :deep(.p-button-icon) {
  font-size: 0.78rem;
}
</style>

<!-- Destructive overflow items are visually separated (separator) and tinted red.
     The popup menu is teleported out of the scoped tree, so this rule is global. -->
<style>
.p-menu .app-row-actions-danger .p-menu-item-link,
.p-menu .app-row-actions-danger .p-menuitem-link {
  color: var(--p-red-500, #dc2626);
}
</style>
