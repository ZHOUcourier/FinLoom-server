/**
 * 管理员API服务
 */

import apiClient from '../client'

export const adminApi = {
  /**
   * 获取系统统计信息
   */
  getStats() {
    return apiClient.get('/admin/stats')
  },

  /**
   * 获取所有用户列表
   */
  getUsers() {
    return apiClient.get('/admin/users')
  },

  /**
   * 获取用户详情
   * @param {number} userId - 用户ID
   */
  getUserDetails(userId) {
    return apiClient.get(`/admin/users/${userId}`)
  },

  /**
   * 更新用户权限
   * @param {number} userId - 用户ID
   * @param {number} permissionLevel - 权限等级
   */
  updateUserPermission(userId, permissionLevel) {
    return apiClient.put(`/admin/user/${userId}/permission`, {
      permission_level: permissionLevel
    })
  },

  /**
   * 更新用户Token限额
   * @param {number} userId - 用户ID
   * @param {number} tokenLimit - Token限额
   */
  updateUserTokenLimit(userId, tokenLimit) {
    return apiClient.put(`/admin/user/${userId}/token-limit`, {
      token_limit: tokenLimit
    })
  },

  /**
   * 获取用户留言列表
   */
  getMessages() {
    return apiClient.get('/admin/messages')
  },

  /**
   * 标记留言为已读
   * @param {number} messageId - 留言ID
   */
  markMessageAsRead(messageId) {
    return apiClient.put(`/admin/messages/${messageId}/read`)
  },

  /**
   * 回复用户留言
   * @param {number} messageId - 留言ID
   * @param {string} reply - 回复内容
   */
  replyToMessage(messageId, reply) {
    return apiClient.post(`/admin/messages/${messageId}/reply`, {
      reply
    })
  }
}

export default adminApi

