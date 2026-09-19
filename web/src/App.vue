<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useTheme } from '@/composables/useTheme'

useTheme()
const route = useRoute()
const hideLayout = computed(() => route.meta?.hideLayout === true)
const collapsed = ref(false)
const toggleSidebar = () => {
  collapsed.value = !collapsed.value
}
</script>

<template>
  <div v-if="hideLayout" class="min-h-screen bg-[var(--bg-primary)]">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>

  <div v-else class="flex h-screen" style="background: var(--bg-primary);">
    <AppSidebar :collapsed="collapsed" />
    <div class="flex-1 flex flex-col overflow-hidden">
      <AppHeader :collapsed="collapsed" @toggle-sidebar="toggleSidebar" />
      <main class="flex-1 overflow-y-auto p-6">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style>
/* 页面切换动画 */
.page-enter-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
