import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('../views/Dashboard.vue') },
  { path: '/projects', component: () => import('../views/Projects.vue') },
  { path: '/scans', component: () => import('../views/Scans.vue') },
  { path: '/reports', component: () => import('../views/Reports.vue') },
  { path: '/agents', component: () => import('../views/Agents.vue') },
  { path: '/experiment', component: () => import('../views/Experiment.vue') },
  { path: '/knowledge', component: () => import('../views/Knowledge.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
