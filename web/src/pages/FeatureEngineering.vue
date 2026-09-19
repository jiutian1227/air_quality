<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCsvData } from '@/composables/useCsvData'

const { loadCsv: loadCsvData } = useCsvData()

const featureList = ref<any[]>([])
const featureStats = ref<any[]>([])
const featureData = ref<any[]>([])

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  try {
    featureList.value = await loadCsvData('/data/特征工程/特征列表.csv')
    featureStats.value = await loadCsvData('/data/特征工程/特征统计信息.csv')
    featureData.value = await loadCsvData('/data/特征工程/特征工程数据.csv')
  } catch (error) {
    console.error('加载特征工程数据失败:', error)
  }
}

const featureCategories = computed(() => {
  const categories: Record<string, string[]> = {
    '原始监测特征': ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3'],
    '时间维度特征': ['年份', '月份', '季节', '星期几', '是否周末'],
    '时序衍生特征': ['AQI_lag1', 'PM2.5_roll7_mean']
  }
  return categories
})

const getFeatureCount = (category: string) => {
  return featureCategories.value[category]?.length || 0
}
</script>

<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-primary">特征工程</h1>
      <p class="text-secondary mt-2">特征提取与处理 - 兰州市空气质量数据</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-card rounded-xl p-5">
        <div class="text-3xl font-bold text-accent">{{ featureList.length }}</div>
        <div class="text-secondary mt-1">总特征数</div>
      </div>
      <div class="bg-card rounded-xl p-5">
        <div class="text-3xl font-bold text-[#3498db]">{{ getFeatureCount('原始监测特征') }}</div>
        <div class="text-secondary mt-1">原始监测特征</div>
      </div>
      <div class="bg-card rounded-xl p-5">
        <div class="text-3xl font-bold text-[#f39c12]">{{ getFeatureCount('时间维度特征') }}</div>
        <div class="text-secondary mt-1">时间维度特征</div>
      </div>
      <div class="bg-card rounded-xl p-5">
        <div class="text-3xl font-bold text-[#e74c3c]">{{ getFeatureCount('时序衍生特征') }}</div>
        <div class="text-secondary mt-1">时序衍生特征</div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-card rounded-xl p-6">
        <h2 class="text-lg font-semibold text-primary mb-4">特征类别分布</h2>
        <div class="space-y-3">
          <div v-for="(features, category) in featureCategories" :key="category">
            <div class="flex justify-between items-center mb-2">
              <span class="text-secondary">{{ category }}</span>
              <span class="text-primary font-medium">{{ features.length }} 个</span>
            </div>
            <div class="bg-secondary rounded-lg p-3 max-h-40 overflow-y-auto">
              <div class="flex flex-wrap gap-2">
                <span 
                  v-for="feature in features" 
                  :key="feature" 
                  class="px-2 py-1 bg-[#00d4aa]/20 text-accent text-xs rounded"
                >
                  {{ feature }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-card rounded-xl p-6">
        <h2 class="text-lg font-semibold text-primary mb-4">特征统计摘要</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-color">
                <th class="text-left py-2 px-3 text-secondary">特征名</th>
                <th class="text-right py-2 px-3 text-secondary">缺失值</th>
                <th class="text-right py-2 px-3 text-secondary">均值</th>
                <th class="text-right py-2 px-3 text-secondary">标准差</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in featureStats" :key="row['特征']" class="border-b border-color/50">
                <td class="py-2 px-3 text-primary text-sm">{{ row['特征'] }}</td>
                <td class="py-2 px-3 text-right text-secondary text-sm">{{ row['缺失值数量'] }}</td>
                <td class="py-2 px-3 text-right text-secondary text-sm">{{ row['均值'] }}</td>
                <td class="py-2 px-3 text-right text-secondary text-sm">{{ row['标准差'] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="featureStats.length > 15" class="text-xs text-[#4a5568] mt-3 text-center">仅显示前15个特征...</p>
      </div>
    </div>

    <div class="mt-6 bg-card rounded-xl p-6">
      <h2 class="text-lg font-semibold text-primary mb-4">特征列表</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-color">
              <th class="text-left py-3 px-4 text-secondary">特征名</th>
              <th class="text-left py-3 px-4 text-secondary">数据类型</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in featureList" :key="row['特征名']" class="border-b border-color/50">
              <td class="py-3 px-4 text-primary">{{ row['特征名'] }}</td>
              <td class="py-3 px-4 text-secondary">{{ row['类型'] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mt-6 bg-card rounded-xl p-6">
      <h2 class="text-lg font-semibold text-primary mb-4">特征工程说明</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-secondary rounded-lg p-4">
          <h3 class="text-[#3498db] font-medium mb-2">原始监测特征</h3>
          <p class="text-secondary text-sm">
            AQI、PM2.5、PM10、NO2、SO2、CO、O3共7个核心污染物指标，直接反映空气质量状况。
          </p>
        </div>
        <div class="bg-secondary rounded-lg p-4">
          <h3 class="text-[#f39c12] font-medium mb-2">时间维度特征</h3>
          <p class="text-secondary text-sm">
            年份、月份、季节、星期几、是否周末，用于捕捉时间规律和周期性污染模式。
          </p>
        </div>
        <div class="bg-secondary rounded-lg p-4">
          <h3 class="text-[#e74c3c] font-medium mb-2">时序衍生特征</h3>
          <p class="text-secondary text-sm">
            AQI滞后1期、PM2.5七日滑动平均，体现空气质量的时间连续性和累积效应。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
