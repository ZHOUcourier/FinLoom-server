<template>
  <v-container fluid class="favorites-view pa-6">
    <v-card rounded="xl">
      <!-- 头部 -->
      <v-card-title class="pa-6 d-flex align-center justify-space-between">
        <div class="d-flex align-center">
          <v-icon start color="warning" size="32">mdi-star</v-icon>
          <div>
            <div class="text-h4 font-weight-bold">收藏对话</div>
            <div class="text-subtitle-1 text-medium-emphasis">
              共 {{ favorites.length }} 个收藏
            </div>
          </div>
        </div>
        
        <v-btn
          color="primary"
          prepend-icon="mdi-history"
          rounded="pill"
          variant="outlined"
          @click="$router.push('/dashboard/chat/history')"
        >
          查看全部对话
        </v-btn>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <!-- 收藏列表 -->
      <v-card-text class="pa-6">
        <v-row v-if="!loading && favorites.length > 0">
          <v-col
            v-for="favorite in favorites"
            :key="favorite.id"
            cols="12"
            md="6"
            lg="4"
          >
            <v-card
              variant="outlined"
              rounded="xl"
              class="favorite-card h-100"
              @click="openConversation(favorite.id)"
            >
              <v-card-text class="pa-6">
                <div class="d-flex justify-space-between align-start mb-3">
                  <v-chip
                    size="small"
                    color="warning"
                    variant="tonal"
                    rounded="lg"
                  >
                    <v-icon start size="16">mdi-star</v-icon>
                    收藏
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
                      <v-list-item @click="openConversation(favorite.id)">
                        <v-list-item-title>
                          <v-icon start size="18">mdi-eye</v-icon>
                          查看对话
                        </v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="editTitle(favorite)">
                        <v-list-item-title>
                          <v-icon start size="18">mdi-pencil</v-icon>
                          编辑标题
                        </v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="exportFavorite(favorite.id)">
                        <v-list-item-title>
                          <v-icon start size="18">mdi-download</v-icon>
                          导出对话
                        </v-list-item-title>
                      </v-list-item>
                      <v-divider></v-divider>
                      <v-list-item @click="removeFavorite(favorite.id)" class="text-warning">
                        <v-list-item-title>
                          <v-icon start size="18">mdi-star-off</v-icon>
                          取消收藏
                        </v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </div>
                
                <div class="text-h6 font-weight-medium mb-2">
                  {{ favorite.title }}
                </div>
                
                <div class="text-body-2 text-medium-emphasis mb-3" style="min-height: 48px">
                  {{ favorite.summary || '暂无摘要' }}
                </div>
                
                <div class="d-flex align-center gap-2 mb-2">
                  <v-chip
                    v-for="tag in favorite.tags"
                    :key="tag"
                    size="x-small"
                    variant="outlined"
                    rounded="lg"
                  >
                    {{ tag }}
                  </v-chip>
                </div>
                
                <div class="d-flex align-center justify-space-between">
                  <div class="text-caption text-medium-emphasis">
                    <v-icon start size="16">mdi-clock-outline</v-icon>
                    {{ formatTime(favorite.favorited_at) }}
                  </div>
                  <v-rating
                    v-model="favorite.rating"
                    size="x-small"
                    density="compact"
                    readonly
                    color="warning"
                  ></v-rating>
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
        <div v-if="!loading && favorites.length === 0" class="text-center py-12">
          <v-avatar color="warning-container" size="96" class="mb-4">
            <v-icon size="48" color="warning">mdi-star-outline</v-icon>
          </v-avatar>
          <div class="text-h5 mb-2">还没有收藏的对话</div>
          <div class="text-body-1 text-medium-emphasis mb-4">
            在对话页面点击星标图标即可收藏重要对话
          </div>
          <v-btn
            color="primary"
            prepend-icon="mdi-history"
            rounded="pill"
            variant="flat"
            size="large"
            @click="$router.push('/dashboard/chat/history')"
          >
            浏览对话历史
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
    
    <!-- 编辑标题对话框 -->
    <v-dialog v-model="editDialog" max-width="500">
      <v-card rounded="xl">
        <v-card-title class="pa-6">
          <v-icon start>mdi-pencil</v-icon>
          编辑收藏标题
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-text-field
            v-model="editingTitle"
            label="收藏标题"
            variant="outlined"
            rounded="lg"
            autofocus
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="editDialog = false" rounded="pill">取消</v-btn>
          <v-btn color="primary" @click="saveTitle" rounded="pill" variant="flat">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const chatStore = useChatStore()

const loading = computed(() => chatStore.loading)
const favorites = computed(() => chatStore.favorites)

const editDialog = ref(false)
const editingTitle = ref('')
const editingFavorite = ref(null)

onMounted(async () => {
  // 使用缓存数据（如果有效）
  await chatStore.fetchFavorites()
})

async function loadFavorites(force = false) {
  // 调用 store 方法，支持强制刷新
  await chatStore.fetchFavorites(force)
}

function openConversation(id) {
  router.push({
    name: 'dashboard-chat',
    query: { id }
  })
}

function editTitle(favorite) {
  editingFavorite.value = favorite
  editingTitle.value = favorite.title
  editDialog.value = true
}

function saveTitle() {
  if (editingFavorite.value && editingTitle.value.trim()) {
    editingFavorite.value.title = editingTitle.value.trim()
  }
  editDialog.value = false
}

async function removeFavorite(id) {
  if (!confirm('确定要取消收藏这个对话吗?')) return
  
  try {
    // await api.chat.unfavoriteConversation(id)
    favorites.value = favorites.value.filter(f => f.id !== id)
  } catch (error) {
    console.error('取消收藏失败:', error)
  }
}

function exportFavorite(id) {
  // 导出功能待实现
  console.log('导出收藏:', id)
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays}天前`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}个月前`
  
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
.favorites-view {
  max-width: 1600px;
  margin: 0 auto;
}

.favorite-card {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-color: rgba(var(--v-theme-warning), 0.2);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(var(--v-theme-warning), 0.15);
    border-color: rgba(var(--v-theme-warning), 0.4);
  }
}
</style>

