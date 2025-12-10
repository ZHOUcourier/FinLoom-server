import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'splash',
      component: () => import('@/views/SplashView.vue'),
      meta: { title: 'FinLoom - 智能量化投资平台' }
    },
    {
      path: '/home',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: 'FinLoom - 首页' }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: 'FinLoom - 登录' }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { 
        title: 'FinLoom - 仪表盘',
        requiresAuth: true
      },
      children: [
        {
          path: '',
          name: 'dashboard-overview',
          component: () => import('@/views/dashboard/OverviewView.vue'),
          meta: { title: '仪表盘概览' }
        },
        {
          path: 'portfolio',
          name: 'dashboard-portfolio',
          component: () => import('@/views/dashboard/PortfolioView.vue'),
          meta: { title: '投资组合' }
        },
        {
          path: 'trades',
          name: 'dashboard-trades',
          component: () => import('@/views/dashboard/TradesView.vue'),
          meta: { title: '交易记录' }
        },
        {
          path: 'backtest',
          name: 'dashboard-backtest',
          component: () => import('@/views/dashboard/BacktestView.vue'),
          meta: { title: '策略回测' }
        },
        {
          path: 'data',
          name: 'dashboard-data',
          component: () => import('@/views/dashboard/DataView.vue'),
          meta: { title: '数据管理' }
        },
        {
          path: 'market',
          name: 'dashboard-market',
          component: () => import('@/views/dashboard/MarketView.vue'),
          meta: { title: '市场分析' }
        },
        {
          path: 'chat',
          name: 'dashboard-chat',
          component: () => import('@/views/dashboard/ChatView.vue'),
          meta: { title: 'AI对话' }
        },
        {
          path: 'admin',
          name: 'dashboard-admin',
          component: () => import('@/views/AdminView.vue'),
          meta: { 
            title: '管理员中心',
            requiresAdmin: true  // 需要管理员权限
          }
        },
        {
          path: 'chat/new',
          name: 'dashboard-chat-new',
          component: () => import('@/views/dashboard/chat/NewChatView.vue'),
          meta: { title: '新对话' }
        },
        {
          path: 'chat/history',
          name: 'dashboard-chat-history',
          component: () => import('@/views/dashboard/chat/HistoryView.vue'),
          meta: { title: '历史记录' }
        },
        {
          path: 'chat/favorites',
          name: 'dashboard-chat-favorites',
          component: () => import('@/views/dashboard/chat/FavoritesView.vue'),
          meta: { title: '收藏对话' }
        },
        {
          path: 'strategy',
          name: 'dashboard-strategy',
          component: () => import('@/views/dashboard/StrategyView.vue'),
          meta: { title: '策略模式' }
        },
        {
          path: 'strategy/create',
          name: 'dashboard-strategy-create',
          component: () => import('@/views/dashboard/strategy/CreateStrategyView.vue'),
          meta: { title: '创建策略' }
        },
        {
          path: 'strategy/library',
          name: 'dashboard-strategy-library',
          component: () => import('@/views/dashboard/strategy/LibraryView.vue'),
          meta: { title: '策略库' }
        },
        {
          path: 'strategy/templates',
          name: 'dashboard-strategy-templates',
          component: () => import('@/views/dashboard/strategy/TemplatesView.vue'),
          meta: { title: '策略模板' }
        },
        {
          path: 'strategy/live',
          name: 'dashboard-strategy-live',
          component: () => import('@/views/dashboard/strategy/LiveTradingView.vue'),
          meta: { title: '实盘运行' }
        },
        {
          path: 'reports',
          name: 'dashboard-reports',
          component: () => import('@/views/dashboard/ReportsView.vue'),
          meta: { title: '报告中心' }
        },
        {
          path: 'notifications',
          name: 'dashboard-notifications',
          component: () => import('@/views/dashboard/NotificationsView.vue'),
          meta: { title: '通知中心' }
        },
        {
          path: 'settings',
          name: 'dashboard-settings',
          component: () => import('@/views/dashboard/SettingsView.vue'),
          meta: { title: '系统设置' }
        },
        {
          path: 'news',
          name: 'news',
          component: () => import('@/views/dashboard/NewsView.vue'),
          meta: { title: '市场资讯' }
        }
      ]
    },
    {
      path: '/test',
      name: 'test',
      component: () => import('@/views/TestView.vue'),
      meta: { title: '测试页面' }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { title: '页面未找到' }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 更新页面标题
  document.title = to.meta.title || 'FinLoom'
  
  console.log('🔀 路由导航:', from.path, '→', to.path)
  
  // 🔒 修改：不再自动登录，即使有token也显示登录界面
  // 用户需要手动点击登录按钮才能进入系统
  // if (to.name === 'login' || to.path === '/login') {
  //   const token = localStorage.getItem('finloom_token')
  //   if (token) {
  //     console.log('✅ 已登录，重定向到dashboard')
  //     next({ name: 'dashboard', replace: true })
  //     return
  //   }
  // }
  
  // 认证检查
  if (to.meta.requiresAuth || to.path.startsWith('/dashboard')) {
    const token = localStorage.getItem('finloom_token')
    
    // 检查token是否存在
    if (!token) {
      console.log('❌ 未登录，跳转到登录页')
      next({ name: 'login', query: { redirect: to.fullPath } })
      return
    }
    
    // 验证token有效性（带超时保护）
    try {
      const { api } = await import('@/services')
      
      // 添加3秒超时保护，避免验证请求卡住导致无法跳转
      const verifyPromise = api.auth.verify()
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('验证请求超时')), 3000)
      )
      
      const response = await Promise.race([verifyPromise, timeoutPromise])
      
      // 注意：响应拦截器已经提取了data
      if (!response.valid) {
        console.log('❌ Token无效，清除并跳转到登录页')
        localStorage.removeItem('finloom_auth')
        localStorage.removeItem('finloom_token')
        localStorage.removeItem('finloom_user')
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
      }
      
      console.log('✅ Token有效，允许访问')
      
      // 检查管理员权限（带超时保护）
      if (to.meta.requiresAdmin) {
        try {
          const profilePromise = api.auth.getProfile()
          const profileTimeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('获取权限信息超时')), 3000)
          )
          
          const profileResponse = await Promise.race([profilePromise, profileTimeoutPromise])
          const permissionLevel = profileResponse.data?.permission_level || 1
          
          if (permissionLevel < 2) {
            console.log('❌ 需要管理员权限')
            next({ name: 'dashboard', replace: true })
            return
          }
          console.log('✅ 管理员权限验证通过')
        } catch (adminError) {
          console.warn('⚠️ 获取管理员权限信息失败，但允许继续访问:', adminError)
          // 权限验证失败不应阻止页面访问，只是降级处理
        }
      }
    } catch (error) {
      console.error('Token验证失败:', error)
      
      // 只有在明确的401错误或token验证失败时才跳转登录
      // 网络超时等问题不应立即踢出用户
      if (error.message && error.message.includes('401')) {
        console.log('❌ 401错误，跳转登录页')
        localStorage.removeItem('finloom_auth')
        localStorage.removeItem('finloom_token')
        localStorage.removeItem('finloom_user')
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
      }
      
      // 超时或其他网络错误：允许访问但提示用户
      console.warn('⚠️ Token验证超时或网络错误，允许继续访问（将在页面中重试）')
      // 继续导航，让页面内部处理错误
    }
  }
  
  next()
})

export default router

