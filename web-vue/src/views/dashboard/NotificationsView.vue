<template>
  <v-container fluid class="notifications-view pa-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
          <h1 class="text-h3 font-weight-bold mb-2">通知中心</h1>
          <p class="text-body-1 text-medium-emphasis">查看系统通知和重要提醒</p>
        </div>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-plus"
            @click="createNotification"
            rounded="pill"
          >
            新建通知
          </v-btn>
        </div>
      </div>
    </div>

    <!-- 通知统计概览 -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" class="metric-card bg-primary-container">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-icon size="48" color="primary">mdi-bell</v-icon>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="viewDetails('totalNotifications')">
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            <div class="text-caption mb-1 text-primary">总通知数</div>
            <div class="text-h4 font-weight-bold mb-3">
              {{ notificationMetrics.totalNotifications }}
            </div>
            <div class="d-flex align-center justify-space-between">
              <v-chip size="small" color="primary" variant="flat" class="bg-primary-lighten-4">
                <v-icon start size="16">mdi-trending-up</v-icon>
                +{{ notificationMetrics.todayNotifications }} 今日
              </v-chip>
              <span class="text-caption text-medium-emphasis">累计</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" class="metric-card bg-error-container">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-icon size="48" color="error">mdi-bell-alert</v-icon>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="viewDetails('unreadNotifications')">
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            <div class="text-caption mb-1 text-error">未读通知</div>
            <div class="text-h4 font-weight-bold mb-3">
              {{ notificationMetrics.unreadNotifications }}
            </div>
            <div class="d-flex align-center justify-space-between">
              <v-chip size="small" color="error" variant="flat" class="bg-error-lighten-4">
                <v-icon start size="16">mdi-alert</v-icon>
                {{ notificationMetrics.urgentNotifications }} 紧急
              </v-chip>
              <span class="text-caption text-medium-emphasis">待处理</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" class="metric-card bg-success-container">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-icon size="48" color="success">mdi-check-circle</v-icon>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="viewDetails('readNotifications')">
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            <div class="text-caption mb-1 text-success">已读通知</div>
            <div class="text-h4 font-weight-bold mb-3">
              {{ notificationMetrics.readNotifications }}
            </div>
            <div class="d-flex align-center justify-space-between">
              <v-chip size="small" color="success" variant="flat" class="bg-success-lighten-4">
                <v-icon start size="16">mdi-trending-up</v-icon>
                {{ notificationMetrics.readRate }}% 阅读率
              </v-chip>
              <span class="text-caption text-medium-emphasis">处理率</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card variant="elevated" class="metric-card bg-info-container">
          <v-card-text class="pa-6">
            <div class="d-flex justify-space-between align-start mb-4">
              <v-icon size="48" color="info">mdi-cog</v-icon>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list>
                  <v-list-item @click="viewDetails('activeSettings')">
                    <v-list-item-title>查看详情</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            <div class="text-caption mb-1 text-info">活跃设置</div>
            <div class="text-h4 font-weight-bold mb-3">
              {{ notificationMetrics.activeSettings }}
            </div>
            <div class="d-flex align-center justify-space-between">
              <v-chip size="small" color="info" variant="flat" class="bg-info-lighten-4">
                <v-icon start size="16">mdi-settings</v-icon>
                {{ notificationMetrics.totalSettings }} 总设置
              </v-chip>
              <span class="text-caption text-medium-emphasis">配置项</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-card variant="elevated">
          <v-card-title class="d-flex align-center justify-space-between pa-6">
            <div class="d-flex align-center">
              <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
                <v-icon>mdi-bell</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">所有通知</div>
                <div class="text-caption text-medium-emphasis">系统通知和提醒</div>
              </div>
            </div>
            <div class="d-flex gap-2">
              <v-btn-toggle v-model="notificationFilter" mandatory>
                <v-btn value="all" size="small">全部</v-btn>
                <v-btn value="unread" size="small">未读</v-btn>
                <v-btn value="urgent" size="small">紧急</v-btn>
              </v-btn-toggle>
              <v-btn color="primary" size="small" @click="markAllRead" prepend-icon="mdi-check-all">
                全部已读
              </v-btn>
            </div>
          </v-card-title>
          
          <v-list lines="three">
            <v-list-item
              v-for="notification in notifications"
              :key="notification.id"
              :class="{ 'bg-grey-lighten-4': !notification.read }"
            >
              <template v-slot:prepend>
                <v-avatar :color="notification.color" size="40">
                  <v-icon :icon="notification.icon" color="white"></v-icon>
                </v-avatar>
              </template>

              <v-list-item-title class="font-weight-bold">
                {{ notification.title }}
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ notification.message }}
              </v-list-item-subtitle>
              <v-list-item-subtitle class="text-caption">
                {{ notification.time }}
              </v-list-item-subtitle>

              <template v-slot:append>
                <v-btn
                  icon="mdi-close"
                  variant="text"
                  size="small"
                  @click="removeNotification(notification.id)"
                ></v-btn>
              </template>
            </v-list-item>
          </v-list>

          <v-alert v-if="notifications.length === 0" type="info" variant="tonal" class="ma-4">
            暂无通知
          </v-alert>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card variant="elevated" class="mb-4">
          <v-card-title class="d-flex align-center pa-4">
            <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-cog</v-icon>
            </v-avatar>
            <span class="text-h6 font-weight-bold">通知设置</span>
          </v-card-title>
          <v-card-text>
            <v-switch
              v-model="settings.priceAlerts"
              label="价格预警"
              color="primary"
              hide-details
              class="mb-2"
            ></v-switch>
            <v-switch
              v-model="settings.tradeNotifications"
              label="交易通知"
              color="primary"
              hide-details
              class="mb-2"
            ></v-switch>
            <v-switch
              v-model="settings.systemUpdates"
              label="系统更新"
              color="primary"
              hide-details
            ></v-switch>
          </v-card-text>
        </v-card>

        <v-card variant="elevated">
          <v-card-title class="d-flex align-center pa-4">
            <v-avatar color="success" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-chart-box</v-icon>
            </v-avatar>
            <span class="text-h6 font-weight-bold">通知统计</span>
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>总通知数</v-list-item-title>
                <template v-slot:append>
                  <v-chip color="primary" size="small">{{ notifications.length }}</v-chip>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>未读通知</v-list-item-title>
                <template v-slot:append>
                  <v-chip color="error" size="small">{{ unreadCount }}</v-chip>
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
import { ref, computed } from 'vue'

const notifications = ref([
  {
    id: 1,
    title: '价格预警',
    message: '股票 000001 已达到目标价格 ¥50.00',
    time: '5分钟前',
    read: false,
    color: 'warning',
    icon: 'mdi-alert',
    type: 'price_alert',
    urgent: true
  },
  {
    id: 2,
    title: '交易完成',
    message: '您的买入订单已成功执行',
    time: '1小时前',
    read: false,
    color: 'success',
    icon: 'mdi-check-circle',
    type: 'trade',
    urgent: false
  },
  {
    id: 3,
    title: '系统维护',
    message: '系统将于今晚22:00进行维护',
    time: '2小时前',
    read: true,
    color: 'info',
    icon: 'mdi-information',
    type: 'system',
    urgent: false
  },
  {
    id: 4,
    title: '风险提醒',
    message: '投资组合风险指标超过预设阈值',
    time: '3小时前',
    read: false,
    color: 'error',
    icon: 'mdi-shield-alert',
    type: 'risk',
    urgent: true
  },
  {
    id: 5,
    title: '策略更新',
    message: '您的投资策略已自动优化',
    time: '1天前',
    read: true,
    color: 'primary',
    icon: 'mdi-strategy',
    type: 'strategy',
    urgent: false
  }
])

const settings = ref({
  priceAlerts: true,
  tradeNotifications: true,
  systemUpdates: true,
  riskAlerts: true,
  strategyUpdates: false,
  marketNews: true
})

const notificationFilter = ref('all')

// 通知指标
const notificationMetrics = ref({
  totalNotifications: 156,
  todayNotifications: 8,
  unreadNotifications: 12,
  urgentNotifications: 3,
  readNotifications: 144,
  readRate: 92.3,
  activeSettings: 4,
  totalSettings: 6
})

// 计算属性
const filteredNotifications = computed(() => {
  let filtered = [...notifications.value]
  
  if (notificationFilter.value === 'unread') {
    filtered = filtered.filter(n => !n.read)
  } else if (notificationFilter.value === 'urgent') {
    filtered = filtered.filter(n => n.urgent)
  }
  
  return filtered
})

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

function markAllRead() {
  notifications.value.forEach(n => n.read = true)
}

function removeNotification(id) {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

function createNotification() {
  // 实现创建通知功能
  console.log('创建通知')
}

function viewDetails(type) {
  // 实现查看详情功能
  console.log('查看详情:', type)
}

function markAsRead(notification) {
  // 标记为已读
  notification.read = true
}

function toggleUrgent(notification) {
  // 切换紧急状态
  notification.urgent = !notification.urgent
}
</script>

<style lang="scss" scoped>
.notifications-view {
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
  .notifications-view {
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
