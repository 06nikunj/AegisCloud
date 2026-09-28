import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
  { path: '/', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { auth: true } },
  { path: '/scan', name: 'scan', component: () => import('../views/ScanView.vue'), meta: { auth: true } },
  { path: '/alerts', name: 'alerts', component: () => import('../views/AlertsView.vue'), meta: { auth: true } },
  { path: '/ai', name: 'ai', component: () => import('../views/AIAnalysisView.vue'), meta: { auth: true } },
  { path: '/monitoring', name: 'monitoring', component: () => import('../views/MonitoringView.vue'), meta: { auth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isAuthenticated) return { name: 'login' }
  if (to.meta.guest && auth.isAuthenticated) return { name: 'dashboard' }
})

export default router