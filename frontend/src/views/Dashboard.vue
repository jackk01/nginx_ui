<template>
  <div class="dashboard">
    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #409EFF;">
            <el-icon :size="32"><Server /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalServers }}</div>
            <div class="stat-label">服务器总数</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #67C23A;">
            <el-icon :size="32"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.onlineServers }}</div>
            <div class="stat-label">在线服务器</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #E6A23C;">
            <el-icon :size="32"><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.configFiles }}</div>
            <div class="stat-label">配置文件</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #F56C6C;">
            <el-icon :size="32"><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.offlineServers }}</div>
            <div class="stat-label">离线服务器</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Quick Actions -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="action-card">
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/servers')">
              <el-icon><Plus /></el-icon>
              添加服务器
            </el-button>
            <el-button @click="refreshStats">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Server List Preview -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>服务器列表</span>
              <el-button type="primary" link @click="$router.push('/servers')">
                查看全部
              </el-button>
            </div>
          </template>
          <el-table :data="servers" v-loading="loading">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="host" label="主机" />
            <el-table-column prop="mode" label="模式">
              <template #default="{ row }">
                <el-tag :type="row.mode === 'local' ? 'success' : 'warning'">
                  {{ row.mode === 'local' ? '本地' : '远程' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
                  {{ row.status === 'online' ? '在线' : '离线' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="{ row }">
                <el-button type="primary" link @click="$router.push(`/servers/${row.id}`)">
                  管理
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { serversApi, Server } from '@/api/servers'

const loading = ref(false)
const servers = ref<Server[]>([])

const stats = reactive({
  totalServers: 0,
  onlineServers: 0,
  offlineServers: 0,
  configFiles: 0
})

async function fetchServers() {
  loading.value = true
  try {
    const response = await serversApi.getServers()
    servers.value = response.data
    stats.totalServers = servers.value.length
    stats.onlineServers = servers.value.filter(s => s.status === 'online').length
    stats.offlineServers = servers.value.filter(s => s.status === 'offline').length
  } catch (error) {
    console.error('Failed to fetch servers:', error)
  } finally {
    loading.value = false
  }
}

function refreshStats() {
  fetchServers()
}

onMounted(() => {
  fetchServers()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  margin-bottom: 10px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.action-card .quick-actions {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>