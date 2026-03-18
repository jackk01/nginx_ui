<template>
  <div class="server-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>服务器列表</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加服务器
          </el-button>
        </div>
      </template>
      
      <el-table :data="servers" v-loading="loading">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="host" label="主机地址" />
        <el-table-column prop="port" label="SSH端口" width="100" />
        <el-table-column prop="mode" label="模式" width="80">
          <template #default="{ row }">
            <el-tag :type="row.mode === 'local' ? 'success' : 'warning'">
              {{ row.mode === 'local' ? '本地' : '远程' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button type="primary" link @click="goToDetail(row.id)">详情</el-button>
            <el-button type="primary" link @click="goToConfig(row.id)">配置</el-button>
            <el-button type="primary" link @click="goToLogs(row.id)">日志</el-button>
            <el-button type="danger" link @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Add Server Dialog -->
    <el-dialog v-model="showAddDialog" title="添加服务器" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="服务器名称" prop="name">
          <el-input v-model="form.name" placeholder="my-nginx-server" />
        </el-form-item>
        <el-form-item label="模式" prop="mode">
          <el-radio-group v-model="form.mode">
            <el-radio label="local">本地</el-radio>
            <el-radio label="remote">远程</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="主机地址" prop="host" v-if="form.mode === 'remote'">
          <el-input v-model="form.host" placeholder="192.168.1.100" />
        </el-form-item>
        <el-form-item label="SSH端口" prop="port" v-if="form.mode === 'remote'">
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="用户名" prop="username" v-if="form.mode === 'remote'">
          <el-input v-model="form.username" placeholder="root" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="form.mode === 'remote'">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="NGINX路径" prop="nginx_path">
          <el-input v-model="form.nginx_path" placeholder="/usr/sbin/nginx" />
        </el-form-item>
        <el-form-item label="配置目录" prop="nginx_conf_path">
          <el-input v-model="form.nginx_conf_path" placeholder="/etc/nginx" />
        </el-form-item>
        <el-form-item label="日志目录" prop="nginx_log_path">
          <el-input v-model="form.nginx_log_path" placeholder="/var/log/nginx" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { serversApi } from '@/api/servers'
import type { Server } from '@/api/servers'

const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const servers = ref<Server[]>([])
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  host: 'localhost',
  port: 22,
  username: '',
  password: '',
  mode: 'local' as 'local' | 'remote',
  nginx_path: '/usr/sbin/nginx',
  nginx_conf_path: '/etc/nginx',
  nginx_log_path: '/var/log/nginx'
})

const rules = {
  name: [{ required: true, message: '请输入服务器名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }]
}

async function fetchServers() {
  loading.value = true
  try {
    const response = await serversApi.getServers()
    servers.value = response.data

    // Check status for each server
    for (const server of servers.value) {
      try {
        const statusResponse = await serversApi.checkServerStatus(server.id)
        server.status = statusResponse.data.status
      } catch (e) {
        // Ignore status check errors
      }
    }
  } catch (error) {
    ElMessage.error('获取服务器列表失败')
  } finally {
    loading.value = false
  }
}

// Auto refresh server status every 30 seconds
let statusInterval: ReturnType<typeof setInterval> | null = null

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await serversApi.createServer(form)
      ElMessage.success('添加成功')
      showAddDialog.value = false
      fetchServers()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '添加失败')
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除这个服务器吗?', '警告', { type: 'warning' })
    await serversApi.deleteServer(id)
    ElMessage.success('删除成功')
    fetchServers()
  } catch (error) {
    // Cancelled
  }
}

function goToDetail(id: number) {
  router.push(`/servers/${id}`)
}

function goToConfig(id: number) {
  router.push(`/servers/${id}/config`)
}

function goToLogs(id: number) {
  router.push(`/servers/${id}/logs`)
}

onMounted(() => {
  fetchServers()
  // Auto refresh server status every 30 seconds
  statusInterval = setInterval(fetchServers, 30000)
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>