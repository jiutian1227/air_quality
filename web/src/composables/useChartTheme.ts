import { computed } from 'vue'
import { useTheme } from './useTheme'

export function useChartTheme() {
  const { isDark } = useTheme()

  const chartColors = computed(() => ({
    textPrimary: isDark.value ? '#f1f5f9' : '#1e293b',
    textSecondary: isDark.value ? '#94a3b8' : '#64748b',
    borderColor: isDark.value ? '#2d3a4f' : '#e2e8f0',
    gridColor: isDark.value ? '#2d3a4f' : '#e2e8f0',
    backgroundColor: isDark.value ? '#1e293b' : '#ffffff',
    accent: '#00d4aa',
    accentPurple: '#8b5cf6',
    colorPalette: [
      '#00d4aa',
      '#3b82f6',
      '#f59e0b',
      '#ef4444',
      '#8b5cf6',
      '#ec4899',
      '#14b8a6',
      '#f97316'
    ],
    qualityColors: {
      '优': '#00d4aa',
      '良': '#84cc16',
      '轻度污染': '#eab308',
      '中度污染': '#f97316',
      '重度污染': '#ef4444',
      '严重污染': '#dc2626'
    }
  }))

  return { chartColors }
}