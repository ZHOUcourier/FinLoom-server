/**
 * 聊天相关API服务
 */

import apiClient from '../client'

export const chatApi = {
  /**
   * 发送聊天消息（增加超时时间适应AI响应）
   */
  send: (message, conversationId = '') => 
    apiClient.post('/chat', { message, conversation_id: conversationId }, {
      timeout: 90000 // AI服务专用超时时间：90秒
    }),
  
  /**
   * 创建新对话
   */
  createConversation: (userId = 'default_user', title = '新对话') =>
    apiClient.post('/v1/chat/conversation', { user_id: userId, title }),
  
  /**
   * 获取对话列表
   */
  getConversations: (userId = 'default_user', limit = 50) =>
    apiClient.get('/v1/chat/conversations', { params: { user_id: userId, limit } }),
  
  /**
   * 获取对话历史
   */
  getHistory: (conversationId) =>
    apiClient.get(`/v1/chat/history/${conversationId}`),
  
  /**
   * 删除对话
   */
  deleteConversation: (conversationId) =>
    apiClient.delete(`/v1/chat/conversation/${conversationId}`),
  
  /**
   * 搜索对话
   */
  searchConversations: (query, userId = 'default_user', limit = 20) =>
    apiClient.get('/v1/chat/search', { params: { query, user_id: userId, limit } }),
  
  /**
   * 添加收藏对话
   */
  addFavorite: (sessionId, data) =>
    apiClient.post('/v1/chat/favorite', { session_id: sessionId, ...data }),
  
  /**
   * 移除收藏对话
   */
  removeFavorite: (sessionId, userId = 'default_user') =>
    apiClient.delete(`/v1/chat/favorite/${sessionId}`, { params: { user_id: userId } }),
  
  /**
   * 获取收藏列表
   */
  getFavorites: (userId = 'default_user', limit = 50) =>
    apiClient.get('/v1/chat/favorites', { params: { user_id: userId, limit } }),
  
  /**
   * 检查是否已收藏
   */
  checkFavorite: (sessionId, userId = 'default_user') =>
    apiClient.get(`/v1/chat/favorite/check/${sessionId}`, { params: { user_id: userId } }),
  
  /**
   * 更新收藏信息
   */
  updateFavorite: (sessionId, data) =>
    apiClient.put(`/v1/chat/favorite/${sessionId}`, data)
}

