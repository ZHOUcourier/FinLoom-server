<template>
  <v-container fluid class="settings-view pa-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
          <h1 class="text-h3 font-weight-bold mb-2">系统设置</h1>
          <p class="text-body-1 text-medium-emphasis">管理您的账户和系统配置</p>
        </div>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-download"
            @click="exportSettings"
            rounded="pill"
          >
            导出设置
          </v-btn>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <v-row>
      <!-- 侧边栏导航 - Material 3 风格 -->
      <v-col cols="12" md="3">
        <v-card variant="flat">
          <v-list nav density="comfortable" bg-color="transparent">
            <v-list-item
              v-for="tab in settingsTabs"
              :key="tab.id"
              :value="tab.id"
              :active="activeTab === tab.id"
              @click="activeTab = tab.id"
              :prepend-icon="tab.icon"
              :title="tab.label"
              rounded="xl"
              color="primary"
            >
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- 内容区域 -->
      <v-col cols="12" md="9">
        <v-window v-model="activeTab" class="settings-window">
          <!-- 个人信息 - Material 3 风格 -->
          <v-window-item value="profile">
            <v-card variant="elevated">
              <v-card-title class="text-h5 font-weight-bold d-flex align-center justify-space-between pa-6">
                <div class="d-flex align-center">
                  <v-avatar color="primary" variant="tonal" size="48" class="mr-4">
                    <v-icon size="32">mdi-account</v-icon>
                  </v-avatar>
                  <div>
                    <div>个人信息</div>
                    <div class="text-caption text-medium-emphasis font-weight-regular">
                      管理您的账户信息
                      <span class="text-warning ml-2" style="font-size: 0.7rem;">每月仅能修改一次</span>
                    </div>
                  </div>
                </div>
                <!-- 显示上次修改时间 -->
                <div v-if="profileLastModified" class="text-caption text-medium-emphasis">
                  上次修改: {{ profileLastModified }}
                </div>
              </v-card-title>
              <v-card-text class="pa-6">
                <v-form ref="profileForm">
                  <v-text-field
                    v-model="profile.username"
                    label="用户名"
                    prepend-inner-icon="mdi-account-circle"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    :readonly="!isEditingProfile"
                    :disabled="!isEditingProfile"
                  ></v-text-field>

                  <v-text-field
                    v-model="profile.email"
                    label="邮箱"
                    type="email"
                    prepend-inner-icon="mdi-email"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    :readonly="!isEditingProfile"
                    :disabled="!isEditingProfile"
                  ></v-text-field>

                  <v-text-field
                    v-model="profile.phone"
                    label="电话"
                    type="tel"
                    prepend-inner-icon="mdi-phone"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    :readonly="!isEditingProfile"
                    :disabled="!isEditingProfile"
                  ></v-text-field>

                  <!-- 密码显示 -->
                  <v-text-field
                    v-model="profile.password"
                    label="当前密码"
                    prepend-inner-icon="mdi-lock"
                    type="password"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    readonly
                    hint="密码已加密保护，不可查看"
                    persistent-hint
                  ></v-text-field>

                  <!-- 修改信息时的密码验证 -->
                  <v-expand-transition>
                    <div v-if="isEditingProfile" class="mt-4 pa-4" style="background: rgba(var(--v-theme-primary), 0.05); border-radius: 8px;">
                      <div class="text-subtitle-2 font-weight-bold mb-3">
                        <v-icon size="small" class="mr-2">mdi-shield-lock</v-icon>
                        安全验证
                      </div>
                      <v-text-field
                        v-model="verifyPassword"
                        label="请输入当前密码以验证身份"
                        prepend-inner-icon="mdi-lock-check"
                        type="password"
                        variant="outlined"
                        density="comfortable"
                        :rules="[v => !!v || '请输入密码以验证身份']"
                        required
                      ></v-text-field>
                    </div>
                  </v-expand-transition>
                </v-form>
              </v-card-text>
              <v-card-actions class="px-6 pb-6">
                <v-btn
                  v-if="!isEditingProfile"
                  color="primary"
                  size="large"
                  variant="elevated"
                  prepend-icon="mdi-pencil"
                  @click="startEditProfile"
                  :disabled="!canModifyProfile"
                >
                  修改信息
                </v-btn>
                <template v-else>
                  <v-btn
                    color="primary"
                    size="large"
                    variant="elevated"
                    prepend-icon="mdi-content-save"
                    @click="confirmSaveProfile"
                    :loading="savingProfile"
                  >
                    保存更改
                  </v-btn>
                  <v-btn
                    size="large"
                    variant="text"
                    @click="cancelEditProfile"
                  >
                    取消
                  </v-btn>
                </template>
                <v-spacer></v-spacer>
                <div v-if="!canModifyProfile" class="text-caption text-error">
                  本月已修改，下月才能再次修改
                </div>
              </v-card-actions>
            </v-card>
          </v-window-item>

          <!-- 交易设置 -->
          <v-window-item value="trading">
            <v-card elevation="2" rounded="lg">
              <v-card-title class="text-h5 font-weight-bold">
                <v-icon start>mdi-chart-line</v-icon>
                交易设置
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-form>
                  <v-select
                    v-model="trading.orderType"
                    :items="orderTypes"
                    label="默认订单类型"
                    prepend-inner-icon="mdi-file-document-edit"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                  ></v-select>

                  <v-text-field
                    v-model.number="trading.riskLimit"
                    label="风险限额 (%)"
                    type="number"
                    prepend-inner-icon="mdi-shield-alert"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    min="0"
                    max="100"
                  ></v-text-field>

                  <v-switch
                    v-model="trading.confirmOrders"
                    label="下单前需要确认"
                    color="primary"
                    inset
                    hide-details
                    class="mb-2"
                  ></v-switch>

                  <v-switch
                    v-model="trading.autoStopLoss"
                    label="自动设置止损"
                    color="primary"
                    inset
                    hide-details
                    class="mb-2"
                  ></v-switch>
                </v-form>
              </v-card-text>
              <v-card-actions class="px-6 pb-6">
                <v-btn
                  color="primary"
                  size="large"
                  variant="elevated"
                  prepend-icon="mdi-content-save"
                  @click="saveTrading"
                >
                  保存更改
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-window-item>

          <!-- 通知设置 -->
          <v-window-item value="notifications">
            <v-card elevation="2" rounded="lg">
              <v-card-title class="text-h5 font-weight-bold">
                <v-icon start>mdi-bell</v-icon>
                通知设置
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-list>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon color="primary">mdi-email</v-icon>
                    </template>
                    <v-list-item-title>邮件通知</v-list-item-title>
                    <v-list-item-subtitle>接收交易和价格提醒邮件</v-list-item-subtitle>
                    <template v-slot:append>
                      <v-switch
                        v-model="notifications.email"
                        color="primary"
                        hide-details
                        inset
                      ></v-switch>
                    </template>
                  </v-list-item>

                  <v-divider></v-divider>

                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon color="primary">mdi-message-text</v-icon>
                    </template>
                    <v-list-item-title>短信通知</v-list-item-title>
                    <v-list-item-subtitle>接收重要交易短信提醒</v-list-item-subtitle>
                    <template v-slot:append>
                      <v-switch
                        v-model="notifications.sms"
                        color="primary"
                        hide-details
                        inset
                      ></v-switch>
                    </template>
                  </v-list-item>

                  <v-divider></v-divider>

                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon color="primary">mdi-cellphone</v-icon>
                    </template>
                    <v-list-item-title>推送通知</v-list-item-title>
                    <v-list-item-subtitle>接收应用推送消息</v-list-item-subtitle>
                    <template v-slot:append>
                      <v-switch
                        v-model="notifications.push"
                        color="primary"
                        hide-details
                        inset
                      ></v-switch>
                    </template>
                  </v-list-item>

                  <v-divider></v-divider>

                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon color="warning">mdi-alert</v-icon>
                    </template>
                    <v-list-item-title>价格预警</v-list-item-title>
                    <v-list-item-subtitle>价格达到设定值时通知</v-list-item-subtitle>
                    <template v-slot:append>
                      <v-switch
                        v-model="notifications.priceAlerts"
                        color="primary"
                        hide-details
                        inset
                      ></v-switch>
                    </template>
                  </v-list-item>
                </v-list>
              </v-card-text>
              <v-card-actions class="px-6 pb-6">
                <v-btn
                  color="primary"
                  size="large"
                  variant="elevated"
                  prepend-icon="mdi-content-save"
                  @click="saveNotifications"
                >
                  保存更改
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-window-item>

          <!-- 安全设置 -->
          <v-window-item value="security">
            <v-card elevation="2" rounded="lg">
              <v-card-title class="text-h5 font-weight-bold d-flex justify-space-between align-center">
                <div>
                  <v-icon start>mdi-shield-lock</v-icon>
                  安全设置
                </div>
                <v-btn
                  color="error"
                  variant="outlined"
                  prepend-icon="mdi-logout"
                  @click="handleLogout"
                >
                  退出登录
                </v-btn>
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-form ref="securityForm">
                  <v-text-field
                    v-model="security.currentPassword"
                    label="当前密码"
                    type="password"
                    prepend-inner-icon="mdi-lock"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    :rules="[rules.required]"
                  ></v-text-field>

                  <v-text-field
                    v-model="security.newPassword"
                    label="新密码"
                    type="password"
                    prepend-inner-icon="mdi-lock-reset"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    :rules="[rules.required, rules.minLength]"
                  ></v-text-field>

                  <v-text-field
                    v-model="security.confirmPassword"
                    label="确认新密码"
                    type="password"
                    prepend-inner-icon="mdi-lock-check"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    :rules="[rules.required, rules.passwordMatch]"
                  ></v-text-field>

                  <v-divider class="my-4"></v-divider>

                  <v-switch
                    v-model="security.twoFactorAuth"
                    label="启用两步验证"
                    color="primary"
                    inset
                    hide-details
                    class="mb-2"
                  >
                    <template v-slot:prepend>
                      <v-icon color="success">mdi-shield-check</v-icon>
                    </template>
                  </v-switch>

                  <v-alert
                    v-if="security.twoFactorAuth"
                    type="info"
                    variant="tonal"
                    class="mt-4"
                    density="compact"
                  >
                    两步验证将增强您的账户安全性
                  </v-alert>
                </v-form>
              </v-card-text>
              <v-card-actions class="px-6 pb-6">
                <v-btn
                  color="primary"
                  size="large"
                  variant="elevated"
                  prepend-icon="mdi-key-change"
                  @click="updatePassword"
                >
                  更新密码
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-window-item>

          <!-- 系统偏好 -->
          <v-window-item value="preferences">
            <v-card elevation="2" rounded="lg">
              <v-card-title class="text-h5 font-weight-bold">
                <v-icon start>mdi-cog</v-icon>
                系统偏好
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-form>
                  <v-select
                    v-model="preferences.language"
                    :items="languages"
                    label="语言"
                    prepend-inner-icon="mdi-translate"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                  ></v-select>

                  <v-select
                    v-model="preferences.timezone"
                    :items="timezones"
                    label="时区"
                    prepend-inner-icon="mdi-clock-outline"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                  ></v-select>

                  <v-select
                    v-model="preferences.theme"
                    :items="themes"
                    label="主题"
                    prepend-inner-icon="mdi-palette"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    @update:model-value="changeTheme"
                  ></v-select>

                  <v-select
                    v-model="preferences.chartStyle"
                    :items="chartStyles"
                    label="图表风格"
                    prepend-inner-icon="mdi-chart-areaspline"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                  ></v-select>
                </v-form>
              </v-card-text>
              <v-card-actions class="px-6 pb-6">
                <v-btn
                  color="primary"
                  size="large"
                  variant="elevated"
                  prepend-icon="mdi-content-save"
                  @click="savePreferences"
                >
                  保存更改
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-window-item>

          <!-- API设置 -->
          <v-window-item value="api">
            <v-card variant="elevated">
              <v-card-title class="text-h5 font-weight-bold d-flex align-center pa-6">
                <v-avatar color="info" variant="tonal" size="48" class="mr-4">
                  <v-icon size="32">mdi-api</v-icon>
                </v-avatar>
                <div>
                  <div>API设置</div>
                  <div class="text-caption text-medium-emphasis font-weight-regular">管理API密钥和接口配置</div>
                </div>
              </v-card-title>
              <v-card-text class="pa-6">
                <v-form>
                  <v-text-field
                    v-model="apiSettings.apiKey"
                    label="API密钥"
                    prepend-inner-icon="mdi-key"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    :type="showApiKey ? 'text' : 'password'"
                    :append-inner-icon="showApiKey ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showApiKey = !showApiKey"
                    readonly
                  ></v-text-field>

                  <v-text-field
                    v-model="apiSettings.secretKey"
                    label="密钥"
                    prepend-inner-icon="mdi-key-variant"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                    :type="showSecretKey ? 'text' : 'password'"
                    :append-inner-icon="showSecretKey ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showSecretKey = !showSecretKey"
                    readonly
                  ></v-text-field>

                  <v-select
                    v-model="apiSettings.environment"
                    :items="apiEnvironments"
                    label="环境"
                    prepend-inner-icon="mdi-server"
                    variant="outlined"
                    density="comfortable"
                    class="mb-4"
                  ></v-select>

                  <v-switch
                    v-model="apiSettings.enabled"
                    label="启用API交易"
                    color="primary"
                    inset
                    hide-details
                    class="mb-2"
                  ></v-switch>

                  <v-switch
                    v-model="apiSettings.autoRefresh"
                    label="自动刷新令牌"
                    color="primary"
                    inset
                    hide-details
                    class="mb-2"
                  ></v-switch>
                </v-form>
              </v-card-text>
              <v-card-actions class="px-6 pb-6">
                <v-btn
                  color="primary"
                  size="large"
                  variant="elevated"
                  prepend-icon="mdi-content-save"
                  @click="saveApi"
                >
                  保存更改
                </v-btn>
                <v-btn
                  color="warning"
                  size="large"
                  variant="outlined"
                  prepend-icon="mdi-refresh"
                  @click="regenerateApiKey"
                >
                  重新生成
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-window-item>

          <!-- 数据备份 -->
          <v-window-item value="backup">
            <v-card variant="elevated">
              <v-card-title class="text-h5 font-weight-bold d-flex align-center pa-6">
                <v-avatar color="success" variant="tonal" size="48" class="mr-4">
                  <v-icon size="32">mdi-backup-restore</v-icon>
                </v-avatar>
                <div>
                  <div>数据备份</div>
                  <div class="text-caption text-medium-emphasis font-weight-regular">备份和恢复您的数据</div>
                </div>
              </v-card-title>
              <v-card-text class="pa-6">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-card variant="outlined" class="pa-4">
                      <div class="d-flex align-center mb-4">
                        <v-icon color="primary" class="mr-3">mdi-download</v-icon>
                        <h3 class="text-h6 font-weight-bold">导出数据</h3>
                      </div>
                      <p class="text-body-2 text-medium-emphasis mb-4">
                        导出您的投资组合、交易记录和设置数据
                      </p>
                      <v-btn
                        color="primary"
                        variant="elevated"
                        prepend-icon="mdi-download"
                        @click="exportData"
                        block
                      >
                        导出数据
                      </v-btn>
                    </v-card>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-card variant="outlined" class="pa-4">
                      <div class="d-flex align-center mb-4">
                        <v-icon color="success" class="mr-3">mdi-upload</v-icon>
                        <h3 class="text-h6 font-weight-bold">导入数据</h3>
                      </div>
                      <p class="text-body-2 text-medium-emphasis mb-4">
                        从备份文件恢复您的数据
                      </p>
                      <v-btn
                        color="success"
                        variant="elevated"
                        prepend-icon="mdi-upload"
                        @click="importData"
                        block
                      >
                        导入数据
                      </v-btn>
                    </v-card>
                  </v-col>
                </v-row>

                <v-divider class="my-6"></v-divider>

                <h3 class="text-h6 font-weight-bold mb-4">备份历史</h3>
                <v-list>
                  <v-list-item
                    v-for="backup in backupHistory"
                    :key="backup.id"
                    class="px-0"
                  >
                    <template v-slot:prepend>
                      <v-avatar color="primary" variant="tonal" size="40">
                        <v-icon>mdi-file-document</v-icon>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="font-weight-bold">{{ backup.name }}</v-list-item-title>
                    <v-list-item-subtitle>{{ backup.date }} | {{ backup.size }}</v-list-item-subtitle>
                    <template v-slot:append>
                      <div class="d-flex gap-1">
                        <v-btn
                          icon="mdi-download"
                          variant="text"
                          size="small"
                          @click="downloadBackup(backup)"
                        ></v-btn>
                        <v-btn
                          icon="mdi-delete"
                          variant="text"
                          size="small"
                          color="error"
                          @click="deleteBackup(backup)"
                        ></v-btn>
                      </div>
                    </template>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-window-item>
        </v-window>
      </v-col>
    </v-row>

    <!-- 确认修改对话框 -->
    <v-dialog v-model="confirmDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-6 d-flex align-center">
          <v-icon color="warning" size="32" class="mr-3">mdi-alert-circle</v-icon>
          <span>确认修改信息</span>
        </v-card-title>
        <v-card-text class="pa-6">
          <div class="text-body-1 mb-4">
            请仔细确认您的信息修改无误？
          </div>
          <v-alert 
            type="warning" 
            variant="tonal" 
            density="compact"
            class="mb-0"
          >
            <div class="text-body-2 font-weight-bold">
              重要提示：每月仅能更改一次个人信息
            </div>
            <div class="text-caption mt-1">
              修改后，本月内将无法再次修改
            </div>
          </v-alert>
        </v-card-text>
        <v-card-actions class="px-6 pb-6">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="confirmDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            @click="executeSaveProfile"
            :loading="savingProfile"
          >
            确认修改
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar 提示 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
      location="top"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn icon="mdi-close" size="small" @click="snackbar.show = false"></v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useTheme } from 'vuetify'
import { useUserStore } from '@/stores/user'
import { useRoute } from 'vue-router'
import { api } from '@/services'

const theme = useTheme()
const userStore = useUserStore()
const route = useRoute()
const activeTab = ref('profile')

// 监听URL query参数切换标签
watch(() => route.query.tab, (newTab) => {
  if (newTab) {
    activeTab.value = newTab
  }
}, { immediate: true })

// 设置标签页 - 根据用户权限动态生成
const settingsTabs = computed(() => {
  const tabs = [
    { id: 'profile', label: '个人信息', icon: 'mdi-account' },
    { id: 'trading', label: '交易设置', icon: 'mdi-chart-line' },
    { id: 'notifications', label: '通知设置', icon: 'mdi-bell' },
    { id: 'security', label: '安全设置', icon: 'mdi-shield-lock' },
    { id: 'preferences', label: '系统偏好', icon: 'mdi-cog' }
  ]
  
  // 仅管理员可见API设置
  if (userStore.isAdmin) {
    tabs.push({ id: 'api', label: 'API设置', icon: 'mdi-api' })
  }
  
  tabs.push({ id: 'backup', label: '数据备份', icon: 'mdi-backup-restore' })
  
  return tabs
})

// 个人信息状态
const profile = ref({
  username: '',
  email: '',
  phone: '',
  password: '********'  // 默认显示为星号
})

const profileForm = ref(null)
const isEditingProfile = ref(false)
const verifyPassword = ref('')
const savingProfile = ref(false)
const confirmDialog = ref(false)
const profileLastModified = ref('')
const canModifyProfile = ref(true)
const originalProfileData = ref({})
const actualPassword = ref('')  // 存储真实密码（仅用于后台验证，不显示给用户）

// 加载用户信息
onMounted(async () => {
  try {
    // 确保用户信息已加载
    if (!userStore.userInfo) {
      await userStore.fetchUserInfo()
    }
    
    // 获取用户完整信息（包括密码和最后修改时间）
    const response = await api.user.getUserProfile()
    
    actualPassword.value = response.data.password || ''
    profile.value = {
      username: userStore.displayName,
      email: userStore.email,
      phone: userStore.phone || '+86 138 0000 0000',
      password: '********'
    }
    
    // 保存原始数据
    originalProfileData.value = { ...profile.value }
    
    // 处理最后修改时间
    if (response.data.last_modified) {
      profileLastModified.value = formatDateTime(response.data.last_modified)
      // 检查是否在本月内修改过
      canModifyProfile.value = !isModifiedThisMonth(response.data.last_modified)
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
    showMessage('加载用户信息失败', 'error')
  }
})

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 检查是否在本月修改过
const isModifiedThisMonth = (lastModified) => {
  if (!lastModified) return false
  const lastDate = new Date(lastModified)
  const now = new Date()
  return lastDate.getFullYear() === now.getFullYear() && 
         lastDate.getMonth() === now.getMonth()
}

// 开始编辑个人信息
const startEditProfile = () => {
  if (!canModifyProfile.value) {
    showMessage('本月已修改过，下月才能再次修改', 'warning')
    return
  }
  isEditingProfile.value = true
  verifyPassword.value = ''
}

// 取消编辑
const cancelEditProfile = () => {
  isEditingProfile.value = false
  profile.value = { ...originalProfileData.value }
  verifyPassword.value = ''
}

// 确认保存（显示对话框）
const confirmSaveProfile = () => {
  // 验证表单
  if (!verifyPassword.value) {
    showMessage('请输入密码以验证身份', 'error')
    return
  }
  
  confirmDialog.value = true
}

// 执行保存
const executeSaveProfile = async () => {
  savingProfile.value = true
  
  try {
    // 验证密码
    if (verifyPassword.value !== actualPassword.value) {
      showMessage('密码验证失败，请检查密码是否正确', 'error')
      savingProfile.value = false
      return
    }
    
    // 调用API更新用户信息
    const response = await api.user.updateProfile({
      username: profile.value.username,
      email: profile.value.email,
      phone: profile.value.phone,
      verify_password: verifyPassword.value
    })
    
    if (response.status === 'success') {
      // 更新本地数据
      originalProfileData.value = { ...profile.value }
      profileLastModified.value = formatDateTime(new Date())
      canModifyProfile.value = false
      
      // 更新userStore
      await userStore.fetchUserInfo()
      
      showMessage('个人信息已成功更新')
      isEditingProfile.value = false
      confirmDialog.value = false
      verifyPassword.value = ''
    }
  } catch (error) {
    console.error('保存个人信息失败:', error)
    showMessage('保存失败: ' + (error.response?.data?.error || error.message), 'error')
  } finally {
    savingProfile.value = false
  }
}

// 交易设置
const trading = ref({
  orderType: 'market',
  riskLimit: 2,
  confirmOrders: true,
  autoStopLoss: false
})

const orderTypes = [
  { title: '市价单', value: 'market' },
  { title: '限价单', value: 'limit' },
  { title: '止损单', value: 'stop' }
]

// 通知设置
const notifications = ref({
  email: true,
  sms: false,
  push: true,
  priceAlerts: true
})

// 安全设置
const security = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
  twoFactorAuth: false
})

// 表单验证规则
const rules = {
  required: value => !!value || '此字段为必填项',
  minLength: value => (value && value.length >= 8) || '密码至少需要8个字符',
  passwordMatch: value => value === security.value.newPassword || '两次输入的密码不匹配'
}

// 系统偏好
const preferences = ref({
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  theme: 'light',
  chartStyle: 'candlestick'
})

const languages = [
  { title: '简体中文', value: 'zh-CN' },
  { title: 'English', value: 'en-US' }
]

const timezones = [
  { title: '上海 (GMT+8)', value: 'Asia/Shanghai' },
  { title: '香港 (GMT+8)', value: 'Asia/Hong_Kong' },
  { title: '纽约 (GMT-5)', value: 'America/New_York' }
]

const themes = [
  { title: '浅色', value: 'light' },
  { title: '深色', value: 'dark' },
  { title: '自动', value: 'auto' }
]

const chartStyles = [
  { title: 'K线图', value: 'candlestick' },
  { title: '折线图', value: 'line' },
  { title: '柱状图', value: 'bar' }
]

// API设置
const apiSettings = ref({
  apiKey: 'ak_1234567890abcdef',
  secretKey: 'sk_abcdef1234567890',
  environment: 'production',
  enabled: true,
  autoRefresh: true
})

const showApiKey = ref(false)
const showSecretKey = ref(false)

const apiEnvironments = [
  { title: '生产环境', value: 'production' },
  { title: '测试环境', value: 'testing' },
  { title: '开发环境', value: 'development' }
]

// 备份历史
const backupHistory = ref([
  {
    id: 1,
    name: '完整备份 - 2025-01-15',
    date: '2025-01-15 14:30',
    size: '2.3 MB'
  },
  {
    id: 2,
    name: '设置备份 - 2025-01-10',
    date: '2025-01-10 09:15',
    size: '156 KB'
  },
  {
    id: 3,
    name: '交易数据备份 - 2025-01-05',
    date: '2025-01-05 16:45',
    size: '1.8 MB'
  }
])

// Snackbar 状态
const snackbar = reactive({
  show: false,
  message: '',
  color: 'success'
})

// 显示提示信息
const showMessage = (message, color = 'success') => {
  snackbar.message = message
  snackbar.color = color
  snackbar.show = true
}

// 其他设置保存方法
const saveTrading = () => {
  showMessage('交易设置已保存')
}

const saveNotifications = () => {
  showMessage('通知设置已保存')
}

const updatePassword = async () => {
  if (security.value.newPassword !== security.value.confirmPassword) {
    showMessage('两次输入的密码不匹配', 'error')
    return
  }
  
  try {
    // 调用API修改密码
    await api.auth.changePassword({
      old_password: security.value.currentPassword,
      new_password: security.value.newPassword
    })
    
    showMessage('密码已更新')
    // 更新实际密码
    actualPassword.value = security.value.newPassword
    security.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
      twoFactorAuth: security.value.twoFactorAuth
    }
  } catch (error) {
    console.error('修改密码失败:', error)
    showMessage('修改密码失败: ' + (error.response?.data?.error || error.message), 'error')
  }
}

const savePreferences = () => {
  showMessage('系统偏好已保存')
}

// 切换主题
const changeTheme = (value) => {
  if (value === 'dark') {
    theme.global.name.value = 'finloomDarkTheme'
  } else if (value === 'light') {
    theme.global.name.value = 'finloomTheme'
  } else {
    // 自动模式：根据系统偏好
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    theme.global.name.value = isDark ? 'finloomDarkTheme' : 'finloomTheme'
  }
}

// 新增方法
const saveApi = () => {
  showMessage('API设置已保存')
}

const regenerateApiKey = () => {
  // 生成新的API密钥
  apiSettings.value.apiKey = 'ak_' + Math.random().toString(36).substr(2, 16)
  apiSettings.value.secretKey = 'sk_' + Math.random().toString(36).substr(2, 16)
  showMessage('API密钥已重新生成', 'warning')
}

const exportSettings = () => {
  showMessage('设置已导出')
}

const exportData = () => {
  showMessage('数据导出已开始')
}

const importData = () => {
  showMessage('数据导入功能开发中', 'info')
}

const downloadBackup = (backup) => {
  showMessage(`正在下载 ${backup.name}`)
}

const deleteBackup = (backup) => {
  const index = backupHistory.value.findIndex(b => b.id === backup.id)
  if (index > -1) {
    backupHistory.value.splice(index, 1)
    showMessage('备份已删除', 'warning')
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    // 调用登出API
    await api.auth.logout()
  } catch (error) {
    console.error('登出API调用失败:', error)
  } finally {
    // 无论API是否成功，都清除本地数据
    localStorage.removeItem('finloom_auth')
    localStorage.removeItem('finloom_token')
    localStorage.removeItem('finloom_user')
    
    // 清除用户store
    userStore.clearUserInfo()
    
    // 跳转到登录页
    window.location.href = '/login'
  }
}
</script>

<style lang="scss" scoped>
.settings-view {
  max-width: 1400px;
  margin: 0 auto;
}

.settings-window {
  // 确保窗口项之间平滑过渡
  :deep(.v-window__container) {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
}

// 自定义卡片样式
:deep(.v-card) {
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  }
}

// 自定义列表项样式
:deep(.v-list-item) {
  margin-bottom: 4px;
  
  &.v-list-item--active {
    font-weight: 600;
  }
}

// 响应式调整
@media (max-width: 960px) {
  .settings-view {
    padding: 1rem !important;
  }
}
</style>

