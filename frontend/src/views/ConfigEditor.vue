<template>
  <div class="config-editor">
    <el-page-header @back="$router.back()" content="配置管理">
      <template #extra>
        <el-button type="primary" @click="handleSave" :loading="saving">
          <el-icon><DocumentChecked /></el-icon>
          保存
        </el-button>
        <el-button @click="handleTest">
          <el-icon><Check /></el-icon>
          测试配置
        </el-button>
        <el-button @click="handleReload">
          <el-icon><Refresh /></el-icon>
          重载配置
        </el-button>
      </template>
    </el-page-header>

    <!-- Breadcrumb navigation -->
    <div class="breadcrumb-nav">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :clickable="currentPath !== ''" @click="goToRoot">
          <el-icon><HomeFilled /></el-icon>
          根目录
        </el-breadcrumb-item>
        <el-breadcrumb-item v-for="(crumb, index) in breadcrumbs" :key="index">
          <span
            :class="{ 'crumb-clickable': index < breadcrumbs.length - 1 }"
            @click="goToBreadcrumb(index)"
          >
            {{ crumb }}
          </span>
        </el-breadcrumb-item>
      </el-breadcrumb>
      <el-button
        v-if="currentPath !== ''"
        size="small"
        @click="goToParent"
        style="margin-left: 12px;"
      >
        <el-icon><ArrowLeft /></el-icon>
        返回上级
      </el-button>
    </div>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- File Tree -->
      <el-col :span="4">
        <el-card class="file-tree-card">
          <template #header>
            <span>配置文件</span>
          </template>
          <el-tree
            :data="configFiles"
            :props="treeProps"
            @node-click="handleNodeClick"
            highlight-current
            default-expand-all
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.is_directory"><Folder /></el-icon>
                <el-icon v-else><Document /></el-icon>
                <span>{{ data.file_name }}</span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>
      
      <!-- Editor -->
      <el-col :span="20">
        <el-card class="editor-card">
          <template #header>
            <div class="editor-header">
              <span>{{ currentFile || '请选择配置文件' }}</span>
              <el-tag v-if="hasChanges" type="warning" size="small">已修改</el-tag>
            </div>
          </template>
          <div class="editor-container">
            <textarea
              v-model="content"
              class="config-textarea"
              spellcheck="false"
              @input="handleContentChange"
            ></textarea>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Test Result Dialog -->
    <el-dialog v-model="showTestResult" title="配置测试结果" width="500px">
      <el-alert :type="testResult?.success ? 'success' : 'error'" :title="testResult?.output" show-icon />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { serversApi, ConfigFile } from '@/api/servers'
import { useDebounceFn } from '@vueuse/core'

const route = useRoute()
const serverId = Number(route.params.id)

const loading = ref(false)
const saving = ref(false)
const configFiles = ref<ConfigFile[]>([])
const currentFile = ref('')
const content = ref('')
const originalContent = ref('')
const hasChanges = ref(false)
const showTestResult = ref(false)
const testResult = ref<{ success: boolean; output: string } | null>(null)
const currentPath = ref('')

// Computed breadcrumbs based on current path
const breadcrumbs = computed(() => {
  if (!currentPath.value) return []
  return currentPath.value.split('/').filter(p => p)
})

const treeProps = {
  children: 'children',
  label: 'file_name'
}

async function fetchConfigFiles(path: string = '') {
  loading.value = true
  try {
    const response = await serversApi.getConfigFiles(serverId, path)
    configFiles.value = response.data
  } catch (error) {
    ElMessage.error('获取配置文件列表失败')
  } finally {
    loading.value = false
  }
}

async function handleNodeClick(data: ConfigFile) {
  if (data.is_directory) {
    // Fetch subdirectory contents - store the path relative to nginx conf path
    const relativePath = data.file_path.replace(server.nginx_conf_path + '/', '').replace(server.nginx_conf_path, '')
    currentPath.value = relativePath.replace(/^\//, '')
    await fetchConfigFiles(currentPath.value)
    return
  }

  // Load file content
  currentFile.value = data.file_path
  try {
    const response = await serversApi.getConfigContent(serverId, data.file_path)
    content.value = response.data.content
    originalContent.value = response.data.content
    hasChanges.value = false
  } catch (error) {
    ElMessage.error('读取配置文件失败')
  }
}

// Go to root directory
function goToRoot() {
  currentPath.value = ''
  fetchConfigFiles('')
}

// Go to parent directory
function goToParent() {
  if (!currentPath.value) return
  const parts = currentPath.value.split('/')
  parts.pop()
  currentPath.value = parts.join('/')
  fetchConfigFiles(currentPath.value)
}

// Go to specific breadcrumb
function goToBreadcrumb(index: number) {
  const parts = currentPath.value.split('/')
  currentPath.value = parts.slice(0, index + 1).join('/')
  fetchConfigFiles(currentPath.value)
}

// Get nginx conf path from server (to be set on mount)
const server = ref({
  nginx_conf_path: '/etc/nginx'
})

const handleContentChange = useDebounceFn(() => {
  hasChanges.value = content.value !== originalContent.value
}, 500)

async function handleSave() {
  if (!currentFile.value) {
    ElMessage.warning('请先选择配置文件')
    return
  }
  
  saving.value = true
  try {
    await serversApi.saveConfigContent(serverId, currentFile.value, content.value)
    ElMessage.success('保存成功')
    originalContent.value = content.value
    hasChanges.value = false
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleTest() {
  try {
    const response = await serversApi.testConfig(serverId)
    testResult.value = response.data
    showTestResult.value = true
  } catch (error) {
    ElMessage.error('测试配置失败')
  }
}

async function handleReload() {
  try {
    const response = await serversApi.reloadNginx(serverId)
    if (response.data.success) {
      ElMessage.success('配置已重载')
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    ElMessage.error('重载失败')
  }
}

onMounted(async () => {
  // Get server info to know nginx_conf_path
  try {
    const response = await serversApi.getServer(serverId)
    server.value = response.data
  } catch (error) {
    console.error('Failed to get server info:', error)
  }
  fetchConfigFiles()
})
</script>

<style scoped>
.breadcrumb-nav {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-radius: 4px;
  margin-top: 16px;
}

.crumb-clickable {
  cursor: pointer;
  color: #409EFF;
}

.crumb-clickable:hover {
  text-decoration: underline;
}

.file-tree-card {
  height: calc(100vh - 180px);
  overflow: auto;
}

.editor-card {
  height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor-container {
  flex: 1;
  min-height: 400px;
}

.config-textarea {
  width: 100%;
  height: 100%;
  min-height: 400px;
  padding: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  border: none;
  resize: none;
  background: #1e1e1e;
  color: #d4d4d4;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>