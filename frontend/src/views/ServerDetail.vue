<template>
  <div class="server-detail">
    <el-page-header @back="$router.back()" content="服务器详情">
      <template #extra>
        <el-button type="primary" @click="$router.push(`/servers/${serverId}/config`)">
          <el-icon><Document /></el-icon>
          配置管理
        </el-button>
        <el-button @click="$router.push(`/servers/${serverId}/logs`)">
          <el-icon><Files /></el-icon>
          日志查看
        </el-button>
      </template>
    </el-page-header>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- Server Info -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>服务器信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="名称">{{ server?.name }}</el-descriptions-item>
            <el-descriptions-item label="主机">{{ server?.host }}</el-descriptions-item>
            <el-descriptions-item label="模式">
              <el-tag :type="server?.mode === 'local' ? 'success' : 'warning'">
                {{ server?.mode === 'local' ? '本地' : '远程' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="nginxStatus?.running ? 'success' : 'danger'">
                {{ nginxStatus?.running ? '运行中' : '未运行' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="版本">{{ nginxStatus?.version || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="PID" v-if="nginxStatus?.pid">{{ nginxStatus?.pid }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      
      <!-- Nginx Control -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>NGINX 控制</span>
          </template>
          <div class="control-buttons">
            <el-button type="success" :loading="loading" @click="handleStart">
              <el-icon><VideoPlay /></el-icon>
              启动
            </el-button>
            <el-button type="danger" :loading="loading" @click="handleStop">
              <el-icon><VideoPause /></el-icon>
              停止
            </el-button>
            <el-button type="warning" :loading="loading" @click="handleReload">
              <el-icon><Refresh /></el-icon>
              重载配置
            </el-button>
            <el-button type="info" :loading="loading" @click="handleRestart">
              <el-icon><RefreshRight /></el-icon>
              重启
            </el-button>
            <el-button @click="handleTestConfig">
              <el-icon><Check /></el-icon>
              测试配置
            </el-button>
          </div>
          
          <el-divider />
          
          <div v-if="testResult" class="test-result">
            <el-alert :type="testResult.success ? 'success' : 'error'" :title="testResult.output" show-icon />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { serversApi, Server, NginxStatus } from '@/api/servers'

const route = useRoute()
const serverId = Number(route.params.id)

const loading = ref(false)
const server = ref<Server | null>(null)
const nginxStatus = ref<NginxStatus | null>(null)
const testResult = ref<{ success: boolean; output: string } | null>(null)

async function fetchServer() {
  try {
    const response = await serversApi.getServer(serverId)
    server.value = response.data
  } catch (error) {
    ElMessage.error('获取服务器信息失败')
  }
}

async function fetchStatus() {
  try {
    const response = await serversApi.getNginxStatus(serverId)
    nginxStatus.value = response.data
  } catch (error) {
    console.error('Failed to fetch status:', error)
  }
}

async function handleStart() {
  loading.value = true
  try {
    const response = await serversApi.startNginx(serverId)
    if (response.data.success) {
      ElMessage.success('NGINX 已启动')
    } else {
      ElMessage.error(response.data.message)
    }
    fetchStatus()
  } catch (error) {
    ElMessage.error('启动失败')
  } finally {
    loading.value = false
  }
}

async function handleStop() {
  loading.value = true
  try {
    const response = await serversApi.stopNginx(serverId)
    if (response.data.success) {
      ElMessage.success('NGINX 已停止')
    } else {
      ElMessage.error(response.data.message)
    }
    fetchStatus()
  } catch (error) {
    ElMessage.error('停止失败')
  } finally {
    loading.value = false
  }
}

async function handleReload() {
  loading.value = true
  try {
    const response = await serversApi.reloadNginx(serverId)
    if (response.data.success) {
      ElMessage.success('配置已重载')
    } else {
      ElMessage.error(response.data.message)
    }
    fetchStatus()
  } catch (error) {
    ElMessage.error('重载失败')
  } finally {
    loading.value = false
  }
}

async function handleRestart() {
  loading.value = true
  try {
    const response = await serversApi.restartNginx(serverId)
    if (response.data.success) {
      ElMessage.success('NGINX 已重启')
    } else {
      ElMessage.error(response.data.message)
    }
    fetchStatus()
  } catch (error) {
    ElMessage.error('重启失败')
  } finally {
    loading.value = false
  }
}

async function handleTestConfig() {
  loading.value = true
  testResult.value = null
  try {
    const response = await serversApi.testConfig(serverId)
    testResult.value = response.data
  } catch (error) {
    ElMessage.error('测试配置失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchServer()
  fetchStatus()
})
</script>

<style scoped>
.control-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.test-result {
  margin-top: 16px;
}
</style>