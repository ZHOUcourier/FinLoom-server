<template>
  <v-container fluid class="portfolio-view pa-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
      <div>
        <h1 class="text-h3 font-weight-bold mb-2">投资组合</h1>
          <p class="text-body-1 text-medium-emphasis">管理您的投资组合和持仓</p>
        </div>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-plus"
            @click="addPosition"
            rounded="pill"
          >
            添加持仓
          </v-btn>
        </div>
      </div>
      
      <!-- 投资组合概览 -->
      <v-row class="mb-6">
        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-primary-container">
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="primary">mdi-wallet</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('totalValue')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-primary">总市值</div>
              <div class="text-h4 font-weight-bold mb-3">
                ¥{{ formatNumber(portfolioMetrics.totalValue) }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip 
                  size="small" 
                  :color="portfolioMetrics.totalChange >= 0 ? 'success' : 'error'" 
                  variant="flat" 
                  :class="portfolioMetrics.totalChange >= 0 ? 'bg-success-lighten-4' : 'bg-error-lighten-4'"
                >
                  <v-icon start size="16">{{ portfolioMetrics.totalChange >= 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}</v-icon>
                  {{ formatPercent(portfolioMetrics.totalChange) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">vs 昨日</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-secondary-container">
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="secondary">mdi-trending-up</v-icon>
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
              <div class="text-caption mb-1 text-secondary">总盈亏</div>
              <div class="text-h4 font-weight-bold mb-3">
                ¥{{ formatNumber(portfolioMetrics.totalPnl) }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip 
                  size="small" 
                  :color="portfolioMetrics.totalPnl >= 0 ? 'success' : 'error'" 
                  variant="flat" 
                  :class="portfolioMetrics.totalPnl >= 0 ? 'bg-success-lighten-4' : 'bg-error-lighten-4'"
                >
                  <v-icon start size="16">{{ portfolioMetrics.totalPnl >= 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}</v-icon>
                  {{ formatPercent(portfolioMetrics.totalPnlRate) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">收益率</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-tertiary-container">
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="tertiary">mdi-chart-pie</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('positions')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-tertiary">持仓数量</div>
              <div class="text-h4 font-weight-bold mb-3">
                {{ portfolioMetrics.positionCount }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip size="small" color="tertiary" variant="flat" class="bg-tertiary-lighten-4">
                  <v-icon start size="16">mdi-package-variant</v-icon>
                  {{ portfolioMetrics.sectorCount }}个板块
                </v-chip>
                <span class="text-caption text-medium-emphasis">分散投资</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card variant="elevated" class="metric-card bg-success-container">
            <v-card-text class="pa-6">
              <div class="d-flex justify-space-between align-start mb-4">
                <v-icon size="48" color="success">mdi-shield-check</v-icon>
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                  </template>
                  <v-list>
                    <v-list-item @click="viewDetails('risk')">
                      <v-list-item-title>查看详情</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
              <div class="text-caption mb-1 text-success">风险等级</div>
              <div class="text-h4 font-weight-bold mb-3">
                {{ portfolioMetrics.riskLevel }}
              </div>
              <div class="d-flex align-center justify-space-between">
                <v-chip 
                  size="small" 
                  :color="getRiskColor(portfolioMetrics.riskScore)" 
                  variant="flat" 
                  :class="getRiskColor(portfolioMetrics.riskScore) + '-lighten-4'"
                >
                  <v-icon start size="16">{{ getRiskIcon(portfolioMetrics.riskScore) }}</v-icon>
                  {{ getRiskLabel(portfolioMetrics.riskScore) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">风险评估</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

      <!-- 持仓列表和图表 -->
      <v-row>
        <!-- 持仓列表 -->
        <v-col cols="12" md="8">
          <v-card variant="elevated" class="mb-6">
            <v-card-title class="d-flex align-center justify-space-between pa-6">
              <div class="d-flex align-center">
                <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
                  <v-icon>mdi-package-variant</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold">持仓列表</div>
                  <div class="text-caption text-medium-emphasis">当前持有的股票</div>
                </div>
              </div>
              <div class="d-flex gap-2">
                <v-btn-toggle v-model="viewMode" mandatory>
                  <v-btn value="grid" size="small" icon="mdi-view-grid"></v-btn>
                  <v-btn value="list" size="small" icon="mdi-view-list"></v-btn>
                </v-btn-toggle>
      <v-btn 
        color="primary" 
                  variant="text"
                  size="small"
                  @click="sortPositions"
                  prepend-icon="mdi-sort"
                >
                  排序
      </v-btn>
    </div>
            </v-card-title>
            <v-card-text class="pa-0">
              <!-- 网格视图 -->
              <div v-if="viewMode === 'grid'" class="pa-6">
    <v-row>
      <v-col 
                    v-for="position in sortedPositions" 
        :key="position.symbol"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
                    <v-card variant="outlined" class="position-card" hover @click="viewPositionDetail(position)">
          <v-card-title class="d-flex justify-space-between align-start pa-4 pb-2">
                        <div class="flex-1">
              <div class="text-h6 font-weight-bold">{{ position.name }}</div>
              <div class="text-caption text-medium-emphasis">{{ position.symbol }}</div>
            </div>
                        <v-menu>
                          <template v-slot:activator="{ props }">
                            <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props" @click.stop></v-btn>
                          </template>
                          <v-list>
                            <v-list-item @click="editPosition(position)">
                              <v-list-item-title>编辑</v-list-item-title>
                            </v-list-item>
                            <v-list-item @click="sellPosition(position)">
                              <v-list-item-title>卖出</v-list-item-title>
                            </v-list-item>
                            <v-list-item @click="setAlert(position)">
                              <v-list-item-title>设置预警</v-list-item-title>
                            </v-list-item>
                          </v-list>
                        </v-menu>
          </v-card-title>

                      <v-card-text class="pa-4 pt-0">
            <v-list density="compact" class="pa-0">
              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon color="grey" size="small">mdi-package-variant</v-icon>
                </template>
                <v-list-item-title class="text-caption">持仓量</v-list-item-title>
                <template v-slot:append>
                  <span class="font-weight-bold">{{ position.quantity }}</span>
                </template>
              </v-list-item>

              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon color="grey" size="small">mdi-currency-usd</v-icon>
                </template>
                <v-list-item-title class="text-caption">成本价</v-list-item-title>
                <template v-slot:append>
                              <span class="font-weight-bold">¥{{ formatNumber(position.cost_price, 2) }}</span>
                </template>
              </v-list-item>

              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon color="grey" size="small">mdi-chart-line</v-icon>
                </template>
                <v-list-item-title class="text-caption">现价</v-list-item-title>
                <template v-slot:append>
                              <span class="font-weight-bold">¥{{ formatNumber(position.current_price, 2) }}</span>
                </template>
              </v-list-item>

              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon color="grey" size="small">mdi-wallet</v-icon>
                </template>
                <v-list-item-title class="text-caption">市值</v-list-item-title>
                <template v-slot:append>
                              <span class="font-weight-bold">¥{{ formatNumber(position.market_value) }}</span>
                </template>
              </v-list-item>

              <v-divider class="my-2"></v-divider>

              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon :color="position.unrealized_pnl > 0 ? 'success' : 'error'" size="small">
                    {{ position.unrealized_pnl > 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}
                  </v-icon>
                </template>
                <v-list-item-title class="text-caption">收益</v-list-item-title>
                <template v-slot:append>
                  <div class="text-end">
                    <div :class="position.unrealized_pnl > 0 ? 'text-success' : 'text-error'" class="font-weight-bold">
                                  ¥{{ formatNumber(position.unrealized_pnl, 2) }}
                    </div>
                    <div :class="position.unrealized_pnl > 0 ? 'text-success' : 'text-error'" class="text-caption">
                                  {{ formatPercent(position.pnl_rate) }}
                    </div>
                              </div>
                            </template>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </div>

              <!-- 列表视图 -->
              <v-data-table
                v-else
                :headers="positionHeaders"
                :items="sortedPositions"
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
                
                <template v-slot:item.sector="{ item }">
                  <v-chip size="small" :color="getSectorColor(item.sector)" variant="tonal">
                    {{ item.sector }}
                  </v-chip>
                </template>
                
                <template v-slot:item.current_price="{ item }">
                  <div class="font-weight-bold">¥{{ formatNumber(item.current_price, 2) }}</div>
                </template>
                
                <template v-slot:item.market_value="{ item }">
                  <div class="font-weight-bold">¥{{ formatNumber(item.market_value) }}</div>
                </template>
                
                <template v-slot:item.unrealized_pnl="{ item }">
                  <div :class="item.unrealized_pnl > 0 ? 'text-success' : 'text-error'" class="font-weight-bold">
                    ¥{{ formatNumber(item.unrealized_pnl, 2) }}
                  </div>
                </template>
                
                <template v-slot:item.pnl_rate="{ item }">
                  <v-chip 
                    :color="item.pnl_rate >= 0 ? 'success' : 'error'" 
                    size="small" 
                    variant="tonal"
                  >
                    {{ formatPercent(item.pnl_rate) }}
                  </v-chip>
                </template>
                
                <template v-slot:item.actions="{ item }">
                  <div class="d-flex gap-1">
                    <v-btn
                      icon="mdi-chart-line"
                      variant="text"
                      size="small"
                      @click="viewPositionDetail(item)"
                    ></v-btn>
                    <v-btn
                      icon="mdi-pencil"
                      variant="text"
                      size="small"
                      @click="editPosition(item)"
                    ></v-btn>
                    <v-btn
                      icon="mdi-delete"
                      variant="text"
                      size="small"
                      @click="deletePosition(item)"
                    ></v-btn>
                  </div>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 投资组合分析 -->
        <v-col cols="12" md="4">
          <v-card variant="elevated" class="mb-6">
            <v-card-title class="d-flex align-center pa-6">
              <v-avatar color="info" variant="tonal" size="40" class="mr-3">
                <v-icon>mdi-chart-donut</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">资产配置</div>
                <div class="text-caption text-medium-emphasis">按板块分布</div>
              </div>
            </v-card-title>
            <v-card-text class="pa-6">
              <div class="chart-container">
                <canvas ref="allocationChartRef"></canvas>
              </div>
            </v-card-text>
          </v-card>

          <v-card variant="elevated">
            <v-card-title class="d-flex align-center pa-6">
              <v-avatar color="warning" variant="tonal" size="40" class="mr-3">
                <v-icon>mdi-chart-line-variant</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">表现分析</div>
                <div class="text-caption text-medium-emphasis">投资组合表现</div>
              </div>
            </v-card-title>
            <v-card-text class="pa-6">
              <v-list density="compact">
                <v-list-item
                  v-for="metric in performanceMetrics"
                  :key="metric.name"
                  class="px-0"
                >
                  <template v-slot:prepend>
                    <v-avatar :color="metric.color" size="32" variant="tonal">
                      <v-icon size="16">{{ metric.icon }}</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title class="text-body-2 font-weight-medium">{{ metric.name }}</v-list-item-title>
                  <template v-slot:append>
                    <div class="text-end">
                      <div :class="metric.value >= 0 ? 'text-success' : 'text-error'" class="font-weight-bold">
                        {{ metric.value >= 0 ? '+' : '' }}{{ formatNumber(metric.value, 2) }}{{ metric.unit }}
                      </div>
                      <div class="text-caption text-medium-emphasis">{{ metric.description }}</div>
                  </div>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-alert v-if="dashboardStore.positions.length === 0" type="info" variant="tonal" class="mt-4">
        <template v-slot:prepend>
          <v-icon>mdi-information</v-icon>
        </template>
        <div>
          <div class="font-weight-bold mb-2">暂无持仓数据</div>
          <div>开始您的投资之旅，添加第一只股票到投资组合中</div>
          <v-btn color="primary" variant="flat" class="mt-3" @click="addPosition">
            添加持仓
          </v-btn>
        </div>
    </v-alert>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import Chart from 'chart.js/auto'

const dashboardStore = useDashboardStore()
const loading = ref(false)
const viewMode = ref('grid')
const sortBy = ref('market_value')
const sortOrder = ref('desc')
const allocationChartRef = ref(null)

// 投资组合指标
const portfolioMetrics = ref({
  totalValue: 1250000,
  totalChange: 0.025,
  totalPnl: 31250,
  totalPnlRate: 0.025,
  positionCount: 8,
  sectorCount: 5,
  riskLevel: '中等',
  riskScore: 65
})

// 表现指标
const performanceMetrics = ref([
  { name: '夏普比率', value: 1.85, unit: '', color: 'success', icon: 'mdi-chart-line', description: '风险调整收益' },
  { name: '最大回撤', value: -8.5, unit: '%', color: 'error', icon: 'mdi-trending-down', description: '历史最大亏损' },
  { name: '波动率', value: 18.2, unit: '%', color: 'warning', icon: 'mdi-chart-scatter-plot', description: '年化波动率' },
  { name: 'Beta系数', value: 1.12, unit: '', color: 'info', icon: 'mdi-scale-balance', description: '相对市场风险' }
])

// 表格头部
const positionHeaders = [
  { title: '股票', key: 'name', sortable: false },
  { title: '板块', key: 'sector', sortable: true },
  { title: '现价', key: 'current_price', sortable: true },
  { title: '市值', key: 'market_value', sortable: true },
  { title: '盈亏', key: 'unrealized_pnl', sortable: true },
  { title: '收益率', key: 'pnl_rate', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

let allocationChart = null

onMounted(() => {
  dashboardStore.fetchPositions()
  initAllocationChart()
})

watch(() => dashboardStore.positions, () => {
  updateAllocationChart()
  updatePortfolioMetrics()
}, { deep: true })

// 计算属性
const sortedPositions = computed(() => {
  const positions = [...dashboardStore.positions]
  return positions.sort((a, b) => {
    const aValue = a[sortBy.value] || 0
    const bValue = b[sortBy.value] || 0
    
    if (sortOrder.value === 'asc') {
      return aValue - bValue
    } else {
      return bValue - aValue
    }
  })
})

// 初始化资产配置图表
function initAllocationChart() {
  if (allocationChartRef.value) {
    allocationChart = new Chart(allocationChartRef.value, {
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
    updateAllocationChart()
  }
}

function updateAllocationChart() {
  if (!allocationChart || dashboardStore.positions.length === 0) return

  // 按板块分组计算市值
  const sectorData = {}
  dashboardStore.positions.forEach(position => {
    const sector = position.sector || '其他'
    if (!sectorData[sector]) {
      sectorData[sector] = 0
    }
    sectorData[sector] += position.market_value || 0
  })

  allocationChart.data.labels = Object.keys(sectorData)
  allocationChart.data.datasets[0].data = Object.values(sectorData)
  allocationChart.update()
}

function updatePortfolioMetrics() {
  const positions = dashboardStore.positions
  if (positions.length === 0) return

  // 计算总市值
  const totalValue = positions.reduce((sum, pos) => sum + (pos.market_value || 0), 0)
  
  // 计算总盈亏
  const totalPnl = positions.reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0)
  
  // 计算收益率
  const totalCost = positions.reduce((sum, pos) => sum + ((pos.cost_price || 0) * (pos.quantity || 0)), 0)
  const totalPnlRate = totalCost > 0 ? totalPnl / totalCost : 0
  
  // 计算板块数量
  const sectors = new Set(positions.map(pos => pos.sector).filter(Boolean))
  
  // 更新指标
  portfolioMetrics.value = {
    ...portfolioMetrics.value,
    totalValue,
    totalPnl,
    totalPnlRate,
    positionCount: positions.length,
    sectorCount: sectors.size
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

function getSectorColor(sector) {
  const colors = {
    '科技': 'primary',
    '金融': 'info',
    '医药': 'success',
    '消费': 'warning',
    '能源': 'error',
    '房地产': 'secondary',
    '其他': 'grey'
  }
  return colors[sector] || 'primary'
}

function getStockLogo(symbol) {
  return `https://logo.clearbit.com/${symbol}.com`
}

function getRiskColor(score) {
  if (score >= 80) return 'error'
  if (score >= 60) return 'warning'
  if (score >= 40) return 'primary'
  return 'success'
}

function getRiskIcon(score) {
  if (score >= 80) return 'mdi-alert-circle'
  if (score >= 60) return 'mdi-alert'
  if (score >= 40) return 'mdi-shield'
  return 'mdi-shield-check'
}

function getRiskLabel(score) {
  if (score >= 80) return '高风险'
  if (score >= 60) return '中高风险'
  if (score >= 40) return '中等风险'
  return '低风险'
}

// 事件处理
async function refreshData() {
  loading.value = true
  try {
    await dashboardStore.fetchPositions()
  } finally {
    loading.value = false
  }
}

function addPosition() {
  // 实现添加持仓功能
  console.log('添加持仓')
}

function exportPortfolio() {
  // 实现导出投资组合功能
  console.log('导出投资组合')
}

function viewDetails(type) {
  // 实现查看详情功能
  console.log('查看详情:', type)
}

function viewPositionDetail(position) {
  // 实现查看持仓详情功能
  console.log('查看持仓详情:', position)
}

function editPosition(position) {
  // 实现编辑持仓功能
  console.log('编辑持仓:', position)
}

function sellPosition(position) {
  // 实现卖出持仓功能
  console.log('卖出持仓:', position)
}

function deletePosition(position) {
  // 实现删除持仓功能
  console.log('删除持仓:', position)
}

function setAlert(position) {
  // 实现设置预警功能
  console.log('设置预警:', position)
}

function sortPositions() {
  // 实现排序功能
  console.log('排序持仓')
}
</script>

<style lang="scss" scoped>
.portfolio-view {
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

.position-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  }
}

.chart-container {
  height: 300px;
  position: relative;
}

// 响应式调整
@media (max-width: 960px) {
  .portfolio-view {
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
.position-card,
.v-card {
  animation: fadeInUp 0.6s ease-out;
}

// 延迟动画
.metric-card:nth-child(1) { animation-delay: 0.1s; }
.metric-card:nth-child(2) { animation-delay: 0.2s; }
.metric-card:nth-child(3) { animation-delay: 0.3s; }
.metric-card:nth-child(4) { animation-delay: 0.4s; }

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
</style>
