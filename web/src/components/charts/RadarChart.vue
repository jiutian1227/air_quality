<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { useChartTheme } from '@/composables/useChartTheme'

const { chartColors } = useChartTheme()

const props = withDefaults(
  defineProps<{
    data: Record<string, any>[]
    indicators: { name: string; max: number }[]
    title?: string
    seriesName?: string
    height?: string
  }>(),
  { title: '', seriesName: '数据', height: '400px' }
)

// 四季固定配色：春绿、夏红、秋黄、冬蓝
const seasonColorList = [
  { main: '#36c687', area: 'rgba(54, 198, 135, 0.2)' }, // 春
  { main: '#f56c6c', area: 'rgba(245, 108, 108, 0.2)' }, // 夏
  { main: '#e6a23c', area: 'rgba(230, 162, 60, 0.2)' }, // 秋
  { main: '#409eff', area: 'rgba(64, 158, 255, 0.2)' }  // 冬
]

const options = computed(() => {
  const colors = chartColors.value

  const splitColors = colors.textSecondary === '#64748b'
    ? ['rgba(226,232,240,0.1)', 'rgba(226,232,240,0.2)']
    : ['rgba(45,58,79,0.1)', 'rgba(45,58,79,0.2)']

  const seriesData = props.data.map((item) => {
    const values = props.indicators.map((ind) => item[ind.name] ?? 0)
    return { value: values, name: item.name ?? props.seriesName }
  })

  return {
    backgroundColor: 'transparent',
    title: {
      text: props.title,
      textStyle: { color: colors.textSecondary, fontSize: 14 }
    },
    tooltip: { backgroundColor: colors.backgroundColor, borderColor: colors.borderColor, textStyle: { color: colors.textPrimary } },
    legend: {
      show: seriesData.length > 1,
      bottom: 0,
      textStyle: { color: colors.textSecondary }
    },
    radar: {
      indicator: props.indicators,
      axisName: { color: colors.textSecondary },
      splitArea: { areaStyle: { color: splitColors } },
      axisLine: { lineStyle: { color: colors.borderColor } },
      splitLine: { lineStyle: { color: colors.borderColor } }
    },
    series: seriesData.map((item, idx) => {
      // 循环取四季配色，多条数据自动轮询
      const colorItem = seasonColorList[idx % seasonColorList.length]
      return {
        type: 'radar',
        data: [item],
        itemStyle: { color: colorItem.main },
        lineStyle: { color: colorItem.main },
        areaStyle: { color: colorItem.area }
      }
    }),
    color: seasonColorList.map(c => c.main)
  }
})
</script>

<template>
  <BaseChart :options="options" :height="height" />
</template>