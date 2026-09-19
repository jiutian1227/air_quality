<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCsvData } from '@/composables/useCsvData'
import { useChartTheme } from '@/composables/useChartTheme'
import BaseChart from '@/components/charts/BaseChart.vue'
import RadarChart from '@/components/charts/RadarChart.vue'

const { loadCsv, clearCache } = useCsvData()
const { chartColors } = useChartTheme()

const loading = ref(true)
const pcaClusteringData = ref<any[]>([])
const clusterStatsData = ref<any[]>([])
const elbowCsvData = ref<any[]>([])
const pcaVarianceData = ref<any[]>([])

// 聚类预测表单
const predictForm = ref({
  pm25: 50,
  pm10: 100,
  no2: 40,
  so2: 20,
  co: 1.0,
  o3: 60,
  aqi_lag1: 80,
  pm25_roll7_mean: 55
})
const predictResult = ref<any>(null)
const predictLoading = ref(false)
const predictError = ref('')
const apiBase = 'http://localhost:8000'

async function runClusterPredict() {
  predictLoading.value = true
  predictError.value = ''
  predictResult.value = null
  try {
    const res = await fetch(`${apiBase}/api/predict/cluster`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(predictForm.value)
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `请求失败: ${res.status}`)
    }
    predictResult.value = await res.json()
  } catch (e: any) {
    predictError.value = e.message || '预测失败，请确认后端服务已启动'
  } finally {
    predictLoading.value = false
  }
}

// 肘部法则图
const elbowOptions = computed(() => {
  if (elbowCsvData.value.length === 0) return null

  const xData = elbowCsvData.value.map((r: any) => Number(r['聚类数量k']))
  const yData = elbowCsvData.value.map((r: any) => Number(r['惯性值']))

  const c = chartColors.value
    return {
    backgroundColor: 'transparent',
    title: { text: '肘部法则 - 确定最佳聚类数', textStyle: { color: c.textSecondary, fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `聚类数 k=${data.name}<br/>惯性值: ${data.value.toFixed(2)}`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: xData,
      name: '聚类数量 (k)',
      nameTextStyle: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } },
      axisLabel: { color: c.textSecondary }
    },
    yAxis: {
      type: 'value',
      name: '惯性 (Inertia)',
      nameTextStyle: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } },
      axisLabel: { color: c.textSecondary },
      splitLine: { lineStyle: { color: c.gridColor, type: 'dashed' } }
    },
    series: [{
      name: '惯性值',
      type: 'line',
      data: yData,
      smooth: false,
      symbol: 'circle',
      symbolSize: 10,
      lineStyle: { color: '#00d4aa', width: 2 },
      itemStyle: { color: c.accent, borderColor: c.backgroundColor, borderWidth: 2 },
      areaStyle: { opacity: 0.1, color: '#00d4aa' }
    }]
  }
})

// PCA方差解释率图
const pcaVarianceOptions = computed(() => {
  if (pcaVarianceData.value.length === 0) return null

  const names = pcaVarianceData.value.map((r: any) => r['主成分'])
  const variance = pcaVarianceData.value.map((r: any) => Number(r['方差解释率']))
  const cumVar = pcaVarianceData.value.map((r: any) => Number(r['累计方差解释率']))

  const c = chartColors.value
    return {
    backgroundColor: 'transparent',
    title: { text: 'PCA方差解释率', textStyle: { color: c.textSecondary, fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p1 = params[0]
        const p2 = params[1]
        return `${p1.name}<br/>${p1.seriesName}: ${(p1.value * 100).toFixed(2)}%<br/>${p2.seriesName}: ${(p2.value * 100).toFixed(2)}%`
      }
    },
    legend: { top: 30, textStyle: { color: c.textSecondary } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: names,
      axisLine: { lineStyle: { color: c.borderColor } },
      axisLabel: { color: c.textSecondary }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: c.textSecondary,
        formatter: (v: number) => `${(v * 100).toFixed(0)}%`
      },
      axisLine: { lineStyle: { color: c.borderColor } },
      splitLine: { lineStyle: { color: c.gridColor, type: 'dashed' } }
    },
    series: [
      {
        name: '方差解释率',
        type: 'bar',
        data: variance,
        itemStyle: { color: '#3b82f6' },
        label: {
          show: true,
          position: 'top',
          formatter: (p: any) => `${(p.value * 100).toFixed(1)}%`,
          color: c.textSecondary
        }
      },
      {
        name: '累计方差解释率',
        type: 'line',
        data: cumVar,
        smooth: true,
        symbol: 'circle',
        symbolSize: 10,
        itemStyle: { color: '#00d4aa' },
        lineStyle: { width: 2 },
        label: {
          show: true,
          position: 'top',
          formatter: (p: any) => `${(p.value * 100).toFixed(1)}%`,
          color: '#00d4aa'
        }
      }
    ]
  }
})

// 聚类划分标准表
const clusterCriteria = computed(() => {
  if (clusterStatsData.value.length === 0) return []

  const nameMap: Record<number, string> = {
    0: '轻度污染', 1: '优良天气', 2: '轻度污染', 3: '沙尘型污染'
  }
  const criteriaMap: Record<number, string> = {
    0: 'PM2.5 > 35 或 PM10 > 70',
    1: 'PM2.5 ≤ 35 且 PM10 ≤ 70',
    2: 'PM2.5 > 35 或 PM10 > 70',
    3: '(PM2.5 > 75 或 PM10 > 150) 且 SO₂ ≤ 50',
  }

  return clusterStatsData.value.map((r: any) => {
    const idx = Number(r['聚类'])
    return {
      cluster: `聚类${idx + 1}`,
      name: nameMap[idx] || '',
      criteria: criteriaMap[idx] || '',
      pm25: Number(r['PM2.5']),
      pm10: Number(r['PM10']),
      so2: Number(r['SO2']),
      count: Number(r['样本数量']),
      pct: Number(r['占比(%)']),
    }
  })
})

// PCA聚类散点图
const pcaClusteringOptions = computed(() => {
  if (pcaClusteringData.value.length === 0) return null

  const clusters = [...new Set(pcaClusteringData.value.map((r: any) => Number(r['聚类'])))]
  const colors = ['#00d4aa', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
  const clusterNameMap: Record<number, string> = {
    0: '轻度污染',
    1: '优良天气',
    2: '轻度污染',
    3: '沙尘型污染'
  }

  const series = clusters.map((cluster) => ({
    name: `聚类${cluster + 1} (${clusterNameMap[cluster] || ''})`,
    type: 'scatter',
    data: pcaClusteringData.value
      .filter((r: any) => Number(r['聚类']) === cluster)
      .map((r: any) => [Number(r['PC1']), Number(r['PC2'])]),
    symbolSize: 6,
    itemStyle: { color: colors[cluster % colors.length], opacity: 0.6 }
  }))

  // 计算聚类中心（PC1、PC2 均值）
  const centroids = clusters.map((cluster) => {
    const points = pcaClusteringData.value
      .filter((r: any) => Number(r['聚类']) === cluster)
      .map((r: any) => [Number(r['PC1']), Number(r['PC2'])])
    const pc1 = points.reduce((s: number, p: number[]) => s + p[0], 0) / points.length
    const pc2 = points.reduce((s: number, p: number[]) => s + p[1], 0) / points.length
    const stats = clusterStatsData.value.find((s: any) => Number(s['聚类']) === cluster)
    return {
      cluster,
      pc1: Math.round(pc1 * 100) / 100,
      pc2: Math.round(pc2 * 100) / 100,
      count: stats ? Number(stats['样本数量']) : points.length,
      pct: stats ? Number(stats['占比(%)']) : 0,
      name: `聚类${cluster + 1} (${clusterNameMap[cluster] || ''})`,
    }
  })

  // 添加聚类中心点（大标记 + 标签）
  centroids.forEach((cent) => {
    series.push({
      type: 'scatter',
      name: `中心-${cent.cluster + 1}`,
      data: [[cent.pc1, cent.pc2]],
      symbolSize: 26,
      itemStyle: {
        color: colors[cent.cluster % colors.length],
        borderColor: '#ffffff',
        borderWidth: 3,
        shadowBlur: 12,
        shadowColor: 'rgba(0,0,0,0.4)',
      },
      label: {
        show: true,
        formatter: `聚类${cent.cluster + 1}中心`,
        fontSize: 11,
        fontWeight: 'bold',
        color: '#ffffff',
        backgroundColor: 'rgba(0,0,0,0.65)',
        padding: [3, 8],
        borderRadius: 4,
        position: 'right',
        distance: 10,
      },
      emphasis: { scale: 1.8 },
      tooltip: {
        formatter: () => {
          return `<b style="font-size:14px;">${cent.name}</b><br/>
  <span style="color:${colors[cent.cluster % colors.length]};">●</span> 聚类中心<br/>
  PC1: <b>${cent.pc1}</b><br/>
  PC2: <b>${cent.pc2}</b><br/>
  样本数: <b>${cent.count}</b>（${cent.pct}%）`
        },
      },
      z: 10,
    })
  })

  const c = chartColors.value
    return {
    backgroundColor: 'transparent',
    title: { text: 'PCA降维K-Means聚类散点图（2D）', textStyle: { color: c.textSecondary, fontSize: 14 } },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `聚类: ${params.seriesName}<br/>PC1: ${params.data[0].toFixed(2)}<br/>PC2: ${params.data[1].toFixed(2)}`
      }
    },
    legend: {
      bottom: '2%',
      data: clusters.map((cl) => `聚类${cl + 1} (${clusterNameMap[cl] || ''})`),
      textStyle: { color: c.textSecondary },
    },
    grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
    xAxis: {
      type: 'value',
      name: '主成分1 (PC1)',
      nameTextStyle: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } },
      axisLabel: { color: c.textSecondary },
      splitLine: { lineStyle: { color: c.gridColor, type: 'dashed' } }
    },
    yAxis: {
      type: 'value',
      name: '主成分2 (PC2)',
      nameTextStyle: { color: c.textSecondary },
      axisLine: { lineStyle: { color: c.borderColor } },
      axisLabel: { color: c.textSecondary },
      splitLine: { lineStyle: { color: c.gridColor, type: 'dashed' } }
    },
    series
  }
})

// 聚类中心雷达图
const clusterRadarData = computed(() => {
  if (clusterStatsData.value.length === 0) return { data: [], indicators: [] }

  const pollutantKeys = ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
  const maxValues: Record<string, number> = {
    'PM2.5': 100, 'PM10': 200, 'NO2': 100, 'SO2': 50, 'CO': 3, 'O3': 100
  }
  const indicators = pollutantKeys.map((k) => ({ name: k, max: maxValues[k] }))

  const data = clusterStatsData.value.map((r: any) => {
    const row: Record<string, any> = { name: `聚类${Number(r['聚类']) + 1}` }
    pollutantKeys.forEach((k) => {
      row[k] = Number(r[k] || 0)
    })
    return row
  })

  return { data, indicators }
})

async function loadData() {
  loading.value = true
  clearCache()
  try {
    const [pcaData, statsData, elbowData, varianceData] = await Promise.all([
      loadCsv('/data/降维聚类/PCA聚类结果.csv').catch(() => []),
      loadCsv('/data/降维聚类/聚类统计信息.csv').catch(() => []),
      loadCsv('/data/降维聚类/肘部法则数据.csv').catch(() => []),
      loadCsv('/data/降维聚类/PCA方差解释率.csv').catch(() => [])
    ])
    pcaClusteringData.value = pcaData
    clusterStatsData.value = statsData
    elbowCsvData.value = elbowData
    pcaVarianceData.value = varianceData
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-xl font-semibold text-primary">降维聚类分析</h2>

    <div v-if="loading" class="text-secondary text-center py-20">数据加载中...</div>

    <template v-else>
      <!-- 第1行：肘部法则图 -->
      <div class="card">
        <BaseChart v-if="elbowOptions" :options="elbowOptions" height="350px" />
        <div v-else class="text-secondary text-center py-10">暂无肘部法则数据</div>
      </div>

      <!-- 第2行：PCA方差解释率 -->
      <div class="card">
        <BaseChart v-if="pcaVarianceOptions" :options="pcaVarianceOptions" height="350px" />
        <div v-else class="text-secondary text-center py-10">暂无PCA方差数据</div>
      </div>

      <!-- 第3行：聚类划分标准 -->
      <div class="card" v-if="clusterCriteria.length > 0">
        <h3 class="text-base font-semibold text-primary mb-4">聚类划分标准</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-secondary border-b" style="border-color: var(--border-color);">
                <th class="text-left py-2.5 px-3 font-medium">聚类</th>
                <th class="text-left py-2.5 px-3 font-medium">名称</th>
                <th class="text-left py-2.5 px-3 font-medium">划分标准</th>
                <th class="text-right py-2.5 px-3 font-medium">PM2.5</th>
                <th class="text-right py-2.5 px-3 font-medium">PM10</th>
                <th class="text-right py-2.5 px-3 font-medium">SO₂</th>
                <th class="text-right py-2.5 px-3 font-medium">样本数</th>
                <th class="text-right py-2.5 px-3 font-medium">占比</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, i) in clusterCriteria"
                :key="i"
                class="border-b transition-colors hover:opacity-80"
                style="border-color: var(--border-color);"
              >
                <td class="py-2.5 px-3 text-primary font-medium">{{ row.cluster }}</td>
                <td class="py-2.5 px-3 text-primary">{{ row.name }}</td>
                <td class="py-2.5 px-3" style="color: var(--text-secondary); font-size: 12px;">{{ row.criteria }}</td>
                <td class="py-2.5 px-3 text-right text-primary">{{ row.pm25.toFixed(1) }}</td>
                <td class="py-2.5 px-3 text-right text-primary">{{ row.pm10.toFixed(1) }}</td>
                <td class="py-2.5 px-3 text-right text-primary">{{ row.so2.toFixed(1) }}</td>
                <td class="py-2.5 px-3 text-right text-primary">{{ row.count }}</td>
                <td class="py-2.5 px-3 text-right text-primary">{{ row.pct }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 第4行：PCA聚类散点图（2D） -->
      <div class="card">
        <BaseChart v-if="pcaClusteringOptions" :options="pcaClusteringOptions" height="450px" />
        <div v-else class="text-secondary text-center py-10">暂无PCA聚类数据</div>
      </div>

      <!-- 第5行：聚类中心雷达图 -->
      <div class="card">
        <RadarChart v-if="clusterRadarData.data.length > 0" :data="clusterRadarData.data" :indicators="clusterRadarData.indicators" title="聚类中心特征对比（雷达图）" height="450px" />
        <div v-else class="text-secondary text-center py-10">暂无聚类中心数据</div>
      </div>

      <!-- 第6行：在线聚类预测 -->
<!--      <div class="card">-->
<!--        <h3 class="text-lg font-medium text-primary mb-4">在线聚类预测（输入污染物数据 → 预测所属类别）</h3>-->
<!--        <div class="grid grid-cols-4 gap-4 mb-4">-->
<!--          <label class="flex flex-col text-sm">-->
<!--            <span class="text-secondary mb-1">PM2.5 (μg/m³)</span>-->
<!--            <input v-model.number="predictForm.pm25" type="number" step="0.1" class="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" />-->
<!--          </label>-->
<!--          <label class="flex flex-col text-sm">-->
<!--            <span class="text-secondary mb-1">PM10 (μg/m³)</span>-->
<!--            <input v-model.number="predictForm.pm10" type="number" step="0.1" class="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" />-->
<!--          </label>-->
<!--          <label class="flex flex-col text-sm">-->
<!--            <span class="text-secondary mb-1">NO2 (μg/m³)</span>-->
<!--            <input v-model.number="predictForm.no2" type="number" step="0.1" class="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" />-->
<!--          </label>-->
<!--          <label class="flex flex-col text-sm">-->
<!--            <span class="text-secondary mb-1">SO2 (μg/m³)</span>-->
<!--            <input v-model.number="predictForm.so2" type="number" step="0.1" class="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" />-->
<!--          </label>-->
<!--          <label class="flex flex-col text-sm">-->
<!--            <span class="text-secondary mb-1">CO (mg/m³)</span>-->
<!--            <input v-model.number="predictForm.co" type="number" step="0.01" class="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" />-->
<!--          </label>-->
<!--          <label class="flex flex-col text-sm">-->
<!--            <span class="text-secondary mb-1">O3 (μg/m³)</span>-->
<!--            <input v-model.number="predictForm.o3" type="number" step="0.1" class="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" />-->
<!--          </label>-->
<!--          <label class="flex flex-col text-sm">-->
<!--            <span class="text-secondary mb-1">AQI_lag1 (昨日AQI)</span>-->
<!--            <input v-model.number="predictForm.aqi_lag1" type="number" step="0.1" class="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" />-->
<!--          </label>-->
<!--          <label class="flex flex-col text-sm">-->
<!--            <span class="text-secondary mb-1">PM2.5_roll7_mean (7日均值)</span>-->
<!--            <input v-model.number="predictForm.pm25_roll7_mean" type="number" step="0.1" class="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" />-->
<!--          </label>-->
<!--        </div>-->
<!--        <div class="flex items-center gap-3">-->
<!--          <button-->
<!--            @click="runClusterPredict"-->
<!--            :disabled="predictLoading"-->
<!--            class="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white rounded transition"-->
<!--          >-->
<!--            {{ predictLoading ? '预测中...' : '开始聚类预测' }}-->
<!--          </button>-->
<!--          <span v-if="predictError" class="text-red-400 text-sm">{{ predictError }}</span>-->
<!--        </div>-->

<!--        <div v-if="predictResult" class="mt-5 p-4 bg-gray-800 border border-gray-700 rounded-lg">-->
<!--          <h4 class="text-base font-semibold text-primary mb-3">预测结果</h4>-->
<!--          <div class="grid grid-cols-2 gap-3 text-sm">-->
<!--            <div>-->
<!--              <span class="text-secondary">所属聚类编号：</span>-->
<!--              <span class="text-white font-bold ml-2">聚类{{ predictResult.cluster_id + 1 }}</span>-->
<!--            </div>-->
<!--            <div>-->
<!--              <span class="text-secondary">聚类名称：</span>-->
<!--              <span class="text-yellow-400 font-bold ml-2">{{ predictResult.cluster_name }}</span>-->
<!--            </div>-->
<!--            <div>-->
<!--              <span class="text-secondary">PC1 坐标：</span>-->
<!--              <span class="text-white ml-2">{{ predictResult.pc1.toFixed(4) }}</span>-->
<!--            </div>-->
<!--            <div>-->
<!--              <span class="text-secondary">PC2 坐标：</span>-->
<!--              <span class="text-white ml-2">{{ predictResult.pc2.toFixed(4) }}</span>-->
<!--            </div>-->
<!--          </div>-->
<!--          <div class="mt-3">-->
<!--            <p class="text-secondary text-sm mb-2">到各聚类中心的距离：</p>-->
<!--            <div class="flex flex-wrap gap-3">-->
<!--              <span-->
<!--                v-for="(d, name) in predictResult.distances"-->
<!--                :key="name"-->
<!--                :class="['px-3 py-1 rounded text-sm', Number(name.replace('聚类','')) - 1 === predictResult.cluster_id ? 'bg-yellow-600 text-white font-bold' : 'bg-gray-700 text-gray-300']"-->
<!--              >-->
<!--                {{ name }}: {{ d }}-->
<!--              </span>-->
<!--            </div>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->
    </template>
  </div>
</template>
