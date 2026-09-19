import { ref, watch, onMounted } from 'vue'

export type Theme = 'dark' | 'light'

const currentTheme = ref<Theme>('dark')

export function useTheme() {
  const isDark = ref(currentTheme.value === 'dark')

  const toggleTheme = () => {
    currentTheme.value = currentTheme.value === 'dark' ? 'light' : 'dark'
    isDark.value = currentTheme.value === 'dark'
  }

  const applyTheme = () => {
    const html = document.documentElement
    if (currentTheme.value === 'dark') {
      html.classList.remove('light')
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
      html.classList.add('light')
    }
    // 设置 color-scheme 让浏览器原生控件也跟随主题
    html.style.colorScheme = currentTheme.value
  }

  watch(currentTheme, () => {
    applyTheme()
    localStorage.setItem('theme', currentTheme.value)
  })

  onMounted(() => {
    const saved = localStorage.getItem('theme') as Theme | null
    if (saved) {
      currentTheme.value = saved
      isDark.value = saved === 'dark'
    } else {
      // 检测系统偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      currentTheme.value = prefersDark ? 'dark' : 'light'
      isDark.value = prefersDark
    }
    applyTheme()
  })

  return {
    isDark,
    toggleTheme,
    currentTheme
  }
}
