import api from './index'

export interface Server {
  id: number
  name: string
  host: string
  port: number
  username: string
  password?: string
  ssh_key_path?: string
  nginx_path: string
  nginx_conf_path: string
  nginx_log_path: string
  mode: 'local' | 'remote'
  status: string
  created_at: string
  updated_at: string
}

export interface ConfigFile {
  file_path: string
  file_name: string
  is_directory: boolean
  content?: string
}

export interface NginxStatus {
  running: boolean
  pid?: number
  version?: string
}

export const serversApi = {
  // Server CRUD
  getServers: () => api.get<Server[]>('/servers'),
  getServer: (id: number) => api.get<Server>(`/servers/${id}`),
  createServer: (data: Partial<Server>) => api.post<Server>('/servers', data),
  updateServer: (id: number, data: Partial<Server>) => api.put<Server>(`/servers/${id}`, data),
  deleteServer: (id: number) => api.delete(`/servers/${id}`),
  testConnection: (id: number) => api.post(`/servers/${id}/test-connection`),
  
  // Config management
  getConfigFiles: (id: number, path: string = '') => 
    api.get<ConfigFile[]>(`/servers/${id}/config/files`, { params: { path } }),
  getConfigContent: (id: number, filePath: string) => 
    api.get<{ content: string; file_path: string }>(`/servers/${id}/config/files/${filePath}`),
  saveConfigContent: (id: number, filePath: string, content: string, autoBackup: boolean = true) => 
    api.put(`/servers/${id}/config/files/${filePath}`, { content, autoBackup }),
  testConfig: (id: number) => api.post(`/servers/${id}/config/test`),
  
  // Logs
  getLogFiles: (id: number) => api.get(`/servers/${id}/logs`),
  getLogContent: (id: number, logPath: string, lines: number = 100) => 
    api.get(`/servers/${id}/logs/${logPath}`, { params: { lines } }),
  
  // Nginx control
  getNginxStatus: (id: number) => api.get<NginxStatus>(`/servers/${id}/nginx/status`),
  reloadNginx: (id: number) => api.post(`/servers/${id}/nginx/reload`),
  restartNginx: (id: number) => api.post(`/servers/${id}/nginx/restart`),
  startNginx: (id: number) => api.post(`/servers/${id}/nginx/start`),
  stopNginx: (id: number) => api.post(`/servers/${id}/nginx/stop`)
}