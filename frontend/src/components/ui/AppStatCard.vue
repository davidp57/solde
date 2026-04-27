<template>
  <component
    :is="to ? RouterLink : 'article'"
    :to="to"
    :class="['app-stat-card', `app-stat-card--${tone}`, { 'app-stat-card--link': to }]"
  >
    <p class="app-stat-card__label">{{ label }}</p>
    <p class="app-stat-card__value">{{ value }}</p>
    <p v-if="caption" class="app-stat-card__caption">{{ caption }}</p>
  </component>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

withDefaults(
  defineProps<{
    label: string
    value: string | number
    caption?: string
    tone?: 'default' | 'success' | 'warn' | 'danger'
    to?: string | Record<string, unknown>
  }>(),
  {
    caption: undefined,
    tone: 'default',
    to: undefined,
  },
)
</script>
