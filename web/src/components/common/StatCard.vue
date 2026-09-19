<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  unit?: string
  color?: string
  icon?: string
}>()
</script>

<template>
  <div
    class="card relative overflow-hidden group"
    :style="{ borderLeft: `3px solid ${color ?? 'var(--accent)'}` }"
  >
    <!-- 背景装饰 -->
    <div
      class="absolute -top-8 -right-8 w-24 h-24 rounded-full opacity-5 group-hover:opacity-10 transition-opacity duration-500"
      :style="{ background: color ?? 'var(--accent)' }"
    ></div>

    <div class="relative z-10">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium" :style="{ color: 'var(--text-secondary)' }">{{ title }}</span>
        <span v-if="icon" class="text-lg" :style="{ color: 'var(--text-tertiary)' }">{{ icon }}</span>
      </div>
      <div class="flex items-baseline gap-1.5">
        <span class="text-2xl font-bold tracking-tight" :style="{ color: 'var(--text-primary)' }">{{ value }}</span>
        <span v-if="unit" class="text-sm" :style="{ color: 'var(--text-tertiary)' }">{{ unit }}</span>
      </div>
    </div>
  </div>
</template>
