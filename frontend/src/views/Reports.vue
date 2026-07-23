<template>
  <div>
    <h3 style="margin-bottom: 20px">漏洞报告</h3>

    <el-card shadow="never" style="margin-bottom: 20px">
      <template #header><span>选择扫描任务</span></template>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-select v-model="selectedScan" placeholder="选择扫描" style="width: 100%" @change="fetchReport">
            <el-option v-for="s in scans" :key="s.id" :label="`#${s.id} - ${projName(s.project_id)} (${statusLabel(s.status)})`" :value="s.id" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input v-model="typeFilter" placeholder="筛选漏洞类型..." clearable @input="applyFilter" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="sevFilter" placeholder="严重程度" clearable style="width:100%" @change="applyFilter">
            <el-option label="全部" value="" />
            <el-option label="CRITICAL" value="critical" />
            <el-option label="HIGH" value="high" />
            <el-option label="MEDIUM" value="medium" />
            <el-option label="LOW" value="low" />
          </el-select>
        </el-col>
        <el-col :span="2">
          <el-button style="width:100%" @click="fetchReport">刷新</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" v-if="filteredVulns.length">
      <template #header>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
          <span>
            漏洞列表
            <el-tag style="margin-left: 12px" type="danger">{{ filteredVulns.length }} 个漏洞</el-tag>
            <el-tag style="margin-left: 8px" type="warning">{{ highCount }} 个高危</el-tag>
            <el-tag style="margin-left: 8px" type="info">{{ lowCount }} 个低危</el-tag>
          </span>
        </div>
      </template>

      <div v-if="currentScanInfo" class="scan-banner">
        <div class="banner-main">
          <span class="banner-project">{{ currentScanInfo.projectName }}</span>
          <el-tag size="small" :type="currentScanInfo.status === 'completed' ? 'success' : 'warning'" style="margin-left:10px">
            {{ statusLabel(currentScanInfo.status) }}
          </el-tag>
        </div>
        <div class="banner-meta">
          <span>扫描 #{{ currentScanInfo.id }}</span>
          <span>分支 {{ currentScanInfo.branch }}</span>
          <span>{{ formatDate(currentScanInfo.created_at) }}</span>
          <span>共 {{ currentScanInfo.total_vulnerabilities }} 个漏洞</span>
        </div>
      </div>

      <el-table
        ref="tableRef"
        :data="filteredVulns"
        stripe
        row-key="id"
        :expand-row-keys="expandRowKeys"
        @row-click="toggleRow"
        style="cursor:pointer"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="vuln-detail">
              <div class="detail-section">
                <div class="detail-label">文件</div>
                <div class="detail-text">
                  <el-tag size="small">{{ row.file_path || 'inline' }}</el-tag>
                  <span style="margin-left:8px;color:#8888b0">行 {{ row.line_start }}{{ row.line_end && row.line_end !== row.line_start ? '-' + row.line_end : '' }}</span>
                </div>
              </div>
              <div class="detail-section">
                <div class="detail-label">漏洞描述</div>
                <div class="detail-text">{{ row.description || '无描述' }}</div>
              </div>
              <div class="detail-section" v-if="row.code_snippet">
                <div class="detail-label">问题代码上下文</div>
                <div class="code-block">
                  <table>
                    <tr v-for="(ln, i) in parseSnippet(row.code_snippet, row)" :key="i" :class="{ 'is-vuln': ln.isVuln }">
                      <td class="ln-num">{{ ln.lineNum }}</td>
                      <td class="ln-code">{{ ln.code }}</td>
                    </tr>
                  </table>
                </div>
              </div>
              <div class="detail-section" v-else>
                <div class="detail-label">问题代码上下文</div>
                <div class="detail-text" style="color:#8888b0">（无代码片段数据，需重新扫描生成）</div>
              </div>
              <div class="detail-section" v-if="row.remediation">
                <div class="detail-label">修复建议</div>
                <div class="fix-text">{{ row.remediation }}</div>
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
        <el-table-column label="文件" width="120">
          <template #default="{ row }">{{ row.file_path ? row.file_path.split('/').pop() : 'inline' }}</template>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { listScans, listProjects, getScanVulnerabilities } from '../api'

const route = useRoute()
const scans = ref([])
const projects = ref([])
const selectedScan = ref(null)
const vulnerabilities = ref([])
const typeFilter = ref('')
const sevFilter = ref('')
const expandRowKeys = ref([])
const tableRef = ref(null)

const filteredVulns = computed(() => {
  let list = vulnerabilities.value
  if (typeFilter.value) {
    const f = typeFilter.value.toLowerCase()
    list = list.filter(v => v.vulnerability_type?.toLowerCase().includes(f))
  }
  if (sevFilter.value) {
    list = list.filter(v => v.severity?.toLowerCase() === sevFilter.value.toLowerCase())
  }
  return list
})

const highCount = computed(() => filteredVulns.value.filter(v => v.severity === 'critical' || v.severity === 'high').length)
const lowCount = computed(() => filteredVulns.value.filter(v => v.severity === 'low' || v.severity === 'info').length)

const currentScanInfo = computed(() => {
  if (!selectedScan.value) return null
  const s = scans.value.find(x => x.id === selectedScan.value)
  if (!s) return null
  return { ...s, projectName: projName(s.project_id) }
})

onMounted(async () => {
  try {
    projects.value = (await listProjects()).data
    scans.value = (await listScans()).data
    if (route.query.scan_id) {
      selectedScan.value = parseInt(route.query.scan_id)
      await fetchReport()
    } else if (route.query.type) {
      const done = scans.value.filter(s => s.status === 'completed')
      if (done.length) {
        selectedScan.value = done[done.length - 1].id
        await fetchReport()
      }
    }
    if (route.query.type) {
      typeFilter.value = route.query.type
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

const applyFilter = () => {}

const formatDate = (val) => {
  if (!val) return '-'
  const d = new Date(val.endsWith('Z') ? val : val + 'Z')
  if (isNaN(d.getTime())) return val
  const pad = (n) => String(n).padStart(2, '0')
  const ms = d.getTime() + 8 * 3600000
  const bj = new Date(ms)
  return `${bj.getUTCFullYear()}-${pad(bj.getUTCMonth()+1)}-${pad(bj.getUTCDate())} ${pad(bj.getUTCHours())}:${pad(bj.getUTCMinutes())}:${pad(bj.getUTCSeconds())}`
}

const fetchReport = async () => {
  if (!selectedScan.value) return
  const res = await getScanVulnerabilities(selectedScan.value)
  vulnerabilities.value = res.data
  expandRowKeys.value = []
}

const toggleRow = (row) => {
  const keys = expandRowKeys.value
  const idx = keys.indexOf(row.id)
  if (idx >= 0) {
    keys.splice(idx, 1)
  } else {
    keys.push(row.id)
  }
}

const parseSnippet = (snippet, row) => {
  if (!snippet) return []
  const lines = snippet.split('\n')
  const hasPipe = lines.some(l => l.includes('|'))
  if (hasPipe) {
    return lines.filter(l => l.includes('|')).map(line => {
      const isVuln = line.startsWith('>>>')
      const rest = isVuln ? line.slice(3) : line
      const trimmed = rest.trimStart()
      const idx = trimmed.indexOf('|')
      const lineNum = trimmed.slice(0, idx).trim()
      const code = trimmed.slice(idx + 1).trim()
      return { lineNum, code, isVuln }
    })
  }
  const start = row?.line_start || 0
  const end = row?.line_end || start
  return lines.map((line, i) => {
    const lineNum = i + 1
    const isVuln = lineNum >= start && lineNum <= end
    return { lineNum: String(lineNum), code: line, isVuln }
  })
}
</script>

<style>
/* ===== Global overrides for code block ===== */
.code-block .ln-code {
  padding: 2px 32px !important;
}
</style>

<style scoped>
.empty-state { text-align: center; padding: 40px; color: #8080a0; }
.scan-banner {
  margin-bottom: 16px; padding: 14px 18px;
  background: linear-gradient(135deg, rgba(64,158,255,0.10), rgba(64,158,255,0.03));
  border: 1px solid rgba(64,158,255,0.25); border-left: 4px solid #409eff;
  border-radius: 6px;
}
.banner-main { display: flex; align-items: center; margin-bottom: 6px; }
.banner-project { font-size: 18px; font-weight: 700; color: #e0e8ff; letter-spacing: 0.3px; }
.banner-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: 12px; color: #8888b0; }
.vuln-detail { padding: 16px 20px; }
.detail-section { margin-bottom: 14px; }
.detail-label {
  font-size: 12px; font-weight: 600; color: #8888b0;
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;
}
.detail-text { font-size: 14px; color: #d0d0e0; line-height: 1.6; }
.fix-text {
  padding: 12px; background: rgba(103,194,58,0.08); border-radius: 6px;
  border-left: 3px solid #67c23a; color: #d0d0e0; line-height: 1.6; font-size: 14px;
}
.code-block {
  background: #0d0d20; border-radius: 6px;
  overflow-x: auto; font-size: 13px; line-height: 1.5;
  border: 1px solid #2a2a4e; max-height: 320px; overflow-y: auto;
}
.code-block table { width: 100%; border-collapse: collapse; background: transparent; }
.code-block tr { background: transparent; transition: background 0.1s; }
.code-block tr:hover { background: rgba(255,255,255,0.04); }
.code-block tr.is-vuln { background: rgba(245,68,68,0.1); }
.code-block tr.is-vuln:hover { background: rgba(245,68,68,0.18); }
.code-block td { background: transparent; padding: 0; border: none; }
.ln-num {
  width: 48px; min-width: 48px; max-width: 48px;
  text-align: right; padding: 2px 12px 2px 8px;
  color: #555577; user-select: none;
  font-family: 'Consolas', 'Courier New', monospace;
  border-right: 1px solid #2a2a4e;
}
.ln-code {
  padding: 2px 12px; white-space: pre;
  color: #d0d0e0;
  font-family: 'Consolas', 'Courier New', monospace;
}
.code-block tr.is-vuln .ln-code { color: #f0c0c0; }
.code-block tr.is-vuln .ln-num { color: #f56c6c; }
</style>
