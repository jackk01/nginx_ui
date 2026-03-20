<template>
  <el-container class="layout-container">
    <!-- Sidebar -->
    <el-aside :width="asideWidth">
      <div class="logo" :class="{ collapsed: isSidebarCollapsed }">
        <span>{{ isSidebarCollapsed ? 'N' : 'NGINX UI' }}</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isSidebarCollapsed"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/servers">
          <el-icon><DataBoard /></el-icon>
          <span>服务器管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- Main Content -->
    <el-container>
      <el-header>
        <div class="header-left">
          <el-button text @click="toggleSidebar" class="collapse-btn">
            <el-icon :size="18">
              <Fold v-if="!isSidebarCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
          <h2>{{ pageTitle }}</h2>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ authStore.user?.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataBoard, Expand, Fold, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isSidebarCollapsed = ref(false)
const asideWidth = computed(() => (isSidebarCollapsed.value ? '64px' : '220px'))

const activeMenu = computed(() => {
  if (route.path.startsWith('/servers')) return '/servers'
  return route.path
})

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/servers': '服务器管理',
    '/servers/:id': '服务器详情',
    '/servers/:id/config': '服务器配置',
    '/servers/:id/nginx-config': '配置文件管理',
    '/servers/:id/logs': '日志查看'
  }
  if (route.path.startsWith('/servers/')) {
    if (route.path.endsWith('/config')) return titles['/servers/:id/config']
    if (route.path.endsWith('/nginx-config')) return titles['/servers/:id/nginx-config']
    if (route.path.endsWith('/logs')) return titles['/servers/:id/logs']
    return titles['/servers/:id']
  }
  return titles[route.path] || '服务器管理'
})

function handleCommand(command: string) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  transition: width 0.2s ease;
  overflow: hidden;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 48px;
  height: 60px;
  color: white;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
  white-space: nowrap;
}

.logo.collapsed {
  justify-content: center;
  padding-left: 0;
}

.sidebar-menu {
  border-right: none;
}

.el-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #333;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-btn {
  padding: 6px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #666;
}

.el-main {
  background: #f0f2f5;
  padding: 20px;
}
</style>
