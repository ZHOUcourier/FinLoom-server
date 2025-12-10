<template>
  <v-container fluid class="market-view pa-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
      <h1 class="text-h3 font-weight-bold mb-2">市场分析</h1>
      <p class="text-body-1 text-medium-emphasis">实时市场概览与分析</p>
        </div>
        <div class="d-flex gap-2">
          <!-- 保留空div以维持布局 -->
        </div>
      </div>
      
      <!-- 市场状态指示器 -->
      <v-alert
        v-if="marketStatus"
        :type="marketStatus.type"
        variant="tonal"
        class="mb-4"
        rounded="lg"
      >
        <template v-slot:prepend>
          <v-icon>{{ marketStatus.icon }}</v-icon>
        </template>
        <div class="d-flex justify-space-between align-center">
          <span>{{ marketStatus.message }}</span>
          <span class="text-caption">{{ lastUpdateTime }}</span>
        </div>
      </v-alert>
    </div>

    <div v-if="loading && !marketData" class="text-center py-10">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      <p class="mt-4 text-body-1">加载市场数据...</p>
    </div>

    <div v-else>
      <!-- 市场指数卡片 -->
      <v-card variant="elevated" class="mb-6">
        <v-card-title class="d-flex align-center justify-space-between pa-6">
          <div class="d-flex align-center">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-chart-multiple</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">市场指数</div>
              <div class="text-caption text-medium-emphasis">主要指数实时表现</div>
            </div>
          </div>
          <v-btn-toggle v-model="indexPeriod" mandatory>
            <v-btn value="1D" size="small">1日</v-btn>
            <v-btn value="1W" size="small">1周</v-btn>
            <v-btn value="1M" size="small">1月</v-btn>
          </v-btn-toggle>
        </v-card-title>
        <v-card-text class="pa-6 pt-0">
          <v-row>
            <v-col v-for="index in marketIndices" :key="index.symbol" cols="12" sm="6" md="3">
              <v-card variant="outlined" class="index-card" hover @click="viewIndexDetail(index)">
                <v-card-text class="pa-4">
                  <div class="d-flex justify-space-between align-center mb-2">
                    <div class="text-subtitle-2 font-weight-bold">{{ index.name }}</div>
                    <v-chip size="x-small" :color="index.change >= 0 ? 'success' : 'error'" variant="tonal">
                      {{ index.change >= 0 ? '+' : '' }}{{ formatPercent(index.change_pct) }}
                    </v-chip>
                  </div>
                  <div class="text-h6 font-weight-bold mb-1">{{ formatNumber(index.value, 2) }}</div>
                  <div class="d-flex align-center justify-space-between">
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
                    <v-icon size="16" class="text-medium-emphasis">mdi-chevron-right</v-icon>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 热门股票和板块分析 -->
      <v-row class="mb-6">
        <!-- 热门股票 -->
        <v-col cols="12" md="8">
          <v-card variant="elevated" class="h-100">
            <v-card-title class="d-flex align-center justify-space-between pa-6">
              <div class="d-flex align-center">
                <v-avatar color="success" variant="tonal" size="40" class="mr-3">
                  <v-icon>mdi-fire</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold">热门股票</div>
                  <div class="text-caption text-medium-emphasis">涨幅榜前10</div>
                </div>
              </div>
              <v-btn-toggle v-model="stockSort" mandatory>
                <v-btn value="change" size="small">涨跌幅</v-btn>
                <v-btn value="volume" size="small">成交量</v-btn>
                <v-btn value="amount" size="small">成交额</v-btn>
              </v-btn-toggle>
            </v-card-title>
            <v-card-text class="pa-0">
              <v-data-table
                :headers="stockHeaders"
                :items="sortedHotStocks"
                :items-per-page="10"
                class="elevation-0"
                hide-default-footer
              >
                <template v-slot:item.name="{ item }">
                  <div class="d-flex align-center">
                    <v-avatar size="32" class="mr-3">
                      <v-img :src="getStockLogo(item.symbol)" :alt="item.name">
                        <template v-slot:error>
                          <v-icon>mdi-chart-line</v-icon>
                        </template>
                      </v-img>
                    </v-avatar>
                    <div>
                      <div class="font-weight-bold">{{ item.name }}</div>
                      <div class="text-caption text-medium-emphasis">{{ item.symbol }}</div>
                    </div>
                  </div>
                </template>
                
                <template v-slot:item.price="{ item }">
                  <div class="font-weight-bold">¥{{ formatNumber(item.price, 2) }}</div>
                </template>
                
                <template v-slot:item.change="{ item }">
                  <div :class="item.change >= 0 ? 'text-success' : 'text-error'" class="font-weight-bold">
                    {{ item.change >= 0 ? '+' : '' }}{{ formatNumber(item.change, 2) }}
                  </div>
                </template>
                
                <template v-slot:item.change_pct="{ item }">
                  <v-chip 
                    :color="item.change_pct >= 0 ? 'success' : 'error'" 
                    size="small" 
                    variant="tonal"
                  >
                    {{ item.change_pct >= 0 ? '+' : '' }}{{ formatPercent(item.change_pct) }}
                  </v-chip>
                </template>
                
                <template v-slot:item.volume="{ item }">
                  <div class="text-body-2">{{ formatVolume(item.volume) }}</div>
                </template>
                
                <template v-slot:item.sector="{ item }">
                  <v-chip size="small" :color="getSectorColor(item.sector)" variant="tonal">
                    {{ item.sector }}
              </v-chip>
                </template>
                
                <template v-slot:item.actions="{ item }">
                  <v-btn
                    icon="mdi-chart-line"
                    variant="text"
                    size="small"
                    @click="viewStockDetail(item)"
                  ></v-btn>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 板块分析 -->
        <v-col cols="12" md="4">
          <v-card variant="elevated" class="h-100">
            <v-card-title class="d-flex align-center pa-6">
              <v-avatar color="info" variant="tonal" size="40" class="mr-3">
                <v-icon>mdi-chart-pie</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">板块分析</div>
                <div class="text-caption text-medium-emphasis">行业表现</div>
              </div>
            </v-card-title>
            <v-card-text class="pa-6">
              <!-- 加载中 -->
              <div v-if="sectorLoading" class="text-center py-8">
                <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
                <p class="mt-2 text-caption text-medium-emphasis">加载中...</p>
              </div>
              <!-- 加载失败 -->
              <div v-else-if="sectorError" class="text-center py-8">
                <v-icon size="48" color="error">mdi-alert-circle-outline</v-icon>
                <p class="mt-2 text-body-2 text-medium-emphasis">数据加载失败</p>
                <v-btn size="small" variant="text" color="primary" @click="loadMarketData(true)">
                  重新加载
                </v-btn>
              </div>
              <!-- 无数据 -->
              <div v-else-if="!sectorPerformance || sectorPerformance.length === 0" class="text-center py-8">
                <v-icon size="48" color="grey">mdi-information-outline</v-icon>
                <p class="mt-2 text-body-2 text-medium-emphasis">暂无板块数据</p>
              </div>
              <!-- 有数据 -->
              <v-list v-else density="compact">
                <v-list-item
                  v-for="sector in sectorPerformance"
                  :key="sector.name"
                  class="px-0"
                >
                  <template v-slot:prepend>
                    <v-avatar :color="sector.color" size="24" variant="tonal">
                      <v-icon size="14">{{ sector.icon }}</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title class="text-body-2">{{ sector.name }}</v-list-item-title>
                  <template v-slot:append>
                    <div class="text-end">
                      <div :class="sector.change >= 0 ? 'text-success' : 'text-error'" class="font-weight-bold">
                        {{ sector.change >= 0 ? '+' : '' }}{{ formatPercent(sector.change) }}
                      </div>
                      <div class="text-caption text-medium-emphasis">{{ sector.count }}只股票</div>
                    </div>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 市场情绪和技术指标 -->
      <v-row class="mb-6">
        <!-- 市场情绪 -->
        <v-col cols="12" md="6">
          <v-card variant="elevated" class="h-100">
        <v-card-title class="d-flex align-center pa-6">
          <v-avatar color="warning" variant="tonal" size="40" class="mr-3">
            <v-icon>mdi-emoticon</v-icon>
          </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">市场情绪</div>
                <div class="text-caption text-medium-emphasis">恐慌贪婪指数</div>
              </div>
        </v-card-title>
            <v-card-text class="pa-6">
              <!-- 加载中 -->
              <div v-if="sentimentLoading" class="text-center py-8">
                <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
                <p class="mt-2 text-caption text-medium-emphasis">加载中...</p>
              </div>
              <!-- 加载失败 -->
              <div v-else-if="sentimentError" class="text-center py-8">
                <v-icon size="48" color="error">mdi-alert-circle-outline</v-icon>
                <p class="mt-2 text-body-2 text-medium-emphasis">数据加载失败</p>
                <v-btn size="small" variant="text" color="primary" @click="loadMarketData(true)">
                  重新加载
                </v-btn>
              </div>
              <!-- 有数据 -->
              <div v-else>
                <div class="mb-6">
                  <div class="d-flex justify-space-between align-center mb-2">
                    <span class="text-body-2">恐慌</span>
                    <span class="font-weight-bold text-h6">{{ marketSentiment.fear_greed_index }}</span>
                    <span class="text-body-2">贪婪</span>
                  </div>
                  <v-progress-linear
                    :model-value="marketSentiment.fear_greed_index"
                    height="20"
                    :color="getSentimentColor(marketSentiment.fear_greed_index)"
                    rounded
                  ></v-progress-linear>
                  <div class="text-center mt-2">
                    <v-chip :color="getSentimentColor(marketSentiment.fear_greed_index)" size="small" variant="tonal">
                      {{ getSentimentLabel(marketSentiment.fear_greed_index) }}
                    </v-chip>
                  </div>
                </div>

                <v-row>
                  <v-col cols="6">
                    <div class="text-center">
                      <div class="text-h5 font-weight-bold text-success">{{ marketSentiment.advancing_stocks }}</div>
                      <div class="text-caption">上涨股票</div>
                    </div>
                  </v-col>
                  <v-col cols="6">
                    <div class="text-center">
                      <div class="text-h5 font-weight-bold text-error">{{ marketSentiment.declining_stocks }}</div>
                      <div class="text-caption">下跌股票</div>
                    </div>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 技术指标 -->
        <v-col cols="12" md="6">
          <v-card variant="elevated" class="h-100">
            <v-card-title class="d-flex align-center pa-6">
              <v-avatar color="info" variant="tonal" size="40" class="mr-3">
                <v-icon>mdi-chart-line-variant</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">技术指标</div>
                <div class="text-caption text-medium-emphasis">市场技术分析</div>
              </div>
            </v-card-title>
            <v-card-text class="pa-6">
              <!-- 加载中 -->
              <div v-if="indicatorsLoading" class="text-center py-8">
                <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
                <p class="mt-2 text-caption text-medium-emphasis">加载中...</p>
              </div>
              <!-- 加载失败 -->
              <div v-else-if="indicatorsError" class="text-center py-8">
                <v-icon size="48" color="error">mdi-alert-circle-outline</v-icon>
                <p class="mt-2 text-body-2 text-medium-emphasis">数据加载失败</p>
                <v-btn size="small" variant="text" color="primary" @click="loadMarketData(true)">
                  重新加载
                </v-btn>
              </div>
              <!-- 无数据 -->
              <div v-else-if="!technicalIndicators || technicalIndicators.length === 0" class="text-center py-8">
                <v-icon size="48" color="grey">mdi-information-outline</v-icon>
                <p class="mt-2 text-body-2 text-medium-emphasis">暂无技术指标数据</p>
              </div>
              <!-- 有数据 -->
              <v-list v-else density="compact">
                <v-list-item
                  v-for="indicator in technicalIndicators"
                  :key="indicator.name"
                  class="px-0"
                >
                  <template v-slot:prepend>
                    <v-avatar :color="indicator.color" size="32" variant="tonal">
                      <v-icon size="16">{{ indicator.icon }}</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title class="text-body-2 font-weight-medium">{{ indicator.name }}</v-list-item-title>
                  <v-list-item-subtitle class="text-caption">{{ indicator.description }}</v-list-item-subtitle>
                  <template v-slot:append>
                    <div class="text-end">
                      <div :class="indicator.value >= 0 ? 'text-success' : 'text-error'" class="font-weight-bold">
                        {{ indicator.value >= 0 ? '+' : '' }}{{ formatNumber(indicator.value, 2) }}
                      </div>
                      <div class="text-caption text-medium-emphasis">{{ indicator.signal }}</div>
                    </div>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
            </v-col>
          </v-row>

      <!-- 市场新闻和公告 -->
      <v-card variant="elevated" class="mb-6">
        <v-card-title class="d-flex align-center justify-space-between pa-6">
          <div class="d-flex align-center">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-newspaper</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">市场资讯</div>
              <div class="text-caption text-medium-emphasis">最新市场动态</div>
            </div>
          </div>
          <v-btn
            color="primary"
            variant="text"
            size="small"
            @click="viewAllNews"
            prepend-icon="mdi-arrow-right"
            v-if="!newsLoading && !newsError && marketNews.length > 0"
          >
            查看更多
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-6">
          <!-- 加载中 -->
          <div v-if="newsLoading" class="text-center py-8">
            <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
            <p class="mt-2 text-caption text-medium-emphasis">加载中...</p>
          </div>
          <!-- 加载失败 -->
          <div v-else-if="newsError" class="text-center py-8">
            <v-icon size="48" color="error">mdi-alert-circle-outline</v-icon>
            <p class="mt-2 text-body-2 text-medium-emphasis">数据加载失败</p>
            <v-btn size="small" variant="text" color="primary" @click="loadMarketData(true)">
              重新加载
            </v-btn>
          </div>
          <!-- 无数据 -->
          <div v-else-if="!marketNews || marketNews.length === 0" class="text-center py-8">
            <v-icon size="48" color="grey">mdi-information-outline</v-icon>
            <p class="mt-2 text-body-2 text-medium-emphasis">暂无市场资讯</p>
          </div>
          <!-- 有数据 -->
          <v-list v-else class="pa-0">
            <v-list-item
              v-for="news in marketNews"
              :key="news.id"
              class="px-0"
            >
              <template v-slot:prepend>
                <v-avatar :color="news.type === 'important' ? 'error' : 'primary'" size="32" variant="tonal">
                  <v-icon size="16">{{ news.type === 'important' ? 'mdi-alert' : 'mdi-newspaper' }}</v-icon>
                </v-avatar>
              </template>
              <v-list-item-title class="font-weight-medium">{{ news.title }}</v-list-item-title>
              <v-list-item-subtitle>{{ news.summary }}</v-list-item-subtitle>
              <template v-slot:append>
                <div class="text-end">
                  <div class="text-caption text-medium-emphasis">{{ formatTime(news.time) }}</div>
                  <v-chip size="x-small" :color="news.type === 'important' ? 'error' : 'primary'" variant="tonal">
                    {{ news.type === 'important' ? '重要' : '资讯' }}
                  </v-chip>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </div>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services'

const router = useRouter()
const indexPeriod = ref('1D')
const stockSort = ref('change')

const loading = ref(false)

// 市场状态
const marketStatus = ref({
  type: 'success',
  icon: 'mdi-check-circle',
  message: '市场正常运行'
})

// 市场指数数据
const marketIndices = ref([
  { symbol: 'SH000001', name: '上证指数', value: 3000.25, change: 15.32, change_pct: 0.51 },
  { symbol: 'SZ399001', name: '深证成指', value: 9500.15, change: -25.18, change_pct: -0.26 },
  { symbol: 'SZ399006', name: '创业板指', value: 1850.45, change: 8.75, change_pct: 0.48 },
  { symbol: 'HKHSI', name: '恒生指数', value: 16500.30, change: 120.45, change_pct: 0.73 }
])

// 热门股票数据
const hotStocks = ref([
  { symbol: '000001', name: '平安银行', price: 12.45, change: 0.85, change_pct: 0.73, volume: 12500000, sector: '银行' },
  { symbol: '000002', name: '万科A', price: 18.32, change: -0.45, change_pct: -0.24, volume: 8900000, sector: '房地产' },
  { symbol: '000858', name: '五粮液', price: 156.80, change: 3.20, change_pct: 2.08, volume: 5600000, sector: '食品饮料' },
  { symbol: '002415', name: '海康威视', price: 45.60, change: 1.20, change_pct: 2.70, volume: 7800000, sector: '电子' },
  { symbol: '300059', name: '东方财富', price: 23.15, change: -0.35, change_pct: -1.49, volume: 15200000, sector: '金融科技' }
])

// 板块表现数据
const sectorPerformance = ref([])
const sectorLoading = ref(true)
const sectorError = ref(false)

// 市场情绪数据
const marketSentiment = ref({
  fear_greed_index: 0,
  advancing_stocks: 0,
  declining_stocks: 0
})
const sentimentLoading = ref(true)
const sentimentError = ref(false)

// 技术指标数据
const technicalIndicators = ref([])
const indicatorsLoading = ref(true)
const indicatorsError = ref(false)

// 市场新闻数据
const marketNews = ref([])
const newsLoading = ref(true)
const newsError = ref(false)

// 表格头部
const stockHeaders = [
  { title: '股票', key: 'name', sortable: false },
  { title: '价格', key: 'price', sortable: true },
  { title: '涨跌', key: 'change', sortable: true },
  { title: '涨跌幅', key: 'change_pct', sortable: true },
  { title: '成交量', key: 'volume', sortable: true },
  { title: '板块', key: 'sector', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

// 计算属性
const sortedHotStocks = computed(() => {
  const stocks = [...hotStocks.value]
  switch (stockSort.value) {
    case 'change':
      return stocks.sort((a, b) => b.change_pct - a.change_pct)
    case 'volume':
      return stocks.sort((a, b) => b.volume - a.volume)
    case 'amount':
      return stocks.sort((a, b) => (b.price * b.volume) - (a.price * a.volume))
    default:
      return stocks
  }
})

const lastUpdateTime = ref('')
let refreshInterval = null

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

function updateLastUpdateTime() {
  const now = new Date()
  lastUpdateTime.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function startAutoRefresh() {
  // 清除旧的定时器
  stopAutoRefresh()
  
  // 检查当前是否在交易时间
  const marketOpen = isMarketOpen()
  
  if (!marketOpen) {
    console.log('⏸️ MarketView - 当前为休市时间，不启动自动刷新')
    // 设置定时器在下一个交易时段检查（每分钟检查一次）
    refreshInterval = setInterval(() => {
      const nowOpen = isMarketOpen()
      if (nowOpen) {
        console.log('🔔 MarketView - 检测到开市，重新启动自动刷新')
        startAutoRefresh() // 递归调用以启动真正的刷新定时器
      }
    }, 60000) // 1分钟检查一次
    return
  }
  
  console.log('▶️ MarketView - 交易时间，启动自动刷新 (15秒间隔)')
  refreshInterval = setInterval(async () => {
    // 每次刷新时都检查是否还在交易时间
    const marketOpen = isMarketOpen()
    
    // 如果已经收市，停止并重新启动（进入等待模式）
    if (!marketOpen) {
      console.log('⏸️ MarketView - 检测到休市，停止自动刷新')
      startAutoRefresh() // 重新调用以进入等待模式
      return
    }
    
    try {
      // 刷新市场数据
      await loadMarketData(true)
      updateLastUpdateTime()
      console.log('✅ MarketView - 实时数据已更新')
    } catch (error) {
      console.error('❌ MarketView - 自动刷新失败:', error)
    }
  }, 15000) // 15秒
}

function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

onMounted(async () => {
  // 加载市场数据（包含指数和热门股票）
  await loadMarketData()
  updateLastUpdateTime()
  
  // 启动自动刷新
  startAutoRefresh()
})

onUnmounted(() => {
  // 组件卸载时清理定时器
  stopAutoRefresh()
})

async function loadMarketData(force = false) {
  try {
    // 设置加载状态
    sectorLoading.value = true
    sentimentLoading.value = true
    indicatorsLoading.value = true
    newsLoading.value = true
    
    // 并行获取所有市场数据，使用 Promise.allSettled 确保部分失败不影响其他
    const results = await Promise.allSettled([
      api.market.getIndices(),
      api.market.getHotStocks(),
      api.market.getSectorAnalysis(),
      api.market.getMarketSentiment(),
      api.market.getTechnicalIndicators(),
      api.market.getMarketNews(10)
    ])
    
    // 更新指数数据
    if (results[0].status === 'fulfilled' && results[0].value.data?.indices) {
      marketIndices.value = results[0].value.data.indices.map(index => ({
        symbol: index.symbol,
        name: index.name,
        value: index.value,
        change: index.change,
        change_pct: index.change_pct
      }))
      console.log('✅ 市场指数数据加载完成:', marketIndices.value.length)
    } else {
      console.warn('⚠️ 市场指数数据加载失败')
    }
    
    // 更新热门股票数据
    if (results[1].status === 'fulfilled' && results[1].value.data?.hot_stocks) {
      hotStocks.value = results[1].value.data.hot_stocks
      console.log('✅ 热门股票数据加载完成:', hotStocks.value.length)
    } else {
      console.warn('⚠️ 热门股票数据加载失败')
    }
    
    // 更新板块分析数据
    sectorLoading.value = false
    if (results[2].status === 'fulfilled' && results[2].value.data?.sectors) {
      sectorPerformance.value = results[2].value.data.sectors
      sectorError.value = false
      console.log('✅ 板块分析数据加载完成:', sectorPerformance.value.length)
    } else {
      sectorError.value = true
      console.warn('⚠️ 板块分析数据加载失败', results[2])
    }
    
    // 更新市场情绪数据
    sentimentLoading.value = false
    if (results[3].status === 'fulfilled' && results[3].value.data) {
      marketSentiment.value = {
        fear_greed_index: results[3].value.data.fear_greed_index,
        advancing_stocks: results[3].value.data.advancing_stocks,
        declining_stocks: results[3].value.data.declining_stocks
      }
      sentimentError.value = false
      console.log('✅ 市场情绪数据加载完成:', marketSentiment.value)
    } else {
      sentimentError.value = true
      console.warn('⚠️ 市场情绪数据加载失败', results[3])
    }
    
    // 更新技术指标数据
    indicatorsLoading.value = false
    if (results[4].status === 'fulfilled' && results[4].value.data?.indicators) {
      technicalIndicators.value = results[4].value.data.indicators
      indicatorsError.value = false
      console.log('✅ 技术指标数据加载完成:', technicalIndicators.value.length)
    } else {
      indicatorsError.value = true
      console.warn('⚠️ 技术指标数据加载失败', results[4])
    }
    
    // 更新市场资讯数据
    newsLoading.value = false
    if (results[5].status === 'fulfilled' && results[5].value.data?.news) {
      marketNews.value = results[5].value.data.news.map(news => ({
        id: news.id,
        title: news.title,
        summary: news.summary,
        time: new Date(news.time),
        type: news.type
      }))
      newsError.value = false
      console.log('✅ 市场资讯数据加载完成:', marketNews.value.length)
    } else {
      newsError.value = true
      console.warn('⚠️ 市场资讯数据加载失败', results[5])
    }
    
    // 统计加载结果
    const successCount = results.filter(r => r.status === 'fulfilled').length
    console.log(`✅ 市场数据加载完成: ${successCount}/6 个API成功`, {
      indices: marketIndices.value.length,
      stocks: hotStocks.value.length,
      sectors: sectorPerformance.value.length,
      indicators: technicalIndicators.value.length,
      news: marketNews.value.length
    })
  } catch (error) {
    console.error('❌ 加载市场数据失败:', error)
    // 设置所有错误状态
    sectorLoading.value = false
    sentimentLoading.value = false
    indicatorsLoading.value = false
    newsLoading.value = false
    sectorError.value = true
    sentimentError.value = true
    indicatorsError.value = true
    newsError.value = true
  }
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

function formatVolume(volume) {
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(1) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(0) + '万'
  }
  return volume.toString()
}

function formatTime(time) {
  const now = new Date()
  const diff = now - time
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  
  if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else {
    return time.toLocaleDateString('zh-CN')
  }
}

// 颜色和标签函数
function getSentimentColor(index) {
  if (index >= 70) return 'error'
  if (index >= 50) return 'warning'
  if (index >= 30) return 'primary'
  return 'success'
}

function getSentimentLabel(index) {
  if (index >= 70) return '极度贪婪'
  if (index >= 50) return '贪婪'
  if (index >= 30) return '中性'
  return '恐慌'
}

function getSectorColor(sector) {
  const colors = {
    '银行': 'primary',
    '房地产': 'warning',
    '食品饮料': 'success',
    '电子': 'info',
    '金融科技': 'secondary'
  }
  return colors[sector] || 'primary'
}

function getStockLogo(symbol) {
  // 这里应该返回实际的股票logo URL
  return `https://logo.clearbit.com/${symbol}.com`
}

// 事件处理
async function refreshData() {
  await loadMarketData()
}

function exportData() {
  // 实现数据导出功能
  console.log('导出市场数据')
}

function viewIndexDetail(index) {
  // 实现查看指数详情功能
  console.log('查看指数详情:', index)
}

function viewStockDetail(stock) {
  // 实现查看股票详情功能
  console.log('查看股票详情:', stock)
}

function viewAllNews() {
  // 跳转到资讯详情页面
  router.push({ name: 'news' })
}
</script>

<style lang="scss" scoped>
.market-view {
  max-width: 1600px;
  margin: 0 auto;
}

.index-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  }
}

// 响应式调整
@media (max-width: 960px) {
  .market-view {
    padding: 1rem !important;
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

.index-card,
.v-card {
  animation: fadeInUp 0.6s ease-out;
}

// 延迟动画
.index-card:nth-child(1) { animation-delay: 0.1s; }
.index-card:nth-child(2) { animation-delay: 0.2s; }
.index-card:nth-child(3) { animation-delay: 0.3s; }
.index-card:nth-child(4) { animation-delay: 0.4s; }

// 表格样式优化
:deep(.v-data-table) {
  .v-data-table__wrapper {
    border-radius: 8px;
  }
  
  .v-data-table__tr {
    &:hover {
      background-color: rgba(var(--v-theme-primary), 0.04) !important;
    }
  }
}

// 进度条样式
:deep(.v-progress-linear) {
  border-radius: 10px;
  overflow: hidden;
}
</style>
