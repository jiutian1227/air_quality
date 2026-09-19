<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { Sun, Moon, Bell, ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps<{ collapsed: boolean }>()
const emit = defineEmits<{
  'toggle-sidebar': []
}>()

const route = useRoute()
const { isDark, toggleTheme } = useTheme()

const pageTitle = computed(() => {
  return (route.meta?.title as string) || '数据总览'
})
</script>

<template>
  <header
    class="h-16 flex items-center justify-between px-6 shrink-0 backdrop-blur-md"
    :style="{
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-color)',
    }"
  >
    <!-- 左侧：侧边栏切换箭头 + 标题 -->
    <div class="flex items-center gap-4">
      <!-- 仅箭头，无文字 -->
      <button
        @click="emit('toggle-sidebar')"
        class="flex items-center rounded-xl border p-2 transition-all duration-200"
        :style="{
          color: 'var(--text-secondary)',
          borderColor: 'var(--border-color)',
          background: 'transparent',
        }"
        @mouseenter="($event) => { ($event.currentTarget as HTMLElement).style.background = 'var(--border-color)'; ($event.currentTarget as HTMLElement).style.color = 'var(--text-primary)' }"
        @mouseleave="($event) => { ($event.currentTarget as HTMLElement).style.background = 'transparent'; ($event.currentTarget as HTMLElement).style.color = 'var(--text-secondary)' }"
        :title="props.collapsed ? '展开侧栏' : '收起侧栏'"
      >
        <component :is="props.collapsed ? ChevronRight : ChevronLeft" class="w-4 h-4" />
      </button>

      <h1
        class="text-lg font-semibold tracking-wide"
        :style="{ color: 'var(--text-primary)' }"
      >
        {{ pageTitle }}
      </h1>
      <span
        class="hidden sm:inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium"
        :style="{
          background: 'rgba(0, 212, 170, 0.1)',
          color: 'var(--accent)',
          border: '1px solid rgba(0, 212, 170, 0.2)',
        }"
      >
        空气监测
      </span>
    </div>

    <!-- 右侧：通知、主题切换 -->
    <div class="flex items-center gap-2">
      <!-- 通知按钮 -->
      <button
        class="p-2.5 rounded-xl transition-all duration-200"
        :style="{ color: 'var(--text-tertiary)' }"
        @mouseenter="($event) => { ($event.currentTarget as HTMLElement).style.background = 'var(--border-color)'; ($event.currentTarget as HTMLElement).style.color = 'var(--text-primary)' }"
        @mouseleave="($event) => { ($event.currentTarget as HTMLElement).style.background = 'transparent'; ($event.currentTarget as HTMLElement).style.color = 'var(--text-tertiary)' }"
        title="通知"
      >
        <Bell class="w-5 h-5" />
      </button>

      <!-- 主题切换 -->
      <button
        @click="toggleTheme"
        class="p-2.5 rounded-xl transition-all duration-200 relative overflow-hidden"
        :style="{ color: 'var(--text-secondary)' }"
        @mouseenter="($event) => { ($event.currentTarget as HTMLElement).style.background = 'var(--border-color)'; ($event.currentTarget as HTMLElement).style.color = 'var(--text-primary)' }"
        @mouseleave="($event) => { ($event.currentTarget as HTMLElement).style.background = 'transparent'; ($event.currentTarget as HTMLElement).style.color = 'var(--text-secondary)' }"
        :title="isDark ? '切换到浅色主题' : '切换到深色主题'"
      >
        <div class="transition-transform duration-500" :class="isDark ? 'rotate-0' : 'rotate-90'">
          <Sun v-if="isDark" class="w-5 h-5" />
          <Moon v-else class="w-5 h-5" />
        </div>
      </button>
    </div>
  </header>
</template>