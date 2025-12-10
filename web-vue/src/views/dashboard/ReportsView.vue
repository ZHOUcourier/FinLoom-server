<template>
  <v-container fluid class="reports-view pa-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
          <h1 class="text-h3 font-weight-bold mb-2">报告中心</h1>
          <p class="text-body-1 text-medium-emphasis">查看和管理您的投资报告</p>
        </div>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-plus"
            @click="createCustomReport"
            rounded="pill"
          >
            自定义报告
          </v-btn>
        </div>
      </div>
    </div>

    <!-- 报告类型选择 -->
    <v-row class="mb-6">
      <v-col v-for="reportType in reportTypes" :key="reportType.id" cols="12" sm="6" md="3">
        <v-card variant="elevated" hover class="h-100 report-type-card" @click="generateReport(reportType)">
          <v-card-text class="pa-6 d-flex flex-column">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-avatar :color="reportType.color" variant="tonal" size="56" class="mb-4">
                <v-icon :icon="reportType.icon" size="32"></v-icon>
              </v-avatar>
              <v-chip 
                :color="reportType.color" 
                size="small" 
                variant="tonal"
                v-if="reportType.isNew"
              >
                新功能
              </v-chip>
            </div>
            <h3 class="text-h6 font-weight-bold mb-3">{{ reportType.title }}</h3>
            <p class="text-body-2 text-medium-emphasis mb-4 flex-grow-1">{{ reportType.description }}</p>
            <div class="d-flex align-center justify-space-between">
              <div class="text-caption text-medium-emphasis">
                <v-icon size="16" class="mr-1">mdi-clock-outline</v-icon>
                预计 {{ reportType.estimatedTime }}
              </div>
              <v-btn 
                :color="reportType.color" 
                variant="elevated" 
                size="small"
                :loading="generatingReport === reportType.id"
                @click.stop="generateReport(reportType)"
              >
                <v-icon start>mdi-file-document</v-icon>
                生成
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 报告统计概览 -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" class="metric-card bg-primary-container">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-icon size="48" color="primary">mdi-file-document</v-icon>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="viewDetails('totalReports')">
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            <div class="text-caption mb-1 text-primary">总报告数</div>
            <div class="text-h4 font-weight-bold mb-3">
              {{ reportMetrics.totalReports }}
            </div>
            <div class="d-flex align-center justify-space-between">
              <v-chip size="small" color="primary" variant="flat" class="bg-primary-lighten-4">
                <v-icon start size="16">mdi-trending-up</v-icon>
                +{{ reportMetrics.thisMonth }} 本月
              </v-chip>
              <span class="text-caption text-medium-emphasis">累计</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" class="metric-card bg-success-container">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-icon size="48" color="success">mdi-download</v-icon>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="viewDetails('downloads')">
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            <div class="text-caption mb-1 text-success">下载次数</div>
            <div class="text-h4 font-weight-bold mb-3">
              {{ reportMetrics.totalDownloads }}
            </div>
            <div class="d-flex align-center justify-space-between">
              <v-chip size="small" color="success" variant="flat" class="bg-success-lighten-4">
                <v-icon start size="16">mdi-trending-up</v-icon>
                +{{ reportMetrics.todayDownloads }} 今日
              </v-chip>
              <span class="text-caption text-medium-emphasis">总计</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" class="metric-card bg-info-container">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-icon size="48" color="info">mdi-share</v-icon>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="viewDetails('shares')">
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            <div class="text-caption mb-1 text-info">分享次数</div>
            <div class="text-h4 font-weight-bold mb-3">
              {{ reportMetrics.totalShares }}
            </div>
            <div class="d-flex align-center justify-space-between">
              <v-chip size="small" color="info" variant="flat" class="bg-info-lighten-4">
                <v-icon start size="16">mdi-trending-up</v-icon>
                +{{ reportMetrics.thisWeek }} 本周
              </v-chip>
              <span class="text-caption text-medium-emphasis">总计</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" class="metric-card bg-warning-container">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-icon size="48" color="warning">mdi-chart-line</v-icon>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="viewDetails('avgScore')">
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            <div class="text-caption mb-1 text-warning">平均评分</div>
            <div class="text-h4 font-weight-bold mb-3">
              {{ reportMetrics.avgScore }}/5
            </div>
            <div class="d-flex align-center justify-space-between">
              <v-chip size="small" color="warning" variant="flat" class="bg-warning-lighten-4">
                <v-icon start size="16">mdi-star</v-icon>
                {{ reportMetrics.ratingCount }} 评价
              </v-chip>
              <span class="text-caption text-medium-emphasis">用户反馈</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 最近生成的报告 -->
    <v-card variant="elevated">
      <v-card-title class="d-flex align-center justify-space-between pa-6">
        <div class="d-flex align-center">
          <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
            <v-icon>mdi-history</v-icon>
          </v-avatar>
          <div>
            <div class="text-h6 font-weight-bold">最近生成的报告</div>
            <div class="text-caption text-medium-emphasis">查看和管理您的报告</div>
          </div>
        </div>
        <div class="d-flex gap-2">
          <v-btn-toggle v-model="reportFilter" mandatory>
            <v-btn value="all" size="small">全部</v-btn>
            <v-btn value="recent" size="small">最近</v-btn>
            <v-btn value="favorite" size="small">收藏</v-btn>
          </v-btn-toggle>
        </div>
      </v-card-title>
      <v-card-text class="pa-0">
        <v-list lines="two">
          <v-list-item 
            v-for="report in filteredReports" 
            :key="report.id" 
            class="py-4 px-6"
            :class="{ 'bg-grey-lighten-5': report.isFavorite }"
          >
            <template v-slot:prepend>
              <v-avatar :color="getReportColor(report.type)" variant="tonal" size="48" class="mr-4">
                <v-icon :icon="getReportIcon(report.type)" size="28"></v-icon>
              </v-avatar>
            </template>
            <v-list-item-title class="font-weight-bold text-body-1 mb-1">
              {{ report.name }}
              <v-chip 
                v-if="report.isNew" 
                size="x-small" 
                color="primary" 
                variant="tonal" 
                class="ml-2"
              >
                新
              </v-chip>
            </v-list-item-title>
            <v-list-item-subtitle class="d-flex align-center">
              <span class="mr-4">{{ report.date }}</span>
              <span class="mr-4">{{ report.size }}</span>
              <v-chip 
                :color="getStatusColor(report.status)" 
                size="x-small" 
                variant="tonal"
              >
                {{ getStatusText(report.status) }}
              </v-chip>
            </v-list-item-subtitle>
            <template v-slot:append>
              <div class="d-flex gap-1">
                <v-btn 
                  icon="mdi-download" 
                  variant="text" 
                  size="small" 
                  color="primary"
                  @click="downloadReport(report)"
                ></v-btn>
                <v-btn 
                  icon="mdi-share" 
                  variant="text" 
                  size="small" 
                  color="info"
                  @click="shareReport(report)"
                ></v-btn>
                <v-btn 
                  icon="mdi-heart" 
                  variant="text" 
                  size="small" 
                  :color="report.isFavorite ? 'error' : 'grey'"
                  @click="toggleFavorite(report)"
                ></v-btn>
                <v-btn 
                  icon="mdi-delete" 
                  variant="text" 
                  size="small" 
                  color="error"
                  @click="deleteReport(report)"
                ></v-btn>
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'

const reportTypes = [
  { 
    id: 1, 
    title: '月度绩效报告', 
    description: '详细的月度投资组合表现分析', 
    icon: 'mdi-chart-line', 
    color: 'primary',
    estimatedTime: '2-3分钟',
    isNew: false
  },
  { 
    id: 2, 
    title: '风险评估报告', 
    description: '全面的风险指标和压力测试结果', 
    icon: 'mdi-shield-check', 
    color: 'error',
    estimatedTime: '3-5分钟',
    isNew: false
  },
  { 
    id: 3, 
    title: '交易分析报告', 
    description: '交易记录和执行质量分析', 
    icon: 'mdi-swap-horizontal', 
    color: 'success',
    estimatedTime: '1-2分钟',
    isNew: false
  },
  { 
    id: 4, 
    title: '策略回测报告', 
    description: '策略历史表现和统计分析', 
    icon: 'mdi-flask', 
    color: 'info',
    estimatedTime: '5-8分钟',
    isNew: false
  },
  { 
    id: 5, 
    title: '市场分析报告', 
    description: '市场趋势和行业分析报告', 
    icon: 'mdi-trending-up', 
    color: 'warning',
    estimatedTime: '4-6分钟',
    isNew: true
  },
  { 
    id: 6, 
    title: '合规性报告', 
    description: '监管合规和审计报告', 
    icon: 'mdi-gavel', 
    color: 'secondary',
    estimatedTime: '6-10分钟',
    isNew: true
  }
]

const recentReports = ref([
  { 
    id: 1, 
    name: '2025年1月月度报告', 
    date: '2025-02-01',
    type: '月度绩效报告',
    size: '2.3 MB',
    status: 'completed',
    downloads: 5,
    isFavorite: true,
    isNew: false
  },
  { 
    id: 2, 
    name: '风险评估报告 - Q4', 
    date: '2025-01-15',
    type: '风险评估报告',
    size: '1.8 MB',
    status: 'completed',
    downloads: 3,
    isFavorite: false,
    isNew: false
  },
  { 
    id: 3, 
    name: '策略回测分析', 
    date: '2025-01-10',
    type: '策略回测报告',
    size: '3.1 MB',
    status: 'completed',
    downloads: 8,
    isFavorite: true,
    isNew: false
  },
  { 
    id: 4, 
    name: '交易执行质量报告', 
    date: '2025-01-05',
    type: '交易分析报告',
    size: '1.2 MB',
    status: 'completed',
    downloads: 2,
    isFavorite: false,
    isNew: false
  }
])

const reportFilter = ref('all')

// 报告指标
const reportMetrics = ref({
  totalReports: 24,
  thisMonth: 6,
  totalDownloads: 156,
  todayDownloads: 8,
  totalShares: 23,
  thisWeek: 5,
  avgScore: 4.6,
  ratingCount: 18
})

const generatingReport = ref(null)

// 计算属性
const filteredReports = computed(() => {
  let reports = [...recentReports.value]
  
  if (reportFilter.value === 'recent') {
    // 只显示最近7天的报告
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
    reports = reports.filter(report => new Date(report.date) >= sevenDaysAgo)
  } else if (reportFilter.value === 'favorite') {
    reports = reports.filter(report => report.isFavorite)
  }
  
  return reports
})

// 工具函数
function getReportColor(type) {
  const colors = {
    '月度绩效报告': 'primary',
    '风险评估报告': 'error',
    '交易分析报告': 'success',
    '策略回测报告': 'info',
    '市场分析报告': 'warning',
    '合规性报告': 'secondary'
  }
  return colors[type] || 'primary'
}

function getReportIcon(type) {
  const icons = {
    '月度绩效报告': 'mdi-chart-line',
    '风险评估报告': 'mdi-shield-check',
    '交易分析报告': 'mdi-swap-horizontal',
    '策略回测报告': 'mdi-flask',
    '市场分析报告': 'mdi-trending-up',
    '合规性报告': 'mdi-gavel'
  }
  return icons[type] || 'mdi-file-document'
}

function getStatusColor(status) {
  const colors = {
    'completed': 'success',
    'processing': 'warning',
    'failed': 'error',
    'pending': 'info'
  }
  return colors[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    'completed': '已完成',
    'processing': '处理中',
    'failed': '失败',
    'pending': '等待中'
  }
  return texts[status] || status
}

// 事件处理
function generateReport(reportType) {
  generatingReport.value = reportType.id
  
  // 模拟报告生成过程
  setTimeout(() => {
    generatingReport.value = null
    // 添加新报告到列表
    const newReport = {
      id: Date.now(),
      name: `${reportType.title} - ${new Date().toLocaleDateString()}`,
      date: new Date().toISOString().split('T')[0],
      type: reportType.title,
      size: '1.5 MB',
      status: 'completed',
      downloads: 0
    }
    recentReports.value.unshift(newReport)
  }, 2000)
}

function createCustomReport() {
  // 实现自定义报告功能
  console.log('创建自定义报告')
}

function viewDetails(type) {
  // 实现查看详情功能
  console.log('查看详情:', type)
}

function downloadReport(report) {
  // 实现下载报告功能
  console.log('下载报告:', report)
}

function shareReport(report) {
  // 实现分享报告功能
  console.log('分享报告:', report)
}

function deleteReport(report) {
  // 实现删除报告功能
  const index = recentReports.value.findIndex(r => r.id === report.id)
  if (index > -1) {
    recentReports.value.splice(index, 1)
  }
}

function toggleFavorite(report) {
  // 切换收藏状态
  report.isFavorite = !report.isFavorite
}
</script>

<style lang="scss" scoped>
.reports-view {
  max-width: 1600px;
  margin: 0 auto;
}

.report-type-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  }
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
  .reports-view {
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

.report-type-card,
.metric-card,
.v-card {
  animation: fadeInUp 0.6s ease-out;
}

// 延迟动画
.report-type-card:nth-child(1) { animation-delay: 0.1s; }
.report-type-card:nth-child(2) { animation-delay: 0.2s; }
.report-type-card:nth-child(3) { animation-delay: 0.3s; }
.report-type-card:nth-child(4) { animation-delay: 0.4s; }
.report-type-card:nth-child(5) { animation-delay: 0.5s; }
.report-type-card:nth-child(6) { animation-delay: 0.6s; }

.metric-card:nth-child(1) { animation-delay: 0.1s; }
.metric-card:nth-child(2) { animation-delay: 0.2s; }
.metric-card:nth-child(3) { animation-delay: 0.3s; }
.metric-card:nth-child(4) { animation-delay: 0.4s; }
</style>
