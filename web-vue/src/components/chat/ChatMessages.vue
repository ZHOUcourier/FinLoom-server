<template>
  <div ref="messagesRef" class="messages-container">
    <!-- 空状态 -->
    <div v-if="messages.length === 0" class="empty-state">
      <div class="welcome-section">
        <v-avatar color="primary" variant="tonal" size="64" class="mb-3">
          <v-icon size="32">mdi-chat-outline</v-icon>
        </v-avatar>
        <h2 class="text-h5 font-weight-bold mb-2">欢迎使用 FIN-R1 AI助手</h2>
        <p class="text-body-1 text-medium-emphasis mb-4">向AI助手描述您的投资需求，获取个性化建议</p>
        
        <!-- 快速开始卡片 -->
        <div class="quick-start-section">
          <h3 class="text-subtitle-1 font-weight-medium mb-3 text-center">快速开始</h3>
          <v-row class="justify-center">
            <v-col 
              v-for="q in quickQuestions" 
              :key="q.text" 
              cols="12" 
              sm="6" 
              md="4"
              class="d-flex justify-center"
            >
              <v-card 
                variant="elevated" 
                class="quick-card pa-4 cursor-pointer w-100"
                rounded="lg"
                elevation="2"
                @click="$emit('ask-question', q.text)"
              >
                <div class="text-center">
                  <v-avatar :color="q.color" variant="tonal" size="48" class="mb-3">
                    <v-icon :icon="q.icon" size="24"></v-icon>
                  </v-avatar>
                  <div class="text-body-2 font-weight-medium mb-1">{{ q.text }}</div>
                  <div class="text-caption text-medium-emphasis">{{ q.description }}</div>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </div>
      </div>
    </div>

    <!-- 消息列表 -->
    <div v-for="message in messages" :key="message.id" class="message-wrapper mb-4">
      <div class="d-flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
        <v-avatar v-if="message.role === 'assistant'" class="mr-3" size="36" color="primary" variant="tonal">
          <v-icon size="20">mdi-robot-outline</v-icon>
        </v-avatar>
        <div
          :class="[
            'message-bubble pa-4 rounded-xl max-width-70',
            message.role === 'user' 
              ? 'bg-primary text-primary-on-surface ml-3 elevation-1' 
              : 'bg-surface-variant mr-3 elevation-1'
          ]"
        >
          <div class="text-body-1">
            <div 
              v-if="message.role === 'assistant' && typeof message.content === 'string'"
              v-html="renderMarkdown(message.content)"
              class="markdown-content"
            ></div>
            <div v-else>
              {{ typeof message.content === 'string' ? message.content : JSON.stringify(message.content) }}
            </div>
          </div>
          <div class="text-caption mt-2 opacity-70">
            {{ formatTime(message.timestamp) }}
          </div>
        </div>
        <v-avatar v-if="message.role === 'user'" class="ml-3" size="36" color="secondary" variant="tonal">
          <v-icon size="20">mdi-account-outline</v-icon>
        </v-avatar>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="d-flex justify-start mb-4">
      <v-avatar class="mr-3" size="36" color="primary" variant="tonal">
        <v-icon size="20">mdi-robot-outline</v-icon>
      </v-avatar>
      <div class="bg-surface-variant pa-4 rounded-xl mr-3 elevation-1">
        <div class="d-flex align-center gap-3">
          <v-progress-circular indeterminate size="20" width="2" color="primary"></v-progress-circular>
          <span class="text-body-1 font-weight-medium">AI正在思考...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { formatTime } from '@/utils/date'

// 配置markdown渲染器
marked.setOptions({
  breaks: true, // 支持换行
  gfm: true,    // 支持GitHub风格Markdown
  headerIds: false, // 禁用标题ID
  mangle: false     // 禁用标题混淆
})

defineProps({
  messages: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  quickQuestions: {
    type: Array,
    required: true
  }
})

defineEmits(['ask-question'])

const messagesRef = ref(null)

// Markdown渲染函数
const renderMarkdown = (content) => {
  try {
    // 先用marked渲染Markdown
    const rawHtml = marked(content)
    // 然后用DOMPurify清理HTML，防止XSS攻击
    return DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre'],
      ALLOWED_ATTR: ['class']
    })
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return content // 如果渲染失败，返回原始文本
  }
}

defineExpose({
  messagesRef
})
</script>

<style scoped>
.messages-container {
  height: 100%;
  overflow-y: auto;
  padding: 1rem;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.welcome-section {
  max-width: 800px;
  width: 100%;
}

.quick-start-section {
  margin-top: 2rem;
}

.quick-card {
  transition: all 0.2s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

.message-wrapper {
  animation: slideIn 0.3s ease-out;
}

.max-width-70 {
  max-width: 70%;
}

.cursor-pointer {
  cursor: pointer;
}

/* Markdown样式 */
.markdown-content {
  line-height: 1.6;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 1em 0 0.5em 0;
  font-weight: 600;
}

.markdown-content h1 {
  font-size: 1.5em;
}

.markdown-content h2 {
  font-size: 1.3em;
}

.markdown-content h3 {
  font-size: 1.1em;
}

.markdown-content p {
  margin: 0.8em 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 0.8em 0;
  padding-left: 1.5em;
}

.markdown-content li {
  margin: 0.3em 0;
}

.markdown-content blockquote {
  border-left: 4px solid #ddd;
  margin: 1em 0;
  padding-left: 1em;
  color: #666;
  font-style: italic;
}

.markdown-content code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 0.9em;
}

.markdown-content pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1em 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
}

.markdown-content strong {
  font-weight: 600;
}

.markdown-content em {
  font-style: italic;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

