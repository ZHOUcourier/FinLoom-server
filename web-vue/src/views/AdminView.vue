<template>
  <v-container fluid class="admin-panel">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 font-weight-bold mb-6">
          <v-icon size="large" class="mr-3">mdi-shield-crown</v-icon>
          管理员中心
        </h1>
      </v-col>
    </v-row>

    <!-- 统计卡片 -->
    <v-row>
      <v-col cols="12" md="3">
        <v-card color="primary" dark>
          <v-card-text>
            <div class="text-overline">总用户数</div>
            <div class="text-h4">{{ stats.total_users || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card color="secondary" dark>
          <v-card-text>
            <div class="text-overline">管理员数</div>
            <div class="text-h4">{{ stats.total_admins || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card color="success" dark>
          <v-card-text>
            <div class="text-overline">30天Token使用</div>
            <div class="text-h4">{{ formatNumber(stats.total_tokens_30d) }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card color="warning" dark>
          <v-card-text>
            <div class="text-overline">未读留言</div>
            <div class="text-h4">{{ stats.unread_messages || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 标签页 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-tabs v-model="currentTab" bg-color="primary">
            <v-tab value="users">
              <v-icon class="mr-2">mdi-account-multiple</v-icon>
              用户管理
            </v-tab>
            <v-tab value="messages">
              <v-icon class="mr-2">mdi-message-alert</v-icon>
              用户留言
              <v-badge v-if="stats.unread_messages" color="error" :content="stats.unread_messages" inline class="ml-2"></v-badge>
            </v-tab>
          </v-tabs>

          <v-window v-model="currentTab">
            <!-- 用户管理标签 -->
            <v-window-item value="users">
              <v-card-text>
                <v-text-field
                  v-model="searchQuery"
                  label="搜索用户"
                  prepend-inner-icon="mdi-magnify"
                  variant="outlined"
                  clearable
                  density="compact"
                  class="mb-4"
                ></v-text-field>

                <v-data-table
                  :headers="userHeaders"
                  :items="filteredUsers"
                  :items-per-page="10"
                  class="elevation-1"
                >
                  <template v-slot:item.permission_level="{ item }">
                    <v-chip :color="getPermissionColor(item.permission_level)" size="small">
                      权限 {{ item.permission_level }}
                    </v-chip>
                  </template>

                  <template v-slot:item.daily_token_limit="{ item }">
                    <span>{{ item.daily_token_limit === -1 ? '无限' : formatNumber(item.daily_token_limit) }}</span>
                  </template>

                  <template v-slot:item.token_usage="{ item }">
                    <div>
                      <div>今日: {{ formatNumber(item.today_usage || 0) }}</div>
                      <div class="text-caption">本月: {{ formatNumber(item.monthly_usage || 0) }}</div>
                    </div>
                  </template>

                  <template v-slot:item.actions="{ item }">
                    <v-btn
                      v-if="item.can_manage"
                      icon="mdi-cog"
                      size="small"
                      variant="text"
                      color="primary"
                      @click="openUserSettings(item)"
                    ></v-btn>
                    <v-btn
                      icon="mdi-information"
                      size="small"
                      variant="text"
                      color="info"
                      @click="viewUserDetails(item)"
                    ></v-btn>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-window-item>

            <!-- 用户留言标签 -->
            <v-window-item value="messages">
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="3">
                    <v-select
                      v-model="messageFilter"
                      :items="messageFilterOptions"
                      label="筛选留言"
                      variant="outlined"
                      density="compact"
                    ></v-select>
                  </v-col>
                </v-row>

                <v-list v-if="filteredMessages.length > 0">
                  <v-list-item
                    v-for="msg in filteredMessages"
                    :key="msg.message_id"
                    :class="msg.status === 'pending' ? 'bg-yellow-lighten-5' : ''"
                  >
                    <template v-slot:prepend>
                      <v-avatar :color="msg.status === 'pending' ? 'warning' : 'grey'">
                        <v-icon>{{ getMessageIcon(msg.message_type) }}</v-icon>
                      </v-avatar>
                    </template>

                    <v-list-item-title>
                      <strong>{{ msg.username }}</strong>
                      {{ msg.subject || '(无主题)' }}
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      {{ msg.content }}
                      <div class="text-caption mt-1">
                        {{ formatDate(msg.created_at) }}
                      </div>
                    </v-list-item-subtitle>

                    <template v-slot:append>
                      <v-btn
                        v-if="msg.status !== 'replied'"
                        color="primary"
                        variant="text"
                        @click="replyToMessage(msg)"
                      >
                        回复
                      </v-btn>
                      <v-chip v-else color="success" size="small">已回复</v-chip>
                    </template>
                  </v-list-item>
                </v-list>
                <v-alert v-else type="info" variant="tonal" class="mt-4">
                  暂无留言
                </v-alert>
              </v-card-text>
            </v-window-item>
          </v-window>
        </v-card>
      </v-col>
    </v-row>

    <!-- 用户设置对话框 -->
    <v-dialog v-model="settingsDialog" max-width="600">
      <v-card v-if="selectedUser">
        <v-card-title>
          <v-icon class="mr-2">mdi-cog</v-icon>
          设置用户权限 - {{ selectedUser.username }}
        </v-card-title>

        <v-card-text>
          <div class="mb-6">
            <div class="text-subtitle-1 font-weight-bold mb-2">
              权限等级: {{ userSettings.permission_level }}
            </div>
            <v-slider
              v-model="userSettings.permission_level"
              :min="1"
              :max="maxPermission"
              :step="1"
              thumb-label="always"
              :color="getPermissionColor(userSettings.permission_level)"
              :disabled="!selectedUser.can_manage"
            >
              <template v-slot:append>
                <v-chip :color="getPermissionColor(userSettings.permission_level)" size="small">
                  {{ userSettings.permission_level === 1 ? '普通用户' : '管理员' }}
                </v-chip>
              </template>
            </v-slider>
            <div class="text-caption text-medium-emphasis">
              权限1=普通用户，2-128=管理员，你的权限: {{ currentUserPermission }}
            </div>
          </div>

          <div class="mb-4">
            <div class="text-subtitle-1 font-weight-bold mb-2">
              每日Token限额: {{ userSettings.token_limit === -1 ? '无限' : formatNumber(userSettings.token_limit) }}
            </div>
            <v-slider
              v-model="userSettings.token_limit"
              :min="-1"
              :max="10000000"
              :step="1000"
              thumb-label="always"
              color="success"
            >
              <template v-slot:prepend>
                <v-btn
                  icon="mdi-infinity"
                  size="small"
                  variant="text"
                  @click="userSettings.token_limit = -1"
                  title="设置为无限"
                ></v-btn>
              </template>
            </v-slider>
            <div class="text-caption text-medium-emphasis">
              -1表示无限，普通用户默认30000
            </div>
          </div>

          <v-alert v-if="settingsError" type="error" variant="tonal" closable @click:close="settingsError = ''">
            {{ settingsError }}
          </v-alert>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="settingsDialog = false">取消</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveUserSettings">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 回复留言对话框 -->
    <v-dialog v-model="replyDialog" max-width="600">
      <v-card v-if="selectedMessage">
        <v-card-title>
          <v-icon class="mr-2">mdi-reply</v-icon>
          回复留言
        </v-card-title>

        <v-card-text>
          <div class="mb-4">
            <div class="text-subtitle-2 font-weight-bold">用户: {{ selectedMessage.username }}</div>
            <div class="text-body-2 mt-2">{{ selectedMessage.content }}</div>
          </div>

          <v-textarea
            v-model="replyContent"
            label="回复内容"
            variant="outlined"
            rows="4"
            auto-grow
          ></v-textarea>

          <v-alert v-if="replyError" type="error" variant="tonal" closable @click:close="replyError = ''">
            {{ replyError }}
          </v-alert>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="replyDialog = false">取消</v-btn>
          <v-btn color="primary" :loading="replying" @click="sendReply">发送</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services'

// 数据状态
const currentTab = ref('users')
const users = ref([])
const messages = ref([])
const stats = ref({})
const searchQuery = ref('')
const messageFilter = ref('all')

// 对话框状态
const settingsDialog = ref(false)
const replyDialog = ref(false)
const selectedUser = ref(null)
const selectedMessage = ref(null)
const userSettings = ref({
  permission_level: 1,
  token_limit: 30000
})
const replyContent = ref('')

// 加载状态
const saving = ref(false)
const replying = ref(false)
const settingsError = ref('')
const replyError = ref('')

// 当前用户权限
const currentUserPermission = ref(1)
const maxPermission = computed(() => Math.max(1, currentUserPermission.value - 1))

// 表格列定义
const userHeaders = [
  { title: '用户名', key: 'username', sortable: true },
  { title: '权限等级', key: 'permission_level', sortable: true },
  { title: 'Token限额', key: 'daily_token_limit', sortable: true },
  { title: 'Token使用', key: 'token_usage', sortable: false },
  { title: '最后登录', key: 'last_login', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

// 留言筛选选项
const messageFilterOptions = [
  { title: '全部', value: 'all' },
  { title: '待处理', value: 'pending' },
  { title: '已读', value: 'read' },
  { title: '已回复', value: 'replied' }
]

// 计算属性
const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(user => 
    user.username.toLowerCase().includes(query) ||
    user.email?.toLowerCase().includes(query)
  )
})

const filteredMessages = computed(() => {
  if (messageFilter.value === 'all') return messages.value
  return messages.value.filter(msg => msg.status === messageFilter.value)
})

// 方法
async function loadData() {
  try {
    // 获取当前用户权限
    const profileRes = await api.auth.getProfile()
    console.log('用户权限响应:', profileRes)
    
    if (profileRes.status === 'success') {
      currentUserPermission.value = profileRes.data?.permission_level || 1
    }

    // 加载统计信息
    const statsRes = await api.admin.getStats()
    console.log('统计信息响应:', statsRes)
    
    if (statsRes.status === 'success') {
      stats.value = statsRes.data
    }

    // 加载用户列表
    const usersRes = await api.admin.getUsers()
    console.log('用户列表响应:', usersRes)
    
    if (usersRes.status === 'success') {
      users.value = usersRes.data || []
      console.log('用户列表加载成功，共', users.value.length, '个用户')
    }

    // 加载留言
    const messagesRes = await api.admin.getMessages()
    console.log('留言响应:', messagesRes)
    
    if (messagesRes.status === 'success') {
      messages.value = messagesRes.data?.messages || []
    }
  } catch (error) {
    console.error('加载管理数据失败:', error)
  }
}

function openUserSettings(user) {
  selectedUser.value = user
  userSettings.value = {
    permission_level: user.permission_level,
    token_limit: user.daily_token_limit
  }
  settingsError.value = ''
  settingsDialog.value = true
}

async function saveUserSettings() {
  if (!selectedUser.value) return

  saving.value = true
  settingsError.value = ''

  try {
    console.log('保存用户设置:', selectedUser.value.user_id, userSettings.value)
    
    // 更新权限
    if (userSettings.value.permission_level !== selectedUser.value.permission_level) {
      const permRes = await api.admin.updateUserPermission(
        selectedUser.value.user_id, 
        userSettings.value.permission_level
      )
      if (permRes.status !== 'success') {
        settingsError.value = permRes.message || '权限更新失败'
        saving.value = false
        return
      }
    }

    // 更新token限额
    if (userSettings.value.token_limit !== selectedUser.value.daily_token_limit) {
      const limitRes = await api.admin.updateUserTokenLimit(
        selectedUser.value.user_id, 
        userSettings.value.token_limit
      )
      if (limitRes.status !== 'success') {
        settingsError.value = limitRes.message || 'Token限额更新失败'
        saving.value = false
        return
      }
    }

    // 刷新数据
    await loadData()
    settingsDialog.value = false
  } catch (error) {
    console.error('保存设置失败:', error)
    settingsError.value = error.message || '保存失败'
  } finally {
    saving.value = false
  }
}

function replyToMessage(msg) {
  selectedMessage.value = msg
  replyContent.value = ''
  replyError.value = ''
  replyDialog.value = true
}

async function sendReply() {
  if (!selectedMessage.value || !replyContent.value.trim()) {
    replyError.value = '请输入回复内容'
    return
  }

  replying.value = true
  replyError.value = ''

  try {
    const res = await api.admin.replyToMessage(
      selectedMessage.value.message_id,
      replyContent.value
    )

    if (res.status === 'success') {
      await loadData()
      replyDialog.value = false
    } else {
      replyError.value = res.message || '回复失败'
    }
  } catch (error) {
    console.error('回复失败:', error)
    replyError.value = error.message || '回复失败'
  } finally {
    replying.value = false
  }
}

function viewUserDetails(user) {
  // TODO: 实现用户详情查看
  console.log('查看用户详情:', user)
}

function getPermissionColor(level) {
  if (level === 1) return 'grey'
  if (level >= 100) return 'purple'
  if (level >= 50) return 'deep-purple'
  if (level >= 10) return 'indigo'
  return 'primary'
}

function getMessageIcon(type) {
  const icons = {
    feedback: 'mdi-message-text',
    bug: 'mdi-bug',
    question: 'mdi-help-circle',
    suggestion: 'mdi-lightbulb'
  }
  return icons[type] || 'mdi-message'
}

function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.admin-panel {
  padding: 24px;
}

.v-data-table {
  border-radius: 8px;
}
</style>


