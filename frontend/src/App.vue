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
          <span style="font-size: 12px; color: #888">v0.1.0</span>
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
.el-card { background: #1a1a2e !important; border: 1px solid #2a2a4e !important; color: #e0e0e0 !important; }
.el-table { background: #1a1a2e !important; color: #e0e0e0 !important; }
.el-table th { background: #16213e !important; color: #b0b0c0 !important; }
.el-table--striped .el-table__body tr.el-table__row--striped td { background: #1e1e3a !important; }
.el-dialog { background: #1a1a2e !important; color: #e0e0e0 !important; }
.el-dialog__title { color: #e0e0e0 !important; }
</style>
