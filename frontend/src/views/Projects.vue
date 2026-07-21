<template>
  <div>
    <h1>项目管理</h1>
    <el-button type="primary" @click="dialogVisible = true">新建项目</el-button>
    <el-table :data="projects" style="margin-top:20px" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="language" label="语言" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="created_at" label="创建时间" />
    </el-table>
    <el-dialog v-model="dialogVisible" title="新建项目">
      <el-form :model="form">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
        <el-form-item label="语言"><el-input v-model="form.language" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { listProjects, createProject } from '../api'
const projects = ref([])
const dialogVisible = ref(false)
const form = ref({ name: '', description: '', language: '' })
onMounted(async () => { projects.value = (await listProjects()).data })
const handleCreate = async () => {
  await createProject(form.value)
  dialogVisible.value = false
  projects.value = (await listProjects()).data
}
</script>
