/**
 * 市场分析相关API服务
 */

import apiClient from '../client'

export const marketApi = {
  /**
   * 获取市场概览（包含指数和热门股票）
   * 设置15秒超时，避免长时间阻塞
   */
  getOverview: () => apiClient.get('/v1/market/overview', { timeout: 15000 }),
  
  /**
   * 获取市场指数（专门为OverviewView优化）
   * 设置12秒超时（后端有10秒超时+2秒缓冲）
   */
  getIndices: () => apiClient.get('/v1/market/indices', { timeout: 12000 }),
  
  /**
   * 获取热门股票（专门为MarketView优化）
   * 设置15秒超时（热门股票可能需要更多时间）
   */
  getHotStocks: () => apiClient.get('/v1/market/hot-stocks', { timeout: 15000 }),
  
  /**
   * 获取板块分析数据
   * 设置10秒超时
   */
  getSectorAnalysis: () => apiClient.get('/v1/market/sector-analysis', { timeout: 10000 }),
  
  /**
   * 获取市场情绪数据
   * 设置10秒超时
   */
  getMarketSentiment: () => apiClient.get('/v1/market/market-sentiment', { timeout: 10000 }),
  
  /**
   * 获取技术指标数据
   * 设置10秒超时
   */
  getTechnicalIndicators: () => apiClient.get('/v1/market/technical-indicators', { timeout: 10000 }),
  
  /**
   * 获取市场资讯
   * @param {number} limit - 获取资讯的数量限制
   * 设置10秒超时
   */
  getMarketNews: (limit = 10) => apiClient.get('/v1/market/market-news', { 
    params: { limit },
    timeout: 10000 
  }),
  
  /**
   * 市场分析子模块
   */
  analysis: {
    /**
     * 异常检测
     */
    detectAnomaly: (params) => 
      apiClient.post('/v1/analysis/anomaly/detect', params),
    
    /**
     * 相关性分析
     */
    analyzeCorrelation: (params) =>
      apiClient.post('/v1/analysis/correlation/analyze', params),
    
    /**
     * 市场状态检测
     */
    detectRegime: (params) =>
      apiClient.post('/v1/analysis/regime/detect', params),
    
    /**
     * 情绪分析
     */
    analyzeSentiment: (params) =>
      apiClient.post('/v1/analysis/sentiment/analyze', params),
    
    /**
     * 聚合情绪分析
     */
    aggregateSentiment: (params) =>
      apiClient.post('/v1/analysis/sentiment/aggregate', params)
  }
}

