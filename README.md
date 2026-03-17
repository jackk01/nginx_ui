# NGINX UI

一个基于 Web 的 NGINX 可视化管理平台，提供简洁高效的 NGINX 配置管理和监控能力。

## 功能特性

- 📊 **服务器管理** - 支持本地和远程 NGINX 服务器管理
- 📝 **配置编辑** - 在线配置预览与编辑，支持语法高亮和自动补全
- 🔄 **服务控制** - 配置检测与热加载（reload/restart）
- 📜 **日志查看** - 实时日志 tail 查看，支持搜索和下载
- 💾 **配置备份** - 支持版本备份和恢复

## 技术栈

### 后端
- Python 3.10+
- FastAPI 0.104+
- SQLAlchemy 2.0+ (SQLite)
- Pydantic 2.0+

### 前端
- Vue 3.4+
- TypeScript 5.0+
- Element Plus 2.5+
- Monaco Editor

## 快速开始

### Docker 部署（推荐）

```bash
# 1. 克隆项目后，进入项目目录
cd nginx_ui

# 2. 启动 Docker 容器
docker-compose up -d

# 3. 访问服务
# 前端: http://localhost
# 后端 API: http://localhost:8000
```

### 本地开发启动

#### 前置条件

- Python 3.10+
- Node.js 18+
- npm 或 yarn

#### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建数据目录
mkdir -p data

# 5. 启动后端服务
python -m app.main
# 或
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install
# 或
yarn install

# 3. 启动开发服务器
npm run dev
# 或
yarn dev

# 4. 访问 http://localhost:5173
```

## 初始账号

首次启动后，系统会自动创建默认管理员账户：

| 属性 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `admin123` |

> ⚠️ **安全建议**：首次登录后请及时修改默认密码！

## 配置说明

### 环境变量

后端支持以下环境变量：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/nginx_ui.db` | 数据库连接地址 |
| `SECRET_KEY` | `nginx-ui-secret-key-change-in-production` | JWT 密钥 |
| `DEBUG` | `true` | 调试模式 |
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8000` | 服务监听端口 |

### 目录结构

```
nginx_ui/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # Pydantic 模型
│   │   ├── services/     # 业务逻辑
│   │   └── main.py       # 应用入口
│   ├── tests/            # 单元测试
│   ├── requirements.txt  # Python 依赖
│   └── Dockerfile        # Docker 配置
├── frontend/
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── stores/       # 状态管理
│   │   ├── api/          # API 调用
│   │   └── ...
│   ├── package.json      # Node 依赖
│   └── Dockerfile        # Docker 配置
├── data/                 # 数据目录（SQLite 数据库）
├── docker-compose.yml    # Docker Compose 配置
└── README.md             # 项目文档
```

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 主要 API 端点

#### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/register` | 用户注册 |
| GET | `/api/auth/me` | 获取当前用户 |
| POST | `/api/auth/logout` | 用户登出 |

#### 服务器管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/servers` | 获取服务器列表 |
| POST | `/api/servers` | 添加服务器 |
| GET | `/api/servers/{id}` | 获取服务器详情 |
| PUT | `/api/servers/{id}` | 更新服务器 |
| DELETE | `/api/servers/{id}` | 删除服务器 |

## 单元测试

```bash
# 进入后端目录
cd backend

# 安装测试依赖
pip install -r requirements.txt

# 运行测试
pytest

# 运行测试并查看覆盖率
pytest --cov=app --cov-report=term-missing
```

## 故障排除

### 数据库权限问题

```bash
# 确保数据目录存在且有写权限
mkdir -p data
chmod 755 data
```

### 端口占用

如果端口 8000 或 80 被占用，可以修改 `docker-compose.yml` 中的端口映射，或使用环境变量指定自定义端口。

### 前端无法连接后端

检查前端 `vite.config.ts` 中的代理配置，确保 API 请求转发到正确的后端地址。

## 许可证

MIT License