# FinLoom Vue3 前端

基于Vue3 + Vite + Pinia的现代化单页应用前端。

## 技术栈

- **Vue 3** - 渐进式JavaScript框架
- **Vite** - 新一代前端构建工具
- **Pinia** - Vue官方状态管理库
- **Vue Router** - 官方路由管理器
- **Axios** - HTTP客户端
- **Chart.js** - 数据可视化
- **Sass** - CSS预处理器
- **vuetify3** - Material3 设计风格

## 项目结构

```
web-vue/
├── src/
│   ├── assets/
│   │   └── styles/
│   │       ├── main.scss          # 全局样式
│   │       └── views/             # 视图专属样式
│   │           └── chat-view.scss # ChatView样式
│   ├── components/
│   │   ├── chat/                  # 聊天组件
│   │   │   ├── ChatSidebar.vue    # 侧边栏
│   │   │   ├── ChatHeader.vue     # 头部
│   │   │   ├── ChatMessages.vue   # 消息列表
│   │   │   ├── ChatInput.vue      # 输入框
│   │   │   └── AISettingsDialog.vue # 设置对话框
│   │   ├── layout/                # 布局组件
│   │   └── ui/                    # UI组件
│   ├── composables/               # 组合式函数
│   │   ├── useChat.js             # 聊天功能
│   │   ├── useConversationActions.js # 对话操作
│   │   ├── useAISettings.js       # AI设置
│   │   └── index.js               # 统一导出
│   ├── constants/                 # 常量配置
│   │   ├── chat.js                # 聊天常量
│   │   └── index.js               # 统一导出
│   ├── layouts/                   # 页面布局
│   ├── router/                    # 路由配置
│   ├── services/                  # API服务（已模块化）
│   │   ├── modules/               # API模块
│   │   │   ├── chat.js            # 聊天API
│   │   │   ├── strategy.js        # 策略API
│   │   │   ├── market.js          # 市场API
│   │   │   ├── dashboard.js       # 仪表盘API
│   │   │   ├── portfolio.js       # 投资组合API
│   │   │   ├── trades.js          # 交易API
│   │   │   ├── backtest.js        # 回测API
│   │   │   ├── data.js            # 数据API
│   │   │   └── health.js          # 健康检查API
│   │   ├── client.js              # Axios客户端
│   │   ├── index.js               # 统一导出
│   │   └── api.js                 # 兼容层
│   ├── stores/                    # Pinia状态管理
│   │   ├── app.js                 # 应用状态（已更新）
│   │   ├── chat.js                # 聊天状态（已更新）
│   │   └── dashboard.js           # 仪表盘状态（已更新）
│   ├── utils/                     # 工具函数
│   │   ├── date.js                # 日期时间工具
│   │   ├── chat.js                # 聊天工具
│   │   ├── clipboard.js           # 剪贴板工具
│   │   └── index.js               # 统一导出
│   ├── views/                     # 页面视图（所有页面已更新API导入）
│   ├── App.vue
│   └── main.js
└── ...
```

> 注：所有文件已完成重构，统一使用 `@/services` 导入API

## 快速开始

### 方式1：使用构建脚本（推荐）

**Linux/Mac:**
```bash
# 在项目根目录执行
./build-vue.sh
python main.py
```

**Windows:**
```bash
build-vue.bat
python main.py
```

访问 http://localhost:8000

### 方式2：手动构建

```bash
# 1. 安装依赖
cd web-vue
npm install

# 2. 构建生产版本
npm run build

# 3. 启动后端
cd ..
python main.py
```

### 方式3：开发模式（前后端分离）

**终端1 - 启动后端:**
```bash
python main.py
```

**终端2 - 启动前端开发服务器:**
```bash
cd web-vue
npm run dev
```

前端访问: http://localhost:5173  
后端访问: http://localhost:8000

开发模式下，API请求会自动代理到后端。

## 功能模块

### 页面路由

- `/` - 启动页
- `/home` - 首页
- `/login` - 登录页
- `/dashboard` - 仪表盘（需要登录）
  - `/dashboard` - 概览
  - `/dashboard/portfolio` - 投资组合
  - `/dashboard/trades` - 交易记录
  - `/dashboard/backtest` - 策略回测
  - `/dashboard/data` - 数据管理
  - `/dashboard/market` - 市场分析
  - `/dashboard/chat` - AI对话
  - `/dashboard/strategy` - 策略模式

### 核心组件

#### 布局组件
- `DashboardLayout` - 仪表盘布局
- `Sidebar` - 侧边栏导航
- `TopNavbar` - 顶部导航栏

#### UI组件
- `Card` - 卡片容器
- `Button` - 按钮
- `StatCard` - 统计卡片
- `LoadingSpinner` - 加载动画

### 状态管理

使用Pinia进行状态管理：

- `useAppStore` - 应用全局状态
- `useDashboardStore` - 仪表盘数据
- `useChatStore` - 聊天对话状态

### API服务

统一的API服务层，支持：

- 自动请求/响应拦截
- 错误处理
- Token管理
- 请求代理（开发模式）

## 开发指南

### 添加新页面

1. 在 `src/views/` 创建新的Vue文件
2. 在 `src/router/index.js` 添加路由配置
3. 如需要，在侧边栏菜单中添加链接

### 添加新API

在 `src/services/modules/` 中创建新的API模块：

```javascript
// src/services/modules/myapi.js
import apiClient from '../client'

export const myApi = {
  getData: () => apiClient.get('/v1/my-endpoint')
}

// src/services/index.js
export { myApi } from './modules/myapi'
```

或直接使用统一的api对象：
```javascript
import { api } from '@/services'
api.chat.send(...)
```

### 使用Store

```vue
<script setup>
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

// 访问状态
console.log(appStore.isReady)

// 调用操作
appStore.checkHealth()
</script>
```

## 样式规范

### 全局变量

在 `src/assets/styles/main.scss` 中定义了CSS变量：

```css
:root {
  --primary: #3b82f6;
  --secondary: #8b5cf6;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  /* ... */
}
```

### 组件样式

使用Scoped CSS和SCSS：

```vue
<style lang="scss" scoped>
.my-component {
  color: var(--primary);
  
  &:hover {
    opacity: 0.8;
  }
}
</style>
```

## 构建配置

### 环境变量

创建 `.env.local` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Vite配置

在 `vite.config.js` 中可配置：

- 路径别名
- 开发服务器
- API代理
- 构建选项

## 常见问题

### 构建失败？
```bash
cd web-vue
rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmmirror.com
npm run build
```

### 访问显示旧版HTML？
确保已构建Vue3前端：
```bash
./build-vue.sh
```

### API请求404？
确保后端运行：
```bash
curl http://localhost:8000/health
```

### npm install慢？
使用国内镜像：
```bash
npm install --registry=https://registry.npmmirror.com
```

