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
          <template #header><span>漏洞趋势（最近7天）</span></template>
          <div style="height: 250px; display: flex; align-items: center; justify-content: center; color: #666">
            等待扫描数据...
          </div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span>漏洞类型分布</span></template>
          <div style="height: 250px; display: flex; align-items: center; justify-content: center; color: #666">
            等待扫描数据...
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { health, listProjects } from '../api'
const stats = ref([
  { label: '扫描项目', value: '-' },
  { label: '发现漏洞', value: '-' },
  { label: '误报率', value: '-' },
  { label: 'Agent状态', value: '就绪' },
])
onMounted(async () => {
  try {
    const h = await health()
    const p = await listProjects()
    stats.value[0].value = p.data.length || 0
    console.log('API connected:', h.data)
  } catch (e) {
    console.log('API not available yet')
  }
})
</script>
