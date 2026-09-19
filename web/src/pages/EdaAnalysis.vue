<script setup lang="ts">import { ref, onMounted, watch } from 'vue';
import * as echarts from 'echarts';
import { useCsvData } from '@/composables/useCsvData';
import { useTheme } from '@/composables/useTheme';

const { isDark } = useTheme();
const chartInstances: echarts.ECharts[] = [];

// Theme-aware color helper - reads current CSS variable values
function tc() {
  const s = getComputedStyle(document.documentElement);
  return {
    p: s.getPropertyValue('--text-primary').trim() || '#e8edf5',
    s: s.getPropertyValue('--text-secondary').trim() || '#8896b0',
    b: s.getPropertyValue('--border-color').trim() || '#1e2d42',
  };
}

watch(isDark, () => {
  chartInstances.forEach(c => { try { c.resize(); } catch(e) {} });
});
const { loadCsv: loadCsvData } = useCsvData();
const statsData = ref<any[]>([]);
const qualityData = ref<any[]>([]);
const monthlyData = ref<any[]>([]);
const seasonalData = ref<any[]>([]);
const correlationData = ref<any[]>([]);
const yearlyCorrelationData = ref<any[]>([]);
const aqiDailyData = ref<any[]>([]);
const scatterPm25Aqi = ref<any[]>([]);
const scatterPm25Pm10 = ref<any[]>([]);
const pollutantsDaily = ref<any[]>([]);
const selectedYear = ref('全部');
const selectedAqiYear = ref('全部');
const selectedPollutantYear = ref('全部');
const availableYears = ref<string[]>(['全部']);
const availableAqiYears = ref<string[]>(['全部']);
const availablePollutantYears = ref<string[]>(['全部']);
let aqiChart: echarts.ECharts | null = null;
let pollutantChart: echarts.ECharts | null = null;

onMounted(async () => {
 await loadData();
 initCharts();
});
const loadData = async () => {
 try {
 statsData.value = await loadCsvData('/data/EDA数据分析/统计汇总表.csv');
 qualityData.value = await loadCsvData('/data/EDA数据分析/空气质量等级分布数据.csv');
 monthlyData.value = await loadCsvData('/data/EDA数据分析/月度平均AQI数据.csv');
 seasonalData.value = await loadCsvData('/data/EDA数据分析/季度平均AQI数据.csv');
 correlationData.value = await loadCsvData('/data/EDA数据分析/相关性矩阵数据.csv');
 yearlyCorrelationData.value = await loadCsvData('/data/EDA数据分析/年度相关性矩阵数据.csv');
 aqiDailyData.value = await loadCsvData('/data/EDA数据分析/AQI每日数据.csv');
 scatterPm25Aqi.value = await loadCsvData('/data/EDA数据分析/PM2.5与AQI散点数据.csv');
 scatterPm25Pm10.value = await loadCsvData('/data/EDA数据分析/PM2.5与PM10散点数据.csv');
 pollutantsDaily.value = await loadCsvData('/data/EDA数据分析/污染物每日数据.csv');

 const years = [...new Set(yearlyCorrelationData.value.map(d => String(d['年份'])))];
 availableYears.value = ['全部', ...years.sort((a, b) => Number(a) - Number(b))];

 const aqiYears = [...new Set(aqiDailyData.value.map((d: any) => String(d['日期']).substring(0, 4)))];
 availableAqiYears.value = ['全部', ...aqiYears.sort((a: string, b: string) => Number(a) - Number(b))];

 const pollutantYears = [...new Set(pollutantsDaily.value.map((d: any) => String(d['日期']).substring(0, 4)))];
 availablePollutantYears.value = ['全部', ...pollutantYears.sort((a: string, b: string) => Number(a) - Number(b))];
 }
 catch (error) {
 console.error('加载EDA数据失败:', error);
 }
};

function getFilteredAqiData(year: string) {
  if (year === '全部') return aqiDailyData.value;
  return aqiDailyData.value.filter((d: any) => String(d['日期']).startsWith(year));
}

function getFilteredPollutantData(year: string) {
  if (year === '全部') return pollutantsDaily.value;
  return pollutantsDaily.value.filter((d: any) => String(d['日期']).startsWith(year));
}

function updateAqiChart() {
  if (!aqiChart) return;
  const filtered = getFilteredAqiData(selectedAqiYear.value);
  const titleSuffix = selectedAqiYear.value === '全部' ? '（全部年份）' : `（${selectedAqiYear.value}年）`;
  aqiChart.setOption({
    title: { text: 'AQI时间趋势' + titleSuffix },
    xAxis: { data: filtered.map(item => item['日期']) },
    series: [{ data: filtered.map(item => item['AQI指数']) }]
  });
}

function updatePollutantChart() {
  if (!pollutantChart) return;
  const filtered = getFilteredPollutantData(selectedPollutantYear.value);
  const dates = filtered.map(item => item['日期']);
  const titleSuffix = selectedPollutantYear.value === '全部' ? '（全部年份）' : `（${selectedPollutantYear.value}年）`;
  pollutantChart.setOption({
    title: { text: '污染物时间趋势' + titleSuffix },
    xAxis: { data: dates },
    series: [
      { data: filtered.map(item => item['PM2.5']) },
      { data: filtered.map(item => item['PM10']) },
      { data: filtered.map(item => item['NO2']) },
      { data: filtered.map(item => item['SO2']) },
      { data: filtered.map(item => item['CO']) },
      { data: filtered.map(item => item['O3']) },
    ]
  });
}

watch(selectedAqiYear, updateAqiChart);
watch(selectedPollutantYear, updatePollutantChart);

const getHeatmapData = () => {
 let data: any[] = [];
 let xLabels: string[] = [];
 let yLabels: string[] = [];

 if (selectedYear.value === '全部') {
 if (correlationData.value.length === 0) return { data: [], xLabels: [], yLabels: [] };
 const allKeys = Object.keys(correlationData.value[0]);

 const rowNameKey = allKeys.find(k => k === '') || allKeys[0];
 const colNames = allKeys.filter(k => k !== '');

 yLabels = correlationData.value.map(r => String(r[rowNameKey]));
 xLabels = colNames;

 data = [];
 correlationData.value.forEach((row: any, yIdx: number) => {
 colNames.forEach((key: string, xIdx: number) => {
 const val = Number(row[key]);
 if (!isNaN(val)) {
 data.push([xIdx, yIdx, Math.round(val * 100) / 100]);
 }
 });
 });
 } else {
 const yearData = yearlyCorrelationData.value.filter((d: any) => String(d['年份']) === selectedYear.value);
 if (yearData.length === 0) return { data: [], xLabels: [], yLabels: [] };

 const indicators = [...new Set(yearData.map((d: any) => d['行']))].sort();
 xLabels = indicators;
 yLabels = indicators;

 const indicatorIndex: Record<string, number> = {};
 indicators.forEach((ind, idx) => { indicatorIndex[ind] = idx; });

 data = yearData.map((d: any) => [
 indicatorIndex[d['列']],
 indicatorIndex[d['行']],
 Math.round(Number(d['相关性']) * 100) / 100
 ]);
 }

 return { data, xLabels, yLabels };
};
const initCharts = () => {
 initQualityPie();
 initMonthlyBar();
 initSeasonalBar();
 initAqiTimeSeries();
 initPollutantsTimeSeries();
 initCorrelationHeatmap();
 initScatterPm25Aqi();
 initScatterPm25Pm10();
};
const initQualityPie = () => {
 const chart = echarts.init(document.getElementById('quality-pie')!);
 chartInstances.push(chart);
 const option: echarts.EChartsOption = {
 title: { text: '空气质量等级分布', left: 'center', textStyle: { color: tc().p } },
 tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
 legend: { orient: 'vertical', right: 10, top: 'middle', textStyle: { color: tc().s } },
 series: [{
 name: '质量等级',
 type: 'pie',
 radius: ['40%', '70%'],
 avoidLabelOverlap: false,
 itemStyle: {
 borderRadius: 10,
 borderColor: tc().b,
 borderWidth: 2
 },
 label: { show: false, position: 'center' },
 emphasis: {
 label: { show: true, fontSize: 18, fontWeight: 'bold' }
 },
 labelLine: { show: false },
 data: qualityData.value.map(item => ({
 value: item['数量'],
 name: item['质量等级'],
 itemStyle: {
 color: getQualityColor(item['质量等级'])
 }
 }))
 }]
 };
 chart.setOption(option);
 window.addEventListener('resize', () => chart.resize());
};
const initMonthlyBar = () => {
 const chart = echarts.init(document.getElementById('monthly-bar')!);
 chartInstances.push(chart);
 const option: echarts.EChartsOption = {
 title: { text: '月度平均AQI', left: 'center', textStyle: { color: tc().p } },
 tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
 grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
 xAxis: { type: 'category', data: monthlyData.value.map(item => item['月份']), axisLabel: { color: tc().s, rotate: 45 } },
 yAxis: { type: 'value', name: 'AQI', nameTextStyle: { color: tc().s }, axisLabel: { color: tc().s } },
 series: [{
 name: 'AQI',
 type: 'bar',
 data: monthlyData.value.map(item => item['AQI']),
 itemStyle: { color: '#3498db', borderRadius: [4, 4, 0, 0] },
 emphasis: { itemStyle: { color: '#2980b9' } }
 }]
 };
 chart.setOption(option);
 window.addEventListener('resize', () => chart.resize());
};
const initSeasonalBar = () => {
 const chart = echarts.init(document.getElementById('seasonal-bar')!);
 chartInstances.push(chart);
 const colors = ['#2ecc71', '#f1c40f', '#e67e22', '#3498db'];
 const option: echarts.EChartsOption = {
 title: { text: '季度平均AQI', left: 'center', textStyle: { color: tc().p } },
 tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
 grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
 xAxis: { type: 'category', data: seasonalData.value.map(item => item['季节']), axisLabel: { color: tc().s } },
 yAxis: { type: 'value', name: 'AQI', nameTextStyle: { color: tc().s }, axisLabel: { color: tc().s } },
 series: [{
 name: 'AQI',
 type: 'bar',
 data: seasonalData.value.map((item, index) => ({
 value: item['AQI'],
 itemStyle: { color: colors[index], borderRadius: [4, 4, 0, 0] }
 }))
 }]
 };
 chart.setOption(option);
 window.addEventListener('resize', () => chart.resize());
};
const initAqiTimeSeries = () => {
 aqiChart = echarts.init(document.getElementById('aqi-time-series')!);
 chartInstances.push(aqiChart);
 const filtered = getFilteredAqiData(selectedAqiYear.value);
 const titleSuffix = selectedAqiYear.value === '全部' ? '（全部年份）' : `（${selectedAqiYear.value}年）`;
 const option: echarts.EChartsOption = {
 title: { text: 'AQI时间趋势' + titleSuffix, left: 'center', textStyle: { color: tc().p } },
 tooltip: { trigger: 'axis', formatter: '{b}<br/>AQI: {c}' },
 grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
 xAxis: { type: 'category', data: filtered.map(item => item['日期']), axisLabel: { color: tc().s, rotate: 45 } },
 yAxis: { type: 'value', name: 'AQI', nameTextStyle: { color: tc().s }, axisLabel: { color: tc().s } },
 series: [{
 name: 'AQI',
 type: 'line',
 data: filtered.map(item => item['AQI指数']),
 smooth: true,
 lineStyle: { width: 1, color: '#3498db' },
 areaStyle: {
 color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
 { offset: 0, color: 'rgba(52, 152, 219, 0.3)' },
 { offset: 1, color: 'rgba(52, 152, 219, 0.05)' }
 ])
 }
 }]
 };
 aqiChart.setOption(option);
 window.addEventListener('resize', () => aqiChart!.resize());
};
const initPollutantsTimeSeries = () => {
 pollutantChart = echarts.init(document.getElementById('pollutants-time-series')!);
 chartInstances.push(pollutantChart);
 const filtered = getFilteredPollutantData(selectedPollutantYear.value);
 const dates = filtered.map(item => item['日期']);
 const titleSuffix = selectedPollutantYear.value === '全部' ? '（全部年份）' : `（${selectedPollutantYear.value}年）`;

 const option: echarts.EChartsOption = {
 title: { text: '污染物时间趋势' + titleSuffix, left: 'center', textStyle: { color: tc().p } },
 tooltip: {
 trigger: 'axis',
 axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } }
 },
 legend: {
 data: ['PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3'],
 textStyle: { color: tc().s },
 bottom: 10
 },
 grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
 xAxis: { type: 'category', data: dates, axisLabel: { color: tc().s, rotate: 45, fontSize: 10 } },
 yAxis: { type: 'value', name: '浓度', nameTextStyle: { color: tc().s }, axisLabel: { color: tc().s } },
 series: [
 {
 name: 'PM2.5',
 type: 'line',
 data: filtered.map(item => item['PM2.5']),
 smooth: true,
 lineStyle: { width: 1.5, color: '#e74c3c' }
 },
 {
 name: 'PM10',
 type: 'line',
 data: filtered.map(item => item['PM10']),
 smooth: true,
 lineStyle: { width: 1.5, color: '#3498db' }
 },
 {
 name: 'NO2',
 type: 'line',
 data: filtered.map(item => item['NO2']),
 smooth: true,
 lineStyle: { width: 1.5, color: '#f39c12' }
 },
 {
 name: 'SO2',
 type: 'line',
 data: filtered.map(item => item['SO2']),
 smooth: true,
 lineStyle: { width: 1.5, color: '#2ecc71' }
 },
 {
 name: 'CO',
 type: 'line',
 data: filtered.map(item => item['CO']),
 smooth: true,
 lineStyle: { width: 1.5, color: '#9b59b6' }
 },
 {
 name: 'O3',
 type: 'line',
 data: filtered.map(item => item['O3']),
 smooth: true,
 lineStyle: { width: 1.5, color: '#1abc9c' }
 }
 ]
 };
 pollutantChart.setOption(option);
 window.addEventListener('resize', () => pollutantChart!.resize());
};
const initCorrelationHeatmap = () => {
 const chart = echarts.init(document.getElementById('correlation-heatmap')!);
 chartInstances.push(chart);

 const updateChart = () => {
 const { data, xLabels, yLabels } = getHeatmapData();
 const option: echarts.EChartsOption = {
 title: { text: `污染物相关性热力图（${selectedYear.value === '全部' ? '全部年份' : selectedYear.value + '年'}）`, left: 'center', textStyle: { color: tc().p } },
 tooltip: { formatter: (params: any) => `${yLabels[params.data[1]]} vs ${xLabels[params.data[0]]}: ${params.data[2]}` },
 grid: { left: '15%', right: '15%', bottom: '15%', top: '10%' },
 xAxis: { type: 'category', data: xLabels, axisLabel: { color: tc().s, rotate: 45 } },
 yAxis: { type: 'category', data: yLabels, axisLabel: { color: tc().s } },
 visualMap: {
 min: -1,
 max: 1,
 calculable: true,
 orient: 'vertical',
 left: '1%',
 bottom: '15%',
 textStyle: { color: tc().s },
 inRange: {
 color: ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71']
 }
 },
 series: [{
 name: '相关性',
 type: 'heatmap',
 data: data,
 label: { show: true, color: '#fff', fontSize: 10 },
 emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
 }]
 };
 chart.setOption(option);
 };

 updateChart();
 window.addEventListener('resize', () => chart.resize());

 selectedYear.value = '全部';
 Object.defineProperty(selectedYear, 'value', {
 get: () => selectedYear._value,
 set: (newVal: string) => {
 selectedYear._value = newVal;
 updateChart();
 }
 });
};
selectedYear._value = '全部';
const initScatterPm25Aqi = () => {
 const chart = echarts.init(document.getElementById('scatter-pm25-aqi')!);
 chartInstances.push(chart);
 const option: echarts.EChartsOption = {
 title: { text: 'PM2.5与AQI散点图', left: 'center', textStyle: { color: tc().p } },
 tooltip: { trigger: 'item', formatter: 'PM2.5: {b}<br/>AQI: {c}' },
 grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
 xAxis: { type: 'value', name: 'PM2.5', nameTextStyle: { color: tc().s }, axisLabel: { color: tc().s } },
 yAxis: { type: 'value', name: 'AQI', nameTextStyle: { color: tc().s }, axisLabel: { color: tc().s } },
 series: [{
 name: 'PM2.5 vs AQI',
 type: 'scatter',
 data: scatterPm25Aqi.value.slice(0, 500).map(item => [item['PM2.5'], item['AQI']]),
 symbolSize: 8,
 itemStyle: { color: '#e74c3c', opacity: 0.6 }
 }]
 };
 chart.setOption(option);
 window.addEventListener('resize', () => chart.resize());
};
const initScatterPm25Pm10 = () => {
 const chart = echarts.init(document.getElementById('scatter-pm25-pm10')!);
 chartInstances.push(chart);
 const option: echarts.EChartsOption = {
 title: { text: 'PM2.5与PM10散点图', left: 'center', textStyle: { color: tc().p } },
 tooltip: { trigger: 'item', formatter: 'PM2.5: {b}<br/>PM10: {c}' },
 grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
 xAxis: { type: 'value', name: 'PM2.5', nameTextStyle: { color: tc().s }, axisLabel: { color: tc().s } },
 yAxis: { type: 'value', name: 'PM10', nameTextStyle: { color: tc().s }, axisLabel: { color: tc().s } },
 series: [{
 name: 'PM2.5 vs PM10',
 type: 'scatter',
 data: scatterPm25Pm10.value.slice(0, 500).map(item => [item['PM2.5'], item['PM10']]),
 symbolSize: 8,
 itemStyle: { color: '#3498db', opacity: 0.6 }
 }]
 };
 chart.setOption(option);
 window.addEventListener('resize', () => chart.resize());
};
const getQualityColor = (level: string): string => {
 const colors: Record<string, string> = {
 '优': '#2ecc71',
 '良': '#3498db',
 '轻度污染': '#f39c12',
 '中度污染': '#e67e22',
 '重度污染': '#e74c3c',
 '严重污染': '#8e44ad'
 };
 return colors[level] || '#95a5a6';
};
</script>

<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-primary">EDA数据分析</h1>
      <p class="text-secondary mt-2">探索性数据分析 - 兰州市空气质量数据</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-card rounded-xl p-6">
        <div id="quality-pie" class="w-full h-80"></div>
      </div>
      <div class="bg-card rounded-xl p-6">
        <div class="flex items-center justify-end mb-4">
          <div class="flex items-center gap-2">
            <span class="text-sm text-secondary">选择年份:</span>
            <select
              v-model="selectedAqiYear"
              class="bg-card border border-color rounded-lg px-3 py-2 text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option v-for="year in availableAqiYears" :key="year" :value="year">{{ year === '全部' ? '全部年份' : year + '年' }}</option>
            </select>
          </div>
        </div>
        <div id="aqi-time-series" class="w-full h-72"></div>
      </div>
      <div class="bg-card rounded-xl p-6">
        <div id="monthly-bar" class="w-full h-80"></div>
      </div>
      <div class="bg-card rounded-xl p-6">
        <div id="seasonal-bar" class="w-full h-80"></div>
      </div>
      <div class="bg-card rounded-xl p-6">
        <div class="flex items-center justify-end mb-4">
          <div class="flex items-center gap-2">
            <span class="text-sm text-secondary">选择年份:</span>
            <select
              v-model="selectedYear"
              class="bg-card border border-color rounded-lg px-3 py-2 text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option v-for="year in availableYears" :key="year" :value="year">{{ year === '全部' ? '全部年份' : year + '年' }}</option>
            </select>
          </div>
        </div>
        <div id="correlation-heatmap" class="w-full h-80"></div>
      </div>
      <div class="bg-card rounded-xl p-6">
        <h2 class="text-lg font-semibold text-primary mb-4">统计汇总表</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-color">
                <th class="text-left py-3 px-4 text-secondary">特征</th>
                <th class="text-right py-3 px-4 text-secondary">均值</th>
                <th class="text-right py-3 px-4 text-secondary">标准差</th>
                <th class="text-right py-3 px-4 text-secondary">最小值</th>
                <th class="text-right py-3 px-4 text-secondary">中位数</th>
                <th class="text-right py-3 px-4 text-secondary">最大值</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in statsData" :key="row['特征']" class="border-b border-color/50">
                <td class="py-3 px-4 text-primary">{{ row['特征'] }}</td>
                <td class="py-3 px-4 text-right text-secondary">{{ row['均值'] }}</td>
                <td class="py-3 px-4 text-right text-secondary">{{ row['标准差'] }}</td>
                <td class="py-3 px-4 text-right text-secondary">{{ row['最小值'] }}</td>
                <td class="py-3 px-4 text-right text-secondary">{{ row['中位数'] }}</td>
                <td class="py-3 px-4 text-right text-secondary">{{ row['最大值'] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="bg-card rounded-xl p-6">
        <div id="scatter-pm25-aqi" class="w-full h-80"></div>
      </div>
      <div class="bg-card rounded-xl p-6">
        <div id="scatter-pm25-pm10" class="w-full h-80"></div>
      </div>
      <div class="bg-card rounded-xl p-6 lg:col-span-2">
        <div class="flex items-center justify-end mb-4">
          <div class="flex items-center gap-2">
            <span class="text-sm text-secondary">选择年份:</span>
            <select
              v-model="selectedPollutantYear"
              class="bg-card border border-color rounded-lg px-3 py-2 text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option v-for="year in availablePollutantYears" :key="year" :value="year">{{ year === '全部' ? '全部年份' : year + '年' }}</option>
            </select>
          </div>
        </div>
        <div id="pollutants-time-series" class="w-full h-80"></div>
      </div>
    </div>
  </div>
</template>
