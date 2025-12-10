<template>
  <v-container fluid class="overview-view pa-6">
    <!-- 全局加载提示条 - 只在首次加载且无缓存时显示 -->
    <v-progress-linear
      v-if="isLoading"
      indeterminate
      color="primary"
      class="loading-bar"
    ></v-progress-linear>
    
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
          <h1 class="text-h3 font-weight-bold mb-2">仪表盘概览</h1>
          <div v-if="isLoading" class="text-caption text-medium-emphasis">
            <v-icon size="small" class="mr-1">mdi-loading mdi-spin</v-icon>
            数据正在加载中...
          </div>
          <div v-else-if="lastUpdateTime" class="text-caption text-medium-emphasis">
            <v-icon size="small" class="mr-1">mdi-update</v-icon>
            最后更新: {{ lastUpdateTime }}
          </div>
        </div>
        <div class="d-flex gap-2">
          <v-alert
            :type="isLoading ? 'info' : isMarketOpenNow ? 'success' : 'warning'"
            variant="tonal"
            class="mb-0"
            rounded="lg"
            density="compact"
          >
            <template v-slot:prepend>
              <v-icon>{{ isLoading ? 'mdi-loading mdi-spin' : isMarketOpenNow ? 'mdi-chart-line' : 'mdi-pause-circle' }}</v-icon>
            </template>
            <span class="text-body-2 font-weight-medium">
              {{ isLoading ? '数据加载中' : isMarketOpenNow ? '交易进行中' : '休市中' }}
            </span>
          </v-alert>
        </div>
      </div>
    </div>

    <!-- 移除了重复的loading显示，统一使用isLoading状态 -->
    <div>
      <!-- 关键指标卡片 - Material 3 风格 -->
      <v-row class="mb-6">
        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-primary-container" hover>
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="primary">mdi-wallet</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('assets')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                    <v-list-item @click="setAlert('assets')">
                      <v-list-item-title>设置预警</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-primary">总资产</div>
              <div class="text-h4 font-weight-bold mb-3">
                ¥{{ formatNumber(metrics.total_assets) }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip 
                  size="small" 
                  :color="metrics.assets_change >= 0 ? 'success' : 'error'" 
                  variant="flat" 
                  :class="metrics.assets_change >= 0 ? 'bg-success-lighten-4' : 'bg-error-lighten-4'"
                >
                  <v-icon start size="16">{{ metrics.assets_change >= 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}</v-icon>
                  {{ formatPercent(metrics.assets_change) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">vs 昨日</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-secondary-container" hover>
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="secondary">mdi-trending-up</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('returns')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                    <v-list-item @click="setAlert('returns')">
                      <v-list-item-title>设置预警</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-secondary">日收益</div>
              <div class="text-h4 font-weight-bold mb-3">
                ¥{{ formatNumber(metrics.daily_return) }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip 
                  size="small" 
                  :color="metrics.daily_return >= 0 ? 'success' : 'error'" 
                  variant="flat" 
                  :class="metrics.daily_return >= 0 ? 'bg-success-lighten-4' : 'bg-error-lighten-4'"
                >
                  <v-icon start size="16">{{ metrics.daily_return >= 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}</v-icon>
                  {{ formatPercent(metrics.daily_return_pct) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">今日</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-tertiary-container" hover>
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="tertiary">mdi-chart-line</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('sharpe')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                    <v-list-item @click="setAlert('sharpe')">
                      <v-list-item-title>设置预警</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-tertiary">夏普比率</div>
              <div class="text-h4 font-weight-bold mb-3">
                {{ formatNumber(metrics.sharpe_ratio, 2) }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip 
                  size="small" 
                  :color="getSharpeColor(metrics.sharpe_ratio)" 
                  variant="flat" 
                  :class="getSharpeColor(metrics.sharpe_ratio) + '-lighten-4'"
                >
                  <v-icon start size="16">{{ getSharpeIcon(metrics.sharpe_ratio) }}</v-icon>
                  {{ getSharpeLabel(metrics.sharpe_ratio) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">风险调整</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-error-container" hover>
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="error">mdi-arrow-down</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('drawdown')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                    <v-list-item @click="setAlert('drawdown')">
                      <v-list-item-title>设置预警</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-error">最大回撤</div>
              <div class="text-h4 font-weight-bold mb-3">
                {{ formatNumber(metrics.max_drawdown, 2) }}%
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip 
                  size="small" 
                  :color="getDrawdownColor(metrics.max_drawdown)" 
                  variant="flat" 
                  :class="getDrawdownColor(metrics.max_drawdown) + '-lighten-4'"
                >
                  <v-icon start size="16">{{ getDrawdownIcon(metrics.max_drawdown) }}</v-icon>
                  {{ getDrawdownLabel(metrics.max_drawdown) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">历史最大</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 新增：市场概览卡片 -->
      <v-row class="mb-6">
        <v-col cols="12">
          <v-card variant="elevated" class="market-overview-card">
            <v-card-title class="d-flex align-center pa-6">
              <v-avatar color="info" variant="tonal" size="40" class="mr-3">
                <v-icon>mdi-chart-multiple</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">市场概览</div>
                <div class="text-caption text-medium-emphasis">主要指数实时表现</div>
              </div>
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                variant="text"
                size="small"
                @click="refreshMarketData"
                :loading="marketLoading"
                prepend-icon="mdi-refresh"
              >
                刷新
              </v-btn>
            </v-card-title>
            <v-card-text class="pa-6 pt-0">
              <v-row>
                <v-col v-for="index in marketIndices" :key="index.symbol" cols="12" sm="6" md="3">
                  <v-card variant="outlined" class="index-card" hover>
                    <v-card-text class="pa-4">
                      <div class="d-flex justify-space-between align-center mb-2">
                        <div class="text-subtitle-2 font-weight-bold">{{ index.name }}</div>
                        <v-chip size="x-small" :color="index.change >= 0 ? 'success' : 'error'" variant="tonal">
                          {{ index.change >= 0 ? '+' : '' }}{{ formatPercent(index.change_pct) }}
                        </v-chip>
                      </div>
                      <div class="text-h6 font-weight-bold mb-1">{{ formatNumber(index.value, 2) }}</div>
                      <div class="d-flex align-center">
                        <v-icon 
                          :color="index.change >= 0 ? 'success' : 'error'" 
                          size="16" 
                          class="mr-1"
                        >
                          {{ index.change >= 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}
                        </v-icon>
                        <span 
                          :class="index.change >= 0 ? 'text-success' : 'text-error'" 
                          class="text-caption font-weight-medium"
                        >
                          {{ index.change >= 0 ? '+' : '' }}{{ formatNumber(index.change, 2) }}
                        </span>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 图表区域 - Material 3 风格 -->
      <v-row>
        <!-- 投资组合分布 -->
        <v-col cols="12" md="6">
          <v-card variant="elevated" class="chart-card">
            <v-card-title class="d-flex align-center justify-space-between pa-6">
              <div class="d-flex align-center">
                <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
                  <v-icon>mdi-chart-donut</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold">投资组合分布</div>
                  <div class="text-caption text-medium-emphasis">按市值占比</div>
                </div>
              </div>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="exportChart('portfolio')">
                    <v-list-item-title>导出图表</v-list-item-title>
                  </v-list-item>
                  <v-list-item @click="viewFullChart('portfolio')">
                    <v-list-item-title>全屏查看</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </v-card-title>
            <v-card-text class="px-6 pb-6">
              <div class="chart-container">
                <canvas ref="portfolioChartRef" v-if="positions.length > 0"></canvas>
                <div v-if="positions.length === 0" class="empty-state">
                  <v-icon size="64" class="text-medium-emphasis mb-4">mdi-chart-donut-variant</v-icon>
                  <p class="text-body-2 text-medium-emphasis">暂无持仓数据</p>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 收益曲线 -->
        <v-col cols="12" md="6">
          <v-card variant="elevated" class="chart-card">
            <v-card-title class="d-flex align-center justify-space-between pa-6">
              <div class="d-flex align-center">
                <v-avatar color="success" variant="tonal" size="40" class="mr-3">
                  <v-icon>mdi-chart-areaspline</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold">收益曲线</div>
                  <div class="text-caption text-medium-emphasis">资产净值变化</div>
                </div>
              </div>
              <div class="d-flex gap-2">
                <v-btn-toggle v-model="chartPeriod" mandatory>
                  <v-btn value="1M" size="small">1M</v-btn>
                  <v-btn value="3M" size="small">3M</v-btn>
                  <v-btn value="1Y" size="small">1Y</v-btn>
                </v-btn-toggle>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="exportChart('equity')">
                      <v-list-item-title>导出图表</v-list-item-title>
                    </v-list-item>
                    <v-list-item @click="viewFullChart('equity')">
                      <v-list-item-title>全屏查看</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
            </v-card-title>
            <v-card-text class="px-6 pb-6">
              <div class="chart-container">
                <canvas ref="equityChartRef"></canvas>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 风险指标仪表盘 -->
        <v-col cols="12" md="6">
          <v-card variant="elevated" class="chart-card">
            <v-card-title class="d-flex align-center pa-6">
              <v-avatar color="warning" variant="tonal" size="40" class="mr-3">
                <v-icon>mdi-gauge</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">风险指标</div>
                <div class="text-caption text-medium-emphasis">实时风险评估</div>
              </div>
            </v-card-title>
            <v-card-text class="pa-6">
              <v-row>
                <v-col cols="6">
                  <div class="text-center">
                    <div class="text-h4 font-weight-bold mb-2" :class="getRiskColor(riskMetrics.var_95)">
                      {{ formatNumber(riskMetrics.var_95, 2) }}%
                    </div>
                    <div class="text-caption text-medium-emphasis">VaR (95%)</div>
                  </div>
                </v-col>
                <v-col cols="6">
                  <div class="text-center">
                    <div class="text-h4 font-weight-bold mb-2" :class="getRiskColor(riskMetrics.beta)">
                      {{ formatNumber(riskMetrics.beta, 2) }}
                    </div>
                    <div class="text-caption text-medium-emphasis">Beta系数</div>
                  </div>
                </v-col>
              </v-row>
              <v-divider class="my-4"></v-divider>
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-body-2">波动率</span>
                <span class="font-weight-bold">{{ formatNumber(riskMetrics.volatility, 2) }}%</span>
              </div>
              <v-progress-linear
                :model-value="Math.min(riskMetrics.volatility, 50)"
                :color="getVolatilityColor(riskMetrics.volatility)"
                height="8"
                rounded
              ></v-progress-linear>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 最近交易 -->
        <v-col cols="12" md="6">
          <v-card variant="elevated" class="chart-card">
            <v-card-title class="d-flex align-center justify-space-between pa-6">
              <div class="d-flex align-center">
                <v-avatar color="info" variant="tonal" size="40" class="mr-3">
                  <v-icon>mdi-history</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold">最近交易</div>
                  <div class="text-caption text-medium-emphasis">最新交易记录</div>
                </div>
              </div>
              <v-btn
                color="primary"
                variant="text"
                size="small"
                @click="viewAllTrades"
                prepend-icon="mdi-arrow-right"
              >
                查看全部
              </v-btn>
            </v-card-title>
            <v-card-text class="pa-0">
              <v-list density="compact">
                <v-list-item
                  v-for="trade in recentTrades.slice(0, 5)"
                  :key="trade.time"
                  class="px-6"
                >
                  <template v-slot:prepend>
                    <v-avatar
                      :color="trade.action === 'BUY' ? 'success' : 'error'"
                      size="32"
                      variant="tonal"
                    >
                      <v-icon size="16">
                        {{ trade.action === 'BUY' ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
                      </v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-medium">{{ trade.name }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ trade.action === 'BUY' ? '买入' : '卖出' }} {{ trade.quantity }}股
                  </v-list-item-subtitle>
                  <template v-slot:append>
                    <div class="text-end">
                      <div class="font-weight-bold">¥{{ formatNumber(trade.price, 2) }}</div>
                      <div class="text-caption text-medium-emphasis">{{ formatTime(trade.time) }}</div>
                    </div>
                  </template>
                </v-list-item>
              </v-list>
              <div v-if="recentTrades.length === 0" class="text-center py-8">
                <v-icon size="48" class="text-medium-emphasis mb-4">mdi-history</v-icon>
                <p class="text-body-2 text-medium-emphasis">暂无交易记录</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useRouter } from 'vue-router'
import { api } from '@/services'
import Chart from 'chart.js/auto'

const dashboardStore = useDashboardStore()
const router = useRouter()

const portfolioChartRef = ref(null)
const equityChartRef = ref(null)
const chartPeriod = ref('3M')
const marketLoading = ref(false)
const isLoading = ref(true)
const lastUpdateTime = ref('')
let refreshInterval = null

// 市场数据缓存
const marketDataCache = ref({
  data: null,
  timestamp: null
})
const MARKET_CACHE_DURATION = 5 * 60 * 1000 // 市场数据缓存 5 分钟

const metrics = computed(() => dashboardStore.metrics)
const positions = computed(() => dashboardStore.positions)
const recentTrades = computed(() => dashboardStore.recentTrades)

// 判断当前是否为交易时间
const isMarketOpenNow = computed(() => {
  const now = new Date()
  const day = now.getDay()
  const hours = now.getHours()
  const minutes = now.getMinutes()
  const timeInMinutes = hours * 60 + minutes
  
  if (day === 0 || day === 6) return false
  
  const morningOpen = 9 * 60 + 30
  const morningClose = 11 * 60 + 30
  const afternoonOpen = 13 * 60
  const afternoonClose = 15 * 60
  
  return (timeInMinutes >= morningOpen && timeInMinutes <= morningClose) ||
         (timeInMinutes >= afternoonOpen && timeInMinutes <= afternoonClose)
})

// 市场指数数据 - 从API获取
const marketIndices = ref([
  { symbol: '000001.SH', name: '上证指数', value: 0, change: 0, change_pct: 0 },
  { symbol: '399001.SZ', name: '深证成指', value: 0, change: 0, change_pct: 0 },
  { symbol: '399006.SZ', name: '创业板指', value: 0, change: 0, change_pct: 0 },
  { symbol: 'HSI', name: '恒生指数', value: 0, change: 0, change_pct: 0 }
])

// 风险指标
const riskMetrics = ref({
  var_95: 2.5,
  beta: 1.2,
  volatility: 18.5
})


let portfolioChart = null
let equityChart = null

onMounted(async () => {
  // 如果有缓存数据，立即显示，不需要加载状态
  const hasCache = dashboardStore.isCacheValid('metrics') && 
                   dashboardStore.metrics.total_assets !== 0
  
  if (!hasCache) {
    isLoading.value = true
  } else {
    console.log('✅ 使用缓存数据，页面立即显示')
  }
  
  try {
    // 🎯 优先级1：核心数据（仓位、资金）- 立即加载
    console.log('📊 [优先级1] 加载核心数据（仓位、资金）...')
    await dashboardStore.fetchMetrics()  // 核心指标
    
    // 更新时间戳
    if (!hasCache) {
      updateLastUpdateTime()
    } else {
      // 显示缓存时间
      const cacheTime = new Date(dashboardStore.cacheTimestamps.metrics)
      lastUpdateTime.value = cacheTime.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }) + ' (缓存)'
    }
    
    // 🎯 优先级2：持仓和交易记录 - 延迟300ms加载（不阻塞页面显示）
    setTimeout(async () => {
      console.log('📊 [优先级2] 加载持仓和交易记录...')
      await Promise.all([
        dashboardStore.fetchPositions(),
        dashboardStore.fetchRecentTrades()
      ])
      // 有持仓数据后再初始化投资组合图表
      if (positions.value.length > 0) {
        initPortfolioChart()
      }
    }, 300)
    
    // 🎯 优先级3：市场数据 - 延迟800ms加载（次要功能，不影响核心体验）
    setTimeout(async () => {
      console.log('📊 [优先级3] 加载市场数据...')
      try {
        await loadMarketData()  // 市场指数（带缓存和超时保护）
      } catch (error) {
        // 市场数据加载失败不影响核心功能
        console.warn('⚠️ 市场数据加载失败，但不影响核心功能:', error)
      }
    }, 800)
    
    // 延迟初始化收益曲线图表
    setTimeout(() => {
      initEquityChart()
    }, 1200)
    
    // 启动自动刷新 - 只在交易时间刷新实时数据
    startAutoRefresh()
    
  } catch (error) {
    console.error('❌ 加载核心数据失败:', error)
    // 即使核心数据加载失败，也不要完全阻塞页面
  } finally {
    isLoading.value = false
    console.log('✅ 页面加载完成，用户可以开始操作')
  }
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopAutoRefresh()
})

// 判断当前是否为交易时间
function isMarketOpen() {
  const now = new Date()
  const day = now.getDay() // 0=周日, 1-5=周一到周五, 6=周六
  const hours = now.getHours()
  const minutes = now.getMinutes()
  const timeInMinutes = hours * 60 + minutes
  
  // 周末不开市
  if (day === 0 || day === 6) {
    return false
  }
  
  // 交易时间段：
  // 上午：9:30-11:30 (570-690分钟)
  // 下午：13:00-15:00 (780-900分钟)
  const morningOpen = 9 * 60 + 30  // 570
  const morningClose = 11 * 60 + 30 // 690
  const afternoonOpen = 13 * 60     // 780
  const afternoonClose = 15 * 60    // 900
  
  return (timeInMinutes >= morningOpen && timeInMinutes <= morningClose) ||
         (timeInMinutes >= afternoonOpen && timeInMinutes <= afternoonClose)
}

function startAutoRefresh() {
  // 清除旧的定时器
  stopAutoRefresh()
  
  // 检查当前是否在交易时间
  const marketOpen = isMarketOpen()
  
  if (!marketOpen) {
    console.log('⏸️ 当前为休市时间，不启动自动刷新')
    // 设置定时器在下一个交易时段检查（每分钟检查一次）
    refreshInterval = setInterval(() => {
      const nowOpen = isMarketOpen()
      if (nowOpen) {
        console.log('🔔 检测到开市，重新启动自动刷新')
        startAutoRefresh() // 递归调用以启动真正的刷新定时器
      }
    }, 60000) // 1分钟检查一次
    return
  }
  
  console.log('▶️ 交易时间，启动自动刷新 (15秒间隔)')
  refreshInterval = setInterval(async () => {
    // 每次刷新时都检查是否还在交易时间
    const marketOpen = isMarketOpen()
    
    // 如果已经收市，停止并重新启动（进入等待模式）
    if (!marketOpen) {
      console.log('⏸️ 检测到休市，停止自动刷新')
      startAutoRefresh() // 重新调用以进入等待模式
      return
    }
    
    try {
      // 只刷新实时数据：市场指数 + 关键指标（强制刷新，忽略缓存）
      await Promise.all([
        loadMarketData(true),  // 交易时间强制刷新
        dashboardStore.fetchMetrics(true)  // 交易时间强制刷新
      ])
      updateLastUpdateTime()
      console.log('✅ 实时数据已更新')
    } catch (error) {
      console.error('❌ 自动刷新失败:', error)
    }
  }, 15000) // 15秒
}

function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

function updateLastUpdateTime() {
  const now = new Date()
  lastUpdateTime.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

watch(positions, () => {
  updatePortfolioChart()
})

watch(chartPeriod, () => {
  updateEquityChart()
})

// 优化：移除统一初始化，改为按需初始化
// function initCharts() {
//   initPortfolioChart()
//   initEquityChart()
// }

function initPortfolioChart() {
  if (portfolioChartRef.value) {
    portfolioChart = new Chart(portfolioChartRef.value, {
      type: 'doughnut',
      data: {
        labels: [],
        datasets: [{
          data: [],
          backgroundColor: [
            '#3b82f6',
            '#8b5cf6',
            '#ec4899',
            '#10b981',
            '#f59e0b',
            '#f97316',
            '#84cc16',
            '#06b6d4'
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = ((context.parsed / total) * 100).toFixed(1)
                return `${context.label}: ¥${context.parsed.toLocaleString()} (${percentage}%)`
              }
            }
          }
        }
      }
    })
    updatePortfolioChart()
  }
}

function initEquityChart() {
  if (equityChartRef.value) {
    equityChart = new Chart(equityChartRef.value, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: '资产净值',
          data: [],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: function(context) {
                return `资产净值: ¥${context.parsed.y.toLocaleString()}`
              }
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            }
          },
          y: {
            beginAtZero: false,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
              callback: function(value) {
                return '¥' + (value / 10000).toFixed(0) + '万'
              }
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      }
    })
    updateEquityChart()
  }
}

function updatePortfolioChart() {
  if (!portfolioChart || positions.value.length === 0) return

  portfolioChart.data.labels = positions.value.map(p => p.name)
  portfolioChart.data.datasets[0].data = positions.value.map(p => p.market_value)
  portfolioChart.update()
}

function updateEquityChart() {
  if (!equityChart) return

  // 根据选择的时间周期生成模拟数据
  const data = generateEquityData(chartPeriod.value)
  equityChart.data.labels = data.labels
  equityChart.data.datasets[0].data = data.values
  equityChart.update()
}

function generateEquityData(period) {
  const baseValue = 1000000
  // 优化：大幅减少数据点数量，使用采样
  const days = period === '1M' ? 30 : period === '3M' ? 90 : 365
  const sampleRate = period === '1M' ? 1 : period === '3M' ? 3 : 7  // 采样率：1天/3天/7天
  const dataPoints = Math.ceil(days / sampleRate)  // 实际数据点：30/30/52个
  
  const labels = []
  const values = []
  
  for (let i = 0; i < dataPoints; i++) {
    const dayOffset = i * sampleRate
    const date = new Date()
    date.setDate(date.getDate() - (days - dayOffset))
    labels.push(date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }))
    
    // 模拟价格波动
    const randomChange = (Math.random() - 0.5) * 0.02
    const value = baseValue * (1 + randomChange * (dayOffset + 1) / days)
    values.push(Math.max(value, baseValue * 0.8))
  }
  
  return { labels, values }
}

// 工具函数
function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined) return '0'
  return Number(value).toLocaleString('zh-CN', { 
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals 
  })
}

function formatPercent(value) {
  if (value === null || value === undefined) return '0.00%'
  return (Number(value) * 100).toFixed(2) + '%'
}

function formatTime(time) {
  return new Date(time).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 风险指标颜色
function getSharpeColor(value) {
  if (value >= 2) return 'success'
  if (value >= 1) return 'primary'
  if (value >= 0) return 'warning'
  return 'error'
}

function getSharpeIcon(value) {
  if (value >= 2) return 'mdi-trending-up'
  if (value >= 1) return 'mdi-trending-neutral'
  if (value >= 0) return 'mdi-trending-down'
  return 'mdi-alert'
}

function getSharpeLabel(value) {
  if (value >= 2) return '优秀'
  if (value >= 1) return '良好'
  if (value >= 0) return '一般'
  return '较差'
}

function getDrawdownColor(value) {
  if (value <= 5) return 'success'
  if (value <= 10) return 'warning'
  if (value <= 20) return 'error'
  return 'error'
}

function getDrawdownIcon(value) {
  if (value <= 5) return 'mdi-check'
  if (value <= 10) return 'mdi-alert'
  return 'mdi-alert-circle'
}

function getDrawdownLabel(value) {
  if (value <= 5) return '低风险'
  if (value <= 10) return '中风险'
  if (value <= 20) return '高风险'
  return '极高风险'
}

function getRiskColor(value) {
  if (value <= 2) return 'text-success'
  if (value <= 5) return 'text-warning'
  return 'text-error'
}

function getVolatilityColor(value) {
  if (value <= 10) return 'success'
  if (value <= 20) return 'warning'
  if (value <= 30) return 'error'
  return 'error'
}

// 事件处理

async function loadMarketData(force = false) {
  // 检查缓存是否有效
  if (!force && marketDataCache.value.timestamp) {
    const elapsed = Date.now() - marketDataCache.value.timestamp
    if (elapsed < MARKET_CACHE_DURATION && marketDataCache.value.data) {
      // 使用缓存数据
      const cachedData = marketDataCache.value.data
      marketIndices.value = cachedData
      console.log('✅ 使用缓存的市场指数数据')
      return
    }
  }
  
  if (!marketLoading.value) {
    marketLoading.value = true
  }
  
  try {
    // 调用专门的市场指数API（优化：只获取指数数据）
    const response = await api.market.getIndices()
    
    if (response.data && response.data.indices) {
      // 更新市场指数数据
      const indices = response.data.indices
      
      // 映射后端数据到前端格式
      const indexMap = {
        '000001.SH': 0,  // 上证指数
        '399001.SZ': 1,  // 深证成指
        '399006.SZ': 2,  // 创业板指
      }
      
      // 更新所有获取到的指数
      indices.forEach(index => {
        const position = indexMap[index.symbol]
        if (position !== undefined && position < marketIndices.value.length) {
          marketIndices.value[position] = {
            symbol: index.symbol,
            name: index.name,
            value: index.value,
            change: index.change,
            change_pct: index.change_pct  // 后端已经是小数
          }
        }
      })
      
      // 缓存数据
      marketDataCache.value = {
        data: [...marketIndices.value],
        timestamp: Date.now()
      }
      
      console.log('✅ 从服务器获取市场指数数据:', {
        count: indices.length,
        indices: indices.map(i => `${i.name}: ${i.value}`)
      })
    }
  } catch (error) {
    console.error('❌ 加载市场指数数据失败:', error)
  } finally {
    marketLoading.value = false
  }
}

async function refreshMarketData() {
  marketLoading.value = true
  try {
    // 强制刷新市场数据和关键指标
    await Promise.all([
      loadMarketData(true),  // force = true
      dashboardStore.fetchMetrics(true)  // force = true
    ])
    updateLastUpdateTime()
    console.log('🔄 手动刷新数据完成')
  } finally {
    marketLoading.value = false
  }
}


function exportChart(type) {
  // 实现图表导出功能
  console.log('导出图表:', type)
}

function viewFullChart(type) {
  // 实现全屏查看图表功能
  console.log('全屏查看图表:', type)
}

function viewDetails(type) {
  // 实现查看详情功能
  console.log('查看详情:', type)
}

function setAlert(type) {
  // 实现设置预警功能
  console.log('设置预警:', type)
}

function viewAllTrades() {
  router.push('/dashboard/trades')
}
</script>

<style lang="scss" scoped>
.overview-view {
  max-width: 1600px;
  margin: 0 auto;
  position: relative;
}

// 全局加载提示条
.loading-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
}

.metric-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  }
}

.chart-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
  
  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  }
}

.chart-container {
  height: 300px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    width: 100%;
  }
}

.market-overview-card {
  .index-card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    }
  }
}

// 响应式调整
@media (max-width: 960px) {
  .overview-view {
    padding: 1rem !important;
  }
  
  .chart-container {
    height: 250px;
  }
}

@media (max-width: 600px) {
  .chart-container {
    height: 200px;
  }
}

// 自定义滚动条
:deep(.v-list) {
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 2px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.3);
  }
}

// 动画效果
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.metric-card,
.chart-card {
  animation: fadeInUp 0.6s ease-out;
}

// 延迟动画
.metric-card:nth-child(1) { animation-delay: 0.1s; }
.metric-card:nth-child(2) { animation-delay: 0.2s; }
.metric-card:nth-child(3) { animation-delay: 0.3s; }
.metric-card:nth-child(4) { animation-delay: 0.4s; }
</style>
