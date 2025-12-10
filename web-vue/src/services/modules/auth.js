/**
 * 用户认证API
 */

import apiClient from '../client'

export const authApi = {
  /**
   * 用户注册
   * @param {Object} data - 注册信息
   * @param {string} data.username - 用户名
   * @param {string} data.password - 密码
   * @param {string} data.email - 邮箱（可选）
   * @param {string} data.display_name - 显示名称（可选）
   * @returns {Promise}
   */
  register: (data) => apiClient.post('/auth/register', data),

  /**
   * 用户登录
   * @param {Object} data - 登录信息
   * @param {string} data.username - 用户名
   * @param {string} data.password - 密码
   * @param {boolean} data.remember - 是否记住我
   * @returns {Promise}
   */
  login: (data) => apiClient.post('/auth/login', data),

  /**
   * 用户登出
   * @returns {Promise}
   */
  logout: () => apiClient.post('/auth/logout'),

  /**
   * 验证令牌
   * @returns {Promise}
   */
  verify: () => apiClient.get('/auth/verify'),

  /**
   * 获取用户资料
   * @returns {Promise}
   */
  getProfile: () => apiClient.get('/auth/profile'),

  /**
   * 更新用户资料
   * @param {Object} data - 用户资料
   * @param {string} data.display_name - 显示名称
   * @param {string} data.email - 邮箱
   * @param {string} data.avatar_url - 头像URL
   * @returns {Promise}
   */
  updateProfile: (data) => apiClient.put('/auth/profile', data),

  /**
   * 修改密码
   * @param {Object} data - 密码信息
   * @param {string} data.old_password - 旧密码
   * @param {string} data.new_password - 新密码
   * @returns {Promise}
   */
  changePassword: (data) => apiClient.post('/auth/change-password', data)
}

export default authApi


