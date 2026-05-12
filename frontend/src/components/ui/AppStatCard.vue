<template>
  <component
    :is="to ? RouterLink : 'article'"
    :to="to"
    :class="['app-stat-card', `app-stat-card--${tone}`, { 'app-stat-card--link': to }]"
  >
    <p class="app-stat-card__label">{{ label }}</p>
    <div v-if="breakdown?.length" class="app-stat-card__breakdown" role="list">
      <p v-for="(item, index) in breakdown" :key="index" class="app-stat-card__breakdown-item" role="listitem">
        <span class="app-stat-card__breakdown-value">{{ item.value }}</span>
        <span class="app-stat-card__breakdown-label">{{ item.label }}</span>
      </p>
    </div>
    <p v-else class="app-stat-card__value">{{ value }}</p>
    <p v-if="caption" class="app-stat-card__caption">{{ caption }}</p>
  </component>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

withDefaults(
  defineProps<{
    label: string
    value: string | number
    breakdown?: Array<{ value: string | number; label: string }>
    caption?: string
    tone?: 'default' | 'success' | 'warn' | 'danger'
    to?: string | Record<string, unknown>
  }>(),
  {
    breakdown: undefined,
    caption: undefined,
    tone: 'default',
    to: undefined,
  },
)
</script>
