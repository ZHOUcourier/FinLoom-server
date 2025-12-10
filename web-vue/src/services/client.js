/**
 * Axios客户端配置
 */

import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 90000, // 增加到60秒，适应AI服务的响应时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    // 添加认证token
    const token = localStorage.getItem('finloom_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    // 直接返回后端的数据（已经是 response.data）
    return response.data
  },
  error => {
    console.error('API错误:', error)
    
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response
      
      if (status === 401) {
        // 未授权，跳转登录
        localStorage.removeItem('finloom_auth')
        localStorage.removeItem('finloom_token')
        localStorage.removeItem('finloom_user')
        window.location.href = '/login'
      }
      
      // 返回后端的错误信息
      return Promise.reject(data || { message: error.message })
    } else if (error.request) {
      // 请求已发送但没有收到响应
      return Promise.reject({ message: '网络错误，请检查服务器连接' })
    } else {
      // 请求配置出错
      return Promise.reject({ message: error.message })
    }
  }
)

export default apiClient

