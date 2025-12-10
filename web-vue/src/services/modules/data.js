/**
 * 数据管理相关API服务
 */

import apiClient from '../client'

export const dataApi = {
  /**
   * 数据采集
   */
  collect: (params) => apiClient.post('/v1/data/collect', params),
  
  /**
   * 获取数据概览
   */
  getOverview: () => apiClient.get('/v1/data/overview')
}

