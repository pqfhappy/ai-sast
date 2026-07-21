<template>
  <el-container style="min-height: 100vh">
    <el-aside width="220px" style="background: #1a1a2e; border-right: 1px solid #2a2a4e">
      <div class="logo">
        <span class="logo-icon">🛡️</span>
        <span class="logo-text">AI-SAST</span>
      </div>
      <el-menu :router="true" background-color="#1a1a2e" text-color="#b0b0c0" active-text-color="#409eff" style="border-right: none">
        <el-menu-item index="/"><span class="menu-icon">📊</span>仪表盘</el-menu-item>
        <el-menu-item index="/projects"><span class="menu-icon">📁</span>项目管理</el-menu-item>
        <el-menu-item index="/scans"><span class="menu-icon">🔍</span>扫描任务</el-menu-item>
        <el-menu-item index="/reports"><span class="menu-icon">📋</span>漏洞报告</el-menu-item>
        <el-menu-item index="/agents"><span class="menu-icon">🤖</span>Agent监控</el-menu-item>
        <el-menu-item index="/knowledge"><span class="menu-icon">⚙️</span>知识库</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background: #16213e; color: #e0e0e0; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #2a2a4e; height: 60px; padding: 0 24px">
        <h2 style="margin: 0; font-size: 18px; font-weight: 500">AI-SAST 智能安全扫描平台</h2>
        <div>
          <el-tag size="small" type="success" effect="dark" style="margin-right: 8px">● 运行中</el-tag>
          <span style="font-size: 12px; color: #8888b0">v0.1.0</span>
        </div>
      </el-header>
      <el-main style="background: #0f0f23; color: #e0e0e0; padding: 20px; min-height: calc(100vh - 60px)">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f23 }
.el-menu { border-right: none !important; }
.logo { height: 60px; display: flex; align-items: center; justify-content: center; gap: 8px; border-bottom: 1px solid #2a2a4e; }
.logo-icon { font-size: 24px; }
.logo-text { font-size: 20px; font-weight: bold; color: #409eff; }
.menu-icon { margin-right: 8px; }
.el-menu-item { display: flex; align-items: center; }

/* ===== Dark Theme Overrides ===== */
.el-card {
  background: #1e1e3a !important;
  border: 1px solid #3a3a5e !important;
  color: #f0f0f0 !important;
}
.el-card__header {
  border-bottom: 1px solid #3a3a5e !important;
  color: #f0f0f0 !important;
  font-weight: 600;
}

.el-table {
  background: #1e1e3a !important;
  color: #f0f0f0 !important;
  --el-table-border-color: #3a3a5e !important;
  --el-table-row-hover-bg-color: #2a2a4e !important;
  --el-fill-color-lighter: transparent !important;
  --el-fill-color: #1e1e3a !important;
}
.el-table th.el-table__cell {
  background: #16213e !important;
  color: #c0c0d0 !important;
  font-weight: 600;
}
.el-table td.el-table__cell {
  color: #f0f0f0 !important;
  border-bottom: 1px solid #2a2a4e !important;
  background: #1e1e3a !important;
}
.el-table--striped .el-table__body tr.el-table__row--striped td {
  background: #252545 !important;
}
.el-table__body tr.el-table__row--striped td.el-table__cell {
  background: #252545 !important;
}
.el-table__body tr.el-table__row > td.el-table__cell {
  background: #1e1e3a !important;
}
.el-table__body tr.el-table__row--striped > td.el-table__cell {
  background: #252545 !important;
}
.el-table tr:hover > td {
  background-color: #2a2a4e !important;
}
.el-table__expanded-cell {
  background: #1a1a30 !important;
}
.el-table__body-wrapper {
  background: #1e1e3a !important;
}

.el-dialog {
  background: #1e1e3a !important;
  color: #f0f0f0 !important;
}
.el-dialog__title { color: #f0f0f0 !important; }
.el-dialog__body { color: #d0d0d0 !important; }

.el-form-item__label { color: #c0c0d0 !important; }
.el-input__wrapper, .el-textarea__inner {
  background: #0f0f23 !important;
  box-shadow: 0 0 0 1px #3a3a5e inset !important;
  color: #f0f0f0 !important;
}
.el-input__inner, .el-textarea__inner { color: #f0f0f0 !important; }
.el-select__wrapper { background: #0f0f23 !important; box-shadow: 0 0 0 1px #3a3a5e inset !important; }
.el-select-dropdown { background: #1e1e3a !important; border: 1px solid #3a3a5e !important; }
.el-select-dropdown__item { color: #d0d0d0 !important; }
.el-select-dropdown__item.hover { background: #2a2a4e !important; }

.el-button--primary { background: #409eff !important; border-color: #409eff !important; }
.el-button--default {
  background: #2a2a4e !important;
  border-color: #3a3a5e !important;
  color: #d0d0d0 !important;
}
.el-button--default:hover {
  background: #3a3a5e !important;
  border-color: #5a5a7e !important;
  color: #f0f0f0 !important;
}

.el-tag { --el-tag-border-color: transparent !important; }

.el-timeline-item__wrapper { color: #d0d0d0 !important; }
.el-divider__text { color: #c0c0d0 !important; background: #1e1e3a !important; }
.el-divider { border-top-color: #3a3a5e !important; }

pre {
  color: #e0e0e0 !important;
  background: #0a0a1a !important;
  border: 1px solid #3a3a5e;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .el-aside { width: 60px !important; }
  .el-aside .logo-text,
  .el-aside .menu-icon + span:not(.el-menu--collapse) { display: none !important; }
  .el-aside .logo { flex-direction: column; gap: 0; }
  .el-aside .el-menu-item { justify-content: center; }
  .el-aside .menu-icon { margin-right: 0; }
  .el-header h2 { font-size: 14px !important; }
  .el-form--inline .el-form-item { display: block !important; margin-right: 0 !important; width: 100% !important; }
  .el-form--inline .el-form-item .el-select,
  .el-form--inline .el-form-item .el-input,
  .el-form--inline .el-form-item .el-textarea { width: 100% !important; }
  .el-table { font-size: 12px !important; }
  .el-table .el-table__cell { padding: 6px 4px !important; }
  .el-card__body { padding: 12px !important; }
  .el-row { margin-left: 0 !important; margin-right: 0 !important; }
  .el-col { padding-left: 0 !important; padding-right: 0 !important; width: 100% !important; }
}
</style>
