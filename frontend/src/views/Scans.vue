<template>
  <div>
    <h3 style="margin-bottom: 20px">扫描任务</h3>

    <el-card shadow="never" style="margin-bottom: 20px">
      <template #header><span>新建扫描</span></template>
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
    </el-card>

    <el-card shadow="never">
      <template #header><span>扫描历史</span></template>
      <el-table :data="scans" stripe @row-click="viewReport" style="cursor: pointer">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="project_id" label="项目" width="80">
          <template #default="{ row }">{{ projName(row.project_id) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="branch" label="分支" width="100" />
        <el-table-column prop="total_vulnerabilities" label="漏洞数" width="80" />
        <el-table-column prop="created_at" label="创建时间" />
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listProjects, listScans, createScan, runScan } from '../api'

const router = useRouter()
const projects = ref([])
const scans = ref([])
const running = ref(false)
const scanForm = ref({ project_id: null, code: '', language: 'python' })

onMounted(async () => {
  try {
    projects.value = (await listProjects()).data
    scans.value = (await listScans()).data
  } catch (e) { console.log('API not ready') }
})

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
  } catch (e) { console.error(e) }
  running.value = false
}

const viewReport = (row) => {
  router.push(`/reports?scan_id=${row.id}`)
}
</script>
