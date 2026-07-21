<template>
  <el-container style="min-height: 100vh">
    <el-aside width="220px" style="background: #1a1a2e">
      <div class="logo">AI-SAST</div>
      <el-menu :router="true" background-color="#1a1a2e" text-color="#fff" active-text-color="#409eff">
        <el-menu-item index="/">📊 仪表盘</el-menu-item>
        <el-menu-item index="/projects">📁 项目管理</el-menu-item>
        <el-menu-item index="/scans">🔍 扫描任务</el-menu-item>
        <el-menu-item index="/reports">📋 漏洞报告</el-menu-item>
        <el-menu-item index="/agents">🤖 Agent监控</el-menu-item>
        <el-menu-item index="/knowledge">⚙️ 知识库</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background: #16213e; color: #fff; display: flex; align-items: center; justify-content: space-between">
        <h2>AI-SAST 智能安全扫描平台</h2>
        <span>v0.1.0</span>
      </el-header>
      <el-main style="background: #0f0f23; color: #fff">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>

<style>
body { margin: 0; }
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  color: #409eff;
  border-bottom: 1px solid #2a2a4e;
}
.el-menu { border-right: none !important; }
</style>
