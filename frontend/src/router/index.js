import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { guest: true, title: 'Sign in' } },
  { path: '/', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { auth: true, title: 'Dashboard' } },
  { path: '/scan', name: 'scan', component: () => import('../views/ScanView.vue'), meta: { auth: true, title: 'Image scans' } },
  { path: '/alerts', name: 'alerts', component: () => import('../views/AlertsView.vue'), meta: { auth: true, title: 'Runtime alerts' } },
  { path: '/ai', name: 'ai', component: () => import('../views/AIAnalysisView.vue'), meta: { auth: true, title: 'AI analysis' } },
  { path: '/monitoring', name: 'monitoring', component: () => import('../views/MonitoringView.vue'), meta: { auth: true, title: 'Metrics' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isAuthenticated) return { name: 'login' }
  if (to.meta.guest && auth.isAuthenticated) return { name: 'dashboard' }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · AegisCloud` : 'AegisCloud'
})

export default router