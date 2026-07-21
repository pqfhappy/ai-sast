<template>
  <div>
    <h3 style="margin-bottom: 20px">Agent协作监控</h3>
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="8" v-for="agent in agents" :key="agent.name">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>{{ agent.icon }} {{ agent.name }}</span>
              <el-tag :type="agent.status === 'ready' ? 'success' : 'warning'" size="small">{{ agent.status }}</el-tag>
            </div>
          </template>
          <div style="font-size: 13px; color: #999">{{ agent.role }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header><span>🎯 AI代码分析</span></template>
      <el-input
        v-model="codeInput"
        type="textarea"
        :rows="8"
        placeholder="粘贴代码进行分析..."
        style="margin-bottom: 16px"
      />
      <div style="display: flex; gap: 12px; margin-bottom: 16px">
        <el-select v-model="language" style="width: 150px">
          <el-option label="Python" value="python" />
          <el-option label="JavaScript" value="javascript" />
          <el-option label="Java" value="java" />
        </el-select>
        <el-button type="primary" @click="analyzeCode" :loading="loading">开始Agent协作分析</el-button>
      </div>

      <div v-if="result" style="margin-top: 16px">
        <el-divider content-position="left">分析结果</el-divider>
        <el-timeline>
          <el-timeline-item v-for="(round, idx) in result.rounds" :key="idx" :timestamp="'第' + (idx + 1) + '轮'" placement="top">
            <div v-if="round.challenges" style="font-size: 12px; color: #e6a23c; margin-bottom: 8px">
              ⚡ 质疑: {{ round.challenges.map(c => c.issue).join(', ') }}
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-table :data="result.vulnerabilities" stripe style="margin-top: 12px">
          <el-table-column prop="type" label="漏洞类型" width="160" />
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="sevType(row.severity)" size="small">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="line" label="行号" width="60" />
          <el-table-column prop="attack_vector" label="攻击路径" />
          <el-table-column prop="confidence" label="置信度" width="80">
            <template #default="{ row }">{{ row.confidence }}%</template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
const agents = ref([
  { name: '代码审查员', icon: '🔍', role: '初步扫描代码，标记可疑模式', status: 'ready' },
  { name: '安全专家', icon: '🛡️', role: '深度分析漏洞，评估风险等级', status: 'ready' },
  { name: '修复顾问', icon: '🔧', role: '生成修复方案，评估修复成本', status: 'ready' },
])
const codeInput = ref('')
const language = ref('python')
const loading = ref(false)
const result = ref(null)

const analyzeCode = async () => {
  if (!codeInput.value) return
  loading.value = true
  try {
    const res = await axios.post('/api/agents/analyze', { code: codeInput.value, language: language.value })
    result.value = res.data
  } catch (e) {
    console.error(e)
  }
  loading.value = false
}

const sevType = (sev) => {
  const map = { critical: 'danger', high: 'danger', medium: 'warning', low: 'info' }
  return map[sev?.toLowerCase()] || 'info'
}
</script>
