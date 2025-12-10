import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services'

export const useAppStore = defineStore('app', () => {
  // 状态
  const isHealthy = ref(true)
  const isReady = ref(false)
  const loading = ref(false)
  const error = ref(null)
  const sidebarCollapsed = ref(false)
  
  // 计算属性
  const appStatus = computed(() => {
    if (!isHealthy.value) return 'unhealthy'
    if (!isReady.value) return 'loading'
    return 'ready'
  })
  
  // 操作
  async function checkHealth() {
    try {
      loading.value = true
      const response = await api.health.check()
      isHealthy.value = response.status === 'healthy'
      
      // 检查就绪状态
      const readyResponse = await api.health.ready()
      isReady.value = readyResponse.ready
      
      error.value = null
    } catch (err) {
      console.error('健康检查失败:', err)
      isHealthy.value = false
      error.value = err.message || '服务不可用'
    } finally {
      loading.value = false
    }
  }
  
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  function setSidebarCollapsed(collapsed) {
    sidebarCollapsed.value = collapsed
  }
  
  function setError(message) {
    error.value = message
  }
  
  function clearError() {
    error.value = null
  }
  
  return {
    // 状态
    isHealthy,
    isReady,
    loading,
    error,
    sidebarCollapsed,
    
    // 计算属性
    appStatus,
    
    // 操作
    checkHealth,
    toggleSidebar,
    setSidebarCollapsed,
    setError,
    clearError
  }
})

