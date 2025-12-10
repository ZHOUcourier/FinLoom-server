<template>
  <div>
    <!-- 悬浮按钮 -->
    <v-btn
      color="primary"
      icon
      size="large"
      elevation="4"
      class="message-fab"
      @click="dialog = true"
    >
      <v-icon>mdi-message-text</v-icon>
    </v-btn>

    <!-- 留言对话框 -->
    <v-dialog v-model="dialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-message-alert</v-icon>
          <span>我想对管理员说</span>
        </v-card-title>

        <v-card-text>
          <v-select
            v-model="messageType"
            :items="messageTypes"
            label="留言类型"
            variant="outlined"
            density="compact"
            class="mb-4"
          ></v-select>

          <v-text-field
            v-model="subject"
            label="主题（可选）"
            variant="outlined"
            density="compact"
            class="mb-4"
          ></v-text-field>

          <v-textarea
            v-model="content"
            label="留言内容"
            variant="outlined"
            rows="6"
            auto-grow
            required
            placeholder="请输入你想对管理员说的话..."
          ></v-textarea>

          <v-alert v-if="errorMessage" type="error" variant="tonal" closable @click:close="errorMessage = ''">
            {{ errorMessage }}
          </v-alert>

          <v-alert v-if="successMessage" type="success" variant="tonal" closable @click:close="successMessage = ''">
            {{ successMessage }}
          </v-alert>

          <!-- 我的留言历史 -->
          <v-expansion-panels v-if="myMessages.length > 0" class="mt-4">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon class="mr-2">mdi-history</v-icon>
                我的留言历史 ({{ myMessages.length }})
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list density="compact">
                  <v-list-item v-for="msg in myMessages" :key="msg.message_id" class="mb-2">
                    <template v-slot:prepend>
                      <v-icon :color="msg.status === 'replied' ? 'success' : 'grey'">
                        {{ msg.status === 'replied' ? 'mdi-check-circle' : 'mdi-clock-outline' }}
                      </v-icon>
                    </template>

                    <v-list-item-title>
                      {{ msg.subject || '(无主题)' }}
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      {{ msg.content }}
                    </v-list-item-subtitle>

                    <v-list-item-subtitle v-if="msg.reply_content" class="mt-2">
                      <v-chip color="success" size="x-small" class="mr-2">管理员回复</v-chip>
                      {{ msg.reply_content }}
                    </v-list-item-subtitle>

                    <v-list-item-subtitle class="text-caption">
                      {{ formatDate(msg.created_at) }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>

        <v-card-actions>
          <v-btn variant="text" @click="loadMyMessages">
            <v-icon class="mr-1">mdi-refresh</v-icon>
            刷新
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="dialog = false">关闭</v-btn>
          <v-btn color="primary" :loading="sending" @click="sendMessage">发送</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services'

// 数据状态
const dialog = ref(false)
const messageType = ref('feedback')
const subject = ref('')
const content = ref('')
const myMessages = ref([])
const sending = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// 留言类型选项
const messageTypes = [
  { title: '💬 反馈建议', value: 'feedback' },
  { title: '🐛 问题报告', value: 'bug' },
  { title: '❓ 疑问咨询', value: 'question' },
  { title: '💡 功能建议', value: 'suggestion' }
]

// 发送留言
async function sendMessage() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!content.value.trim()) {
    errorMessage.value = '请输入留言内容'
    return
  }

  sending.value = true

  try {
    const res = await api.post('/messages/send', {
      message_type: messageType.value,
      subject: subject.value,
      content: content.value
    })

    if (res.data.status === 'success') {
      successMessage.value = '留言发送成功！管理员会尽快回复'
      content.value = ''
      subject.value = ''
      messageType.value = 'feedback'
      
      // 刷新留言历史
      await loadMyMessages()
    } else {
      errorMessage.value = res.data.message || '发送失败'
    }
  } catch (error) {
    console.error('发送留言失败:', error)
    errorMessage.value = error.response?.data?.message || '发送失败，请稍后重试'
  } finally {
    sending.value = false
  }
}

// 加载我的留言
async function loadMyMessages() {
  try {
    const res = await api.get('/messages/my')
    if (res.data.status === 'success') {
      myMessages.value = res.data.data || []
    }
  } catch (error) {
    console.error('加载留言历史失败:', error)
  }
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadMyMessages()
})
</script>

<style scoped>
.message-fab {
  position: fixed;
  bottom: 100px;
  right: 32px;
  z-index: 200;
  transition: all 0.3s ease;
}

.message-fab:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(103, 80, 164, 0.35) !important;
}
</style>


