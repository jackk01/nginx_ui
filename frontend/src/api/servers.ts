import api from './index'
import type { Server, ConfigFile, NginxStatus } from './types'

// Re-export types - these are used at compile time and should be stripped at runtime
export type { Server, ConfigFile, NginxStatus } from './types'

export const serversApi = {
  // Server CRUD
  getServers: () => api.get<Server[]>('/servers'),
  getServer: (id: number) => api.get<Server>(`/servers/${id}`),
  createServer: (data: Partial<Server>) => api.post<Server>('/servers', data),
  updateServer: (id: number, data: Partial<Server>) => api.put<Server>(`/servers/${id}`, data),
  deleteServer: (id: number) => api.delete(`/servers/${id}`),
  testConnection: (id: number) => api.post(`/servers/${id}/test-connection`),
  checkServerStatus: (id: number) => api.post<{ status: string; message: string }>(`/servers/${id}/check-status`),
  
  // Config management
  getConfigFiles: (id: number, path: string = '') => 
    api.get<ConfigFile[]>(`/servers/${id}/config/files`, { params: { path } }),
  getConfigContent: (id: number, filePath: string) => {
    // Do NOT remove leading slash - let backend handle path normalization
    // Just encode the path for safe URL transmission
    return api.get<{ content: string; file_path: string }>(`/servers/${id}/config/files/${encodeURIComponent(filePath)}`)
  },
  saveConfigContent: (id: number, filePath: string, content: string, autoBackup: boolean = true) => {
    // Do NOT remove leading slash - let backend handle path normalization
    return api.put(`/servers/${id}/config/files/${encodeURIComponent(filePath)}`, { content, autoBackup })
  },
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