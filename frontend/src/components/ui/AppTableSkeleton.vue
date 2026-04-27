<template>
  <div class="app-table-skeleton" role="status" :aria-label="t('common.loading')">
    <div
      v-for="n in rows"
      :key="n"
      class="app-table-skeleton__row"
      :style="{ gridTemplateColumns: `repeat(${cols}, 1fr)` }"
    >
      <Skeleton v-for="c in cols" :key="c" height="2.25rem" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import Skeleton from 'primevue/skeleton'

withDefaults(defineProps<{ rows?: number; cols?: number }>(), { rows: 8, cols: 4 })

const { t } = useI18n()
</script>
