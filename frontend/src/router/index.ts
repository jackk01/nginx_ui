import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/servers'
      },
      {
        path: 'servers',
        name: 'Servers',
        component: () => import('@/views/ServerList.vue')
      },
      {
        path: 'servers/:id',
        name: 'ServerDetail',
        component: () => import('@/views/ServerDetail.vue')
      },
      {
        path: 'servers/:id/config',
        name: 'ConfigEditor',
        component: () => import('@/views/ConfigEditor.vue')
      },
      {
        path: 'servers/:id/nginx-config',
        name: 'NginxConfigEditor',
        component: () => import('@/views/NginxConfigEditor.vue')
      },
      {
        path: 'servers/:id/logs',
        name: 'LogViewer',
        component: () => import('@/views/LogViewer.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/servers')
  } else {
    next()
  }
})

export default router
