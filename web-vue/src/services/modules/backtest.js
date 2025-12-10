/**
 * 回测相关API服务
 */

import apiClient from '../client'

export const backtestApi = {
  /**
   * 运行回测
   */
  run: (params) => apiClient.post('/v1/backtest/run', params)
}

