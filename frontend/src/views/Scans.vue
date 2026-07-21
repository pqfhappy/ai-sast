<template>
  <div>
    <h1>扫描任务</h1>
    <el-table :data="scans" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="project_id" label="项目ID" width="80" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="branch" label="分支" width="120" />
      <el-table-column prop="total_vulnerabilities" label="漏洞数" width="100" />
      <el-table-column prop="created_at" label="创建时间" />
    </el-table>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { listScans } from '../api'
const scans = ref([])
onMounted(async () => { scans.value = (await listScans()).data })
</script>
