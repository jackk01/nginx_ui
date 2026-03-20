<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>服务器列表</span>
              <el-button @click="refreshServers">
                <el-icon><Refresh /></el-icon>
                刷新
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
import { ref, onMounted } from 'vue'
import { serversApi } from '@/api/servers'
import type { Server } from '@/api/servers'

const loading = ref(false)
const servers = ref<Server[]>([])

async function fetchServers() {
  loading.value = true
  try {
    const response = await serversApi.getServers()
    servers.value = response.data
  } catch (error) {
    console.error('Failed to fetch servers:', error)
  } finally {
    loading.value = false
  }
}

function refreshServers() {
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
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
