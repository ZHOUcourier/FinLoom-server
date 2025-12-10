import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services'

export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref(null)
  const loading = ref(false)
  const error = ref(null)
  
  // 计算属性
  const isLoggedIn = computed(() => !!userInfo.value)
  const username = computed(() => userInfo.value?.username || '')
  const displayName = computed(() => userInfo.value?.display_name || userInfo.value?.username || 'FinLoom用户')
  const email = computed(() => userInfo.value?.email || 'user@finloom.com')
  const phone = computed(() => userInfo.value?.phone || '')
  const permissionLevel = computed(() => userInfo.value?.permission_level || 1)
  const isAdmin = computed(() => permissionLevel.value >= 2)
  
  // 操作
  async function fetchUserInfo() {
    try {
      loading.value = true
      error.value = null
      
      const response = await api.auth.getProfile()
      
      // 处理不同的响应格式
      if (response.data?.data) {
        userInfo.value = response.data.data
      } else if (response.data) {
        userInfo.value = response.data
      } else {
        userInfo.value = response
      }
      
      console.log('用户信息获取成功:', userInfo.value)
      return userInfo.value
    } catch (err) {
      console.error('获取用户信息失败:', err)
      error.value = err.message || '获取用户信息失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  async function updateUserInfo(data) {
    try {
      loading.value = true
      error.value = null
      
      const response = await api.auth.updateProfile(data)
      
      // 更新本地用户信息
      if (response.data?.data) {
        userInfo.value = { ...userInfo.value, ...response.data.data }
      } else if (response.data) {
        userInfo.value = { ...userInfo.value, ...response.data }
      }
      
      return response
    } catch (err) {
      console.error('更新用户信息失败:', err)
      error.value = err.message || '更新用户信息失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  function clearUserInfo() {
    userInfo.value = null
    error.value = null
  }
  
  function setUserInfo(data) {
    userInfo.value = data
  }
  
  return {
    // 状态
    userInfo,
    loading,
    error,
    
    // 计算属性
    isLoggedIn,
    username,
    displayName,
    email,
    phone,
    permissionLevel,
    isAdmin,
    
    // 操作
    fetchUserInfo,
    updateUserInfo,
    clearUserInfo,
    setUserInfo
  }
})


