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