/**
 * 健康检查相关API服务
 */

import axios from 'axios'
import apiClient from '../client'

export const healthApi = {
  /**
   * 基础健康检查
   */
  check: () => axios.get('/health'),
  
  /**
   * 就绪检查
   */
  ready: () => apiClient.get('/v1/ready')
}

