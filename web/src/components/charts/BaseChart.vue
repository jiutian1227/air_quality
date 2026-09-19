<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import {
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  HeatmapChart,
  RadarChart,
  BoxplotChart,
  GaugeChart,
  SankeyChart,
  FunnelChart,
  ParallelChart,
  MapChart,
  EffectScatterChart,
  CustomChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  DataZoomComponent,
  ToolboxComponent,
  GeoComponent,
  CalendarComponent,
  PolarComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import 'echarts-wordcloud'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  HeatmapChart,
  RadarChart,
  BoxplotChart,
  CustomChart,
  GaugeChart,
  SankeyChart,
  FunnelChart,
  ParallelChart,
  MapChart,
  EffectScatterChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  DataZoomComponent,
  ToolboxComponent,
  GeoComponent,
  CalendarComponent,
  PolarComponent
])

defineProps<{ options: Record<string, any>; height?: string }>()
</script>

<template>
  <VChart :option="options" :style="{ height: height || '400px' }" autoresize />
</template>
