<template>
  <div class="log-viewer">
    <el-page-header @back="$router.back()" content="日志查看">
      <template #extra>
        <el-button @click="toggleAutoRefresh" :type="autoRefresh ? 'success' : 'default'">
          <el-icon><Clock /></el-icon>
          {{ autoRefresh ? '实时刷新中' : '自动刷新' }}
        </el-button>
        <el-button @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </template>
    </el-page-header>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- Log Files List -->
      <el-col :span="4">
        <el-card class="log-list-card">
          <template #header>
            <span>日志文件</span>
          </template>
          <el-list>
            <el-list-item
              v-for="file in logFiles"
              :key="file.file_path"
              :class="{ active: currentLog === file.file_path }"
              @click="selectLog(file.file_path)"
            >
              <el-icon><Document /></el-icon>
              <span>{{ file.file_name }}</span>
              <el-tag size="small" style="margin-left: 8px;">
                {{ formatSize(file.size) }}
              </el-tag>
            </el-list-item>
          </el-list>
        </el-card>
      </el-col>
      
      <!-- Log Content -->
      <el-col :span="20">
        <el-card class="log-content-card">
          <template #header>
            <div class="log-header">
              <span>{{ currentLog || '请选择日志文件' }}</span>
              <div class="log-actions">
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索..."
                  style="width: 200px; margin-right: 12px;"
                  clearable
                  @input="handleSearch"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                <el-button @click="handleClear">清空</el-button>
              </div>
            </div>
          </template>
          <div class="log-content" ref="logContainer">
            <pre>{{ logContent }}</pre>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { serversApi } from '@/api/servers'

const route = useRoute()
const serverId = Number(route.params.id)

const loading = ref(false)
const logFiles = ref<any[]>([])
const currentLog = ref('')
const logContent = ref('')
const originalContent = ref('')
const searchKeyword = ref('')
const autoRefresh = ref(false)
const logContainer = ref<HTMLElement>()

let refreshInterval: ReturnType<typeof setInterval> | null = null

async function fetchLogFiles() {
  try {
    const response = await serversApi.getLogFiles(serverId)
    logFiles.value = response.data
  } catch (error) {
    ElMessage.error('获取日志文件列表失败')
  }
}

async function selectLog(filePath: string) {
  currentLog.value = filePath
  await fetchLogContent()
}

async function fetchLogContent() {
  if (!currentLog.value) return
  
  loading.value = true
  try {
    const response = await serversApi.getLogContent(serverId, currentLog.value, 200)
    logContent.value = response.data.content
    originalContent.value = response.data.content
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('获取日志内容失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  if (!searchKeyword.value) {
    logContent.value = originalContent.value
    return
  }
  
  // Simple search - highlight matching lines
  const lines = originalContent.value.split('\n')
  const matched = lines.filter(line => 
    line.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
  logContent.value = matched.join('\n')
}

function handleRefresh() {
  fetchLogContent()
}

function handleClear() {
  logContent.value = ''
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  
  if (autoRefresh.value) {
    refreshInterval = setInterval(fetchLogContent, 3000)
  } else if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(() => {
  fetchLogFiles()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.log-list-card {
  height: calc(100vh - 180px);
  overflow: auto;
}

.log-list-item {
  cursor: pointer;
  padding: 8px 12px;
}

.log-list-item.active {
  background: #ecf5ff;
  color: #409EFF;
}

.log-content-card {
  height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-actions {
  display: flex;
  align-items: center;
}

.log-content {
  flex: 1;
  overflow: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-content pre {
  margin: 0;
}
</style>