<template>
  <div class="server-config">
    <el-page-header title="" @back="$router.back()" content="服务器配置">
      <template #extra>
        <el-button type="primary" :loading="saving" @click="handleSave">
          <el-icon><DocumentChecked /></el-icon>
          保存配置
        </el-button>
      </template>
    </el-page-header>

    <el-card style="margin-top: 20px; max-width: 760px;">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
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
          <el-input v-model="form.password" type="password" show-password placeholder="留空则保持不变" />
        </el-form-item>

        <el-divider content-position="left">Nginx 基础路径</el-divider>

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
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { serversApi } from '@/api/servers'

const route = useRoute()
const serverId = Number(route.params.id)

const formRef = ref<FormInstance>()
const saving = ref(false)

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

async function fetchServerConfig() {
  try {
    const response = await serversApi.getServer(serverId)
    const server = response.data
    form.name = server.name
    form.host = server.host
    form.port = server.port
    form.username = server.username || ''
    form.password = ''
    form.mode = server.mode
    form.nginx_path = server.nginx_path
    form.nginx_conf_path = server.nginx_conf_path
    form.nginx_log_path = server.nginx_log_path
  } catch (error) {
    ElMessage.error('获取服务器配置失败')
  }
}

async function handleSave() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const payload: Record<string, unknown> = {
        name: form.name,
        mode: form.mode,
        nginx_path: form.nginx_path,
        nginx_conf_path: form.nginx_conf_path,
        nginx_log_path: form.nginx_log_path
      }

      if (form.mode === 'remote') {
        payload.host = form.host
        payload.port = form.port
        payload.username = form.username
        if (form.password.trim()) {
          payload.password = form.password
        }
      } else {
        payload.host = 'localhost'
        payload.port = 22
        payload.username = ''
      }

      await serversApi.updateServer(serverId, payload)
      ElMessage.success('服务器配置已保存')
      form.password = ''
    } catch (error: any) {
      ElMessage.error(error?.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

onMounted(() => {
  fetchServerConfig()
})
</script>

<style scoped>
:deep(.el-page-header__title) {
  display: none;
}
</style>
