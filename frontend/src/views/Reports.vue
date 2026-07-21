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

      <el-table :data="vulnerabilities" stripe @row-click="toggleRow">
        <el-table-column type="expand" width="1">
          <template #default="{ row }">
            <div v-if="row === expandedRow" class="vuln-detail">
              <div class="detail-section">
                <div class="detail-label">漏洞描述</div>
                <div class="detail-text">{{ row.description || '无描述' }}</div>
              </div>
              <div class="detail-section" v-if="row.code_snippet">
                <div class="detail-label">问题代码</div>
                <pre class="code-block">{{ row.code_snippet }}</pre>
              </div>
              <div class="detail-section" v-if="row.remediation">
                <div class="detail-label">修复建议</div>
                <div class="detail-text fix-text">{{ row.remediation }}</div>
              </div>
              <div class="detail-section" v-if="row.agent_notes">
                <div class="detail-label">Agent分析备注</div>
                <div class="detail-text">{{ row.agent_notes }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="vulnerability_type" label="漏洞类型" width="180" />
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="sevTag(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="line_start" label="行号" width="70">
          <template #default="{ row }">{{ row.line_start }}{{ row.line_end && row.line_end !== row.line_start ? '-' + row.line_end : '' }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="confidence" label="置信度" width="80">
          <template #default="{ row }">{{ row.confidence }}%</template>
        </el-table-column>
        <el-table-column label="来源" width="70">
          <template #default="{ row }">
            <el-tag size="small">{{ row.source || 'ai' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" v-else-if="selectedScan">
      <div class="empty-state">该扫描未发现漏洞，或报告正在生成中...</div>
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
const expandedRow = ref(null)

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

const toggleRow = (row) => {
  expandedRow.value = expandedRow.value === row ? null : row
}
</script>

<style scoped>
.empty-state { text-align: center; padding: 40px; color: #8080a0; }
.vuln-detail { padding: 16px 20px; }
.detail-section { margin-bottom: 14px; }
.detail-label {
  font-size: 12px; font-weight: 600; color: #8888b0;
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;
}
.detail-text { font-size: 14px; color: #d0d0e0; line-height: 1.6; }
.fix-text {
  padding: 12px; background: rgba(103,194,58,0.08); border-radius: 6px;
  border-left: 3px solid #67c23a;
}
.code-block {
  background: #0a0a1a !important; color: #e0e0e0 !important;
  padding: 12px; border-radius: 6px; overflow-x: auto;
  font-size: 13px; line-height: 1.6; border: 1px solid #3a3a5e;
  white-space: pre-wrap; max-height: 300px; overflow-y: auto;
}
</style>
