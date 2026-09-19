/**
 * 批量替换 Vue 文件中硬编码的颜色值为 CSS 变量
 * 运行: node fix-colors.mjs
 */
import { readFileSync, writeFileSync, readdirSync, statSync } from 'fs'
import { join } from 'path'

const pagesDir = 'f:/PythonProject/Machine learning/课程设计/web/src'

// 需要处理的文件
const files = [
  'pages/Dashboard.vue',
  'pages/EdaAnalysis.vue',
  'pages/Trend.vue',
  'pages/Distribution.vue',
  'pages/Correlation.vue',
  'pages/Clustering.vue',
  'pages/MapView.vue',
  'pages/FeatureEngineering.vue',
  'pages/PredictionAnalysis.vue',
  'components/common/StatCard.vue',
  'components/common/DataTable.vue',
  'components/charts/MapChart.vue',
]

// 颜色映射表
const replacements = [
  // 文本颜色
  { from: /class="[^"]*text-\[#f1f5f9\][^"]*"/g, to: (m) => m.replace('text-[#f1f5f9]', 'style="color: var(--text-primary)"').replace(/class="/, 'class="') },
  { from: /class="[^"]*\btext-\[#94a3b8\][^"]*"/g, to: (m) => m.replace('text-[#94a3b8]', 'style="color: var(--text-secondary)"') },

  // 背景颜色
  { from: /bg-\[#1a2332\]/g, to: 'style="background: var(--bg-secondary)"' },
  { from: /bg-\[#2d3a4f\]\/50/g, to: 'style="background: var(--border-color)"' },
  { from: /bg-\[#2d3a4f\]/g, to: 'style="background: var(--border-color)"' },
  { from: /bg-\[#1e293b\]/g, to: 'style="background: var(--bg-card)"' },
  { from: /bg-\[#4a5568\]/g, to: 'style="background: var(--border-color)"' },

  // 边框颜色
  { from: /border-\[#2d3a4f\]/g, to: 'style="border-color: var(--border-color)"' },
  { from: /border-\[#334155\]/g, to: 'style="border-color: var(--border-color)"' },
  { from: /border-\[#4a5568\]/g, to: 'style="border-color: var(--border-color)"' },
  { from: /border-\[#1e293b\]/g, to: 'style="border-color: var(--border-color)"' },
]

for (const file of files) {
  const path = join(pagesDir, file)
  try {
    let content = readFileSync(path, 'utf-8')
    let changed = false

    for (const { from, to } of replacements) {
      const newContent = content.replace(from, to)
      if (newContent !== content) {
        changed = true
        content = newContent
      }
    }

    if (changed) {
      writeFileSync(path, content, 'utf-8')
      console.log(`✓ Updated: ${file}`)
    } else {
      console.log(`- No changes: ${file}`)
    }
  } catch (err) {
    console.error(`✗ Error: ${file} - ${err.message}`)
  }
}

console.log('\nDone!')
