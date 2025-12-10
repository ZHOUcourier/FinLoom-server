/**
 * 投资组合相关API服务
 */

import apiClient from '../client'

export const portfolioApi = {
  /**
   * 获取持仓信息
   */
  getPositions: () => apiClient.get('/v1/portfolio/positions')
}

