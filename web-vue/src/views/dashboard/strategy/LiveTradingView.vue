<template>
  <v-container fluid class="live-trading-view pa-6">
    <!-- 页面标题 -->
    <div class="d-flex align-center mb-6">
      <v-icon size="40" class="mr-4 text-primary">mdi-chart-line</v-icon>
      <div>
        <h1 class="text-h4 font-weight-bold">实盘运行管理</h1>
        <p class="text-body-1 text-medium-emphasis">监控和管理您的实盘策略</p>
      </div>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        size="large"
        prepend-icon="mdi-refresh"
        rounded="pill"
        variant="flat"
        @click="refreshData"
        :loading="isLoading"
      >
        刷新数据
      </v-btn>
    </div>

    <!-- 统计卡片 -->
    <v-row class="mb-6">
      <v-col cols="12" md="3">
        <v-card rounded="xl" color="primary" dark>
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between mb-2">
              <v-icon size="32">mdi-check-circle</v-icon>
              <span class="text-h4 font-weight-bold">{{ stats.activeCount }}</span>
            </div>
            <div class="text-subtitle-1">活跃策略</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card rounded="xl" color="success" dark>
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between mb-2">
              <v-icon size="32">mdi-trending-up</v-icon>
              <span class="text-h4 font-weight-bold">{{ formatPnl(stats.totalPnl) }}</span>
            </div>
            <div class="text-subtitle-1">总收益 (¥)</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card rounded="xl" color="info" dark>
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between mb-2">
              <v-icon size="32">mdi-briefcase</v-icon>
              <span class="text-h4 font-weight-bold">{{ stats.totalPositions }}</span>
            </div>
            <div class="text-subtitle-1">持仓股票</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card rounded="xl" color="warning" dark>
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between mb-2">
              <v-icon size="32">mdi-swap-horizontal</v-icon>
              <span class="text-h4 font-weight-bold">{{ stats.totalTrades }}</span>
            </div>
            <div class="text-subtitle-1">交易次数</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 策略列表 -->
    <v-card rounded="xl">
      <v-card-title class="text-h5 font-weight-medium pa-6">
        <v-icon start size="24">mdi-format-list-bulleted</v-icon>
        活跃策略列表
      </v-card-title>
      <v-divider></v-divider>
      
      <v-card-text v-if="isLoading" class="pa-10 text-center">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        <p class="mt-4 text-body-1">加载中...</p>
      </v-card-text>

      <v-card-text v-else-if="strategies.length === 0" class="pa-10 text-center">
        <v-icon size="64" color="grey-lighten-1">mdi-inbox</v-icon>
        <p class="mt-4 text-h6 text-medium-emphasis">暂无活跃策略</p>
        <p class="text-body-2 text-medium-emphasis">前往策略生成页面创建并激活策略</p>
        <v-btn
          color="primary"
          class="mt-4"
          prepend-icon="mdi-plus"
          rounded="pill"
          to="/dashboard/strategy"
        >
          创建策略
        </v-btn>
      </v-card-text>

      <v-card-text v-else class="pa-0">
        <v-list>
          <v-list-item
            v-for="strategy in strategies"
            :key="strategy.strategyId"
            class="pa-6"
          >
            <template v-slot:prepend>
              <v-avatar :color="getStatusColor(strategy.status)" size="48">
                <v-icon color="white">{{ getStatusIcon(strategy.status) }}</v-icon>
              </v-avatar>
            </template>

            <v-list-item-title class="text-h6 font-weight-medium mb-2">
              {{ strategy.strategyName || `策略 ${strategy.strategyId.slice(0, 8)}` }}
            </v-list-item-title>
            
            <v-list-item-subtitle class="mb-3">
              <v-chip size="small" :color="getStatusColor(strategy.status)" variant="outlined" class="mr-2">
                {{ getStatusText(strategy.status) }}
              </v-chip>
              激活时间: {{ formatDate(strategy.activatedAt) }}
            </v-list-item-subtitle>

            <div class="d-flex flex-wrap gap-4 mt-3">
              <div>
                <div class="text-caption text-medium-emphasis">当前资金</div>
                <div class="text-body-1 font-weight-medium">¥{{ formatNumber(strategy.currentCapital) }}</div>
              </div>
              <div>
                <div class="text-caption text-medium-emphasis">总收益</div>
                <div class="text-body-1 font-weight-medium" :class="strategy.totalPnl >= 0 ? 'text-success' : 'text-error'">
                  ¥{{ formatPnl(strategy.totalPnl) }} ({{ (strategy.totalPnlPct * 100).toFixed(2) }}%)
                </div>
              </div>
              <div>
                <div class="text-caption text-medium-emphasis">持仓</div>
                <div class="text-body-1 font-weight-medium">{{ strategy.activePositions }} 只</div>
              </div>
              <div>
                <div class="text-caption text-medium-emphasis">交易次数</div>
                <div class="text-body-1 font-weight-medium">{{ strategy.totalTrades }}</div>
              </div>
              <div>
                <div class="text-caption text-medium-emphasis">最后运行</div>
                <div class="text-body-1 font-weight-medium">{{ formatDate(strategy.lastRunAt) || '未运行' }}</div>
              </div>
            </div>

            <template v-slot:append>
              <div class="d-flex flex-column gap-2">
                <v-btn
                  v-if="strategy.status === 'active'"
                  color="warning"
                  variant="outlined"
                  size="small"
                  prepend-icon="mdi-pause"
                  @click="pauseStrategy(strategy.strategyId)"
                  :loading="actionLoading[strategy.strategyId]"
                >
                  暂停
                </v-btn>
                <v-btn
                  v-if="strategy.status === 'paused'"
                  color="success"
                  variant="outlined"
                  size="small"
                  prepend-icon="mdi-play"
                  @click="resumeStrategy(strategy.strategyId)"
                  :loading="actionLoading[strategy.strategyId]"
                >
                  恢复
                </v-btn>
                <v-btn
                  color="error"
                  variant="outlined"
                  size="small"
                  prepend-icon="mdi-stop"
                  @click="stopStrategy(strategy.strategyId)"
                  :loading="actionLoading[strategy.strategyId]"
                >
                  停止
                </v-btn>
                <v-btn
                  color="primary"
                  variant="text"
                  size="small"
                  prepend-icon="mdi-information"
                  @click="viewDetails(strategy)"
                >
                  详情
                </v-btn>
              </div>
            </template>
          </v-list-item>
          <v-divider v-if="index < strategies.length - 1" :key="`divider-${strategy.strategyId}`"></v-divider>
        </v-list>
      </v-card-text>
    </v-card>

    <!-- 手动运行每日任务按钮 -->
    <v-card rounded="xl" class="mt-6">
      <v-card-title class="text-h5 font-weight-medium pa-6">
        <v-icon start size="24">mdi-cog</v-icon>
        手动操作
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <p class="text-body-1 mb-4">手动触发每日任务，为所有活跃策略生成交易信号并执行交易。</p>
        <v-btn
          color="primary"
          size="large"
          prepend-icon="mdi-play-circle"
          rounded="pill"
          variant="flat"
          @click="runDailyTask"
          :loading="isDailyTaskRunning"
        >
          运行每日任务
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- 策略详情对话框 -->
    <v-dialog v-model="detailsDialog" max-width="800">
      <v-card rounded="xl" v-if="selectedStrategy">
        <v-card-title class="text-h5 font-weight-medium pa-6">
          <v-icon start>mdi-information</v-icon>
          策略详情
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-list density="comfortable">
            <v-list-item>
              <v-list-item-title class="font-weight-medium">策略ID</v-list-item-title>
              <v-list-item-subtitle>{{ selectedStrategy.strategyId }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="font-weight-medium">状态</v-list-item-title>
              <v-list-item-subtitle>
                <v-chip size="small" :color="getStatusColor(selectedStrategy.status)">
                  {{ getStatusText(selectedStrategy.status) }}
                </v-chip>
              </v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="font-weight-medium">激活时间</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(selectedStrategy.activatedAt) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="font-weight-medium">最后运行</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(selectedStrategy.lastRunAt) || '未运行' }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="font-weight-medium">当前资金</v-list-item-title>
              <v-list-item-subtitle>¥{{ formatNumber(selectedStrategy.currentCapital) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="font-weight-medium">总收益</v-list-item-title>
              <v-list-item-subtitle :class="selectedStrategy.totalPnl >= 0 ? 'text-success' : 'text-error'">
                ¥{{ formatPnl(selectedStrategy.totalPnl) }} ({{ (selectedStrategy.totalPnlPct * 100).toFixed(2) }}%)
              </v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="font-weight-medium">持仓股票数</v-list-item-title>
              <v-list-item-subtitle>{{ selectedStrategy.activePositions }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="font-weight-medium">交易次数</v-list-item-title>
              <v-list-item-subtitle>{{ selectedStrategy.totalTrades }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions class="pa-6">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="detailsDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '@/services'

const isLoading = ref(false)
const isDailyTaskRunning = ref(false)
const strategies = ref([])
const actionLoading = ref({})
const detailsDialog = ref(false)
const selectedStrategy = ref(null)

const stats = ref({
  activeCount: 0,
  totalPnl: 0,
  totalPositions: 0,
  totalTrades: 0
})

let refreshInterval = null

onMounted(async () => {
  await loadStrategies()
  // 每30秒自动刷新
  refreshInterval = setInterval(loadStrategies, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

async function loadStrategies() {
  isLoading.value = true
  try {
    const data = await api.strategy.live.listActive()
    strategies.value = data
    calculateStats()
  } catch (error) {
    console.error('加载策略列表失败:', error)
  } finally {
    isLoading.value = false
  }
}

function calculateStats() {
  stats.value.activeCount = strategies.value.filter(s => s.status === 'active').length
  stats.value.totalPnl = strategies.value.reduce((sum, s) => sum + (s.totalPnl || 0), 0)
  stats.value.totalPositions = strategies.value.reduce((sum, s) => sum + (s.activePositions || 0), 0)
  stats.value.totalTrades = strategies.value.reduce((sum, s) => sum + (s.totalTrades || 0), 0)
}

async function refreshData() {
  await loadStrategies()
}

async function pauseStrategy(strategyId) {
  actionLoading.value[strategyId] = true
  try {
    await api.strategy.live.pause(strategyId)
    await loadStrategies()
  } catch (error) {
    console.error('暂停策略失败:', error)
    alert(error?.message || '暂停策略失败')
  } finally {
    actionLoading.value[strategyId] = false
  }
}

async function resumeStrategy(strategyId) {
  actionLoading.value[strategyId] = true
  try {
    await api.strategy.live.resume(strategyId)
    await loadStrategies()
  } catch (error) {
    console.error('恢复策略失败:', error)
    alert(error?.message || '恢复策略失败')
  } finally {
    actionLoading.value[strategyId] = false
  }
}

async function stopStrategy(strategyId) {
  if (!confirm('确定要停止此策略吗？停止后将无法恢复。')) {
    return
  }
  
  actionLoading.value[strategyId] = true
  try {
    await api.strategy.live.stop(strategyId)
    await loadStrategies()
  } catch (error) {
    console.error('停止策略失败:', error)
    alert(error?.message || '停止策略失败')
  } finally {
    actionLoading.value[strategyId] = false
  }
}

function viewDetails(strategy) {
  selectedStrategy.value = strategy
  detailsDialog.value = true
}

async function runDailyTask() {
  if (!confirm('确定要手动运行每日任务吗？这将为所有活跃策略生成交易信号。')) {
    return
  }

  isDailyTaskRunning.value = true
  try {
    const result = await api.strategy.live.runDaily()
    alert('每日任务执行成功！')
    await loadStrategies()
  } catch (error) {
    console.error('执行每日任务失败:', error)
    alert(error?.message || '执行每日任务失败')
  } finally {
    isDailyTaskRunning.value = false
  }
}

function getStatusColor(status) {
  const colorMap = {
    active: 'success',
    paused: 'warning',
    stopped: 'error',
    error: 'error',
    inactive: 'grey'
  }
  return colorMap[status] || 'grey'
}

function getStatusIcon(status) {
  const iconMap = {
    active: 'mdi-play-circle',
    paused: 'mdi-pause-circle',
    stopped: 'mdi-stop-circle',
    error: 'mdi-alert-circle',
    inactive: 'mdi-circle-outline'
  }
  return iconMap[status] || 'mdi-help-circle'
}

function getStatusText(status) {
  const textMap = {
    active: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    error: '错误',
    inactive: '未激活'
  }
  return textMap[status] || '未知'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatPnl(pnl) {
  if (pnl === null || pnl === undefined) return '0.00'
  const sign = pnl >= 0 ? '+' : ''
  return sign + pnl.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}

.gap-4 {
  gap: 16px;
}
</style>
