<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCsvData } from '@/composables/useCsvData'
import { useTheme } from '@/composables/useTheme'
import BaseChart from '@/components/charts/BaseChart.vue'
import DataTable from '@/components/common/DataTable.vue'

const { loadCsv, clearCache } = useCsvData()
const { isDark } = useTheme()

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

interface ParamResult {
  '模型': string
  '参数名': string
  '搜索区间': string
  '最优值': string | number
  'CV_RMSE': number
}

interface ModelBestParams {
  [key: string]: string | number
}

const modelConfig: Record<string, { color: string; params: string[] }> = {
  '随机森林': { 
    color: '#10b981', 
    params: ['n_estimators', 'max_depth', 'min_samples_split'] 
  },
  'LightGBM': { 
    color: '#8b5cf6', 
    params: ['learning_rate', 'num_leaves', 'n_estimators'] 
  },
  'SVR': { 
    color: '#ec4899', 
    params: ['C', 'gamma', 'epsilon'] 
  },
  'MLP': { 
    color: '#f59e0b', 
    params: ['hidden_units', 'dropout_rate', 'learning_rate'] 
  },
}

const activeModel = ref('随机森林')
const modelParams = ref<Record<string, ModelBestParams>>({})
const cvResults = ref<Record<string, any[]>>({})
const metricsData = ref<Record<string, { CV_RMSE: number; RMSE: number; MAE: number; R2: number }>>({})

async function loadAllData() {
  loading.value = true
  clearCache()
  const models = Object.keys(modelConfig)

  for (const model of models) {
    try {
      const [paramsRaw, resultsRaw, metricsRaw] = await Promise.all([
        loadCsv(`/data/预测分析/${model}/最优参数.csv`).catch(() => []),
        loadCsv(`/data/预测分析/${model}/网格搜索结果_完整.csv`).catch(() => []),
        loadCsv(`/data/预测分析/${model}/评估指标.csv`).catch(() => [])
      ])

      if (paramsRaw.length > 0) {
        modelParams.value[model] = paramsRaw[0] as ModelBestParams
      }
      if (resultsRaw.length > 0) {
        cvResults.value[model] = resultsRaw
      }
      if (metricsRaw.length > 0) {
        metricsData.value[model] = {
          CV_RMSE: metricsRaw[0]['CV_RMSE'],
          RMSE: metricsRaw[0]['RMSE'],
          MAE: metricsRaw[0]['MAE'],
          R2: metricsRaw[0]['R²']
        }
      }
    } catch (e) {
      console.error(`加载 ${model} 数据失败:`, e)
    }
  }

  loading.value = false
}

const modelTabs = computed(() => Object.keys(modelConfig))

const paramTableData = computed(() => {
  const data: ParamResult[] = []
  const models = Object.keys(modelConfig)
  
  const paramRanges: Record<string, Record<string, string>> = {
    '随机森林': {
      'n_estimators': '[50, 100, 150, 200]',
      'max_depth': '[10, 15, 20, 25]',
      'min_samples_split': '[2, 5, 8]'
    },
    'LightGBM': {
      'learning_rate': '[0.01, 0.05, 0.1]',
      'num_leaves': '[15, 31, 50]',
      'n_estimators': '[100, 300, 500]'
    },
    'SVR': {
      'C': '[1, 10, 100, 200]',
      'gamma': '[0.01, 0.1, scale]',
      'epsilon': '[0.01, 0.1, 0.5]'
    },
    'MLP': {
      'hidden_units': '[64, 128]',
      'dropout_rate': '[0.2, 0.3]',
      'learning_rate': '[0.001, 0.01]'
    }
  }

  models.forEach(model => {
    const params = modelConfig[model].params
    const bestParams = modelParams.value[model]
    const cvRmse = metricsData.value[model]?.CV_RMSE || 0

    params.forEach(param => {
      data.push({
        '模型': model,
        '参数名': param,
        '搜索区间': paramRanges[model][param] || '-',
        '最优值': bestParams?.[param] || '-',
        'CV_RMSE': cvRmse
      })
    })
  })

  return data
})

const paramTableColumns = [
  { key: '模型', label: '模型' },
  { key: '参数名', label: '参数名' },
  { key: '搜索区间', label: '搜索区间' },
  { key: '最优值', label: '最优值' },
  { key: 'CV_RMSE', label: 'CV_RMSE' },
]

const comparisonOptions = computed(() => {
  isDark.value; const c = colors()
  const models = Object.keys(modelConfig)
  const cvRmse = models.map(m => metricsData.value[m]?.CV_RMSE || 0)
  const testRmse = models.map(m => metricsData.value[m]?.RMSE || 0)

  return {
    backgroundColor: 'transparent',
    title: { text: '模型超参数寻优CV_RMSE对比', textStyle: { color: c.textSecondary, fontSize: 14 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 30, textStyle: { color: c.textSecondary } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: models,
      axisLabel: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } }
    },
    yAxis: {
      type: 'value', name: 'RMSE',
      axisLabel: { color: c.textSecondary },
      nameTextStyle: { color: c.textSecondary },
      splitLine: { lineStyle: { color: c.borderColor, type: 'dashed' } }
    },
    series: [
      {
        name: 'CV_RMSE', type: 'bar', data: cvRmse,
        itemStyle: { color: '#3b82f6' },
        label: { show: true, position: 'top', formatter: (p: any) => p.value.toFixed(3), color: c.textSecondary }
      },
      {
        name: 'Test_RMSE', type: 'bar', data: testRmse,
        itemStyle: { color: '#ef4444' },
        label: { show: true, position: 'top', formatter: (p: any) => p.value.toFixed(2), color: c.textSecondary }
      }
    ]
  }
})

const tuningCurveOptions = computed(() => {
  const data = cvResults.value[activeModel.value]
  if (!data || data.length === 0) return null

  isDark.value; const c = colors()
  const params = modelConfig[activeModel.value].params
  
  const option: any = {
    backgroundColor: 'transparent',
    title: { text: `${activeModel.value}: 超参数寻优曲线`, textStyle: { color: c.textSecondary, fontSize: 14 }, top: 5, left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { top: 30, textStyle: { color: c.textSecondary } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map((r: any) => {
        const paramValues = params.map(p => r[p]).join('-')
        return paramValues
      }).slice(0, 20),
      axisLabel: { color: c.textSecondary, rotate: 45 },
      axisLine: { lineStyle: { color: c.borderColor } }
    },
    yAxis: {
      type: 'value', name: 'RMSE',
      axisLabel: { color: c.textSecondary },
      nameTextStyle: { color: c.textSecondary },
      splitLine: { lineStyle: { color: c.borderColor, type: 'dashed' } }
    },
    series: [
      {
        name: 'RMSE', type: 'line', 
        data: data.slice(0, 20).map((r: any) => r['RMSE']),
        itemStyle: { color: modelConfig[activeModel.value].color },
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { width: 2 }
      }
    ]
  }

  return option
})

const paramsImportanceOptions = computed(() => {
  isDark.value; const c = colors()
  const models = Object.keys(modelConfig)
  const paramCounts = { '随机森林': 3, 'LightGBM': 3, 'SVR': 3, 'MLP': 3 }
  const cvRmses = models.map(m => metricsData.value[m]?.CV_RMSE || 0)

  return {
    backgroundColor: 'transparent',
    title: { text: '各模型寻优参数数量与CV_RMSE', textStyle: { color: c.textSecondary, fontSize: 14 }, top: 5, left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { top: 30, textStyle: { color: c.textSecondary } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: [
      {
        type: 'category',
        data: models,
        axisLabel: { color: c.textSecondary },
        axisLine: { lineStyle: { color: c.borderColor } }
      }
    ],
    yAxis: [
      {
        type: 'value', name: 'CV_RMSE', position: 'left',
        axisLabel: { color: c.textSecondary },
        nameTextStyle: { color: c.textSecondary },
        splitLine: { lineStyle: { color: c.borderColor, type: 'dashed' } }
      },
      {
        type: 'value', name: '参数数量', position: 'right',
        axisLabel: { color: c.textSecondary },
        nameTextStyle: { color: c.textSecondary },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: 'CV_RMSE', type: 'bar', data: cvRmses,
        itemStyle: { color: '#3b82f6' },
        label: { show: true, position: 'top', formatter: (p: any) => p.value.toFixed(3), color: c.textSecondary }
      },
      {
        name: '参数数量', type: 'line', data: models.map(m => paramCounts[m]),
        itemStyle: { color: '#10b981' },
        symbol: 'circle',
        symbolSize: 8,
        yAxisIndex: 1,
        lineStyle: { width: 2 }
      }
    ]
  }
})

const bestParamsTableData = computed(() => {
  const data: any[] = []
  const models = Object.keys(modelConfig)
  
  models.forEach(model => {
    const params = modelParams.value[model]
    const metrics = metricsData.value[model]
    
    if (params) {
      const row: any = { '模型': model }
      modelConfig[model].params.forEach(param => {
        row[param] = params[param] || '-'
      })
      row['CV_RMSE'] = metrics?.CV_RMSE || '-'
      row['R²'] = metrics?.R2 ? metrics.R2.toFixed(4) : '-'
      data.push(row)
    }
  })

  return data
})

const bestParamsColumns = computed(() => {
  const cols = [{ key: '模型', label: '模型' }]
  const allParams = new Set<string>()
  
  Object.values(modelConfig).forEach(config => {
    config.params.forEach(p => allParams.add(p))
  })
  
  allParams.forEach(p => cols.push({ key: p, label: p }))
  
  cols.push({ key: 'CV_RMSE', label: 'CV_RMSE' })
  cols.push({ key: 'R²', label: 'R²' })
  
  return cols
})

onMounted(loadAllData)
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-xl font-semibold text-primary">超参数调优</h2>

    <div v-if="loading" class="text-secondary text-center py-20">数据加载中...</div>

    <template v-else>
      <!-- 模型寻优对比 -->
      <div class="card">
        <BaseChart v-if="comparisonOptions" :options="comparisonOptions" height="400px" />
      </div>

      <!-- 参数数量与CV_RMSE对比 -->
      <div class="card">
        <BaseChart v-if="paramsImportanceOptions" :options="paramsImportanceOptions" height="350px" />
      </div>

      <!-- 最优参数汇总表 -->
      <div class="card">
        <h3 class="text-sm font-medium text-secondary mb-4">各模型最优参数汇总</h3>
        <DataTable :columns="bestParamsColumns" :data="bestParamsTableData" />
      </div>

      <!-- 参数寻优详情表 -->
      <div class="card">
        <h3 class="text-sm font-medium text-secondary mb-4">参数寻优详情</h3>
        <DataTable :columns="paramTableColumns" :data="paramTableData" />
      </div>

      <!-- 模型切换与参数寻优图 -->
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

        <!-- 超参数寻优综合图 -->
        <div class="space-y-8">
          <div>
            <h3 class="text-sm font-medium text-secondary mb-4">超参数寻优综合图 - 3x3网格</h3>
            <img 
              :src="`/data/预测分析/${activeModel}/超参数寻优综合图_3x3网格.png`"
              :alt="`${activeModel} 超参数寻优综合图 - 3x3网格`"
              class="w-full rounded-lg"
              @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
            />
          </div>
          
          <div>
            <h3 class="text-sm font-medium text-secondary mb-4">超参数寻优综合图 - 指标对比</h3>
            <img 
              :src="`/data/预测分析/${activeModel}/超参数寻优综合图_指标对比.png`"
              :alt="`${activeModel} 超参数寻优综合图 - 指标对比`"
              class="w-full rounded-lg"
              @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
            />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
