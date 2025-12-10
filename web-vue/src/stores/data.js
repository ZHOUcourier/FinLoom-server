import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services'

export const useDataStore = defineStore('data', () => {
  // 状态
  const overview = ref({
    total_records: 0,
    symbols_count: 0,
    last_update: null,
    storage_size: 0
  })
  const loading = ref(false)
  const error = ref(null)
  
  // 缓存时间戳
  const cacheTimestamp = ref(null)
  
  // 缓存有效期（10分钟 - 数据统计不需要频繁更新）
  const CACHE_DURATION = 10 * 60 * 1000
  
  // 检查缓存是否有效
  function isCacheValid() {
    if (!cacheTimestamp.value) return false
    
    const elapsed = Date.now() - cacheTimestamp.value
    return elapsed < CACHE_DURATION
  }
  
  // 获取数据概览
  async function fetchOverview(force = false) {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!force && isCacheValid() && overview.value.total_records !== 0) {
      console.log('✅ 使用缓存的数据概览')
      return
    }
    
    try {
      loading.value = true
      const response = await api.data.getOverview()
      overview.value = response.data || {}
      cacheTimestamp.value = Date.now()
      error.value = null
      console.log('✅ 从服务器获取数据概览')
    } catch (err) {
      console.error('获取数据概览失败:', err)
      error.value = err.message || '获取数据概览失败'
    } finally {
      loading.value = false
    }
  }
  
  // 清除缓存
  function clearCache() {
    cacheTimestamp.value = null
  }
  
  return {
    // 状态
    overview,
    loading,
    error,
    cacheTimestamp,
    
    // 操作
    fetchOverview,
    clearCache,
    isCacheValid
  }
})

