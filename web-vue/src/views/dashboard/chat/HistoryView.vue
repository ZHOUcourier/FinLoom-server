<template>
  <v-container fluid class="history-view pa-6">
    <v-card rounded="xl">
      <!-- 头部 -->
      <v-card-title class="pa-6 d-flex align-center justify-space-between">
        <div class="d-flex align-center">
          <v-icon start color="primary" size="32">mdi-history</v-icon>
          <div>
            <div class="text-h4 font-weight-bold">对话历史</div>
            <div class="text-subtitle-1 text-medium-emphasis">
              共 {{ filteredConversations.length }} 个对话
            </div>
          </div>
        </div>
        
        <div class="d-flex align-center gap-2">
          <v-text-field
            v-model="searchQuery"
            placeholder="搜索对话..."
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="comfortable"
            hide-details
            rounded="lg"
            style="max-width: 300px"
          ></v-text-field>
          
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            rounded="pill"
            variant="flat"
            @click="$router.push('/dashboard/chat/new')"
          >
            新对话
          </v-btn>
        </div>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <!-- 筛选器 -->
      <v-card-text class="pa-6">
        <v-chip-group v-model="selectedFilter" mandatory>
          <v-chip
            v-for="filter in filters"
            :key="filter.value"
            :value="filter.value"
            rounded="lg"
          >
            <v-icon start size="18">{{ filter.icon }}</v-icon>
            {{ filter.label }}
          </v-chip>
        </v-chip-group>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <!-- 对话列表 -->
      <v-card-text class="pa-6">
        <v-row v-if="!loading && filteredConversations.length > 0">
          <v-col
            v-for="conversation in filteredConversations"
            :key="conversation.id"
            cols="12"
            md="6"
            lg="4"
          >
            <v-card
              variant="outlined"
              rounded="xl"
              class="conversation-card h-100"
              @click="openConversation(conversation.id)"
            >
              <v-card-text class="pa-6">
                <div class="d-flex justify-space-between align-start mb-3">
                  <v-chip
                    size="small"
                    :color="getTypeColor(conversation.type)"
                    variant="tonal"
                    rounded="lg"
                  >
                    {{ getTypeLabel(conversation.type) }}
                  </v-chip>
                  
                  <v-menu>
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-dots-vertical"
                        variant="text"
                        size="small"
                        v-bind="props"
                      ></v-btn>
                    </template>
                    <v-list>
                      <v-list-item @click="viewDetails(conversation.id)">
                        <v-list-item-title>
                          <v-icon start size="18">mdi-eye</v-icon>
                          查看详情
                        </v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="exportConversation(conversation.id)">
                        <v-list-item-title>
                          <v-icon start size="18">mdi-download</v-icon>
                          导出对话
                        </v-list-item-title>
                      </v-list-item>
                      <v-divider></v-divider>
                      <v-list-item @click="deleteConversation(conversation.id)" class="text-error">
                        <v-list-item-title>
                          <v-icon start size="18">mdi-delete</v-icon>
                          删除对话
                        </v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </div>
                
                <div class="text-h6 font-weight-medium mb-2 text-truncate">
                  {{ conversation.title }}
                </div>
                
                <div class="text-body-2 text-medium-emphasis mb-3" style="min-height: 48px">
                  {{ conversation.last_message }}
                </div>
                
                <div class="d-flex align-center justify-space-between">
                  <div class="text-caption text-medium-emphasis">
                    <v-icon start size="16">mdi-clock-outline</v-icon>
                    {{ formatTime(conversation.updated_at) }}
                  </div>
                  <v-chip size="x-small" variant="tonal">
                    {{ conversation.message_count }} 条消息
                  </v-chip>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
          <div class="text-h6 mt-4">加载中...</div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="!loading && filteredConversations.length === 0" class="text-center py-12">
          <v-avatar color="surface-variant" size="96" class="mb-4">
            <v-icon size="48" color="medium-emphasis">mdi-chat-outline</v-icon>
          </v-avatar>
          <div class="text-h5 mb-2">暂无对话记录</div>
          <div class="text-body-1 text-medium-emphasis mb-4">
            {{ searchQuery ? '没有找到匹配的对话' : '开始您的第一个对话吧' }}
          </div>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            rounded="pill"
            variant="flat"
            size="large"
            @click="$router.push('/dashboard/chat/new')"
          >
            创建新对话
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const chatStore = useChatStore()

const conversations = computed(() => chatStore.conversations)
const loading = computed(() => chatStore.loading)
const searchQuery = ref('')
const selectedFilter = ref('all')

const filters = [
  { label: '全部', value: 'all', icon: 'mdi-view-grid-outline' },
  { label: '最近', value: 'recent', icon: 'mdi-clock-outline' },
  { label: '投资', value: 'investment', icon: 'mdi-chart-line' },
  { label: '风险', value: 'risk', icon: 'mdi-shield-alert' }
]

const filteredConversations = computed(() => {
  let filtered = [...conversations.value]
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(conv =>
      conv.title.toLowerCase().includes(query) ||
      conv.last_message?.toLowerCase().includes(query)
    )
  }
  
  // 类型过滤
  if (selectedFilter.value !== 'all') {
    if (selectedFilter.value === 'recent') {
      const sevenDaysAgo = new Date()
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
      filtered = filtered.filter(conv =>
        new Date(conv.updated_at) >= sevenDaysAgo
      )
    } else {
      filtered = filtered.filter(conv => conv.type === selectedFilter.value)
    }
  }
  
  return filtered
})

onMounted(async () => {
  // 使用缓存数据（如果有效）
  await chatStore.fetchConversations()
})

async function loadConversations(force = false) {
  // 调用 store 方法，支持强制刷新
  await chatStore.fetchConversations(force)
}

function openConversation(id) {
  router.push({
    name: 'dashboard-chat',
    query: { id }
  })
}

function viewDetails(id) {
  router.push({
    name: 'dashboard-chat',
    query: { id, view: 'details' }
  })
}

async function deleteConversation(id) {
  if (!confirm('确定要删除这个对话吗?')) return
  
  try {
    const { api } = await import('@/services')
    await api.chat.deleteConversation(id)
    // 清除缓存并重新加载
    chatStore.clearCache('conversations')
    await loadConversations(true)
  } catch (error) {
    console.error('删除对话失败:', error)
  }
}

function exportConversation(id) {
  // 导出功能待实现
  console.log('导出对话:', id)
}

function getTypeColor(type) {
  const colors = {
    investment: 'primary',
    risk: 'error',
    strategy: 'secondary',
    general: 'default',
    analysis: 'info'
  }
  return colors[type] || 'default'
}

function getTypeLabel(type) {
  const labels = {
    investment: '投资',
    risk: '风险',
    strategy: '策略',
    general: '一般',
    analysis: '分析'
  }
  return labels[type] || '一般'
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
.history-view {
  max-width: 1600px;
  margin: 0 auto;
}

.conversation-card {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(var(--v-theme-primary), 0.12);
  }
}
</style>







