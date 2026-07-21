<template>
  <div>
    <h3 style="margin-bottom: 20px">漏洞知识库</h3>
    <el-card shadow="never">
      <template #header><span>常见漏洞类型</span></template>
      <el-table :data="vulns" stripe v-if="vulns.length">
        <el-table-column prop="name" label="漏洞名称" width="160" />
        <el-table-column prop="cwe" label="CWE编号" width="100" />
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="row.severity === 'HIGH' || row.severity === 'CRITICAL' ? 'danger' : 'warning'" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="fix" label="修复建议" />
      </el-table>
      <div v-else style="color: #8080a0; text-align: center; padding: 40px">正在加载知识库...</div>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { listProjects } from '../api'
const vulns = ref([])
onMounted(async () => {
  try {
    const res = await (await fetch('/api/knowledge/vulnerabilities')).json()
    vulns.value = res
  } catch (e) { console.log('Knowledge API not ready') }
})
</script>
