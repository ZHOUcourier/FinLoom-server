<template>
  <v-container fluid class="data-view pa-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
          <h1 class="text-h3 font-weight-bold mb-2">数据管理</h1>
          <p class="text-body-1 text-medium-emphasis">管理和收集市场数据</p>
        </div>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-download"
            @click="batchCollect"
            rounded="pill"
          >
            批量采集
          </v-btn>
        </div>
      </div>
    </div>

    <!-- 数据采集和概览 -->
    <v-row>
      <!-- 数据采集 -->
      <v-col cols="12" md="4">
        <v-card variant="elevated" class="mb-6">
          <v-card-title class="d-flex align-center pa-6">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-download</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">数据采集</div>
              <div class="text-caption text-medium-emphasis">采集市场数据</div>
            </div>
          </v-card-title>
          <v-card-text class="pa-6">
            <v-form @submit.prevent="collectData">
              <v-text-field
                v-model="collectConfig.symbol"
                label="股票代码"
                prepend-inner-icon="mdi-chart-candlestick"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                placeholder="例如: 000001"
                hint="输入股票代码，支持多个代码用逗号分隔"
                persistent-hint
              ></v-text-field>

              <v-select
                v-model="collectConfig.period"
                :items="periodOptions"
                label="时间周期"
                prepend-inner-icon="mdi-calendar"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                hint="选择要采集的时间范围"
                persistent-hint
              ></v-select>

              <v-select
                v-model="collectConfig.data_type"
                :items="dataTypeOptions"
                label="数据类型"
                prepend-inner-icon="mdi-chart-timeline-variant"
                variant="outlined"
                density="comfortable"
                class="mb-4"
                hint="选择K线数据类型"
                persistent-hint
              ></v-select>

              <v-switch
                v-model="collectConfig.include_financials"
                label="包含财务数据"
                color="primary"
                class="mb-4"
              ></v-switch>

              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="collecting"
                prepend-icon="mdi-download"
                rounded="lg"
              >
                开始采集
              </v-btn>
            </v-form>

            <v-alert v-if="collectResult" type="success" variant="tonal" class="mt-4">
              <template v-slot:prepend>
                <v-icon>mdi-check-circle</v-icon>
              </template>
              <div>
                <div class="font-weight-bold">采集完成</div>
                <div>成功采集 {{ collectResult.records_count }} 条数据</div>
              </div>
            </v-alert>
          </v-card-text>
        </v-card>

        <!-- 数据质量检查 -->
        <v-card variant="elevated">
          <v-card-title class="d-flex align-center pa-6">
            <v-avatar color="info" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-chart-line-variant</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">数据质量</div>
              <div class="text-caption text-medium-emphasis">检查数据完整性</div>
            </div>
          </v-card-title>
          <v-card-text class="pa-6">
            <v-list density="compact">
              <v-list-item
                v-for="metric in dataQualityMetrics"
                :key="metric.name"
                class="px-0"
              >
                <template v-slot:prepend>
                  <v-avatar :color="metric.color" size="32" variant="tonal">
                    <v-icon size="16">{{ metric.icon }}</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2">{{ metric.name }}</v-list-item-title>
                <template v-slot:append>
                  <div class="text-end">
                    <div :class="metric.color + '--text'" class="font-weight-bold">
                      {{ metric.value }}
                    </div>
                    <div class="text-caption text-medium-emphasis">{{ metric.description }}</div>
                  </div>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card variant="elevated">
          <v-card-title class="d-flex justify-space-between align-center pa-4">
            <div class="d-flex align-center">
              <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
                <v-icon>mdi-database</v-icon>
              </v-avatar>
              <span class="text-h6 font-weight-bold">数据概览</span>
            </div>
            <v-btn
              color="primary"
              prepend-icon="mdi-refresh"
              @click="loadOverview"
              size="small"
            >
              刷新
            </v-btn>
          </v-card-title>
          
          <v-card-text v-if="loadingOverview" class="text-center py-10">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <p class="mt-4">加载中...</p>
          </v-card-text>

          <v-card-text v-else-if="overview">
            <v-row class="mb-4">
              <v-col cols="6">
                <v-card color="primary" dark>
                  <v-card-text>
                    <div class="text-h4 font-weight-bold">{{ overview.total_symbols }}</div>
                    <div class="text-caption">股票数量</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="6">
                <v-card color="success" dark>
                  <v-card-text>
                    <div class="text-h4 font-weight-bold">{{ overview.total_records?.toLocaleString() }}</div>
                    <div class="text-caption">数据记录</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <h4 class="text-h6 mb-3">最近更新</h4>
            <v-list>
              <v-list-item v-for="symbol in overview.symbols" :key="symbol.symbol">
                <v-list-item-title class="font-weight-bold">{{ symbol.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ symbol.symbol }}</v-list-item-subtitle>
                <template v-slot:append>
                  <div class="text-end">
                    <div class="font-weight-bold">¥{{ symbol.latest_price }}</div>
                    <div class="text-caption">{{ symbol.records_count }} 条</div>
                  </div>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services'
import { useDataStore } from '@/stores/data'

const dataStore = useDataStore()

const collectConfig = ref({
  symbol: '000001',
  period: '1y',
  data_type: 'daily',
  include_financials: false
})

const collecting = ref(false)
const collectResult = ref(null)

const loadingOverview = computed(() => dataStore.loading)
const overview = computed(() => dataStore.overview)

// 选项数据
const periodOptions = [
  { title: '1年', value: '1y' },
  { title: '2年', value: '2y' },
  { title: '5年', value: '5y' },
  { title: '10年', value: '10y' },
  { title: '全部', value: 'all' }
]

const dataTypeOptions = [
  { title: '日线', value: 'daily' },
  { title: '周线', value: 'weekly' },
  { title: '月线', value: 'monthly' },
  { title: '分钟线', value: 'minute' }
]

// 数据质量指标
const dataQualityMetrics = ref([
  { name: '数据完整性', value: '98.5%', color: 'success', icon: 'mdi-check-circle', description: '缺失数据比例' },
  { name: '数据准确性', value: '99.2%', color: 'success', icon: 'mdi-shield-check', description: '数据验证通过率' },
  { name: '更新及时性', value: '95.8%', color: 'warning', icon: 'mdi-clock', description: '实时更新比例' },
  { name: '数据覆盖度', value: '87.3%', color: 'info', icon: 'mdi-chart-areaspline', description: '股票覆盖范围' }
])

onMounted(async () => {
  // 使用缓存数据（如果有效）
  await dataStore.fetchOverview()
})

async function collectData() {
  collecting.value = true
  collectResult.value = null

  try {
    const response = await api.data.collect(collectConfig.value)
    collectResult.value = response.data
    // 数据采集后强制刷新概览，清除缓存
    setTimeout(() => { 
      dataStore.clearCache()
      loadOverview(true) 
    }, 1000)
  } catch (error) {
    console.error('数据采集失败:', error)
  } finally {
    collecting.value = false
  }
}

async function loadOverview(force = false) {
  // 调用 store 方法，支持强制刷新
  await dataStore.fetchOverview(force)
}

function batchCollect() {
  // 实现批量采集功能
  console.log('批量采集')
}

function exportData() {
  // 实现数据导出功能
  console.log('导出数据')
}

function cleanData() {
  // 实现数据清理功能
  console.log('清理数据')
}

function validateData() {
  // 实现数据验证功能
  console.log('验证数据')
}
</script>

<style lang="scss" scoped>
.data-view {
  max-width: 1600px;
  margin: 0 auto;
}

// 响应式调整
@media (max-width: 960px) {
  .data-view {
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
