<template>
  <div>
    <h3 style="margin-bottom: 6px">实验专区</h3>
    <p class="subtitle">基于真实开源靶场项目，验证多引擎扫描与 Agent 博弈的实际效果（数据来自真实扫描，非伪造）</p>

    <div v-if="loading" class="loading-box">加载实验数据中...</div>
    <div v-else-if="error" class="loading-box" style="color:#f56c6c">{{ error }}</div>

    <template v-else>
      <!-- 总体博弈效果对比 -->
      <el-card shadow="never" style="margin-bottom: 20px" v-if="overall">
        <template #header><span>总体 Agent 博弈效果（全部项目聚合）</span></template>
        <ComparisonTable :cmp="overall" />
      </el-card>

      <!-- 每个项目 -->
      <div v-for="p in projects" :key="p.project_name">
        <el-card shadow="never" style="margin-bottom: 20px">
          <template #header>
            <div class="proj-header">
              <a :href="p.repo_url" target="_blank" rel="noopener" class="proj-link">{{ p.project_name }} ↗</a>
              <el-tag size="small" type="info">{{ p.language }}</el-tag>
            </div>
          </template>

          <p class="proj-desc">{{ p.description }}</p>

          <!-- 诉求1: 资源描述 + 指标 -->
          <el-row :gutter="12" class="metric-row">
            <el-col :span="4">
              <div class="metric-box">
                <div class="metric-val">{{ p.expected_count }}</div>
                <div class="metric-lbl">预期漏洞数</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="metric-box">
                <div class="metric-val" style="color:#67c23a">{{ p.actual_count }}</div>
                <div class="metric-lbl">实际检出数</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="metric-box">
                <div class="metric-val" style="color:#409eff">{{ pct(p.metrics.detection_rate) }}</div>
                <div class="metric-lbl">已知漏洞覆盖率</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="metric-box">
                <div class="metric-val">{{ p.metrics.files_scanned }}</div>
                <div class="metric-lbl">扫描文件数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="metric-box sev-box">
                <div class="metric-lbl" style="margin-bottom:6px">严重度分布</div>
                <div class="sev-chips">
                  <span class="sev-chip crit">C {{ sev(p,'critical') }}</span>
                  <span class="sev-chip high">H {{ sev(p,'high') }}</span>
                  <span class="sev-chip med">M {{ sev(p,'medium') }}</span>
                  <span class="sev-chip low">L {{ sev(p,'low') }}</span>
                </div>
              </div>
            </el-col>
          </el-row>

          <!-- 诉求2: 博弈效果真实对比 -->
          <div class="cmp-title">Agent 博弈效果对比（真实扫描数据）</div>
          <ComparisonTable :cmp="p.agent_comparison" />

          <!-- 命中/漏报类别 -->
          <div class="cat-section">
            <div class="cat-row" v-for="mode in ['baseline','single_agent','debate']" :key="mode">
              <span class="cat-mode">{{ modeLabel(mode) }}</span>
              <span class="cat-hit">命中 {{ p.agent_comparison[mode].ground_truth_hits }}/{{ p.agent_comparison[mode].ground_truth_total }}:</span>
              <el-tag v-for="c in p.agent_comparison[mode].categories_detected" :key="c" size="small" type="success" class="cat-tag">{{ c }}</el-tag>
              <el-tag v-for="c in p.agent_comparison[mode].categories_missed" :key="'m'+c" size="small" type="danger" effect="plain" class="cat-tag">漏 {{ c }}</el-tag>
            </div>
          </div>
        </el-card>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { experimentSummary } from '../api'
import ComparisonTable from '../components/ComparisonTable.vue'

const projects = ref([])
const overall = ref(null)
const loading = ref(true)
const error = ref('')

const pct = (r) => (r == null ? '-' : Math.round(r * 100) + '%')
const sev = (p, k) => (p.metrics.severity_distribution || {})[k] || 0
const modeLabel = (m) => ({ baseline: '无Agent', single_agent: '单Agent', debate: '博弈后' }[m] || m)

onMounted(async () => {
  try {
    const res = await experimentSummary()
    projects.value = res.data.projects || []
    overall.value = res.data.overall || null
  } catch (e) {
    error.value = '实验数据尚未生成或加载失败：' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.subtitle { color: #8888b0; font-size: 13px; margin-bottom: 20px; }
.loading-box { text-align: center; padding: 60px; color: #8080a0; }

.proj-header { display: flex; align-items: center; gap: 12px; }
.proj-link { color: #7fc1ff; text-decoration: none; font-size: 16px; font-weight: 600; }
.proj-link:hover { text-decoration: underline; color: #a0d4ff; }
.proj-desc { color: #a0a0c0; font-size: 13px; margin: 0 0 16px; }

.metric-row { margin-bottom: 8px; }
.metric-box { text-align: center; padding: 12px 6px; background: rgba(255,255,255,0.03); border-radius: 6px; }
.metric-val { font-size: 26px; font-weight: bold; color: #e0e0e0; }
.metric-lbl { font-size: 12px; color: #8888b0; margin-top: 4px; }
.sev-box { text-align: left; padding: 10px 14px; }
.sev-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.sev-chip { font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.sev-chip.crit { background: rgba(245,68,68,0.18); color: #f56c6c; }
.sev-chip.high { background: rgba(230,162,60,0.18); color: #e6a23c; }
.sev-chip.med { background: rgba(64,158,255,0.18); color: #409eff; }
.sev-chip.low { background: rgba(103,194,58,0.18); color: #67c23a; }

.cmp-title { font-size: 14px; font-weight: 600; color: #c0c0e0; margin: 18px 0 10px; }

.cat-section { margin-top: 16px; padding-top: 14px; border-top: 1px solid #2a2a4e; }
.cat-row { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.cat-mode { font-size: 13px; font-weight: 600; color: #c0c0e0; width: 70px; }
.cat-hit { font-size: 12px; color: #8888b0; }
.cat-tag { margin: 0; }
</style>
