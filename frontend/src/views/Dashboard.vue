<template>
  <div>
    <h1>仪表盘</h1>
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in stats" :key="card.label">
        <el-card style="margin-bottom:20px">
          <h3>{{ card.value }}</h3>
          <p>{{ card.label }}</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { health } from '../api'
const stats = ref([
  { label: '扫描项目', value: '-' },
  { label: '发现漏洞', value: '-' },
  { label: '误报率', value: '-' },
  { label: '平均耗时', value: '-' },
])
onMounted(async () => {
  const res = await health()
  console.log('API:', res.data)
})
</script>
