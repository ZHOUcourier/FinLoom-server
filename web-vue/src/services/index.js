/**
 * API服务统一导出
 */

import { authApi } from './modules/auth'
import { healthApi } from './modules/health'
import { chatApi } from './modules/chat'
import { strategyApi } from './modules/strategy'
import { marketApi } from './modules/market'
import { dashboardApi } from './modules/dashboard'
import { portfolioApi } from './modules/portfolio'
import { tradesApi } from './modules/trades'
import { backtestApi } from './modules/backtest'
import { dataApi } from './modules/data'
import { userApi } from './modules/user'
import { adminApi } from './modules/admin'
import apiClient from './client'

// 统一导出API对象（兼容旧版本）
export const api = {
  auth: authApi,
  health: healthApi,
  chat: chatApi,
  strategy: strategyApi,
  market: marketApi,
  dashboard: dashboardApi,
  portfolio: portfolioApi,
  trades: tradesApi,
  backtest: backtestApi,
  data: dataApi,
  user: userApi,
  admin: adminApi,
  
  // 兼容旧版本的analyze接口
  analyze: (params) => apiClient.post('/v1/analyze', params)
}

// 导出各个模块（供按需引入）
export {
  authApi,
  healthApi,
  chatApi,
  strategyApi,
  marketApi,
  dashboardApi,
  portfolioApi,
  tradesApi,
  backtestApi,
  dataApi,
  userApi,
  adminApi
}

// 导出axios实例
export { default as apiClient } from './client'

// 默认导出
export default api

