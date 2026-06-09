# 摄影工作室修图片单流转与客户选片锁定系统

基于 Python + Litestar + SQLAlchemy + MySQL + SvelteKit + TypeScript 构建的摄影工作室管理系统。

## 功能特性

### 核心功能
- **用户登录与权限管理**：管理员、摄影师、修图师、客户四种角色
- **拍摄订单管理**：创建、查询、更新、删除订单
- **原片批次导入**：按片单管理照片批次
- **初修片分发**：分配修图师，追踪修图进度
- **客户在线选片**：创建选片记录、编辑、最终确认
- **加修请求**：多版本管理，历史记录不可覆盖
- **定稿锁片**：锁定后禁止修改已确认片单
- **交付版本追踪**：受保护版本不可覆盖删除

### 系统约束
- 同一订单锁片后不能再次修改已确认片单
- 客户入选数量不能超过可选总数
- 选片截止后未确认的片单自动标记为待人工跟进
- 加修请求提交后至少保留一版历史记录不可覆盖
- 最终确认时间不能早于首次选片时间

### 数据看板
- 修图师负载统计
- 订单选片进度追踪
- 延期未锁片订单预警

## 技术栈

### 后端
- **Python 3.11+**
- **Litestar 2.x** - Web 框架
- **SQLAlchemy 2.x** - ORM
- **MySQL 8.x** - 数据库
- **PyMySQL** - MySQL 驱动
- **Pydantic v2** - 数据验证
- **python-jose** - JWT 认证
- **passlib + bcrypt** - 密码哈希

### 前端
- **SvelteKit 2.x** - 前端框架
- **TypeScript** - 类型系统
- **Tailwind CSS 3** - UI 样式
- **Axios** - HTTP 客户端
- **Lucide Svelte** - 图标库
- **Day.js** - 日期处理

## 项目结构

```
.
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── core/               # 核心模块
│   │   │   ├── config.py       # 配置
│   │   │   ├── database.py     # 数据库
│   │   │   ├── security.py     # 安全认证
│   │   │   └── dependencies.py # 依赖注入
│   │   ├── models/             # 数据模型
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── routers/            # API 路由
│   │   └── main.py             # 应用入口
│   ├── scripts/
│   │   └── init_db.py          # 数据库初始化
│   └── requirements.txt        # Python 依赖
└── frontend/                   # 前端项目
    ├── src/
    │   ├── routes/             # 页面路由
    │   ├── lib/
    │   │   ├── api/            # API 调用
    │   │   ├── types/          # TypeScript 类型
    │   │   └── utils/          # 工具函数
    │   ├── app.html            # HTML 模板
    │   ├── app.css             # 全局样式
    │   └── app.d.ts            # 类型声明
    ├── package.json
    ├── svelte.config.js
    ├── tailwind.config.js
    ├── tsconfig.json
    └── vite.config.ts
```

## 快速开始

### 1. 准备数据库

创建 MySQL 数据库：

```sql
CREATE DATABASE photo_studio CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 `backend/app/core/config.py` 中的数据库连接信息，或设置环境变量。

### 2. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（创建表结构和默认账号）
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端 API 文档地址：http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务
npm run dev
```

前端访问地址：http://localhost:5173

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| photographer | 123456 | 摄影师 |
| retoucher | 123456 | 修图师 |
| customer | 123456 | 客户 |

## API 接口

### 认证
- `POST /api/auth/login` - 登录
- `POST /api/auth/register` - 注册
- `GET /api/auth/me` - 获取当前用户

### 用户管理
- `GET /api/users/` - 用户列表
- `GET /api/users/{id}` - 用户详情
- `POST /api/users/` - 创建用户
- `PUT /api/users/{id}` - 更新用户
- `DELETE /api/users/{id}` - 删除/禁用用户

### 订单管理
- `GET /api/orders/` - 订单列表
- `GET /api/orders/{id}` - 订单详情
- `POST /api/orders/` - 创建订单
- `PUT /api/orders/{id}` - 更新订单
- `DELETE /api/orders/{id}` - 删除订单

### 片单管理
- `GET /api/photo-sheets/` - 片单列表
- `GET /api/photo-sheets/{id}` - 片单详情
- `POST /api/photo-sheets/` - 创建片单
- `PUT /api/photo-sheets/{id}` - 更新片单
- `POST /api/photo-sheets/{id}/lock` - 锁定片单
- `DELETE /api/photo-sheets/{id}` - 删除片单

### 批次管理
- `GET /api/batches/` - 批次列表
- `GET /api/batches/{id}` - 批次详情
- `POST /api/batches/` - 导入批次
- `PUT /api/batches/{id}` - 更新批次
- `DELETE /api/batches/{id}` - 删除批次

### 选片管理
- `GET /api/selections/` - 选片记录列表
- `GET /api/selections/{id}` - 选片记录详情
- `POST /api/selections/` - 创建选片记录
- `PUT /api/selections/{id}` - 更新选片记录
- `POST /api/selections/{id}/confirm` - 最终确认选片

### 加修请求
- `GET /api/retouch/` - 加修请求列表
- `GET /api/retouch/{id}` - 加修请求详情
- `POST /api/retouch/` - 创建加修请求
- `PUT /api/retouch/{id}` - 更新加修请求
- `POST /api/retouch/{id}/new-version` - 创建新版本

### 交付版本
- `GET /api/delivery/` - 交付版本列表
- `GET /api/delivery/{id}` - 交付版本详情
- `POST /api/delivery/` - 创建交付版本
- `PUT /api/delivery/{id}` - 更新交付版本
- `DELETE /api/delivery/{id}` - 删除交付版本

### 数据看板
- `GET /api/dashboard/stats` - 综合统计
- `GET /api/dashboard/retouchers-workload` - 修图师负载
- `GET /api/dashboard/selection-progress` - 选片进度
- `GET /api/dashboard/overdue-sheets` - 延期片单
