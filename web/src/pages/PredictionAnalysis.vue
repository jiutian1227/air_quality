<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCsvData } from '@/composables/useCsvData'
import { useTheme } from '@/composables/useTheme'
import BaseChart from '@/components/charts/BaseChart.vue'

const { loadCsv, clearCache } = useCsvData()
const { isDark } = useTheme()

// 读取当前CSS变量实际颜色值
function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
function colors() {
  return {
    textPrimary: cssVar('--text-primary') || '#e8edf5',
    textSecondary: cssVar('--text-secondary') || '#8896b0',
    borderColor: cssVar('--border-color') || '#1e2d42',
  }
}

const loading = ref(true)

interface ModelMetrics {
  '模型': string
  'RMSE': number
  'MAE': number
  'R²': number
}

interface ModelResult {
  '日期': string
  '实际AQI': number
  '预测AQI': number
  '残差': number
}

interface ModelData {
  metrics: ModelMetrics | null
  results: ModelResult[]
  color: string
}

const modelConfig: Record<string, { color: string }> = {
  '线性回归': { color: '#3b82f6' },
  '随机森林': { color: '#10b981' },
  'MLP': { color: '#f59e0b' },
  'LightGBM': { color: '#8b5cf6' },
  'SVR': { color: '#ec4899' },
}

const activeModel = ref('线性回归')
const modelData = ref<Record<string, ModelData>>({})

async function loadAllData() {
  loading.value = true
  clearCache()
  const models = Object.keys(modelConfig)

  for (const model of models) {
    try {
      const [metricsRaw, resultsRaw] = await Promise.all([
        loadCsv(`/data/预测分析/${model}/评估指标.csv`).catch(() => []),
        loadCsv(`/data/预测分析/${model}/预测结果.csv`).catch(() => [])
      ])

      modelData.value[model] = {
        metrics: (metricsRaw.length > 0 ? metricsRaw[0] : null) as ModelMetrics | null,
        results: resultsRaw as ModelResult[],
        color: modelConfig[model].color
      }
    } catch (e) {
      console.error(`加载 ${model} 数据失败:`, e)
      modelData.value[model] = { metrics: null, results: [], color: modelConfig[model].color }
    }
  }

  loading.value = false
}

const comparisonOptions = computed(() => {
  isDark.value; const c = colors()
  const models = Object.keys(modelConfig)
  const metrics = models.map(m => modelData.value[m]?.metrics)

  if (!metrics[0] || metrics.some(m => !m)) return null

  const r2 = metrics.map(m => m!['R²'])
  const rmse = metrics.map(m => m!['RMSE'])
  const mae = metrics.map(m => m!['MAE'])

  return {
    backgroundColor: 'transparent',
    title: { text: '模型性能对比', textStyle: { color: c.textSecondary, fontSize: 14 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 30, textStyle: { color: c.textSecondary } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: models,
      axisLabel: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } }
    },
    yAxis: [
      {
        type: 'value', name: 'R²', position: 'left',
        axisLabel: { color: c.textSecondary },
        nameTextStyle: { color: c.textSecondary },
        splitLine: { lineStyle: { color: c.borderColor, type: 'dashed' } }
      },
      {
        type: 'value', name: 'RMSE / MAE', position: 'right',
        axisLabel: { color: c.textSecondary },
        nameTextStyle: { color: c.textSecondary },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: 'R²', type: 'bar', data: r2,
        itemStyle: { color: '#3b82f6' }, yAxisIndex: 0,
        label: { show: true, position: 'top', formatter: (p: any) => p.value.toFixed(3), color: c.textSecondary }
      },
      {
        name: 'RMSE', type: 'bar', data: rmse,
        itemStyle: { color: '#ef4444' }, yAxisIndex: 1,
        label: { show: true, position: 'top', formatter: (p: any) => p.value.toFixed(2), color: c.textSecondary }
      },
      {
        name: 'MAE', type: 'bar', data: mae,
        itemStyle: { color: '#10b981' }, yAxisIndex: 1,
        label: { show: true, position: 'top', formatter: (p: any) => p.value.toFixed(2), color: c.textSecondary }
      }
    ]
  }
})

const modelTabs = computed(() => Object.keys(modelConfig))

const compareChartOptions = computed(() => {
  const data = modelData.value[activeModel.value]
  if (!data || data.results.length === 0) return null

  isDark.value; const c = colors()
  // 取样（数据太多时抽样显示）
  const results = data.results
  const dates = results.map(r => r['日期'])
  const actual = results.map(r => r['实际AQI'])
  const predicted = results.map(r => r['预测AQI'])

  return {
    backgroundColor: 'transparent',
    title: { text: `${activeModel.value}: 实际值 vs 预测值`, textStyle: { color: c.textSecondary, fontSize: 14 }, top: 5, left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { top: 30, textStyle: { color: c.textSecondary } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category', data: dates,
      axisLabel: { color: c.textSecondary, rotate: 45 },
      axisLine: { lineStyle: { color: c.borderColor } }
    },
    yAxis: {
      name: 'AQI',
      axisLabel: { color: c.textSecondary },
      nameTextStyle: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } },
      splitLine: { lineStyle: { color: c.borderColor, type: 'dashed' } }
    },
    series: [
      {
        name: '实际', type: 'line', data: actual,
        itemStyle: { color: '#3b82f6' }, showSymbol: false, lineStyle: { width: 1 }
      },
      {
        name: '预测', type: 'line', data: predicted,
        itemStyle: { color: '#ef4444' }, showSymbol: false, lineStyle: { width: 1 }
      }
    ]
  }
})

const residualChartOptions = computed(() => {
  const data = modelData.value[activeModel.value]
  if (!data || data.results.length === 0) return null

  isDark.value; const c = colors()
  const results = data.results
  const dates = results.map(r => r['日期'])
  const residuals = results.map(r => r['残差'])

  return {
    backgroundColor: 'transparent',
    title: { text: `${activeModel.value}: 残差分析`, textStyle: { color: c.textSecondary, fontSize: 14 }, top: 5, left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category', data: dates,
      axisLabel: { color: c.textSecondary, rotate: 45 },
      axisLine: { lineStyle: { color: c.borderColor } }
    },
    yAxis: {
      name: '残差',
      axisLabel: { color: c.textSecondary },
      nameTextStyle: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } },
      splitLine: { lineStyle: { color: c.borderColor, type: 'dashed' } }
    },
    series: [{
      type: 'scatter', data: residuals,
      itemStyle: { color: '#64748b', opacity: 0.5 }, symbolSize: 4,
      markLine: {
        data: [{ yAxis: 0 }],
        lineStyle: { type: 'dashed', color: '#ef4444' }
      }
    }]
  }
})

const scatterChartOptions = computed(() => {
  const data = modelData.value[activeModel.value]
  if (!data || data.results.length === 0) return null

  isDark.value; const c = colors()
  const results = data.results
  const actual = results.map(r => r['实际AQI'])
  const predicted = results.map(r => r['预测AQI'])
  const scatterData = actual.map((a, i) => [a, predicted[i]])

  const minVal = Math.min(...actual, ...predicted)
  const maxVal = Math.max(...actual, ...predicted)

  return {
    backgroundColor: 'transparent',
    title: { text: `${activeModel.value}: 实际值 vs 预测值散点图`, textStyle: { color: c.textSecondary, fontSize: 14 }, top: 5, left: 'center' },
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => `实际: ${p.data[0].toFixed(1)}<br/>预测: ${p.data[1].toFixed(1)}`
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: {
      name: '实际AQI',
      axisLabel: { color: c.textSecondary },
      nameTextStyle: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } },
      splitLine: { lineStyle: { color: c.borderColor, type: 'dashed' } }
    },
    yAxis: {
      name: '预测AQI',
      axisLabel: { color: c.textSecondary },
      nameTextStyle: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } },
      splitLine: { lineStyle: { color: c.borderColor, type: 'dashed' } }
    },
    series: [
      {
        type: 'scatter', data: scatterData,
        itemStyle: { color: '#3b82f6', opacity: 0.3 }, symbolSize: 6
      },
      {
        type: 'line', data: [[minVal, minVal], [maxVal, maxVal]],
        itemStyle: { color: '#ef4444' }, showSymbol: false,
        lineStyle: { type: 'dashed', width: 2 }
      }
    ]
  }
})

onMounted(loadAllData)
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-xl font-semibold text-primary">预测分析</h2>

    <div v-if="loading" class="text-secondary text-center py-20">数据加载中...</div>

    <template v-else>
      <!-- 模型对比 -->
      <div class="card">
        <BaseChart v-if="comparisonOptions" :options="comparisonOptions" height="400px" />
      </div>

      <!-- 模型标签切换 -->
      <div class="card">
        <div class="flex flex-wrap gap-2 mb-6">
          <button
            v-for="model in modelTabs"
            :key="model"
            @click="activeModel = model"
            class="px-4 py-2 rounded-lg text-sm transition-all"
            :class="activeModel === model
              ? 'bg-[#00d4aa]/20 text-accent font-medium'
              : 'bg-card text-secondary hover:text-primary'"
          >
            {{ model }}
          </button>
        </div>

        <!-- 指标卡片 -->
        <div v-if="modelData[activeModel]?.metrics" class="grid grid-cols-3 gap-4 mb-6">
          <div class="bg-card/30 rounded-lg p-4 text-center">
            <div class="text-sm text-secondary">R²</div>
            <div class="text-2xl font-bold text-accent">{{ modelData[activeModel].metrics!['R²'].toFixed(3) }}</div>
          </div>
          <div class="bg-card/30 rounded-lg p-4 text-center">
            <div class="text-sm text-secondary">RMSE</div>
            <div class="text-2xl font-bold text-[#ef4444]">{{ modelData[activeModel].metrics!['RMSE'].toFixed(2) }}</div>
          </div>
          <div class="bg-card/30 rounded-lg p-4 text-center">
            <div class="text-sm text-secondary">MAE</div>
            <div class="text-2xl font-bold text-[#f59e0b]">{{ modelData[activeModel].metrics!['MAE'].toFixed(2) }}</div>
          </div>
        </div>

        <!-- 对比图 -->
        <BaseChart v-if="compareChartOptions" :options="compareChartOptions" height="400px" class="mb-6" />

        <!-- 残差图 -->
        <BaseChart v-if="residualChartOptions" :options="residualChartOptions" height="350px" class="mb-6" />

        <!-- 散点图 -->
        <BaseChart v-if="scatterChartOptions" :options="scatterChartOptions" height="400px" />
      </div>
    </template>
  </div>
</template>
