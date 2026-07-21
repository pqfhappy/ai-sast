<template>
  <div>
    <h3 style="margin-bottom: 20px">漏洞报告</h3>

    <el-card shadow="never" style="margin-bottom: 20px">
      <template #header><span>选择扫描任务</span></template>
      <el-select v-model="selectedScan" placeholder="选择扫描" style="width: 300px" @change="fetchReport">
        <el-option v-for="s in scans" :key="s.id" :label="`#${s.id} - ${projName(s.project_id)} (${statusLabel(s.status)})`" :value="s.id" />
      </el-select>
      <el-button style="margin-left: 12px" @click="fetchReport" :disabled="!selectedScan">刷新</el-button>
    </el-card>

    <el-card shadow="never" v-if="vulnerabilities.length">
      <template #header>
        <span>
          漏洞列表
          <el-tag style="margin-left: 12px" type="danger">{{ total }} 个漏洞</el-tag>
          <el-tag style="margin-left: 8px" type="warning">{{ highCount }} 个高危</el-tag>
          <el-tag style="margin-left: 8px" type="info">{{ lowCount }} 个低危</el-tag>
        </span>
      </template>
      <el-table :data="vulnerabilities" stripe>
        <el-table-column prop="vulnerability_type" label="漏洞类型" width="180" />
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="sevTag(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="line_start" label="行号" width="70">
          <template #default="{ row }">{{ row.line_start }}{{ row.line_end && row.line_end !== row.line_start ? '-' + row.line_end : '' }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="confidence" label="置信度" width="80">
          <template #default="{ row }">{{ row.confidence }}%</template>
        </el-table-column>
        <el-table-column label="来源" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.source || 'ai' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-divider content-position="left" v-if="expandedVuln">漏洞详情</el-divider>
      <div v-if="expandedVuln" style="padding: 12px; background: #252545; border-radius: 6px; margin-top: 12px; border: 1px solid #3a3a5e">
        <p><strong>类型：</strong>{{ expandedVuln.vulnerability_type }}</p>
        <p><strong>描述：</strong>{{ expandedVuln.description }}</p>
        <p v-if="expandedVuln.remediation"><strong>修复建议：</strong>{{ expandedVuln.remediation }}</p>
        <p v-if="expandedVuln.code_snippet"><strong>代码片段：</strong></p>
        <pre v-if="expandedVuln.code_snippet" style="background: #0d0d1a; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 12px">{{ expandedVuln.code_snippet }}</pre>
      </div>
    </el-card>

    <el-card shadow="never" v-else-if="selectedScan">
      <div style="text-align: center; padding: 40px; color: #8080a0">该扫描未发现漏洞，或报告正在生成中...</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { listScans, listProjects, getScanVulnerabilities } from '../api'

const route = useRoute()
const scans = ref([])
const projects = ref([])
const selectedScan = ref(null)
const vulnerabilities = ref([])
const expandedVuln = ref(null)

const total = ref(0)
const highCount = ref(0)
const lowCount = ref(0)

onMounted(async () => {
  try {
    projects.value = (await listProjects()).data
    scans.value = (await listScans()).data
    if (route.query.scan_id) {
      selectedScan.value = parseInt(route.query.scan_id)
      await fetchReport()
    }
  } catch (e) { console.log('API not ready') }
})

const projName = (id) => {
  const p = projects.value.find(p => p.id === id)
  return p ? p.name : id
}
const statusLabel = (s) => {
  const map = { completed: '已完成', running: '运行中', pending: '等待中', failed: '失败' }
  return map[s] || s
}
const sevTag = (s) => {
  const map = { critical: 'danger', high: 'danger', medium: 'warning', low: 'info', info: 'info' }
  return map[s] || 'info'
}

const fetchReport = async () => {
  if (!selectedScan.value) return
  const res = await getScanVulnerabilities(selectedScan.value)
  vulnerabilities.value = res.data
  total.value = res.data.length
  highCount.value = res.data.filter(v => v.severity === 'critical' || v.severity === 'high').length
  lowCount.value = res.data.filter(v => v.severity === 'low' || v.severity === 'info').length
}
</script>
