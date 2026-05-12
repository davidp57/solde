<template>
  <!-- Limit active + server has more items: prominent warning -->
  <Message
    v-if="showWarning"
    severity="error"
    :closable="false"
    class="app-list-limit-banner app-list-limit-banner--warning mb-2"
  >
    <span class="app-list-limit-banner__text">
      {{
        t('common.list_limit_active_warning', {
          limit: n(props.limit, 'decimal'),
          total: n(total, 'decimal'),
        })
      }}
    </span>
    <a
      href="#"
      class="app-list-limit-banner__link"
      @click.prevent="limitStore.disableLimit(props.viewKey); emit('reload')"
    >
      {{ t('common.list_limit_disable') }}
    </a>
  </Message>

  <!-- Limit disabled: subtle info -->
  <Message
    v-else-if="showDisabled"
    severity="secondary"
    :closable="false"
    class="app-list-limit-banner app-list-limit-banner--disabled mb-2"
  >
    <span class="app-list-limit-banner__text">
      {{
        t('common.list_limit_disabled_info', {
          limit: n(props.limit, 'decimal'),
        })
      }}
    </span>
    <a
      href="#"
      class="app-list-limit-banner__link"
      @click.prevent="limitStore.enableLimit(props.viewKey); emit('reload')"
    >
      {{ t('common.list_limit_enable') }}
    </a>
  </Message>
</template>

<script setup lang="ts">
import Message from 'primevue/message'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useListLimitStore } from '../../stores/listLimit'

const props = defineProps<{
  /** Unique key identifying the view/list (e.g. 'invoices-client', 'bank-transactions'). */
  viewKey: string
  /** Number of items currently shown in the list. */
  fetchedCount: number
  /** The system limit value (0 = unlimited system-wide). */
  limit: number
}>()

const emit = defineEmits<{
  /** Emitted when the user toggles the limit, so the parent can reload. */
  reload: []
}>()

const { t, n } = useI18n()
const limitStore = useListLimitStore()

const total = computed(() => limitStore.totalCounts[props.viewKey] ?? 0)

/** Show warning when: limit is active for this view AND server has more items than fetched. */
const showWarning = computed(
  () =>
    props.limit > 0 &&
    !limitStore.isDisabled(props.viewKey) &&
    limitStore.hasMore(props.viewKey, props.fetchedCount),
)

/** Show disabled notice when: user has disabled the limit for this view. */
const showDisabled = computed(() => limitStore.isDisabled(props.viewKey))
</script>

<style scoped>
.app-list-limit-banner--warning :deep(.p-message-text) {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1rem;
  font-weight: 700;
}

.app-list-limit-banner--disabled :deep(.p-message-text) {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
  font-weight: 400;
}

.app-list-limit-banner__text {
  flex: 1;
}

.app-list-limit-banner__link {
  white-space: nowrap;
  font-weight: 600;
  text-decoration: underline;
  color: inherit;
  cursor: pointer;
}

.app-list-limit-banner__link:hover {
  opacity: 0.8;
}
</style>
