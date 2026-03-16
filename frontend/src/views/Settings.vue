<template>
  <div class="settings">
    <el-card>
      <template #header>
        <span>系统设置</span>
      </template>
      
      <el-form label-width="120px">
        <el-form-item label="默认用户名">
          <el-input v-model="settings.username" disabled />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="settings.email" />
        </el-form-item>
        
        <el-form-item label="主题">
          <el-radio-group v-model="settings.theme">
            <el-radio label="light">浅色</el-radio>
            <el-radio label="dark">深色</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="自动保存">
          <el-switch v-model="settings.autoSave" />
        </el-form-item>
        
        <el-form-item label="自动保存间隔">
          <el-input-number v-model="settings.autoSaveInterval" :min="1" :max="60" :disabled="!settings.autoSave" />
          <span style="margin-left: 8px;">秒</span>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>关于</span>
      </template>
      
      <el-descriptions :column="1" border>
        <el-descriptions-item label="版本">1.0.0</el-descriptions-item>
        <el-descriptions-item label="NGINX UI">基于 Web 的 NGINX 配置管理平台</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const settings = reactive({
  username: authStore.user?.username || 'admin',
  email: authStore.user?.email || '',
  theme: 'light',
  autoSave: true,
  autoSaveInterval: 3
})
</script>

<style scoped>
.settings {
  max-width: 800px;
}
</style>