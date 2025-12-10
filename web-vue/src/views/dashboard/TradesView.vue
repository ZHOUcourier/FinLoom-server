<template>
  <v-container fluid class="trades-view pa-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
        <div class="d-flex align-center">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            class="mr-4"
            @click="goBack"
          ></v-btn>
          <div>
            <h1 class="text-h3 font-weight-bold mb-2">交易记录</h1>
            <p class="text-body-1 text-medium-emphasis">查看和管理您的交易历史</p>
          </div>
        </div>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-plus"
            @click="addTrade"
            rounded="pill"
          >
            添加交易
          </v-btn>
        </div>
      </div>
      
      <!-- 交易统计概览 -->
      <v-row class="mb-6">
        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-primary-container">
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="primary">mdi-swap-horizontal</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('totalTrades')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-primary">总交易次数</div>
              <div class="text-h4 font-weight-bold mb-3">
                {{ tradeMetrics.totalTrades }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip size="small" color="primary" variant="flat" class="bg-primary-lighten-4">
                  <v-icon start size="16">mdi-trending-up</v-icon>
                  +{{ tradeMetrics.todayTrades }} 今日
                </v-chip>
                <span class="text-caption text-medium-emphasis">本月</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-success-container">
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="success">mdi-trending-up</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('totalPnl')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-success">总盈亏</div>
              <div class="text-h4 font-weight-bold mb-3">
                ¥{{ formatNumber(tradeMetrics.totalPnl) }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip 
                  size="small" 
                  :color="tradeMetrics.totalPnl >= 0 ? 'success' : 'error'" 
                  variant="flat" 
                  :class="tradeMetrics.totalPnl >= 0 ? 'bg-success-lighten-4' : 'bg-error-lighten-4'"
                >
                  <v-icon start size="16">{{ tradeMetrics.totalPnl >= 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}</v-icon>
                  {{ formatPercent(tradeMetrics.pnlRate) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">收益率</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-info-container">
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="info">mdi-chart-line</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('winRate')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-info">胜率</div>
              <div class="text-h4 font-weight-bold mb-3">
                {{ formatPercent(tradeMetrics.winRate) }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip size="small" color="info" variant="flat" class="bg-info-lighten-4">
                  <v-icon start size="16">mdi-target</v-icon>
                  {{ tradeMetrics.winningTrades }}/{{ tradeMetrics.totalTrades }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">盈利交易</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-warning-container">
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="warning">mdi-currency-usd</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('totalVolume')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-warning">总成交额</div>
              <div class="text-h4 font-weight-bold mb-3">
                ¥{{ formatNumber(tradeMetrics.totalVolume) }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip size="small" color="warning" variant="flat" class="bg-warning-lighten-4">
                  <v-icon start size="16">mdi-chart-areaspline</v-icon>
                  {{ formatNumber(tradeMetrics.avgVolume) }} 平均
                </v-chip>
                <span class="text-caption text-medium-emphasis">本月</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- 交易记录表格 -->
    <v-card variant="elevated">
      <v-card-title class="d-flex align-center justify-space-between pa-6">
        <div class="d-flex align-center">
          <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
            <v-icon>mdi-swap-horizontal</v-icon>
          </v-avatar>
          <div>
            <div class="text-h6 font-weight-bold">交易记录</div>
            <div class="text-caption text-medium-emphasis">所有交易历史</div>
          </div>
        </div>
        <div class="d-flex gap-2">
          <v-btn-toggle v-model="filterType" mandatory>
            <v-btn value="all" size="small">全部</v-btn>
            <v-btn value="buy" size="small">买入</v-btn>
            <v-btn value="sell" size="small">卖出</v-btn>
          </v-btn-toggle>
          <v-btn
            color="primary"
            variant="text"
            size="small"
            @click="sortTrades"
            prepend-icon="mdi-sort"
          >
            排序
        </v-btn>
        </div>
      </v-card-title>
      
      <v-card-text class="pa-0">
        <v-data-table
          :headers="headers"
          :items="filteredTrades"
          :items-per-page="20"
          class="elevation-0"
          :loading="loading"
        >
          <template v-slot:item.time="{ item }">
            <div class="text-body-2">{{ formatTime(item.time) }}</div>
            <div class="text-caption text-medium-emphasis">{{ formatDate(item.time) }}</div>
          </template>

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

          <template v-slot:item.action="{ item }">
            <v-chip 
              :color="item.action === 'BUY' ? 'success' : 'error'" 
              size="small"
              variant="tonal"
            >
              <v-icon start size="16">
                {{ item.action === 'BUY' ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
              </v-icon>
              {{ item.action === 'BUY' ? '买入' : '卖出' }}
            </v-chip>
          </template>

          <template v-slot:item.price="{ item }">
            <div class="font-weight-bold">¥{{ formatNumber(item.price, 2) }}</div>
          </template>

          <template v-slot:item.quantity="{ item }">
            <div class="text-body-2">{{ formatNumber(item.quantity) }}</div>
          </template>

          <template v-slot:item.amount="{ item }">
            <div class="font-weight-bold">¥{{ formatNumber(item.amount) }}</div>
          </template>

          <template v-slot:item.pnl="{ item }">
            <div :class="item.pnl >= 0 ? 'text-success' : 'text-error'" class="font-weight-bold">
              ¥{{ formatNumber(item.pnl, 2) }}
            </div>
            <div :class="item.pnl >= 0 ? 'text-success' : 'text-error'" class="text-caption">
              {{ formatPercent(item.pnlRate) }}
            </div>
          </template>

          <template v-slot:item.status="{ item }">
            <v-chip 
              :color="getStatusColor(item.status)" 
              size="small" 
              variant="tonal"
            >
              {{ getStatusText(item.status) }}
            </v-chip>
          </template>

          <template v-slot:item.actions="{ item }">
            <div class="d-flex gap-1">
              <v-btn
                icon="mdi-chart-line"
                variant="text"
                size="small"
                @click="viewTradeDetail(item)"
              ></v-btn>
              <v-btn
                icon="mdi-pencil"
                variant="text"
                size="small"
                @click="editTrade(item)"
              ></v-btn>
              <v-btn
                icon="mdi-delete"
                variant="text"
                size="small"
                @click="deleteTrade(item)"
              ></v-btn>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'

const router = useRouter()
const dashboardStore = useDashboardStore()
const loading = ref(false)
const filterType = ref('all')

// 交易指标
const tradeMetrics = ref({
  totalTrades: 156,
  todayTrades: 8,
  totalPnl: 125000,
  pnlRate: 0.125,
  winRate: 0.68,
  winningTrades: 106,
  totalVolume: 2500000,
  avgVolume: 16025
})

const headers = [
  { title: '时间', key: 'time', sortable: true },
  { title: '股票', key: 'name', sortable: false },
  { title: '操作', key: 'action', sortable: true },
  { title: '价格', key: 'price', sortable: true },
  { title: '数量', key: 'quantity', sortable: true },
  { title: '金额', key: 'amount', sortable: true },
  { title: '盈亏', key: 'pnl', sortable: true },
  { title: '状态', key: 'status', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

// 计算属性
const filteredTrades = computed(() => {
  let trades = [...dashboardStore.recentTrades]
  
  if (filterType.value === 'buy') {
    trades = trades.filter(trade => trade.action === 'BUY')
  } else if (filterType.value === 'sell') {
    trades = trades.filter(trade => trade.action === 'SELL')
  }
  
  return trades
})

onMounted(() => {
  refreshData()
})

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
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatDate(time) {
  return new Date(time).toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit'
  })
}

function getStockLogo(symbol) {
  return `https://logo.clearbit.com/${symbol}.com`
}

function getStatusColor(status) {
  const colors = {
    'COMPLETED': 'success',
    'PENDING': 'warning',
    'CANCELLED': 'error',
    'FAILED': 'error'
  }
  return colors[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    'COMPLETED': '已完成',
    'PENDING': '待处理',
    'CANCELLED': '已取消',
    'FAILED': '失败'
  }
  return texts[status] || status
}

// 事件处理
async function refreshData() {
  loading.value = true
  try {
    await dashboardStore.fetchRecentTrades()
  } finally {
    loading.value = false
  }
}

function exportTrades() {
  // 实现导出交易记录功能
  console.log('导出交易记录')
}

function addTrade() {
  // 实现添加交易功能
  console.log('添加交易')
}

function viewDetails(type) {
  // 实现查看详情功能
  console.log('查看详情:', type)
}

function viewTradeDetail(trade) {
  // 实现查看交易详情功能
  console.log('查看交易详情:', trade)
}

function editTrade(trade) {
  // 实现编辑交易功能
  console.log('编辑交易:', trade)
}

function deleteTrade(trade) {
  // 实现删除交易功能
  console.log('删除交易:', trade)
}

function sortTrades() {
  // 实现排序功能
  console.log('排序交易')
}

function goBack() {
  router.push('/dashboard')
}
</script>

<style lang="scss" scoped>
.trades-view {
  max-width: 1600px;
  margin: 0 auto;
}

.metric-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  }
}

// 响应式调整
@media (max-width: 960px) {
  .trades-view {
    padding: 1rem !important;
  }
}

// 自定义滚动条
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
.v-card {
  animation: fadeInUp 0.6s ease-out;
}

// 延迟动画
.metric-card:nth-child(1) { animation-delay: 0.1s; }
.metric-card:nth-child(2) { animation-delay: 0.2s; }
.metric-card:nth-child(3) { animation-delay: 0.3s; }
.metric-card:nth-child(4) { animation-delay: 0.4s; }
</style>
