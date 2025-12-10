<template>
  <v-card 
    variant="flat" 
    class="sidebar-card h-100"
    rounded="0"
  >
    <!-- 头部 -->
    <v-card-text class="pa-4">
      <div class="d-flex justify-space-between align-center mb-4">
        <div class="d-flex align-center">
          <v-avatar color="primary" variant="tonal" size="32" class="mr-3">
            <v-icon size="18">mdi-chat-outline</v-icon>
          </v-avatar>
          <div>
            <div class="text-subtitle-1 font-weight-medium">对话历史</div>
            <div class="text-caption text-medium-emphasis">{{ conversations.length }} 个对话</div>
          </div>
        </div>
        <div class="d-flex gap-1">
          <v-btn 
            icon="mdi-plus" 
            variant="text" 
            size="small" 
            @click="$emit('new-conversation')"
            color="primary"
            rounded="lg"
          ></v-btn>
          <v-btn 
            icon="mdi-cog-outline" 
            variant="text" 
            size="small" 
            @click="$emit('open-settings')"
            color="primary"
            rounded="lg"
          ></v-btn>
        </div>
      </div>
      
      <!-- 搜索框 -->
      <v-text-field
        :model-value="searchQuery"
        @update:model-value="$emit('update:searchQuery', $event)"
        placeholder="搜索对话..."
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="comfortable"
        hide-details
        rounded="lg"
        class="mb-3"
        bg-color="surface-variant"
      ></v-text-field>
      
      <!-- 筛选按钮 -->
      <div class="d-flex gap-1 flex-wrap">
        <v-chip
          v-for="filter in filters"
          :key="filter.value"
          :color="activeFilter === filter.value ? 'primary' : 'surface-variant'"
          :variant="activeFilter === filter.value ? 'flat' : 'outlined'"
          size="small"
          @click="$emit('update:activeFilter', filter.value)"
          class="cursor-pointer"
          rounded="lg"
        >
          {{ filter.label }}
        </v-chip>
      </div>
    </v-card-text>
    
    <!-- 对话列表 -->
    <v-card-text class="pa-2 pt-0">
      <div
        v-for="conv in conversations"
        :key="conv.id"
        :class="[
          'conversation-item pa-3 mb-2 rounded-xl cursor-pointer transition-all',
          conv.id === currentConversationId 
            ? 'bg-primary-container text-primary-on-container elevation-1' 
            : 'hover:bg-surface-variant hover:elevation-1'
        ]"
        @click="$emit('switch-conversation', conv.id)"
      >
        <div class="d-flex justify-space-between align-center">
          <div class="flex-1 min-width-0">
            <div class="d-flex align-center mb-1">
              <v-icon 
                :icon="getConversationIcon(conv.type)" 
                size="16" 
                class="mr-2"
                :class="'text-' + getConversationColor(conv.type)"
              ></v-icon>
              <div class="text-body-2 font-weight-medium text-truncate">{{ conv.title }}</div>
              <v-chip 
                v-if="conv.isPinned" 
                size="x-small" 
                color="warning" 
                variant="tonal" 
                class="ml-2"
              >
                置顶
              </v-chip>
            </div>
            <div class="text-caption text-medium-emphasis">{{ formatTime(conv.updatedAt || conv.createdAt) }}</div>
            <div v-if="conv.lastMessage" class="text-caption text-medium-emphasis mt-1 text-truncate">
              {{ conv.lastMessage }}
            </div>
          </div>
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn 
                icon="mdi-dots-vertical" 
                variant="text" 
                size="x-small" 
                v-bind="props"
                class="text-medium-emphasis ml-2"
              ></v-btn>
            </template>
            <v-list>
              <v-list-item @click="$emit('pin-conversation', conv.id)">
                <v-list-item-title>
                  <v-icon start size="16">{{ conv.isPinned ? 'mdi-pin-off' : 'mdi-pin' }}</v-icon>
                  {{ conv.isPinned ? '取消置顶' : '置顶' }}
                </v-list-item-title>
              </v-list-item>
              <v-list-item @click="$emit('rename-conversation', conv.id)">
                <v-list-item-title>
                  <v-icon start size="16">mdi-pencil</v-icon>
                  重命名
                </v-list-item-title>
              </v-list-item>
              <v-list-item @click="$emit('export-conversation', conv.id)">
                <v-list-item-title>
                  <v-icon start size="16">mdi-download</v-icon>
                  导出
                </v-list-item-title>
              </v-list-item>
              <v-divider></v-divider>
              <v-list-item @click="$emit('delete-conversation', conv.id)" class="text-error">
                <v-list-item-title>
                  <v-icon start size="16">mdi-delete</v-icon>
                  删除
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="conversations.length === 0" class="text-center py-12">
        <v-avatar color="surface-variant" variant="tonal" size="64" class="mb-4">
          <v-icon size="32" color="medium-emphasis">mdi-chat-outline</v-icon>
        </v-avatar>
        <div class="text-body-1 text-medium-emphasis">暂无对话</div>
        <div class="text-caption text-medium-emphasis mt-1">开始新的对话吧</div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { getConversationIcon, getConversationColor } from '@/utils/chat'
import { formatTime } from '@/utils/date'

defineProps({
  conversations: {
    type: Array,
    required: true
  },
  currentConversationId: {
    type: String,
    default: ''
  },
  searchQuery: {
    type: String,
    default: ''
  },
  activeFilter: {
    type: String,
    default: 'all'
  },
  filters: {
    type: Array,
    required: true
  }
})

defineEmits([
  'new-conversation',
  'open-settings',
  'switch-conversation',
  'delete-conversation',
  'pin-conversation',
  'rename-conversation',
  'export-conversation',
  'update:searchQuery',
  'update:activeFilter'
])
</script>

