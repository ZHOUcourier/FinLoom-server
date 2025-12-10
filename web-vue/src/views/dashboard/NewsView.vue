<template>
  <v-container fluid class="news-view pa-6">
    <div class="mb-6">
      <h1 class="text-h4 font-weight-bold mb-2">市场资讯</h1>
      <p class="text-body-1 text-medium-emphasis">最新市场动态与资讯</p>
    </div>

    <!-- Tab切换 -->
    <v-tabs v-model="activeTab" class="mb-6" color="primary">
      <v-tab value="news">要闻</v-tab>
      <v-tab value="flash">快讯</v-tab>
      <v-tab value="reports">研报</v-tab>
      <v-tab value="announcements">公告</v-tab>
    </v-tabs>

    <!-- 要闻列表 -->
    <v-window v-model="activeTab">
      <v-window-item value="news">
        <v-card>
          <v-card-text>
            <!-- 加载中 -->
            <div v-if="loading" class="text-center py-12">
              <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
              <p class="mt-4 text-body-1">加载中...</p>
            </div>

            <!-- 加载失败 -->
            <div v-else-if="error" class="text-center py-12">
              <v-icon size="64" color="error">mdi-alert-circle-outline</v-icon>
              <p class="mt-4 text-h6">数据加载失败</p>
              <v-btn color="primary" class="mt-4" @click="loadNews">
                重新加载
              </v-btn>
            </div>

            <!-- 新闻列表 -->
            <v-list v-else>
              <v-list-item
                v-for="(news, index) in newsList"
                :key="index"
                class="mb-2"
              >
                <template v-slot:prepend>
                  <v-avatar :color="news.type === 'important' ? 'error' : 'primary'" variant="tonal" size="40">
                    <v-icon>{{ news.type === 'important' ? 'mdi-alert' : 'mdi-newspaper' }}</v-icon>
                  </v-avatar>
                </template>

                <v-list-item-title class="font-weight-medium mb-1">
                  {{ news.title }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ news.summary }}
                </v-list-item-subtitle>

                <template v-slot:append>
                  <div class="text-end">
                    <div class="text-caption text-medium-emphasis mb-1">
                      {{ formatTime(news.time) }}
                    </div>
                    <v-chip 
                      size="small" 
                      :color="news.type === 'important' ? 'error' : 'primary'" 
                      variant="tonal"
                    >
                      {{ news.type === 'important' ? '重要' : '资讯' }}
                    </v-chip>
                  </div>
                </template>
              </v-list-item>

              <!-- 空状态 -->
              <div v-if="newsList.length === 0" class="text-center py-12">
                <v-icon size="64" color="grey">mdi-information-outline</v-icon>
                <p class="mt-4 text-body-1 text-medium-emphasis">暂无资讯数据</p>
              </div>
            </v-list>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="flash">
        <v-card>
          <v-card-text class="text-center py-12">
            <v-icon size="64" color="grey">mdi-flash</v-icon>
            <p class="mt-4 text-body-1">快讯功能开发中...</p>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="reports">
        <v-card>
          <v-card-text class="text-center py-12">
            <v-icon size="64" color="grey">mdi-file-document</v-icon>
            <p class="mt-4 text-body-1">研报功能开发中...</p>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="announcements">
        <v-card>
          <v-card-text class="text-center py-12">
            <v-icon size="64" color="grey">mdi-bullhorn</v-icon>
            <p class="mt-4 text-body-1">公告功能开发中...</p>
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services'

const activeTab = ref('news')
const loading = ref(false)
const error = ref(false)
const newsList = ref([])

onMounted(() => {
  loadNews()
})

async function loadNews() {
  loading.value = true
  error.value = false

  try {
    const response = await api.market.getMarketNews(50)
    
    if (response.data?.news) {
      newsList.value = response.data.news.map(news => ({
        id: news.id,
        title: news.title,
        summary: news.summary,
        time: new Date(news.time),
        type: news.type || 'normal'
      }))
    }
  } catch (err) {
    console.error('加载新闻失败:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

function formatTime(date) {
  if (!date) return ''
  
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
}
</script>

<style lang="scss" scoped>
.news-view {
  max-width: 1400px;
  margin: 0 auto;
}
</style>

