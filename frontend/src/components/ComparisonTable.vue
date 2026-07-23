<template>
  <div class="cmp-wrap">
    <table class="cmp-table">
      <thead>
        <tr>
          <th class="metric-col">指标</th>
          <th v-for="m in modes" :key="m.key" :class="['mode-col', m.key, { best: m.key === bestMode }]">
            <div class="mode-name">{{ m.label }}</div>
            <div class="mode-sub">{{ m.sub }}</div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.key">
          <td class="metric-col">{{ row.label }}</td>
          <td v-for="m in modes" :key="m.key" :class="['mode-col', m.key, { best: m.key === bestMode && row.higherBetter }]">
            <span class="cell-val">{{ fmt(row, m.key) }}</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 检测率条形图 -->
    <div class="rate-chart">
      <div class="rate-title">已知漏洞检测率对比</div>
      <div v-for="m in modes" :key="m.key" class="rate-row">
        <span class="rate-label">{{ m.label }}</span>
        <div class="rate-track">
          <div class="rate-fill" :class="m.key" :style="{ width: rate(m.key) + '%' }"></div>
        </div>
        <span class="rate-val">{{ rate(m.key) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ cmp: { type: Object, required: true } })

const modes = [
  { key: 'baseline', label: '无 Agent', sub: '仅传统工具' },
  { key: 'single_agent', label: '单 Agent', sub: '工具+1个Agent' },
  { key: 'debate', label: '博弈后', sub: '三Agent辩论仲裁' },
]

const rows = [
  { key: 'findings_count', label: '检出漏洞数', higherBetter: true },
  { key: 'confirmed_count', label: '确认漏洞数', higherBetter: true },
  { key: 'critical_high_count', label: '高危漏洞数', higherBetter: true },
  { key: 'unique_types', label: '唯一漏洞类型', higherBetter: true },
  { key: 'gt', label: '命中已知漏洞类', higherBetter: true },
]

const fmt = (row, modeKey) => {
  const d = props.cmp[modeKey] || {}
  if (row.key === 'gt') return `${d.ground_truth_hits ?? 0}/${d.ground_truth_total ?? 0}`
  const v = d[row.key]
  return v == null ? '—' : v
}

const rate = (modeKey) => {
  const d = props.cmp[modeKey] || {}
  return d.detection_rate == null ? 0 : Math.round(d.detection_rate * 100)
}

// best mode = highest detection rate (tie-break by findings)
const bestMode = computed(() => {
  let best = 'baseline', bestScore = -1
  for (const m of modes) {
    const d = props.cmp[m.key] || {}
    const score = (d.detection_rate || 0) * 1000 + (d.findings_count || 0)
    if (score > bestScore) { bestScore = score; best = m.key }
  }
  return best
})
</script>

<style scoped>
.cmp-wrap { display: flex; gap: 20px; flex-wrap: wrap; }
.cmp-table { flex: 1; min-width: 320px; border-collapse: collapse; font-size: 13px; }
.cmp-table th, .cmp-table td { padding: 8px 10px; border-bottom: 1px solid #2a2a4e; text-align: center; }
.cmp-table thead th { background: rgba(255,255,255,0.03); }
.metric-col { text-align: left !important; color: #a0a0c0; width: 130px; }
.mode-name { font-weight: 600; color: #e0e0e0; }
.mode-sub { font-size: 11px; color: #8888b0; font-weight: normal; margin-top: 2px; }
.cell-val { color: #d0d0e0; font-weight: 500; }
td.best { background: rgba(103,194,58,0.10); }
td.best .cell-val { color: #67c23a; font-weight: 700; }
.mode-col.debate .mode-name { color: #67c23a; }

.rate-chart { flex: 1; min-width: 280px; }
.rate-title { font-size: 13px; color: #a0a0c0; margin-bottom: 12px; }
.rate-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.rate-label { width: 70px; font-size: 12px; color: #c0c0e0; }
.rate-track { flex: 1; height: 18px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
.rate-fill { height: 100%; border-radius: 4px; transition: width 0.6s; }
.rate-fill.baseline { background: #909399; }
.rate-fill.single_agent { background: #409eff; }
.rate-fill.debate { background: #67c23a; }
.rate-val { width: 42px; text-align: right; font-size: 12px; color: #e0e0e0; font-weight: 600; }
</style>
