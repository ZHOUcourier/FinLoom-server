/**
 * 策略相关API服务
 */

import apiClient from '../client'

export const strategyApi = {
  /**
   * 生成策略
   */
  generate: (requirements) =>
    apiClient.post('/v1/strategy/generate', { requirements }),

  /**
   * 启动智能策略工作流
   */
  startWorkflow: (payload) =>
    apiClient.post('/v1/strategy/workflow/start', payload),

  /**
   * 查询策略工作流状态
   */
  getWorkflowStatus: (jobId) =>
    apiClient.get(`/v1/strategy/workflow/${jobId}/status`),

  /**
   * 获取策略工作流结果
   */
  getWorkflowResult: (jobId) =>
    apiClient.get(`/v1/strategy/workflow/${jobId}/result`),
  
  /**
   * 保存策略
   */
  save: (strategyData) =>
    apiClient.post('/v1/strategy/save', strategyData),
  
  /**
   * 获取策略列表
   */
  list: (statusFilter = null, limit = 100, offset = 0) =>
    apiClient.get('/v1/strategy/list', { 
      params: { 
        status_filter: statusFilter, 
        limit, 
        offset 
      } 
    }),
  
  /**
   * 获取策略详情
   */
  get: (strategyId) =>
    apiClient.get(`/v1/strategy/${strategyId}`),
  
  /**
   * 删除策略
   */
  delete: (strategyId) =>
    apiClient.delete(`/v1/strategy/${strategyId}`),
  
  /**
   * 复制策略
   */
  duplicate: (strategyId, name) =>
    apiClient.post(`/v1/strategy/${strategyId}/duplicate`, { name }),
  
  /**
   * 优化策略
   */
  optimize: (parameters, symbols = ['000001']) =>
    apiClient.post('/v1/strategy/optimize', { parameters, symbols }),
  
  /**
   * 回测策略
   */
  backtest: (strategyId, params) =>
    apiClient.post(`/v1/strategy/${strategyId}/backtest`, params),
  
  /**
   * 启动手动回测
   */
  startBacktest: (request) =>
    apiClient.post('/v1/strategy/backtest/start', request),
  
  /**
   * 策略模板
   */
  templates: {
    /**
     * 获取模板列表
     */
    list: () =>
      apiClient.get('/v1/strategy/templates'),
    
    /**
     * 获取模板详情
     */
    get: (templateId) =>
      apiClient.get(`/v1/strategy/templates/${templateId}`),
    
    /**
     * 从模板创建策略
     */
    createFrom: (templateId, name, parameters = {}) =>
      apiClient.post(`/v1/strategy/from-template/${templateId}`, { name, parameters })
  },

  /**
   * 实盘交易管理
   */
  live: {
    /**
     * 激活策略到实盘
     */
    activate: (strategyId, config) =>
      apiClient.post('/v1/strategy/live/activate', {
        strategyId,
        initialCapital: config.initialCapital || 100000,
        maxPositionPerStock: config.maxPositionPerStock || 0.2,
        maxTotalPosition: config.maxTotalPosition || 0.8,
        maxDailyLoss: config.maxDailyLoss || 0.05,
        maxDrawdown: config.maxDrawdown || 0.15,
        stopLoss: config.stopLoss || 0.1,
        takeProfit: config.takeProfit || 0.2,
        riskLevel: config.riskLevel || 'medium',
        notificationChannels: config.notificationChannels || ['email']
      }),
    
    /**
     * 暂停策略
     */
    pause: (strategyId) =>
      apiClient.post(`/v1/strategy/live/${strategyId}/pause`),
    
    /**
     * 恢复策略
     */
    resume: (strategyId) =>
      apiClient.post(`/v1/strategy/live/${strategyId}/resume`),
    
    /**
     * 停止策略
     */
    stop: (strategyId) =>
      apiClient.post(`/v1/strategy/live/${strategyId}/stop`),
    
    /**
     * 获取策略实盘状态
     */
    getStatus: (strategyId) =>
      apiClient.get(`/v1/strategy/live/${strategyId}/status`),
    
    /**
     * 获取所有活跃策略
     */
    listActive: () =>
      apiClient.get('/v1/strategy/live/active'),
    
    /**
     * 手动触发每日任务
     */
    runDaily: () =>
      apiClient.post('/v1/strategy/live/run-daily')
  }
}

