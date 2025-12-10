<template>
  <!-- 子路由视图 -->
  <router-view v-if="$route.path !== '/dashboard/chat'" />
  
  <!-- 主聊天界面 -->
  <v-container v-else fluid class="chat-view pa-0" :class="{ 'has-messages': messages.length > 0 }" style="height: calc(100vh - 70px - 4rem);">
    <!-- 新对话界面 (无消息时全屏显示) -->
    <transition name="fade-slide">
      <div v-if="messages.length === 0" class="new-chat-fullscreen">
        <v-card variant="flat" class="new-chat-card h-100" rounded="lg">
          <!-- 顶部工具栏 -->
          <div class="new-chat-toolbar">
            <v-btn
              variant="text"
              prepend-icon="mdi-history"
              @click="showHistoryDialog = true"
              class="history-btn"
            >
              历史记录 ({{ conversations.length }})
            </v-btn>
            <v-btn
              icon="mdi-cog-outline"
              variant="text"
              size="small"
              @click="openSettings"
              color="primary"
            ></v-btn>
          </div>

          <!-- 消息区域 (新对话欢迎界面) -->
          <ChatMessages
            ref="messagesComponent"
            :messages="messages"
            :loading="loading"
            :quick-questions="quickQuestions"
            @ask-question="askQuestion"
          />

          <!-- 输入区域 -->
          <ChatInput
            v-model="inputMessage"
            :loading="loading"
            @send="sendMessage"
          />
        </v-card>
      </div>
    </transition>

    <!-- 带侧边栏的对话界面 (有消息时显示) -->
    <transition name="fade-slide">
      <v-row v-if="messages.length > 0" no-gutters style="height: 100%; flex: 1;">
        <!-- 侧边栏 -->
        <v-col cols="auto" class="sidebar-col">
          <ChatSidebar
            :conversations="filteredConversations"
            :current-conversation-id="conversationId"
            v-model:search-query="searchQuery"
            v-model:active-filter="activeFilter"
            :filters="conversationFilters"
            @new-conversation="handleNewConversation"
            @open-settings="openSettings"
            @switch-conversation="switchConversation"
            @delete-conversation="deleteConversation"
            @pin-conversation="pinConversation"
            @rename-conversation="renameConversation"
            @export-conversation="exportConversationHandler"
          />
        </v-col>

        <!-- 聊天区域 -->
        <v-col class="chat-area-col">
          <v-card variant="flat" class="chat-area-card h-100" rounded="0">
            <!-- 头部 -->
            <ChatHeader
              :loading="loading"
              @refresh="refreshChat"
              @copy="copyConversation"
              @clear="clearMessages"
            />

            <!-- 消息区域 -->
            <ChatMessages
              ref="messagesComponent"
              :messages="messages"
              :loading="loading"
              :quick-questions="quickQuestions"
              @ask-question="askQuestion"
            />

            <!-- 输入区域 -->
            <ChatInput
              v-model="inputMessage"
              :loading="loading"
              @send="sendMessage"
            />
          </v-card>
        </v-col>
      </v-row>
    </transition>

    <!-- 历史记录对话框 -->
    <v-dialog v-model="showHistoryDialog" max-width="600px" scrollable>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h6">对话历史</span>
          <v-btn icon="mdi-close" variant="text" size="small" @click="showHistoryDialog = false"></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-2" style="max-height: 500px;">
          <!-- 搜索框 -->
          <v-text-field
            v-model="searchQuery"
            placeholder="搜索对话..."
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="comfortable"
            hide-details
            rounded="lg"
            class="mb-3 mx-2"
          ></v-text-field>
          
          <!-- 筛选按钮 -->
          <div class="d-flex gap-1 flex-wrap mb-3 px-2">
            <v-chip
              v-for="filter in conversationFilters"
              :key="filter.value"
              :color="activeFilter === filter.value ? 'primary' : 'surface-variant'"
              :variant="activeFilter === filter.value ? 'flat' : 'outlined'"
              size="small"
              @click="activeFilter = filter.value"
              class="cursor-pointer"
            >
              {{ filter.label }}
            </v-chip>
          </div>

          <!-- 对话列表 -->
          <div
            v-for="conv in filteredConversations"
            :key="conv.id"
            class="conversation-item-dialog pa-3 mb-2 rounded-lg cursor-pointer"
            @click="selectHistoryConversation(conv.id)"
          >
            <div class="d-flex justify-space-between align-center">
              <div class="flex-1 min-width-0">
                <div class="text-body-2 font-weight-medium mb-1">{{ conv.title }}</div>
                <div class="text-caption text-medium-emphasis">{{ formatTime(conv.updatedAt || conv.createdAt) }}</div>
                <div v-if="conv.lastMessage" class="text-caption text-medium-emphasis mt-1 text-truncate">
                  {{ conv.lastMessage }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-if="filteredConversations.length === 0" class="text-center py-8">
            <v-avatar color="surface-variant" variant="tonal" size="64" class="mb-4">
              <v-icon size="32" color="medium-emphasis">mdi-chat-outline</v-icon>
            </v-avatar>
            <div class="text-body-1 text-medium-emphasis">暂无对话</div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 设置对话框 -->
    <AISettingsDialog
      v-model="settingsOpen"
      :settings="localSettings"
      @save="saveSettings"
      @cancel="settingsOpen = false"
      @update-setting="updateSettingValue"
    />
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatHeader from '@/components/chat/ChatHeader.vue'
import ChatMessages from '@/components/chat/ChatMessages.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import AISettingsDialog from '@/components/chat/AISettingsDialog.vue'
import { useChat } from '@/composables/useChat'
import { useConversationActions } from '@/composables/useConversationActions'
import { useAISettings } from '@/composables/useAISettings'
import { CONVERSATION_FILTERS, QUICK_QUESTIONS } from '@/constants/chat'
import { formatTime } from '@/utils/date'

// 使用组合式函数
const {
  inputMessage,
  messagesRef,
  searchQuery,
  activeFilter,
  filteredConversations,
  messages,
  conversations,
  conversationId,
  loading,
  error,
  sendMessage,
  scrollToBottom,
  askQuestion,
  newConversation,
  switchConversation,
  deleteConversation,
  clearMessages,
  refreshChat
} = useChat()

const {
  pinConversation,
  renameConversation,
  exportConversation: exportConversationHandler,
  copyConversation
} = useConversationActions()

const {
  settingsOpen,
  localSettings,
  openSettings,
  saveSettings
} = useAISettings()

// 常量
const conversationFilters = CONVERSATION_FILTERS
const quickQuestions = QUICK_QUESTIONS

// 消息组件引用
const messagesComponent = ref(null)

// 历史记录对话框
const showHistoryDialog = ref(false)

// 处理新对话按钮点击
function handleNewConversation() {
  newConversation()
  // 新对话创建后，界面会自动切换到新对话视图（因为 messages.length === 0）
}

// 从历史记录中选择对话
function selectHistoryConversation(id) {
  switchConversation(id)
  showHistoryDialog.value = false
}

// 更新设置值
function updateSettingValue(key, value) {
  localSettings.value[key] = value
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/views/chat-view.scss';
</style>

