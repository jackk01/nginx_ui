<template>
  <div class="log-viewer">
    <el-page-header @back="$router.back()" content="日志查看">
      <template #extra>
        <el-select v-model="logLines" style="width: 120px; margin-right: 12px;" @change="handleLinesChange">
          <el-option label="100行" :value="100" />
          <el-option label="200行" :value="200" />
          <el-option label="500行" :value="500" />
          <el-option label="1000行" :value="1000" />
        </el-select>
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

    <el-row :gutter="20" style="margin-top: 20px; height: calc(100vh - 180px);">
      <!-- Log Files List -->
      <el-col :span="4">
        <el-card class="log-list-card" body-style="padding: 0;">
          <template #header>
            <div class="log-list-header">
              <el-icon><Folder /></el-icon>
              <span>日志文件</span>
              <el-tag size="small" type="info">{{ logFiles.length }}</el-tag>
            </div>
          </template>
          <el-scrollbar>
            <div
              v-for="file in logFiles"
              :key="file.file_path"
              :class="['log-file-item', { active: currentLog === file.file_path }]"
              @click="selectLog(file.file_path)"
            >
              <div class="file-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <span class="file-name">{{ file.file_name }}</span>
              </div>
              <div class="file-meta">
                <el-tag size="small" :type="getSizeType(file.size)">
                  {{ formatSize(file.size) }}
                </el-tag>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>

      <!-- Log Content -->
      <el-col :span="20">
        <el-card class="log-content-card" body-style="padding: 0;">
          <template #header>
            <div class="log-header">
              <div class="log-title">
                <el-icon><Document /></el-icon>
                <span>{{ currentLog || '请选择日志文件' }}</span>
              </div>
              <div class="log-actions">
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索日志..."
                  style="width: 220px; margin-right: 12px;"
                  clearable
                  @input="handleSearch"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                <el-button @click="handleDownload" :disabled="!currentLog">
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
                <el-button @click="handleClear" :disabled="!logContent">
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
              </div>
            </div>
          </template>
          <div class="log-content" ref="logContainer">
            <div v-if="!currentLog" class="log-empty">
              <el-icon size="48"><DocumentAdd /></el-icon>
              <p>请选择左侧日志文件</p>
            </div>
            <pre v-else>{{ logContent }}</pre>
          </div>
          <div v-if="currentLog" class="log-footer">
            <span class="log-stats">
              共 {{ logLines }} 行
              <span v-if="searchKeyword"> | 匹配 {{ matchedLines }} 行</span>
            </span>
            <el-button size="small" text @click="scrollToTop">
              <el-icon><Top /></el-icon>
              顶部
            </el-button>
            <el-button size="small" text @click="scrollToBottom">
              <el-icon><Bottom /></el-icon>
              底部
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
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
const logLines = ref(200)
const matchedLines = ref(0)

let refreshInterval: ReturnType<typeof setInterval> | null = null

// Get matched lines count
const matchedCount = computed(() => {
  if (!searchKeyword.value || !originalContent.value) return 0
  const lines = originalContent.value.split('\n')
  return lines.filter(line =>
    line.toLowerCase().includes(searchKeyword.value.toLowerCase())
  ).length
})

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
    const response = await serversApi.getLogContent(serverId, currentLog.value, logLines.value)
    logContent.value = response.data.content
    originalContent.value = response.data.content
    matchedLines.value = logLines.value
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('获取日志内容失败')
  } finally {
    loading.value = false
  }
}

function handleLinesChange() {
  fetchLogContent()
}

function handleSearch() {
  if (!searchKeyword.value) {
    logContent.value = originalContent.value
    matchedLines.value = logLines.value
    return
  }

  // Simple search - highlight matching lines
  const lines = originalContent.value.split('\n')
  const matched = lines.filter(line =>
    line.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
  logContent.value = matched.join('\n')
  matchedLines.value = matched.length
}

function handleRefresh() {
  fetchLogContent()
}

function handleClear() {
  logContent.value = ''
  ElMessage.success('日志已清空')
}

function handleDownload() {
  if (!currentLog.value || !logContent.value) return
  const blob = new Blob([logContent.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = currentLog.value.split('/').pop() || 'log.txt'
  a.click()
  URL.revokeObjectURL(url)
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

function scrollToTop() {
  if (logContainer.value) {
    logContainer.value.scrollTop = 0
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function getSizeType(bytes: number): string {
  if (bytes < 1024 * 1024) return 'info'
  if (bytes < 10 * 1024 * 1024) return 'warning'
  return 'danger'
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
  height: 100%;
  display: flex;
  flex-direction: column;
}

.log-list-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.log-file-item:hover {
  background: #f5f7fa;
}

.log-file-item.active {
  background: #ecf5ff;
  border-left: 3px solid #409EFF;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.file-icon {
  color: #909399;
  flex-shrink: 0;
}

.file-name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-content-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
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
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-content pre {
  margin: 0;
}

.log-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.log-empty p {
  margin-top: 16px;
}

.log-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f5f7fa;
  border-top: 1px solid #e4e7ed;
}

.log-stats {
  font-size: 12px;
  color: #909399;
}
</style>