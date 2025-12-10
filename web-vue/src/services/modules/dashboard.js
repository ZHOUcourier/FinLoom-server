/**
 * 仪表盘相关API服务
 */

import apiClient from '../client'

export const dashboardApi = {
  /**
   * 获取仪表盘指标
   */
  getMetrics: () => apiClient.get('/v1/dashboard/metrics')
}

