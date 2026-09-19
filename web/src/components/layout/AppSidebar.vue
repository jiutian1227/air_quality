<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CircleDot,
  BarChart3,
  Activity,
  TrendingUpDown,
  User,
  LogOut,
  Settings,
  LineChart,
} from 'lucide-vue-next'
import { ref } from 'vue'

const props = defineProps<{ collapsed: boolean }>()
const route = useRoute()
const router = useRouter()

// 弹窗状态
const showLogoutModal = ref(false)

const navItems = [
  { name: 'eda', path: '/eda', label: 'EDA数据分析', icon: BarChart3 },
  { name: 'feature', path: '/feature', label: '特征工程', icon: Activity },
  { name: 'clustering', path: '/clustering', label: '聚类分析', icon: CircleDot },
  { name: 'tuning', path: '/tuning', label: '超参数调优', icon: Settings },
  { name: 'prediction', path: '/prediction', label: '预测分析', icon: LineChart },
  { name: 'online-prediction', path: '/online-prediction', label: '在线预测', icon: TrendingUpDown },
]

// 获取当前登录用户
const currentUser = computed(() => {
  try {
    const userStr = window.localStorage.getItem('currentUser')
    return userStr ? JSON.parse(userStr) : null
  } catch {
    return null
  }
})

const isActive = computed(() => (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
})

// 映射课程名称
const courseName = computed(() => {
  return '神经网络与机器学习课程设计'
})

// 退出登录
const handleLogout = () => {
  window.localStorage.removeItem('currentUser')
  showLogoutModal.value = false
  // 跳转到登录页，请根据你实际登录路由修改
  router.push('/login')
}
</script>

<template>
  <aside
    class="relative flex flex-col shrink-0 transition-all duration-300 ease-in-out"
    :class="props.collapsed ? 'w-20' : 'w-64'"
    style="background: var(--bg-secondary); border-right: 1px solid var(--border-color);"
  >
    <!-- Logo -->
    <div
      class="flex items-center gap-3 px-5 h-16 shrink-0"
      :class="props.collapsed ? 'justify-center px-0' : ''"
      style="border-bottom: 1px solid var(--border-color);"
    >
      <div
        class="w-9 h-9 rounded-xl bg-transparent flex items-center justify-center shadow-lg shrink-0"
        style="box-shadow: 0 0 20px rgba(0, 212, 170, 0.25);"
      >
        <img src="/favicon.png" alt="AQ" class="text-white text-sm font-bold" />
      </div>
      <transition name="fade">
        <span v-if="!props.collapsed" class="font-semibold text-base tracking-wide truncate" style="color: var(--text-primary);">兰州市空气质量平台</span>
      </transition>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 px-3 space-y-1 overflow-y-auto overflow-x-hidden">
      <!-- 常规导航项 -->
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        class="flex items-center gap-3 rounded-xl text-sm font-medium transition-all duration-200 group relative"
        :class="[
          props.collapsed ? 'px-0 py-3 justify-center' : 'px-3 py-2.5',
          isActive(item.path)
            ? 'nav-item-active'
            : 'nav-item-inactive'
        ]"
        :style="isActive(item.path)
          ? { background: 'rgba(0, 212, 170, 0.12)', color: 'var(--accent)' }
          : { color: 'var(--text-secondary)' }"
        @mouseenter="($event) => { if (!isActive(item.path)) { ($event.currentTarget as HTMLElement).style.background = 'var(--border-color)'; ($event.currentTarget as HTMLElement).style.color = 'var(--text-primary)' } }"
        @mouseleave="($event) => { if (!isActive(item.path)) { ($event.currentTarget as HTMLElement).style.background = 'transparent'; ($event.currentTarget as HTMLElement).style.color = 'var(--text-secondary)' } }"
      >
        <component :is="item.icon" class="w-5 h-5 shrink-0" />
        <transition name="fade">
          <span v-if="!props.collapsed">{{ item.label }}</span>
        </transition>
        <div v-if="isActive(item.path)" class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full" style="background: var(--accent);"></div>
      </router-link>

    </nav>

    <!-- 底部：用户信息 + 退出按钮 -->
    <div 
      class="shrink-0 py-4 border-t"
      style="border-color: var(--border-color);"
    >
      <!-- 侧边栏展开 -->
      <div v-if="!props.collapsed" class="px-4">
        <div class="flex items-center gap-3 p-3 rounded-xl" style="background: var(--border-color);">
          <User class="w-5 h-5 shrink-0" style="color: var(--accent);" />
          <div class="flex flex-col truncate flex-1">
            <span class="text-sm font-medium truncate" style="color: var(--text-primary);">
              {{ currentUser?.username || '未知用户' }}
            </span>
            <span class="text-xs mt-0.5 truncate" style="color: var(--text-tertiary);">
              {{ courseName }}
            </span>
          </div>
          <!-- 退出登录按钮 -->
          <button
            @click="showLogoutModal = true"
            class="p-2 rounded-lg transition-all hover:opacity-80"
            style="color: var(--text-tertiary);"
            title="退出登录"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- 侧边栏收起 -->
      <div v-else class="flex justify-center">
        <button
          @click="showLogoutModal = true"
          class="p-2 rounded-xl transition-all hover:opacity-80"
          style="background: var(--border-color); color: var(--accent);"
          title="退出登录"
        >
          <User class="w-5 h-5" />
        </button>
      </div>
    </div>
  </aside>

  <!-- 退出确认弹窗 -->
  <div v-if="showLogoutModal" class="fixed inset-0 flex items-center justify-center z-50" style="background: rgba(0,0,0,0.4);">
    <div 
      class="w-72 p-5 rounded-2xl shadow-xl"
      style="background: var(--bg-secondary); border: 1px solid var(--border-color);"
    >
      <h3 class="text-base font-medium mb-3" style="color: var(--text-primary);">温馨提示</h3>
      <p class="text-sm mb-6" style="color: var(--text-secondary);">确定要退出当前账号吗？</p>
      <div class="flex justify-end gap-3">
        <button
          @click="showLogoutModal = false"
          class="px-4 py-2 rounded-lg text-sm transition-all"
          style="border: 1px solid var(--border-color); color: var(--text-secondary);"
        >
          取消
        </button>
        <button
          @click="handleLogout"
          class="px-4 py-2 rounded-lg text-sm text-white transition-all"
          style="background: var(--accent);"
        >
          确定退出
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 导航悬浮效果 */
.nav-item-inactive:hover {
  background: var(--border-color) !important;
  color: var(--text-primary) !important;
}

/* 滚动条细化 */
aside::-webkit-scrollbar {
  width: 3px;
}
</style>