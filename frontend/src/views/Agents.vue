<template>
  <div>
    <h3 style="margin-bottom: 20px">Agent协作监控</h3>

    <!-- Agent Status Cards -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="8" v-for="agent in agents" :key="agent.name">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>{{ agent.icon }} {{ agent.name }}</span>
              <el-tag :type="agent.status === 'ready' ? 'success' : 'warning'" size="small">{{ agent.status === 'ready' ? '就绪' : '忙碌' }}</el-tag>
            </div>
          </template>
          <div class="agent-role">{{ agent.role }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Code Input -->
    <el-card shadow="never" class="mb-20">
      <template #header><span>AI代码分析</span></template>
      <el-input
        v-model="codeInput"
        type="textarea"
        :rows="8"
        placeholder="粘贴代码进行分析..."
        class="mb-16"
      />
      <div class="flex-row mb-16">
        <el-select v-model="language" style="width: 150px">
          <el-option label="Python" value="python" />
          <el-option label="JavaScript" value="javascript" />
          <el-option label="Java" value="java" />
          <el-option label="C" value="c" />
          <el-option label="C++" value="cpp" />
          <el-option label="Rust" value="rust" />
          <el-option label="Go" value="go" />
        </el-select>
        <el-button type="primary" @click="analyzeCode" :loading="loading">开始Agent协作分析</el-button>
        <el-tag v-if="taskStatus === 'running'" type="warning" effect="dark">
          <span style="display:inline-block;animation:pulse 1s infinite">●</span> 分析中...
        </el-tag>
        <el-tag v-else-if="taskStatus === 'completed'" type="success">分析完成</el-tag>
        <el-tag v-else-if="taskStatus === 'failed'" type="danger">分析失败</el-tag>
      </div>
    </el-card>

    <!-- Analysis Results -->
    <div v-if="result">
      <!-- Summary -->
      <el-card shadow="never" class="mb-20">
        <template #header>
          <span>
            分析结论
            <el-tag type="danger" style="margin-left: 12px">{{ result.total_vulnerabilities }} 个漏洞</el-tag>
            <el-tag type="warning" style="margin-left: 8px">风险评分: {{ result.risk_score }}</el-tag>
          </span>
        </template>
        <div class="summary-grid">
          <div class="summary-item">
            <div class="summary-label">审查员总结</div>
            <div class="summary-text">{{ result.review_summary || '无' }}</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">安全专家总结</div>
            <div class="summary-text">{{ result.summary || '无' }}</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">修复建议</div>
            <div class="summary-text">{{ result.fix_summary || '无' }}</div>
          </div>
        </div>
      </el-card>

      <!-- Debate Flow -->
      <el-card shadow="never" class="mb-20">
        <template #header>
          <span>Agent博弈过程 (共 {{ result.total_rounds }} 轮)</span>
        </template>

        <div class="debate-flow">
          <div v-for="(round, idx) in result.rounds" :key="idx" class="debate-round">
            <div class="round-header" @click="toggleRound(idx)">
              <span class="round-badge">第{{ idx + 1 }}轮</span>
              <span v-if="idx === 0" class="round-desc">初始分析</span>
              <span v-else class="round-desc">辩论轮次</span>
              <span class="toggle-icon">{{ expandedRounds[idx] ? '▼' : '▶' }}</span>
            </div>

            <div v-show="expandedRounds[idx]" class="round-body">
              <!-- Initial round: show each agent's result -->
              <div v-if="idx === 0" class="agent-results">
                <div class="debate-agent reviewer">
                  <div class="agent-label">🔍 审查员</div>
                  <div class="agent-content">
                    <div v-if="round.result?.findings" class="finding-tags">
                      <el-tag v-for="f in round.result.findings" :key="f.type" size="small" :type="sevTag(f.severity)" style="margin: 2px">{{ f.type }}</el-tag>
                    </div>
                    <div v-else class="no-data">无发现</div>
                  </div>
                </div>
                <div class="debate-agent security">
                  <div class="agent-label">🛡️ 安全专家</div>
                  <div class="agent-content">
                    <div v-if="round.result?.confirmed_findings" class="finding-tags">
                      <el-tag v-for="f in round.result.confirmed_findings" :key="f.type" size="small" :type="sevTag(f.severity)" style="margin: 2px">{{ f.type }}</el-tag>
                    </div>
                    <div v-else class="no-data">无发现</div>
                  </div>
                </div>
                <div class="debate-agent fixer">
                  <div class="agent-label">🔧 修复顾问</div>
                  <div class="agent-content">
                    <div v-if="round.result?.fixes" class="finding-tags">
                      <el-tag v-for="f in round.result.fixes" :key="f.type" size="small" type="success" style="margin: 2px">{{ f.type }}</el-tag>
                    </div>
                    <div v-else class="no-data">无修复方案</div>
                  </div>
                </div>
              </div>

              <!-- Debate rounds: show challenges -->
              <div v-else>
                <div v-if="round.challenges?.length" class="challenge-list">
                  <div v-for="(c, ci) in round.challenges" :key="ci" class="challenge-item">
                    <div class="challenge-header">
                      <span class="challenge-from">{{ c.from }}</span>
                      <span class="challenge-arrow">→ 质疑 →</span>
                      <span class="challenge-to">{{ c.to }}</span>
                    </div>
                    <div class="challenge-body">{{ c.reason || c.issue }}</div>
                  </div>
                </div>
                <div v-else class="no-data">辩论已收敛，无进一步质疑</div>

                <div v-if="round.reviewer || round.security || round.fixer" class="revised-results">
                  <div v-if="round.reviewer" class="debate-agent reviewer">
                    <div class="agent-label">🔍 审查员 (修正)</div>
                    <div class="agent-content">
                      <el-tag v-for="f in round.reviewer.findings" :key="f.type" size="small" :type="sevTag(f.severity)" style="margin: 2px">{{ f.type }}</el-tag>
                    </div>
                  </div>
                  <div v-if="round.security" class="debate-agent security">
                    <div class="agent-label">🛡️ 安全专家 (修正)</div>
                    <div class="agent-content">
                      <el-tag v-for="f in round.security.confirmed_findings" :key="f.type" size="small" :type="sevTag(f.severity)" style="margin: 2px">{{ f.type }}</el-tag>
                    </div>
                  </div>
                  <div v-if="round.fixer" class="debate-agent fixer">
                    <div class="agent-label">🔧 修复顾问 (修正)</div>
                    <div class="agent-content">
                      <el-tag v-for="f in round.fixer.fixes" :key="f.type" size="small" type="success" style="margin: 2px">{{ f.type }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Vulnerability Results -->
      <el-card shadow="never">
        <template #header><span>检测到的漏洞</span></template>
        <el-table :data="result.vulnerabilities" stripe>
          <el-table-column prop="type" label="漏洞类型" min-width="160" />
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="sevTag(row.severity)" size="small">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="line" label="行号" width="60" />
          <el-table-column prop="cvss_score" label="CVSS" width="80" />
          <el-table-column prop="attack_vector" label="攻击路径" min-width="200" show-overflow-tooltip />
          <el-table-column prop="impact" label="影响" min-width="150" show-overflow-tooltip />
          <el-table-column prop="confidence" label="置信度" width="80">
            <template #default="{ row }">{{ row.confidence }}%</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'confirmed' ? 'danger' : 'warning'" size="small">{{ row.status === 'confirmed' ? '已确认' : '新增' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="修复代码" width="100">
            <template #default="{ row }">
              <el-button v-if="row.fix" size="small" type="primary" link @click="showFix(row)">查看</el-button>
              <span v-else class="no-data">无</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Fix Code Dialog -->
      <el-dialog v-model="fixDialog" title="修复代码" width="60%">
        <pre class="fix-code">{{ currentFix }}</pre>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const agents = ref([
  { name: '代码审查员', icon: '🔍', role: '初步扫描代码，标记可疑模式，调用Semgrep引擎', status: 'ready' },
  { name: '安全专家', icon: '🛡️', role: '深度分析漏洞，验证审查员发现，评估CVSS风险等级', status: 'ready' },
  { name: '修复顾问', icon: '🔧', role: '生成修复方案，评估修复成本和最佳实践', status: 'ready' },
])
const codeInput = ref('')
const language = ref('python')
const loading = ref(false)
const result = ref(null)
const expandedRounds = ref({})
const fixDialog = ref(false)
const currentFix = ref('')
const taskStatus = ref('')

let pollTimer = null

onMounted(() => {
  const savedTaskId = localStorage.getItem('agent_task_id')
  const savedCode = localStorage.getItem('agent_code')
  const savedLang = localStorage.getItem('agent_language')
  if (savedTaskId) {
    codeInput.value = savedCode || ''
    language.value = savedLang || 'python'
    taskStatus.value = 'running'
    loading.value = true
    pollTask(savedTaskId)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const startAsyncAnalysis = async () => {
  if (!codeInput.value) return
  loading.value = true
  taskStatus.value = 'running'
  try {
    const res = await axios.post('/api/agents/analyze/async', { code: codeInput.value, language: language.value })
    const taskId = res.data.task_id
    localStorage.setItem('agent_task_id', taskId)
    localStorage.setItem('agent_code', codeInput.value)
    localStorage.setItem('agent_language', language.value)
    pollTask(taskId)
  } catch (e) {
    console.error(e)
    loading.value = false
    taskStatus.value = 'failed'
  }
}

const pollTask = (taskId) => {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const res = await axios.get(`/api/agents/analyze/${taskId}`)
      if (res.data.status === 'completed') {
        clearInterval(pollTimer)
        pollTimer = null
        result.value = res.data.result
        expandedRounds.value = {}
        for (let i = 0; i < (res.data.result?.rounds?.length || 0); i++) {
          expandedRounds.value[i] = true
        }
        loading.value = false
        taskStatus.value = 'completed'
        localStorage.removeItem('agent_task_id')
        localStorage.removeItem('agent_code')
        localStorage.removeItem('agent_language')
      } else if (res.data.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        loading.value = false
        taskStatus.value = 'failed'
        console.error('Analysis failed:', res.data.error)
        localStorage.removeItem('agent_task_id')
        localStorage.removeItem('agent_code')
        localStorage.removeItem('agent_language')
      }
    } catch (e) {
      // polling error, ignore
    }
  }, 2000)
}

const toggleRound = (idx) => {
  expandedRounds.value[idx] = !expandedRounds.value[idx]
}

const analyzeCode = async () => {
  startAsyncAnalysis()
}

const sevTag = (sev) => {
  const map = { critical: 'danger', high: 'danger', medium: 'warning', low: 'info' }
  return map[sev?.toLowerCase()] || 'info'
}

const showFix = (row) => {
  currentFix.value = row.fix
  fixDialog.value = true
}
</script>

<style scoped>
.agent-role { font-size: 13px; color: #a0a0c0; margin-top: 4px; }
.mb-20 { margin-bottom: 20px; }
.mb-16 { margin-bottom: 16px; }
.flex-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.summary-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.summary-item { padding: 12px; background: #252545; border-radius: 6px; }
.summary-label { font-size: 12px; color: #8888b0; margin-bottom: 6px; }
.summary-text { font-size: 13px; color: #d0d0e0; line-height: 1.5; }
.no-data { font-size: 12px; color: #666; font-style: italic; }

/* Debate Flow */
.debate-flow { display: flex; flex-direction: column; gap: 12px; }
.debate-round { background: #252545; border-radius: 8px; overflow: hidden; }
.round-header {
  display: flex; align-items: center; gap: 12px; padding: 12px 16px;
  cursor: pointer; user-select: none;
  background: #1e1e3a; border-bottom: 1px solid #3a3a5e;
}
.round-header:hover { background: #2a2a4e; }
.round-badge {
  display: inline-block; padding: 2px 10px; border-radius: 10px;
  background: #409eff; color: #fff; font-size: 12px; font-weight: 600;
}
.round-desc { font-size: 13px; color: #a0a0c0; flex: 1; }
.toggle-icon { font-size: 12px; color: #888; }
.round-body { padding: 16px; }

.agent-results, .revised-results { display: flex; flex-direction: column; gap: 12px; }
.debate-agent { padding: 12px; border-radius: 6px; border-left: 3px solid; }
.debate-agent.reviewer { background: rgba(64,158,255,0.08); border-left-color: #409eff; }
.debate-agent.security { background: rgba(245,108,108,0.08); border-left-color: #f56c6c; }
.debate-agent.fixer { background: rgba(103,194,58,0.08); border-left-color: #67c23a; }
.agent-label { font-size: 13px; font-weight: 600; color: #d0d0e0; margin-bottom: 6px; }
.agent-content { }
.finding-tags { display: flex; flex-wrap: wrap; gap: 2px; }

.challenge-list { display: flex; flex-direction: column; gap: 8px; }
.challenge-item {
  padding: 10px 12px; background: rgba(230,162,60,0.08); border-radius: 6px;
  border-left: 3px solid #e6a23c;
}
.challenge-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.challenge-from { font-size: 12px; font-weight: 600; color: #f56c6c; }
.challenge-arrow { font-size: 11px; color: #e6a23c; }
.challenge-to { font-size: 12px; font-weight: 600; color: #409eff; }
.challenge-body { font-size: 13px; color: #c0c0d0; line-height: 1.5; }

.fix-code {
  background: #0a0a1a !important; color: #e0e0e0 !important;
  padding: 16px; border-radius: 6px; overflow-x: auto;
  font-size: 13px; line-height: 1.6; white-space: pre-wrap;
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

@media (max-width: 768px) {
  .summary-grid { grid-template-columns: 1fr; }
  .flex-row { flex-direction: column; align-items: stretch; }
  .flex-row .el-select { width: 100% !important; }
}
</style>
