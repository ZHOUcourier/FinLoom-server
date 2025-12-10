import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services'

export const useDashboardStore = defineStore('dashboard', () => {
  // 状态
  const metrics = ref({
    total_assets: 0,
    daily_return: 0,
    sharpe_ratio: 0,
    max_drawdown: 0,
    win_rate: 0,
    total_trades: 0
  })
  
  const positions = ref([])
  const recentTrades = ref([])
  const loading = ref(false)
  const error = ref(null)
  
  // 缓存时间戳
  const cacheTimestamps = ref({
    metrics: null,
    positions: null,
    trades: null
  })
  
  // 缓存有效期（毫秒）
  const CACHE_DURATION = {
    metrics: 5 * 60 * 1000,      // 关键指标缓存 5 分钟
    positions: 10 * 60 * 1000,   // 持仓数据缓存 10 分钟
    trades: 5 * 60 * 1000        // 交易记录缓存 5 分钟
  }
  
  // 检查缓存是否有效
  function isCacheValid(type) {
    const timestamp = cacheTimestamps.value[type]
    if (!timestamp) return false
    
    const duration = CACHE_DURATION[type]
    const elapsed = Date.now() - timestamp
    return elapsed < duration
  }
  
  // 操作
  async function fetchMetrics(force = false) {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!force && isCacheValid('metrics') && metrics.value.total_assets !== 0) {
      console.log('✅ 使用缓存的指标数据')
      return
    }
    
    try {
      loading.value = true
      const response = await api.dashboard.getMetrics()
      metrics.value = response.data || {}
      cacheTimestamps.value.metrics = Date.now()
      error.value = null
      console.log('✅ 从服务器获取指标数据')
    } catch (err) {
      console.error('获取仪表盘指标失败:', err)
      error.value = err.message || '获取数据失败'
    } finally {
      loading.value = false
    }
  }
  
  async function fetchPositions(force = false) {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!force && isCacheValid('positions') && positions.value.length > 0) {
      console.log('✅ 使用缓存的持仓数据')
      return
    }
    
    try {
      loading.value = true
      const response = await api.portfolio.getPositions()
      positions.value = response.data?.positions || []
      cacheTimestamps.value.positions = Date.now()
      error.value = null
      console.log('✅ 从服务器获取持仓数据')
    } catch (err) {
      console.error('获取持仓数据失败:', err)
      error.value = err.message || '获取持仓失败'
    } finally {
      loading.value = false
    }
  }
  
  async function fetchRecentTrades(force = false) {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!force && isCacheValid('trades') && recentTrades.value.length > 0) {
      console.log('✅ 使用缓存的交易数据')
      return
    }
    
    try {
      loading.value = true
      const response = await api.trades.getRecent()
      recentTrades.value = response.data?.trades || []
      cacheTimestamps.value.trades = Date.now()
      error.value = null
      console.log('✅ 从服务器获取交易数据')
    } catch (err) {
      console.error('获取交易记录失败:', err)
      error.value = err.message || '获取交易记录失败'
    } finally {
      loading.value = false
    }
  }
  
  async function refreshAll(force = false) {
    await Promise.all([
      fetchMetrics(force),
      fetchPositions(force),
      fetchRecentTrades(force)
    ])
  }
  
  // 清除缓存
  function clearCache(type = null) {
    if (type) {
      cacheTimestamps.value[type] = null
    } else {
      cacheTimestamps.value = {
        metrics: null,
        positions: null,
        trades: null
      }
    }
  }
  
  return {
    // 状态
    metrics,
    positions,
    recentTrades,
    loading,
    error,
    cacheTimestamps,
    
    // 操作
    fetchMetrics,
    fetchPositions,
    fetchRecentTrades,
    refreshAll,
    clearCache,
    isCacheValid
  }
})

