<template>
  <div>
    <h3 style="margin-bottom: 20px">仪表盘概览</h3>

    <!-- Stats Cards (clickable) -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in stats" :key="card.label">
        <el-card shadow="never" class="stat-card" @click="card.to ? $router.push(card.to) : null">
          <div style="font-size: 32px; font-weight: bold; color: #409eff">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- Recent Scans -->
      <el-col :span="14">
        <el-card shadow="never">
          <template #header><span>最近扫描</span></template>
          <el-table :data="recentScans" stripe v-if="recentScans.length" @row-click="goToReport">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column label="项目" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">
                <span style="cursor:pointer;color:#7fc1ff" @click.stop="$router.push('/projects')">{{ projName(row.project_id) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_vulnerabilities" label="漏洞数" width="80" />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'running'" type="warning" size="small">
                  <span class="scan-pulse"></span> 扫描中
                </el-tag>
                <el-tag v-else :type="row.status === 'completed' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" min-width="160">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>
          <div v-else class="empty-box">暂无扫描数据</div>
        </el-card>
      </el-col>

      <!-- Donut Chart + Tag Cloud -->
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span>漏洞类型分布</span></template>
          <div v-if="typeStats.length" class="dist-container">
            <!-- Donut Chart -->
            <div class="donut-wrapper">
              <svg viewBox="0 0 100 100" class="donut-svg">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#2a2a4e" stroke-width="12" />
                <circle
                  v-for="(seg, i) in donutSegments" :key="i"
                  cx="50" cy="50" r="40" fill="none"
                  :stroke="seg.color" stroke-width="12"
                  stroke-linecap="butt"
                  :stroke-dasharray="seg.dash"
                  :stroke-dashoffset="seg.offset"
                  transform="rotate(-90, 50, 50)"
                  style="transition: all 0.5s"
                />
                <text x="50" y="48" text-anchor="middle" fill="#f0f0f0" font-size="16" font-weight="bold">{{ totalVulns }}</text>
                <text x="50" y="62" text-anchor="middle" fill="#8888b0" font-size="6">漏洞总数</text>
              </svg>
            </div>
            <!-- Tag Cloud -->
            <div class="tag-cloud">
              <span
                v-for="t in typeStats" :key="t.type"
                class="vuln-tag"
                :style="{ fontSize: t.fontSize + 'px', color: t.color, borderColor: t.color }"
                :title="`${t.type}: ${t.count}个`"
                @click="$router.push('/reports?type=' + encodeURIComponent(t.type))"
              >{{ t.type }} ({{ t.count }})</span>
            </div>
            <!-- Legend -->
            <div class="legend">
              <div v-for="t in typeStats" :key="t.type" class="legend-item">
                <span class="legend-dot" :style="{ background: t.color }"></span>
                <span class="legend-label">{{ t.type }}</span>
                <span class="legend-count">{{ t.count }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-box">暂无漏洞数据</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { listProjects, listScans } from '../api'
import axios from 'axios'

const router = useRouter()
const projects = ref([])
const scans = ref([])
const recentScans = ref([])
const typeStats = ref([])
const totalVulns = ref(0)
let pollTimer = null

const hasRunning = computed(() => scans.value.some(s => s.status === 'running' || s.status === 'pending'))

const stats = ref([
  { label: '项目数', value: '-', to: '/projects' },
  { label: '扫描次数', value: '-', to: '/scans' },
  { label: '发现漏洞', value: '-', to: '/reports' },
  { label: 'Agent状态', value: '就绪', to: '/agents' },
])

const donutSegments = computed(() => {
  const total = typeStats.value.reduce((s, t) => s + t.count, 0) || 1
  const circumference = 2 * Math.PI * 40
  let currentOffset = 0
  return typeStats.value.map(t => {
    const length = (t.count / total) * circumference
    const seg = {
      color: t.color,
      dash: `${length} ${circumference - length}`,
      offset: -currentOffset,
    }
    currentOffset += length
    return seg
  })
})

const DONUT_COLORS = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a', '#b37feb', '#36cfc9', '#909399', '#79bbff']

const fetchData = async () => {
  try {
    projects.value = (await listProjects()).data
    scans.value = (await listScans()).data
    recentScans.value = scans.value.slice(0, 5)
    stats.value[0].value = projects.value.length
    stats.value[1].value = scans.value.length

    const typeMap = {}
    totalVulns.value = 0
    for (const s of scans.value) {
      if (s.status === 'completed' && s.total_vulnerabilities) {
        totalVulns.value += s.total_vulnerabilities
        try {
          const vulns = (await axios.get(`/api/reports/scan/${s.id}`)).data
          for (const v of vulns) {
            const t = v.vulnerability_type || '未分类'
            typeMap[t] = (typeMap[t] || 0) + 1
          }
        } catch (e) { /* skip */ }
      }
    }
    stats.value[2].value = totalVulns.value

    const entries = Object.entries(typeMap).sort((a, b) => b[1] - a[1])
    const maxCount = entries.length ? entries[0][1] : 1
    typeStats.value = entries.map(([type, count], i) => ({
      type, count,
      pct: Math.round(count / maxCount * 100),
      color: DONUT_COLORS[i % DONUT_COLORS.length],
      fontSize: 12 + (count / maxCount) * 8,
    }))
  } catch (e) { console.log('API not ready', e) }
}

const startPolling = () => {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    if (!hasRunning.value) {
      stopPolling()
      return
    }
    try {
      scans.value = (await listScans()).data
      recentScans.value = scans.value.slice(0, 5)
    } catch (e) { /* ignore */ }
  }, 3000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(async () => {
  await fetchData()
  if (hasRunning.value) startPolling()
})

onUnmounted(() => stopPolling())

const projName = (id) => {
  const p = projects.value.find(p => p.id === id)
  return p ? p.name : id
}

const goToReport = (row) => {
  router.push(`/reports?scan_id=${row.id}`)
}

const formatDate = (val) => {
  if (!val) return '-'
  const d = new Date(val.endsWith('Z') ? val : val + 'Z')
  if (isNaN(d.getTime())) return val
  const pad = (n) => String(n).padStart(2, '0')
  const ms = d.getTime() + 8 * 3600000
  const bj = new Date(ms)
  return `${bj.getUTCFullYear()}-${pad(bj.getUTCMonth()+1)}-${pad(bj.getUTCDate())} ${pad(bj.getUTCHours())}:${pad(bj.getUTCMinutes())}:${pad(bj.getUTCSeconds())}`
}
</script>

<style scoped>
.stat-card { text-align: center; cursor: pointer; transition: transform 0.15s; }
.stat-card:hover { transform: translateY(-2px); }
.stat-label { font-size: 14px; color: #a0a0c0; margin-top: 8px; }
.empty-box { height: 200px; display: flex; align-items: center; justify-content: center; color: #8080a0; }

/* Donut + Tags */
.dist-container { padding: 8px; }
.donut-wrapper { display: flex; justify-content: center; margin-bottom: 16px; }
.donut-svg { width: 140px; height: 140px; }

.tag-cloud { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin-bottom: 12px; }
.vuln-tag {
  display: inline-block; padding: 2px 8px; border-radius: 12px;
  border: 1px solid; cursor: pointer; transition: all 0.15s;
  background: rgba(255,255,255,0.03);
}
.vuln-tag:hover { background: rgba(255,255,255,0.1); transform: scale(1.05); }

.legend { display: flex; flex-direction: column; gap: 4px; padding: 0 8px; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.legend-label { color: #c0c0d0; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.legend-count { color: #8888b0; }

@media (max-width: 768px) {
  .el-col { width: 100% !important; }
  .donut-svg { width: 100px; height: 100px; }
}

.scan-pulse {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #e6a23c;
  margin-right: 4px;
  animation: pulse 1s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}
</style>
