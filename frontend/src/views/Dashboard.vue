<template>
  <div>
    <h3 style="margin-bottom: 20px">仪表盘概览</h3>
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in stats" :key="card.label">
        <el-card shadow="never" style="margin-bottom: 20px; text-align: center">
          <div style="font-size: 32px; font-weight: bold; color: #409eff">{{ card.value }}</div>
          <div style="font-size: 14px; color: #888; margin-top: 8px">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header><span>最近扫描</span></template>
          <el-table :data="recentScans" stripe v-if="recentScans.length">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column label="项目" width="120">
              <template #default="{ row }">{{ projName(row.project_id) }}</template>
            </el-table-column>
            <el-table-column prop="total_vulnerabilities" label="漏洞数" width="80" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" />
          </el-table>
          <div v-else style="height: 200px; display: flex; align-items: center; justify-content: center; color: #666">
            暂无扫描数据
          </div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span>漏洞类型分布</span></template>
          <div v-if="typeStats.length" style="padding: 12px">
            <div v-for="t in typeStats" :key="t.type" style="margin-bottom: 10px">
              <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px">
                <span>{{ t.type || '未分类' }}</span>
                <span>{{ t.count }}</span>
              </div>
              <el-progress :percentage="t.pct" :stroke-width="12" :color="t.color" />
            </div>
          </div>
          <div v-else style="height: 200px; display: flex; align-items: center; justify-content: center; color: #666">
            暂无漏洞数据
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listProjects, listScans } from '../api'
import axios from 'axios'

const projects = ref([])
const scans = ref([])
const recentScans = ref([])
const typeStats = ref([])

const stats = ref([
  { label: '项目数', value: '-' },
  { label: '扫描次数', value: '-' },
  { label: '发现漏洞', value: '-' },
  { label: 'Agent状态', value: '就绪' },
])

onMounted(async () => {
  try {
    projects.value = (await listProjects()).data
    scans.value = (await listScans()).data
    recentScans.value = scans.value.slice(0, 5)
    stats.value[0].value = projects.value.length
    stats.value[1].value = scans.value.length

    let totalVulns = 0
    const typeMap = {}
    for (const s of scans.value) {
      if (s.status === 'completed' && s.total_vulnerabilities) {
        totalVulns += s.total_vulnerabilities
        try {
          const vulns = (await axios.get(`/api/reports/scan/${s.id}`)).data
          for (const v of vulns) {
            const t = v.vulnerability_type || '未分类'
            typeMap[t] = (typeMap[t] || 0) + 1
          }
        } catch (e) { /* skip */ }
      }
    }
    stats.value[2].value = totalVulns

    const entries = Object.entries(typeMap).sort((a, b) => b[1] - a[1])
    const maxCount = entries.length ? entries[0][1] : 1
    const colors = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a', '#909399', '#b37feb', '#36cfc9']
    typeStats.value = entries.map(([type, count], i) => ({
      type, count, pct: Math.round(count / maxCount * 100), color: colors[i % colors.length]
    }))
  } catch (e) { console.log('API not ready', e) }
})

const projName = (id) => {
  const p = projects.value.find(p => p.id === id)
  return p ? p.name : id
}
</script>
