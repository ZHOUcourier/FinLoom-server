/**
 * 交易相关API服务
 */

import apiClient from '../client'

export const tradesApi = {
  /**
   * 获取最近交易记录
   */
  getRecent: () => apiClient.get('/v1/trades/recent')
}

