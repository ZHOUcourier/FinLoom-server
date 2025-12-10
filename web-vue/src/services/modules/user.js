/**
 * 用户信息API
 */

import apiClient from '../client'

export const userApi = {
  /**
   * 获取用户完整资料（包括密码等敏感信息）
   * @returns {Promise}
   */
  getUserProfile: () => apiClient.get('/user/profile/full'),

  /**
   * 更新用户资料（需要密码验证）
   * @param {Object} data - 用户资料
   * @param {string} data.username - 用户名
   * @param {string} data.email - 邮箱
   * @param {string} data.phone - 电话
   * @param {string} data.verify_password - 验证密码
   * @returns {Promise}
   */
  updateProfile: (data) => apiClient.put('/user/profile', data),

  /**
   * 获取用户信息（包括最后修改时间）
   * @returns {Promise}
   */
  getUserInfo: () => apiClient.get('/user/info'),

  /**
   * 检查是否可以修改个人信息
   * @returns {Promise}
   */
  canModifyProfile: () => apiClient.get('/user/can-modify')
}

export default userApi


