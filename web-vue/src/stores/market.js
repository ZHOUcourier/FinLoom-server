import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services'

export const useMarketStore = defineStore('market', () => {
  // 状态 - 分离指数和热门股票数据
  const indices = ref([])
  const hotStocks = ref([])
  const marketSentiment = ref({})
  const loading = ref(false)
  const error = ref(null)
  
  // 缓存时间戳
  const cacheTimestamps = ref({
    indices: null,
    hotStocks: null
  })
  
  // 缓存有效期（5分钟）
  const CACHE_DURATION = 5 * 60 * 1000
  
  // 检查缓存是否有效
  function isCacheValid(type) {
    const timestamp = cacheTimestamps.value[type]
    if (!timestamp) return false
    
    const elapsed = Date.now() - timestamp
    return elapsed < CACHE_DURATION
  }
  
  // 获取市场指数数据
  async function fetchIndices(force = false) {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!force && isCacheValid('indices') && indices.value.length > 0) {
      console.log('✅ 使用缓存的市场指数数据')
      return
    }
    
    try {
      loading.value = true
      const response = await api.market.getIndices()
      indices.value = response.data?.indices || []
      cacheTimestamps.value.indices = Date.now()
      error.value = null
      console.log('✅ 从服务器获取市场指数数据')
    } catch (err) {
      console.error('获取市场指数失败:', err)
      error.value = err.message || '获取市场指数失败'
    } finally {
      loading.value = false
    }
  }
  
  // 获取热门股票数据
  async function fetchHotStocks(force = false) {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!force && isCacheValid('hotStocks') && hotStocks.value.length > 0) {
      console.log('✅ 使用缓存的热门股票数据')
      return
    }
    
    try {
      loading.value = true
      const response = await api.market.getHotStocks()
      hotStocks.value = response.data?.hot_stocks || []
      marketSentiment.value = response.data?.market_sentiment || {}
      cacheTimestamps.value.hotStocks = Date.now()
      error.value = null
      console.log('✅ 从服务器获取热门股票数据')
    } catch (err) {
      console.error('获取热门股票失败:', err)
      error.value = err.message || '获取热门股票失败'
    } finally {
      loading.value = false
    }
  }
  
  // 获取完整市场数据（并行获取指数和热门股票）
  async function fetchMarketData(force = false) {
    await Promise.all([
      fetchIndices(force),
      fetchHotStocks(force)
    ])
  }
  
  // 清除缓存
  function clearCache(type = null) {
    if (type) {
      cacheTimestamps.value[type] = null
    } else {
      cacheTimestamps.value = {
        indices: null,
        hotStocks: null
      }
    }
  }
  
  return {
    // 状态
    indices,
    hotStocks,
    marketSentiment,
    loading,
    error,
    cacheTimestamps,
    
    // 操作
    fetchIndices,
    fetchHotStocks,
    fetchMarketData,
    clearCache,
    isCacheValid
  }
})

