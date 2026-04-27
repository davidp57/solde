<template>
  <section :class="['app-page', widthClass]">
    <slot />
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    width?: 'default' | 'wide'
  }>(),
  {
    width: 'default',
  },
)

const widthClass = computed(() => `app-page--${props.width}`)
</script>
