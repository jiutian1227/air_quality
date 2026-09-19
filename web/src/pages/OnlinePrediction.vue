<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import BaseChart from '@/components/charts/BaseChart.vue'

const apiBase = 'http://localhost:8000'

// ===================== 响应式状态 =====================

// 污染物输入表单
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

// LightGBM预测结果
const predictResult = ref<any>(null)
// 聚类预测结果
const clusterResult = ref<any>(null)
const predictLoading = ref(false)
const predictError = ref('')

// PCA聚类散点数据（用于聚类散点图背景）
const scatterData = ref<any[]>([])
const scatterLoading = ref(true)

// ===================== 常量 =====================

// AQI等级颜色
const LEVEL_COLOR_MAP: Record<string, string> = {
  '优': '#00d4aa',
  '良': '#84cc16',
  '轻度污染': '#eab308',
  '中度污染': '#f97316',
  '重度污染': '#ef4444',
  '严重污染': '#dc2626'
}

// AQI等级描述
const LEVEL_DESC_MAP: Record<string, string> = {
  '优': '空气质量令人满意，基本无空气污染，各类人群可正常活动',
  '良': '空气质量可接受，但某些污染物可能对极少数异常敏感人群健康有较弱影响',
  '轻度污染': '易感人群症状有轻度加剧，健康人群出现刺激症状',
  '中度污染': '进一步加剧易感人群症状，可能对健康人群心脏、呼吸系统有影响',
  '重度污染': '心脏病和肺病患者症状显著加剧，运动耐受力降低',
  '严重污染': '健康人群运动耐受力降低，有明显强烈症状，避免户外活动'
}

// 聚类颜色与名称
const CLUSTER_COLORS = ['#eab308', '#00d4aa', '#f97316', '#ef4444']
const CLUSTER_NAMES = ['聚类1: 轻度污染', '聚类2: 优良天气', '聚类3: 轻度污染', '聚类4: 沙尘型污染']

// 污染物国标二级24小时均值限值
const STANDARD_LIMITS: Record<string, { limit: number; unit: string; label: string }> = {
  pm25: { limit: 75, unit: 'μg/m³', label: 'PM2.5' },
  pm10: { limit: 150, unit: 'μg/m³', label: 'PM10' },
  no2: { limit: 80, unit: 'μg/m³', label: 'NO₂' },
  so2: { limit: 150, unit: 'μg/m³', label: 'SO₂' },
  co: { limit: 4, unit: 'mg/m³', label: 'CO' },
  o3: { limit: 160, unit: 'μg/m³', label: 'O₃' }
}

const POLLUTANT_KEYS = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3'] as const

// ===================== 计算属性 =====================

// 当前等级颜色
const levelColor = computed(() => {
  if (!predictResult.value) return '#64748b'
  return LEVEL_COLOR_MAP[predictResult.value.level] || '#64748b'
})

// 当前等级描述
const levelDescription = computed(() => {
  if (!predictResult.value) return ''
  return LEVEL_DESC_MAP[predictResult.value.level] || ''
})

// 状态判断函数
function getPollutantStatus(key: string, value: number): { color: string; bgColor: string; label: string } {
  const info = STANDARD_LIMITS[key]
  if (!info) return { color: '#64748b', bgColor: 'rgba(100,116,139,0.15)', label: '--' }
  const ratio = value / info.limit
  if (ratio <= 0.5) return { color: '#00d4aa', bgColor: 'rgba(0,212,170,0.15)', label: '优' }
  if (ratio <= 1) return { color: '#eab308', bgColor: 'rgba(234,179,8,0.15)', label: '达标' }
  return { color: '#ef4444', bgColor: 'rgba(239,68,68,0.15)', label: '超标' }
}

// 顶部指标卡片数据
const metricCards = computed(() => {
  const cards: Array<{ key: string; label: string; value: number | string; unit: string; status: string; color: string; bgColor: string }> = []
  for (const key of POLLUTANT_KEYS) {
    const info = STANDARD_LIMITS[key]
    const val = predictForm.value[key]
    const status = getPollutantStatus(key, val)
    cards.push({
      key,
      label: info.label,
      value: val,
      unit: info.unit,
      status: status.label,
      color: status.color,
      bgColor: status.bgColor
    })
  }
  // AQI_lag1
  cards.push({
    key: 'aqi_lag1',
    label: '昨日AQI',
    value: predictForm.value.aqi_lag1,
    unit: '',
    status: '参考',
    color: '#60a5fa',
    bgColor: 'rgba(96,165,250,0.15)'
  })
  // pm25_roll7_mean
  cards.push({
    key: 'pm25_roll7_mean',
    label: 'PM2.5 7日均值',
    value: predictForm.value.pm25_roll7_mean,
    unit: 'μg/m³',
    status: '趋势',
    color: '#a78bfa',
    bgColor: 'rgba(167,139,250,0.15)'
  })
  return cards
})

// 雷达图配置
const radarOptions = computed(() => {
  const indicators = [
    { name: 'PM2.5', max: 150 },
    { name: 'PM10', max: 250 },
    { name: 'NO₂', max: 100 },
    { name: 'SO₂', max: 150 },
    { name: 'CO', max: 500 },
    { name: 'O₃', max: 200 }
  ]
  const nationalStandard = [75, 150, 80, 150, 400, 160]

  return {
    backgroundColor: 'transparent',
    title: {
      text: '污染物浓度雷达图',
      textStyle: { color: '#8896b0', fontSize: 13 },
      left: 'center',
      top: 8
    },
    legend: {
      data: ['当前输入', '国标二级限值'],
      bottom: 2,
      textStyle: { color: '#8896b0', fontSize: 10 }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30, 45, 66, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#e8edf5' },
      formatter: (params: any) => {
        if (params.seriesName === '国标二级限值') {
          return `${params.name}: ${params.value / (params.name === 'CO' ? 100 : 1)} ${params.name === 'CO' ? 'mg/m³' : 'μg/m³'}<br/><span style="color:#f59e0b;">国标二级限值</span>`
        }
        return `${params.name}: ${params.value / (params.name === 'CO' ? 100 : 1)} ${params.name === 'CO' ? 'mg/m³' : 'μg/m³'}`
      }
    },
    radar: {
      indicator: indicators,
      radius: '60%',
      center: ['50%', '55%'],
      splitNumber: 4,
      axisName: { color: '#8896b0', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      splitArea: { areaStyle: { color: ['rgba(0,212,170,0.02)', 'rgba(0,212,170,0.06)', 'rgba(0,212,170,0.1)', 'rgba(0,212,170,0.15)'] } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }
    },
    series: [
      {
        type: 'radar',
        name: '当前输入',
        data: [{
          value: [
            predictForm.value.pm25,
            predictForm.value.pm10,
            predictForm.value.no2,
            predictForm.value.so2,
            predictForm.value.co * 100,
            predictForm.value.o3
          ],
          name: '当前输入',
          lineStyle: { color: '#00d4aa', width: 2.5 },
          areaStyle: { color: 'rgba(0,212,170,0.25)' },
          itemStyle: { color: '#00d4aa' },
          symbol: 'circle',
          symbolSize: 6
        }]
      },
      {
        type: 'radar',
        name: '国标二级限值',
        data: [{
          value: nationalStandard,
          name: '国标二级限值',
          lineStyle: { color: '#f59e0b', width: 2, type: 'dashed' },
          areaStyle: { color: 'rgba(245,158,11,0.08)' },
          itemStyle: { color: '#f59e0b' },
          symbol: 'diamond',
          symbolSize: 5
        }]
      }
    ]
  }
})

// AQI仪表盘配置
const gaugeOptions = computed(() => {
  const value = predictResult.value?.predicted_aqi || 0
  return {
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: 300,
      splitNumber: 6,
      radius: '80%',
      center: ['50%', '60%'],
      axisLine: {
        lineStyle: {
          width: 15,
          color: [
            [50 / 300, '#00d4aa'],
            [100 / 300, '#84cc16'],
            [150 / 300, '#eab308'],
            [200 / 300, '#f97316'],
            [250 / 300, '#ef4444'],
            [1, '#dc2626']
          ]
        }
      },
      pointer: {
        icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
        length: '55%',
        width: 10,
        offsetCenter: [0, '-10%'],
        itemStyle: { color: '#00d4aa' }
      },
      axisTick: { distance: -20, length: 6, lineStyle: { color: '#fff', width: 1 } },
      splitLine: { distance: -25, length: 12, lineStyle: { color: '#fff', width: 2 } },
      axisLabel: { color: '#8896b0', distance: 35, fontSize: 11 },
      detail: {
        valueAnimation: true,
        formatter: (val: number) => `{val|${Math.round(val)}}`,
        rich: { val: { fontSize: 36, fontWeight: 'bold', color: levelColor.value } },
        offsetCenter: [0, '35%']
      },
      title: { offsetCenter: [0, '70%'], fontSize: 14, color: '#8896b0' },
      data: [{ value, name: '预测AQI' }]
    }]
  }
})

// 聚类散点图配置
const clusterScatterOptions = computed(() => {
  if (!clusterResult.value?.centroids || !scatterData.value.length) {
    return {
      backgroundColor: 'transparent',
      title: { text: '空气质量聚类分布', textStyle: { color: '#64748b', fontSize: 13 }, left: 'center', top: 8 },
      grid: { left: '5%', right: '5%', bottom: '10%', top: '15%', containLabel: true },
      xAxis: { type: 'value', name: 'PC1', axisLabel: { color: '#64748b' }, splitLine: { show: false } },
      yAxis: { type: 'value', name: 'PC2', axisLabel: { color: '#64748b' }, splitLine: { show: false } },
      series: [{ type: 'scatter', data: [], symbolSize: 1 }]
    }
  }

  // 按聚类分组背景散点
  const series: any[] = []
  const clusterIds = [...new Set(scatterData.value.map((d: any) => d['聚类']))].sort() as number[]

  for (const cId of clusterIds) {
    const points = scatterData.value
      .filter((d: any) => d['聚类'] === cId)
      .map((d: any) => [d.PC1, d.PC2])

    series.push({
      type: 'scatter',
      name: CLUSTER_NAMES[cId] || `聚类${cId + 1}`,
      data: points,
      itemStyle: { color: CLUSTER_COLORS[cId] || '#64748b', opacity: 0.3 },
      symbolSize: 4,
      emphasis: { scale: 1.5 }
    })
  }

  // 质心（大标记+标签）
  for (const centroid of clusterResult.value.centroids) {
    series.push({
      type: 'scatter',
      name: centroid.cluster_name,
      data: [[centroid.pc1, centroid.pc2]],
      itemStyle: {
        color: CLUSTER_COLORS[centroid.cluster_id] || '#64748b',
        borderColor: '#ffffff',
        borderWidth: 2
      },
      symbolSize: 22,
      label: {
        show: true,
        formatter: centroid.cluster_name.replace('聚类', ''),
        color: '#e8edf5',
        fontSize: 11,
        fontWeight: 'bold',
        position: 'right',
        backgroundColor: 'rgba(15,23,42,0.7)',
        padding: [2, 6],
        borderRadius: 4
      },
      emphasis: { scale: 2 }
    })
  }

  // 当前预测点（高亮特效）
  series.push({
    type: 'effectScatter',
    name: '← 当前预测',
    data: [[clusterResult.value.pc1, clusterResult.value.pc2]],
    itemStyle: { color: '#ffffff', borderColor: '#00d4aa', borderWidth: 3, shadowBlur: 10, shadowColor: '#00d4aa' },
    symbol: 'circle',
    symbolSize: 24,
    rippleEffect: { brushType: 'stroke', scale: 4, period: 3, color: '#00d4aa' },
    label: {
      show: true,
      formatter: '当前预测点',
      color: '#ffffff',
      fontSize: 12,
      fontWeight: 'bold',
      position: 'top',
      backgroundColor: 'rgba(0,212,170,0.8)',
      padding: [3, 8],
      borderRadius: 4
    },
    z: 10
  })

  return {
    backgroundColor: 'transparent',
    title: {
      text: '空气质量聚类分布（PCA降维）',
      textStyle: { color: '#8896b0', fontSize: 13 },
      left: 'center',
      top: 8
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30, 45, 66, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#e8edf5', fontSize: 12 },
      formatter: (params: any) => {
        if (params.seriesName === '← 当前预测') {
          return `<b style="color:#00d4aa;">当前预测点</b><br/>所属: ${clusterResult.value.cluster_name}<br/>PC1: ${clusterResult.value.pc1.toFixed(3)}<br/>PC2: ${clusterResult.value.pc2.toFixed(3)}`
        }
        if (params.componentType === 'series' && params.data) {
          return `<b>${params.seriesName}</b>`
        }
        return params.seriesName || ''
      }
    },
    legend: {
      data: [
        ...CLUSTER_NAMES.map((name, i) => ({ name, itemStyle: { color: CLUSTER_COLORS[i] } })),
        { name: '← 当前预测', itemStyle: { color: '#ffffff' } }
      ],
      bottom: 2,
      textStyle: { color: '#8896b0', fontSize: 9 },
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8
    },
    grid: { left: '6%', right: '6%', bottom: '18%', top: '18%', containLabel: true },
    xAxis: {
      type: 'value',
      name: 'PC1 (64.9%)',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#8896b0', fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)', type: 'dashed' } }
    },
    yAxis: {
      type: 'value',
      name: 'PC2 (15.1%)',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#8896b0', fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)', type: 'dashed' } }
    },
    series
  }
})

// 国标对比柱状图
const nationalStandardBarOptions = computed(() => {
  const inputData = [
    predictForm.value.pm25,
    predictForm.value.pm10,
    predictForm.value.no2,
    predictForm.value.so2,
    predictForm.value.co,
    predictForm.value.o3
  ]
  const standardData = [75, 150, 80, 150, 4, 160]
  const categories = ['PM2.5', 'PM10', 'NO₂', 'SO₂', 'CO', 'O₃']
  const units = ['μg/m³', 'μg/m³', 'μg/m³', 'μg/m³', 'mg/m³', 'μg/m³']

  return {
    backgroundColor: 'transparent',
    title: {
      text: '污染物浓度 vs 国标二级限值',
      textStyle: { color: '#8896b0', fontSize: 13 },
      left: 'center',
      top: 8
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30, 45, 66, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#e8edf5' },
      formatter: (params: any[]) => {
        let result = ''
        params.forEach((p: any) => {
          result += `${p.marker} ${p.seriesName}: ${p.value} ${units[p.dataIndex]}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['当前输入值', '国标二级限值'],
      bottom: 2,
      textStyle: { color: '#8896b0', fontSize: 10 }
    },
    grid: { left: '3%', right: '5%', bottom: '15%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: '#8896b0', fontSize: 11 },
      axisLine: { lineStyle: { color: '#334155' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '浓度值',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: { color: '#8896b0', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
    },
    series: [
      {
        name: '当前输入值',
        type: 'bar',
        data: inputData.map((val, i) => ({
          value: val,
          itemStyle: {
            color: val > standardData[i] ? '#ef4444' : '#00d4aa',
            borderRadius: [4, 4, 0, 0]
          }
        })),
        barWidth: '35%',
        barGap: '30%'
      },
      {
        name: '国标二级限值',
        type: 'bar',
        data: standardData.map(val => ({
          value: val,
          itemStyle: {
            color: '#f59e0b',
            borderColor: '#fbbf24',
            borderWidth: 1,
            borderType: 'dashed',
            borderRadius: [4, 4, 0, 0],
            opacity: 0.7
          }
        })),
        barWidth: '35%'
      }
    ]
  }
})

// AQI范围文本
const aqiRangeText = computed(() => {
  if (!predictResult.value) return ''
  const map: Record<string, string> = {
    '优': '0～50',
    '良': '51～100',
    '轻度污染': '101～150',
    '中度污染': '151～200',
    '重度污染': '201～300',
    '严重污染': '>300'
  }
  return map[predictResult.value.level] || ''
})

// ===================== 业务方法 =====================

// 加载PCA聚类散点数据
async function loadScatterData() {
  try {
    const res = await fetch(`${apiBase}/api/predict/cluster-scatter`)
    if (res.ok) {
      scatterData.value = await res.json()
    }
  } catch (e) {
    console.error('加载PCA散点数据失败:', e)
  } finally {
    scatterLoading.value = false
  }
}

// 执行预测（并行调用LightGBM + 聚类）
async function runPredict() {
  predictLoading.value = true
  predictError.value = ''
  predictResult.value = null
  clusterResult.value = null

  try {
    const [lightgbmRes, clusterRes] = await Promise.all([
      fetch(`${apiBase}/api/predict/lightgbm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(predictForm.value)
      }),
      fetch(`${apiBase}/api/predict/cluster`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(predictForm.value)
      })
    ])

    if (!lightgbmRes.ok) {
      const err = await lightgbmRes.json().catch(() => ({}))
      throw new Error(err.detail || `预测请求失败: ${lightgbmRes.status}`)
    }

    predictResult.value = await lightgbmRes.json()

    if (clusterRes.ok) {
      clusterResult.value = await clusterRes.json()
    }
  } catch (e: any) {
    predictError.value = e.message || '预测失败，请确认后端服务已启动'
  } finally {
    predictLoading.value = false
  }
}

// 重置
function resetForm() {
  predictForm.value = {
    pm25: 50,
    pm10: 100,
    no2: 40,
    so2: 20,
    co: 1.0,
    o3: 60,
    aqi_lag1: 80,
    pm25_roll7_mean: 55
  }
  predictResult.value = null
  clusterResult.value = null
}

// 获取首要污染物
const primaryPollutant = computed(() => {
  const ratios = POLLUTANT_KEYS.map(key => ({
    key,
    label: STANDARD_LIMITS[key].label,
    ratio: predictForm.value[key] / STANDARD_LIMITS[key].limit
  }))
  ratios.sort((a, b) => b.ratio - a.ratio)
  return ratios[0]?.label || '--'
})

onMounted(loadScatterData)
</script>

<template>
  <div class="space-y-6">
    <!-- ======== 页面标题 ======== -->
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-primary flex items-center gap-2">
        <svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/>
        </svg>
        在线空气质量预测
      </h2>
      <div class="flex items-center gap-2 text-xs text-secondary">
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
          优
        </span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-yellow-400"></span>
          达标
        </span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-red-400"></span>
          超标
        </span>
      </div>
    </div>

    <!-- ======== 第一行：数据仪表盘 — 污染物输入数据一览 ======== -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-medium text-primary flex items-center gap-2">
          <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          污染物输入数据一览
        </h3>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-3">
        <div
          v-for="card in metricCards"
          :key="card.key"
          class="relative rounded-lg p-3 transition-all duration-200 hover:scale-[1.02]"
          :style="{ backgroundColor: card.bgColor }"
        >
          <div class="text-xs text-secondary mb-1 truncate">{{ card.label }}</div>
          <div class="text-lg font-bold text-white truncate">{{ card.value }}</div>
          <div class="flex items-center justify-between mt-1">
            <span class="text-[10px] text-gray-500">{{ card.unit }}</span>
            <span class="text-[10px] font-medium" :style="{ color: card.color }">● {{ card.status }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ======== 第二行：输入表单 + 雷达图 ======== -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <!-- 左侧：输入表单 -->
      <div class="lg:col-span-2">
        <div class="card h-full">
          <h3 class="text-base font-medium text-primary mb-4 flex items-center gap-2">
            <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
            输入污染物数据
          </h3>

          <div class="grid grid-cols-2 gap-x-4 gap-y-3">
            <label class="flex flex-col text-sm" v-for="item in [
              { key: 'pm25', label: 'PM2.5', unit: 'μg/m³', step: 0.1 },
              { key: 'pm10', label: 'PM10', unit: 'μg/m³', step: 0.1 },
              { key: 'no2', label: 'NO₂', unit: 'μg/m³', step: 0.1 },
              { key: 'so2', label: 'SO₂', unit: 'μg/m³', step: 0.1 },
              { key: 'co', label: 'CO', unit: 'mg/m³', step: 0.01 },
              { key: 'o3', label: 'O₃', unit: 'μg/m³', step: 0.1 },
            ]" :key="item.key">
              <span class="text-secondary mb-1 text-xs">{{ item.label }} ({{ item.unit }})</span>
              <input
                v-model.number="(predictForm as any)[item.key]"
                type="number"
                :step="item.step"
                min="0"
                class="bg-gray-700/50 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all"
              />
            </label>

            <label class="flex flex-col text-sm col-span-2">
              <span class="text-secondary mb-1 text-xs">昨日AQI (AQI_lag1)</span>
              <input v-model.number="predictForm.aqi_lag1" type="number" step="0.1" min="0" class="bg-gray-700/50 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all" />
            </label>
            <label class="flex flex-col text-sm col-span-2">
              <span class="text-secondary mb-1 text-xs">PM2.5 7日均值 (μg/m³)</span>
              <input v-model.number="predictForm.pm25_roll7_mean" type="number" step="0.1" min="0" class="bg-gray-700/50 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all" />
            </label>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-3 mt-5">
            <button
              @click="runPredict"
              :disabled="predictLoading"
              class="flex-1 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg font-medium transition-all shadow-lg hover:shadow-blue-500/25 text-sm"
            >
              <span v-if="predictLoading" class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                预测中...
              </span>
              <span v-else class="flex items-center justify-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
                开始预测
              </span>
            </button>
            <button
              @click="resetForm"
              class="px-5 py-2.5 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-all text-sm"
            >
              重置
            </button>
          </div>

          <!-- 错误提示 -->
          <div v-if="predictError" class="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p class="text-red-400 text-sm">{{ predictError }}</p>
          </div>
        </div>
      </div>

      <!-- 右侧：雷达图 -->
      <div class="lg:col-span-3">
        <div class="card h-full flex flex-col">
          <div class="flex-1 min-h-0">
            <BaseChart :options="radarOptions" height="100%" />
          </div>
        </div>
      </div>
    </div>

    <!-- ======== 第三行：预测结果 ======== -->
    <div v-if="predictResult" class="space-y-6">
      <!-- 预测结果主卡片 -->
      <div class="card" :style="{ borderTop: `3px solid ${levelColor}` }">
        <div class="flex flex-col md:flex-row items-center gap-6">
          <!-- AQI大数值 -->
          <div class="flex-shrink-0 text-center">
            <div class="text-5xl font-bold" :style="{ color: levelColor }">
              {{ predictResult.predicted_aqi }}
            </div>
            <div class="text-xs text-secondary mt-1">预测AQI值</div>
          </div>

          <!-- 分隔线 -->
          <div class="hidden md:block w-px h-16 bg-gray-600/50"></div>

          <!-- 等级信息 -->
          <div class="flex-1 text-center md:text-left">
            <div class="flex items-center gap-3 justify-center md:justify-start">
              <span
                class="px-3 py-1 rounded-full text-sm font-bold"
                :style="{ backgroundColor: `${levelColor}25`, color: levelColor }"
              >
                {{ predictResult.level }}
              </span>
              <span class="text-xs text-secondary">AQI范围: {{ aqiRangeText }}</span>
            </div>
            <p class="text-xs text-secondary mt-2">{{ levelDescription }}</p>
          </div>

          <!-- 聚类信息 -->
          <div v-if="clusterResult" class="flex-shrink-0 text-center px-4 py-2 rounded-lg" style="background: rgba(0,212,170,0.08);">
            <div class="text-xs text-secondary">所属类别</div>
            <div class="text-sm font-bold text-emerald-400 mt-0.5">{{ clusterResult.cluster_name }}</div>
          </div>
        </div>

        <!-- AQI仪表盘 -->
        <div class="mt-4">
          <BaseChart :options="gaugeOptions" height="280px" />
        </div>
      </div>

      <!-- 图表行：聚类散点图 + 国标对比 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 聚类散点图 -->
        <div class="card">
          <BaseChart :options="clusterScatterOptions" height="380px" />
        </div>

        <!-- 国标对比柱状图 -->
        <div class="card">
          <BaseChart :options="nationalStandardBarOptions" height="380px" />
        </div>
      </div>

      <!-- 详情行：预测详情 + 健康建议 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 预测详情 -->
        <div class="card">
          <h4 class="text-base font-medium text-primary mb-4 flex items-center gap-2">
            <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            预测详情
          </h4>
          <div class="grid grid-cols-2 gap-3">
            <div class="p-3 bg-gray-700/30 rounded-lg">
              <div class="text-xs text-secondary">预测模型</div>
              <div class="text-sm text-white font-medium mt-0.5">LightGBM</div>
            </div>
            <div class="p-3 bg-gray-700/30 rounded-lg">
              <div class="text-xs text-secondary">空气质量等级</div>
              <div class="text-sm font-bold mt-0.5" :style="{ color: levelColor }">{{ predictResult.level }}</div>
            </div>
            <div class="p-3 bg-gray-700/30 rounded-lg">
              <div class="text-xs text-secondary">预测AQI值</div>
              <div class="text-sm text-white font-medium mt-0.5">{{ predictResult.predicted_aqi }}</div>
            </div>
            <div class="p-3 bg-gray-700/30 rounded-lg">
              <div class="text-xs text-secondary">AQI范围</div>
              <div class="text-sm text-white font-medium mt-0.5">{{ aqiRangeText }}</div>
            </div>
            <div class="p-3 bg-gray-700/30 rounded-lg">
              <div class="text-xs text-secondary">首要污染物</div>
              <div class="text-sm text-white font-medium mt-0.5">{{ primaryPollutant }}</div>
            </div>
            <div class="p-3 bg-gray-700/30 rounded-lg">
              <div class="text-xs text-secondary">所属聚类</div>
              <div class="text-sm text-emerald-400 font-medium mt-0.5">{{ clusterResult?.cluster_name || '--' }}</div>
            </div>
          </div>

          <!-- 聚类距离详情 -->
          <div v-if="clusterResult?.distances" class="mt-4">
            <h5 class="text-xs text-secondary mb-2">距各聚类中心距离</h5>
            <div class="flex flex-wrap gap-2">
              <div
                v-for="(dist, name) in clusterResult.distances"
                :key="name"
                class="px-2.5 py-1.5 rounded text-xs"
                :class="name === `聚类${clusterResult.cluster_id + 1}` ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-gray-700/30 text-gray-400'"
              >
                {{ name }}: {{ dist }}
              </div>
            </div>
          </div>
        </div>

        <!-- 健康建议 -->
        <div class="card">
          <h4 class="text-base font-medium text-primary mb-4 flex items-center gap-2">
            <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
            健康建议
          </h4>
          <div class="p-4 rounded-lg" :style="{ backgroundColor: `${levelColor}12`, borderLeft: `3px solid ${levelColor}` }">
            <p class="text-sm font-medium mb-2" :style="{ color: levelColor }">
              当前空气质量等级：{{ predictResult.level }}
            </p>
            <p class="text-sm text-secondary leading-relaxed">{{ levelDescription }}</p>
          </div>

          <div class="mt-4 grid grid-cols-2 gap-3">
            <div class="p-3 rounded-lg bg-gray-700/30">
              <div class="flex items-center gap-2 mb-1">
                <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span class="text-xs text-green-400 font-medium">建议</span>
              </div>
              <p class="text-xs text-secondary">
                <template v-if="predictResult.level === '优'">非常适合户外运动，请保持开窗通风。</template>
                <template v-else-if="predictResult.level === '良'">可正常活动，敏感人群适当减少户外运动。</template>
                <template v-else-if="predictResult.level === '轻度污染'">敏感人群减少户外活动，外出建议佩戴口罩。</template>
                <template v-else-if="predictResult.level === '中度污染'">建议减少户外活动，必要时佩戴防护口罩。</template>
                <template v-else>避免户外活动，外出必须佩戴专业防护口罩。</template>
              </p>
            </div>
            <div class="p-3 rounded-lg bg-gray-700/30">
              <div class="flex items-center gap-2 mb-1">
                <svg class="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                </svg>
                <span class="text-xs text-yellow-400 font-medium">注意事项</span>
              </div>
              <p class="text-xs text-secondary">
                <template v-if="predictResult.level === '优'">各类人群可正常活动，无需特别防护。</template>
                <template v-else-if="predictResult.level === '良'">极少数敏感人群应注意减少长时间户外活动。</template>
                <template v-else-if="predictResult.level === '轻度污染'">儿童、老年人及心脏病、呼吸系统疾病患者应减少长时间、高强度户外锻炼。</template>
                <template v-else-if="predictResult.level === '中度污染'">疾病患者避免长时间、高强度户外锻炼，一般人群适量减少户外运动。</template>
                <template v-else>所有人群都应避免户外活动。</template>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态（未预测时） -->
    <div v-else class="card">
      <div class="flex flex-col items-center justify-center py-16">
        <svg class="w-24 h-24 mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        <p class="text-secondary text-lg mb-2">请输入污染物数据</p>
        <p class="text-gray-500 text-sm">在上方输入污染物浓度后，点击"开始预测"按钮获取AQI预测结果</p>
      </div>
    </div>
  </div>
</template>
