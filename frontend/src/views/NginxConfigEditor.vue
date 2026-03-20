<template>
  <div class="config-editor">
    <el-page-header title="" @back="$router.back()" content="配置管理">
      <template #extra>
        <el-button @click="handleFormat" :disabled="!currentFile">
          <el-icon><MagicStick /></el-icon>
          格式化
        </el-button>
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
      <el-col :span="4">
        <el-card class="file-tree-card" v-loading="loading">
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
            <template #default="{ data }">
              <span class="tree-node">
                <el-icon v-if="data.is_directory"><Folder /></el-icon>
                <el-icon v-else><Document /></el-icon>
                <span>{{ data.file_name }}</span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <el-col :span="20">
        <el-card class="editor-card">
          <template #header>
            <div class="editor-header">
              <span>{{ currentFile || '请选择配置文件' }}</span>
              <el-tag v-if="hasChanges" type="warning" size="small">已修改</el-tag>
            </div>
          </template>
          <div class="editor-container">
            <div ref="editorContainer" class="monaco-editor-container"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showTestResult" title="配置测试结果" width="500px">
      <el-alert :type="testResult?.success ? 'success' : 'error'" :title="testResult?.output" show-icon />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useDebounceFn } from '@vueuse/core'
import * as monaco from 'monaco-editor/esm/vs/editor/editor.api'
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import { serversApi, type ConfigFile } from '@/api/servers'

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
const editorContainer = ref<HTMLElement | null>(null)

let editor: monaco.editor.IStandaloneCodeEditor | null = null
let syncingEditorValue = false

const breadcrumbs = computed(() => {
  if (!currentPath.value) return []
  return currentPath.value.split('/').filter((p) => p)
})

const treeProps = {
  children: 'children',
  label: 'file_name'
}

function ensureNginxLanguage() {
  const exists = monaco.languages.getLanguages().some((lang) => lang.id === 'nginx')
  if (exists) return

  monaco.languages.register({ id: 'nginx' })

  monaco.languages.setMonarchTokensProvider('nginx', {
    defaultToken: '',
    tokenPostfix: '.nginx',
    keywords: [
      'server', 'location', 'http', 'events', 'upstream', 'map', 'stream', 'geo', 'types',
      'if', 'set', 'return', 'rewrite', 'try_files', 'proxy_pass', 'include', 'listen',
      'server_name', 'root', 'index', 'error_page', 'access_log', 'error_log', 'ssl',
      'ssl_certificate', 'ssl_certificate_key', 'proxy_set_header', 'proxy_read_timeout'
    ],
    tokenizer: {
      root: [
        [/\s+/, ''],
        [/#.*$/, 'comment'],
        [/"([^"\\]|\\.)*"/, 'string'],
        [/'([^'\\]|\\.)*'/, 'string'],
        [/[{}]/, '@brackets'],
        [/;/, 'delimiter'],
        [/\b\d+\b/, 'number'],
        [/\$[\w_]+/, 'variable'],
        [/\b[a-zA-Z_][\w-]*\b/, {
          cases: {
            '@keywords': 'keyword',
            '@default': 'identifier'
          }
        }],
        [/./, '']
      ]
    }
  })

  monaco.languages.setLanguageConfiguration('nginx', {
    comments: { lineComment: '#' },
    brackets: [
      ['{', '}']
    ],
    autoClosingPairs: [
      { open: '{', close: '}' },
      { open: '"', close: '"' },
      { open: "'", close: "'" }
    ],
    surroundingPairs: [
      { open: '{', close: '}' },
      { open: '"', close: '"' },
      { open: "'", close: "'" }
    ]
  })
}

function initEditor() {
  if (!editorContainer.value) return

  ;(self as any).MonacoEnvironment = {
    getWorker() {
      return new editorWorker()
    }
  }

  ensureNginxLanguage()

  editor = monaco.editor.create(editorContainer.value, {
    value: content.value,
    language: 'nginx',
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: false },
    fontSize: 13,
    lineNumbers: 'on',
    wordWrap: 'on',
    scrollBeyondLastLine: false,
    tabSize: 2,
    insertSpaces: true
  })

  editor.onDidChangeModelContent(() => {
    if (syncingEditorValue || !editor) return
    content.value = editor.getValue()
    handleContentChange()
  })
}

function updateEditorContent(nextValue: string) {
  if (!editor) return
  if (editor.getValue() === nextValue) return

  syncingEditorValue = true
  editor.setValue(nextValue)
  syncingEditorValue = false
}

function formatNginxContent(raw: string): string {
  const lines = raw.replace(/\r\n/g, '\n').split('\n')
  const output: string[] = []
  let indent = 0

  for (const originalLine of lines) {
    const line = originalLine.trim()

    if (line === '') {
      output.push('')
      continue
    }

    const leadingCloseMatch = line.match(/^\}+/)
    const leadingCloseCount = leadingCloseMatch ? leadingCloseMatch[0].length : 0
    const opens = (line.match(/\{/g) || []).length
    const closes = (line.match(/\}/g) || []).length

    const currentIndent = Math.max(indent - leadingCloseCount, 0)
    output.push(`${'  '.repeat(currentIndent)}${line}`)

    indent = currentIndent + opens - (closes - leadingCloseCount)
    if (indent < 0) indent = 0
  }

  return output.join('\n')
}

async function fetchConfigFiles(path: string = '') {
  loading.value = true
  try {
    const response = await serversApi.getConfigFiles(serverId, path)
    configFiles.value = response.data
  } catch {
    ElMessage.error('获取配置文件列表失败')
  } finally {
    loading.value = false
  }
}

async function handleNodeClick(data: ConfigFile) {
  if (data.is_directory) {
    currentPath.value = currentPath.value
      ? `${currentPath.value}/${data.file_name}`
      : data.file_name
    await fetchConfigFiles(currentPath.value)
    return
  }

  currentFile.value = data.file_path
  try {
    const response = await serversApi.getConfigContent(serverId, data.file_path)
    content.value = response.data.content
    originalContent.value = response.data.content
    hasChanges.value = false
    updateEditorContent(content.value)
  } catch {
    ElMessage.error('读取配置文件失败')
  }
}

function goToRoot() {
  currentPath.value = ''
  void fetchConfigFiles('')
}

function goToParent() {
  if (!currentPath.value) return
  const parts = currentPath.value.split('/')
  parts.pop()
  currentPath.value = parts.join('/')
  void fetchConfigFiles(currentPath.value)
}

function goToBreadcrumb(index: number) {
  const parts = currentPath.value.split('/')
  currentPath.value = parts.slice(0, index + 1).join('/')
  void fetchConfigFiles(currentPath.value)
}

const handleContentChange = useDebounceFn(() => {
  hasChanges.value = content.value !== originalContent.value
}, 200)

function handleFormat() {
  if (!currentFile.value) {
    ElMessage.warning('请先选择配置文件')
    return
  }

  const formatted = formatNginxContent(content.value)
  content.value = formatted
  updateEditorContent(formatted)
  handleContentChange()
}

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
  } catch {
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
  } catch {
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
  } catch {
    ElMessage.error('重载失败')
  }
}

function handleResize() {
  editor?.layout()
}

onMounted(() => {
  initEditor()
  void fetchConfigFiles()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  editor?.dispose()
  editor = null
})
</script>

<style scoped>
:deep(.el-page-header__title) {
  display: none;
}

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
  color: #409eff;
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

.monaco-editor-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
