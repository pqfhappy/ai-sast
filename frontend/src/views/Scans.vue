<template>
  <div>
    <h3 style="margin-bottom: 20px">扫描任务</h3>

    <el-card shadow="never" style="margin-bottom: 20px">
      <template #header><span>新建扫描</span></template>
      <el-tabs v-model="scanMode" style="margin-top:-8px">
        <el-tab-pane label="粘贴代码扫描" name="code">
          <el-form :inline="true" :model="scanForm">
            <el-form-item label="项目">
              <el-select v-model="scanForm.project_id" placeholder="选择项目" style="width: 200px">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="代码">
              <el-input v-model="scanForm.code" type="textarea" :rows="3" placeholder="粘贴要扫描的代码" style="width: 400px" />
            </el-form-item>
            <el-form-item label="语言">
              <el-select v-model="scanForm.language" style="width: 120px">
                <el-option label="Python" value="python" />
                <el-option label="JavaScript" value="javascript" />
                <el-option label="Java" value="java" />
                <el-option label="C" value="c" />
                <el-option label="C++" value="cpp" />
                <el-option label="Rust" value="rust" />
                <el-option label="Go" value="go" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleCreateAndRun" :loading="running">创建并扫描</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="真实项目扫描 (GitHub)" name="repo">
          <el-form :inline="true" :model="repoForm">
            <el-form-item label="项目">
              <el-select v-model="repoForm.project_id" placeholder="选择项目" style="width: 200px">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="仓库地址">
              <el-input v-model="repoForm.repo_url" placeholder="https://github.com/xxx/yyy.git" style="width: 320px" />
            </el-form-item>
            <el-form-item label="语言">
              <el-select v-model="repoForm.language" style="width: 120px">
                <el-option label="Python" value="python" />
                <el-option label="JavaScript" value="javascript" />
                <el-option label="Java" value="java" />
                <el-option label="PHP" value="php" />
                <el-option label="Go" value="go" />
                <el-option label="C" value="c" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleRepoScan" :loading="running">开始扫描</el-button>
            </el-form-item>
          </el-form>
          <div style="color:#8888b0;font-size:12px;margin-top:4px">
            AI 编排 Agent 将自主决定扫描策略（gitleaks 密钥检测 → trivy 依赖 CVE → semgrep → bandit → AI 深挖），扫描过程在后台进行，可实时查看状态。
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card shadow="never">
      <template #header><span>扫描历史</span></template>
      <el-table :data="scans" stripe @row-click="viewReport" style="cursor: pointer">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="项目" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span style="cursor:pointer;color:#7fc1ff" @click.stop="$router.push('/projects')">{{ projName(row.project_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'running'" type="warning" size="small">
              <el-icon class="is-loading" style="vertical-align: middle; margin-right: 4px"><Loading /></el-icon>
              扫描中
            </el-tag>
            <el-tag v-else :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="branch" label="分支" width="100" />
        <el-table-column prop="total_vulnerabilities" label="漏洞数" width="80">
          <template #default="{ row }">
            <span style="cursor:pointer;color:#7fc1ff" @click.stop="viewReport(row)">{{ row.total_vulnerabilities }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click.stop="viewReport(row)">查看报告</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listProjects, listScans, createScan, runScan, runProjectScan } from '../api'

const router = useRouter()
const projects = ref([])
const scans = ref([])
const running = ref(false)
const scanMode = ref('code')
const scanForm = ref({ project_id: null, code: '', language: 'python' })
const repoForm = ref({ project_id: null, repo_url: '', language: 'python' })
let pollTimer = null

const hasRunning = computed(() => scans.value.some(s => s.status === 'running' || s.status === 'pending'))

const fetchData = async () => {
  try {
    projects.value = (await listProjects()).data
    scans.value = (await listScans()).data
  } catch (e) { console.log('API not ready') }
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

const statusType = (s) => {
  const map = { completed: 'success', running: 'warning', pending: 'info', failed: 'danger' }
  return map[s] || 'info'
}
const statusLabel = (s) => {
  const map = { completed: '已完成', running: '运行中', pending: '等待中', failed: '失败' }
  return map[s] || s
}

const handleCreateAndRun = async () => {
  if (!scanForm.value.project_id || !scanForm.value.code) return
  running.value = true
  try {
    const scan = (await createScan({ project_id: scanForm.value.project_id, branch: 'master' })).data
    await runScan(scan.id, { code: scanForm.value.code, language: scanForm.value.language })
    scans.value = (await listScans()).data
    startPolling()
  } catch (e) { console.error(e) }
  running.value = false
}

const handleRepoScan = async () => {
  if (!repoForm.value.project_id || !repoForm.value.repo_url) {
    ElMessage.warning('请选择项目并填写仓库地址')
    return
  }
  running.value = true
  try {
    const scan = (await createScan({ project_id: repoForm.value.project_id, branch: 'master' })).data
    await runProjectScan(scan.id, { repo_url: repoForm.value.repo_url, language: repoForm.value.language })
    scans.value = (await listScans()).data
    startPolling()
    ElMessage.success('扫描已在后台启动，状态将自动刷新')
  } catch (e) {
    console.error(e)
    ElMessage.error('启动扫描失败')
  }
  running.value = false
}

const viewReport = (row) => {
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
