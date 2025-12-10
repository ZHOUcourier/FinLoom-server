<template>
  <v-container fluid class="backtest-view pa-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
          <h1 class="text-h3 font-weight-bold mb-2">策略回测</h1>
          <p class="text-body-1 text-medium-emphasis">测试您的交易策略历史表现</p>
        </div>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-plus"
            @click="createNewBacktest"
            rounded="pill"
          >
            新建回测
          </v-btn>
        </div>
      </div>
    </div>

    <!-- 回测配置和结果 -->
    <v-row>
      <!-- 回测配置 -->
      <v-col cols="12" md="4">
        <v-card variant="elevated" class="mb-6">
          <v-card-title class="d-flex align-center pa-6">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-cog</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">回测配置</div>
              <div class="text-caption text-medium-emphasis">设置策略参数</div>
            </div>
          </v-card-title>
          <v-card-text class="pa-6">
            <v-form @submit.prevent="runBacktest">
              <v-text-field
                v-model="config.symbol"
                label="股票代码"
                prepend-inner-icon="mdi-chart-candlestick"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                placeholder="例如: 000001"
                hint="输入股票代码，如000001"
                persistent-hint
              ></v-text-field>

              <v-select
                v-model="config.strategy"
                :items="strategyOptions"
                label="策略类型"
                prepend-inner-icon="mdi-strategy"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                hint="选择要测试的交易策略"
                persistent-hint
              ></v-select>

              <v-row>
                <v-col cols="6">
                  <v-text-field
                    v-model="config.start_date"
                    label="开始日期"
                    type="date"
                    prepend-inner-icon="mdi-calendar-start"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                  ></v-text-field>
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="config.end_date"
                    label="结束日期"
                    type="date"
                    prepend-inner-icon="mdi-calendar-end"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-text-field
                v-model.number="config.initial_capital"
                label="初始资金"
                type="number"
                prepend-inner-icon="mdi-currency-usd"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                step="1000"
                hint="设置回测的初始资金"
                persistent-hint
              ></v-text-field>

              <v-text-field
                v-model.number="config.commission"
                label="手续费率"
                type="number"
                prepend-inner-icon="mdi-percent"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                step="0.001"
                hint="交易手续费率，如0.001表示0.1%"
                persistent-hint
              ></v-text-field>

              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                prepend-icon="mdi-play"
                rounded="lg"
              >
                开始回测
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- 历史回测记录 -->
        <v-card variant="elevated">
          <v-card-title class="d-flex align-center pa-6">
            <v-avatar color="info" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-history</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">历史回测</div>
              <div class="text-caption text-medium-emphasis">查看之前的回测结果</div>
            </div>
          </v-card-title>
          <v-card-text class="pa-6">
            <v-list density="compact">
              <v-list-item
                v-for="(record, index) in backtestHistory"
                :key="index"
                @click="loadBacktestRecord(record)"
                class="mb-2"
              >
                <template v-slot:prepend>
                  <v-avatar color="primary" size="32" variant="tonal">
                    <v-icon size="16">mdi-chart-line</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2">{{ record.strategy }} - {{ record.symbol }}</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ record.date }} | 收益: {{ record.return }}%
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    icon="mdi-delete"
                    variant="text"
                    size="small"
                    @click.stop="deleteBacktestRecord(index)"
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card v-if="result" variant="elevated">
          <v-card-title class="d-flex align-center pa-4">
            <v-avatar color="success" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-chart-areaspline</v-icon>
            </v-avatar>
            <span class="text-h6 font-weight-bold">回测结果</span>
          </v-card-title>
          <v-card-text>
            <v-row class="mb-4">
              <v-col cols="12" sm="6" md="3">
                <v-card variant="flat" class="bg-primary-container">
                  <v-card-text class="text-center pa-4">
                    <div class="text-h5 font-weight-bold">{{ result.total_return?.toFixed(2) }}%</div>
                    <div class="text-caption">总收益率</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="flat" class="bg-secondary-container">
                  <v-card-text class="text-center pa-4">
                    <div class="text-h5 font-weight-bold">{{ result.annualized_return?.toFixed(2) }}%</div>
                    <div class="text-caption">年化收益</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="flat" class="bg-tertiary-container">
                  <v-card-text class="text-center pa-4">
                    <div class="text-h5 font-weight-bold">{{ result.sharpe_ratio?.toFixed(2) }}</div>
                    <div class="text-caption">夏普比率</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="flat" class="bg-error-container">
                  <v-card-text class="text-center pa-4">
                    <div class="text-h5 font-weight-bold">{{ result.max_drawdown?.toFixed(2) }}%</div>
                    <div class="text-caption">最大回撤</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <v-row class="mb-4">
              <v-col cols="6" md="3">
                <div class="text-center">
                  <div class="text-h6 font-weight-bold">{{ (result.win_rate * 100).toFixed(2) }}%</div>
                  <div class="text-caption text-medium-emphasis">胜率</div>
                </div>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-center">
                  <div class="text-h6 font-weight-bold">{{ result.total_trades }}</div>
                  <div class="text-caption text-medium-emphasis">总交易次数</div>
                </div>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-center">
                  <div class="text-h6 font-weight-bold text-success">{{ result.winning_trades }}</div>
                  <div class="text-caption text-medium-emphasis">盈利交易</div>
                </div>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-center">
                  <div class="text-h6 font-weight-bold text-error">{{ result.losing_trades }}</div>
                  <div class="text-caption text-medium-emphasis">亏损交易</div>
                </div>
              </v-col>
            </v-row>

            <h4 class="text-h6 mb-3">资金曲线</h4>
            <div style="height: 300px; position: relative;">
              <canvas ref="equityChartRef"></canvas>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services'
import Chart from 'chart.js/auto'

const config = ref({
  symbol: '000001',
  strategy: 'sma',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  initial_capital: 1000000,
  commission: 0.001
})

const loading = ref(false)
const result = ref(null)
const equityChartRef = ref(null)
let equityChart = null

// 策略选项
const strategyOptions = [
  { title: '移动平均线策略', value: 'sma', subtitle: '基于短期和长期均线交叉' },
  { title: 'RSI策略', value: 'rsi', subtitle: '基于相对强弱指标' },
  { title: '布林带策略', value: 'bollinger', subtitle: '基于布林带突破' },
  { title: 'MACD策略', value: 'macd', subtitle: '基于MACD指标' },
  { title: 'KDJ策略', value: 'kdj', subtitle: '基于随机指标' },
  { title: '自定义策略', value: 'custom', subtitle: '用户自定义策略' }
]

// 历史回测记录
const backtestHistory = ref([
  {
    id: 1,
    symbol: '000001',
    strategy: '移动平均线',
    date: '2024-01-15',
    return: 12.5,
    sharpe: 1.2,
    maxDrawdown: -8.5
  },
  {
    id: 2,
    symbol: '000002',
    strategy: 'RSI策略',
    date: '2024-01-14',
    return: -3.2,
    sharpe: 0.8,
    maxDrawdown: -15.2
  },
  {
    id: 3,
    symbol: '000858',
    strategy: '布林带策略',
    date: '2024-01-13',
    return: 8.7,
    sharpe: 1.5,
    maxDrawdown: -5.8
  }
])

onMounted(() => {
  // 初始化默认日期
  const today = new Date()
  const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate())
  
  config.value.end_date = today.toISOString().split('T')[0]
  config.value.start_date = oneYearAgo.toISOString().split('T')[0]
})

async function runBacktest() {
  loading.value = true
  result.value = null

  try {
    const response = await api.backtest.run(config.value)
    result.value = response.data
    await new Promise(resolve => setTimeout(resolve, 100))
    renderEquityChart()
  } catch (error) {
    console.error('回测失败:', error)
  } finally {
    loading.value = false
  }
}

function renderEquityChart() {
  if (!equityChartRef.value || !result.value?.equity_curve) return

  if (equityChart) {
    equityChart.destroy()
  }

  const dates = result.value.equity_curve.map(d => d.date)
  const values = result.value.equity_curve.map(d => d.value)

  equityChart = new Chart(equityChartRef.value, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [{
        label: '资金净值',
        data: values,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      }
    }
  })
}

function createNewBacktest() {
  // 重置配置
  config.value = {
    symbol: '',
    strategy: 'sma',
    start_date: '',
    end_date: '',
    initial_capital: 1000000,
    commission: 0.001
  }
  result.value = null
}

function loadBacktestRecord(record) {
  // 加载历史回测记录
  config.value.symbol = record.symbol
  config.value.strategy = record.strategy.toLowerCase()
  // 可以加载更多配置信息
}

function deleteBacktestRecord(index) {
  backtestHistory.value.splice(index, 1)
}

function exportBacktestResult() {
  // 导出回测结果
  console.log('导出回测结果')
}

function saveBacktestResult() {
  // 保存回测结果到历史记录
  if (result.value) {
    const newRecord = {
      id: Date.now(),
      symbol: config.value.symbol,
      strategy: strategyOptions.find(s => s.value === config.value.strategy)?.title || config.value.strategy,
      date: new Date().toISOString().split('T')[0],
      return: result.value.total_return || 0,
      sharpe: result.value.sharpe_ratio || 0,
      maxDrawdown: result.value.max_drawdown || 0
    }
    backtestHistory.value.unshift(newRecord)
  }
}
</script>

<style lang="scss" scoped>
.backtest-view {
  max-width: 1600px;
  margin: 0 auto;
}

// 响应式调整
@media (max-width: 960px) {
  .backtest-view {
    padding: 1rem !important;
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

.v-card {
  animation: fadeInUp 0.6s ease-out;
}

// 延迟动画
.v-card:nth-child(1) { animation-delay: 0.1s; }
.v-card:nth-child(2) { animation-delay: 0.2s; }
.v-card:nth-child(3) { animation-delay: 0.3s; }
</style>
