<template>
  <div class="login-view">
    <v-container fluid class="login-container">
      <v-row no-gutters class="fill-height">
        <!-- 登录表单区域 -->
        <v-col cols="12" md="6" class="d-flex align-center justify-center pa-6">
          <v-card variant="elevated" class="login-card" max-width="480" width="100%">
            <v-card-text class="pa-8">
              <!-- Logo和标题 -->
              <div class="text-center mb-8">
                <div class="logo mb-4">
                  <v-icon size="48" color="white">mdi-chart-network</v-icon>
                </div>
                <h1 class="text-h3 font-weight-bold mb-2">欢迎回来</h1>
                <p class="text-body-1 text-medium-emphasis">登录您的FinLoom账户</p>
                
                <!-- 保存的账号提示 -->
                <v-alert
                  v-if="savedUserInfo"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="mt-4"
                  rounded="lg"
                >
                  <template v-slot:prepend>
                    <v-icon>mdi-account-check</v-icon>
                  </template>
                  <div class="d-flex align-center justify-space-between">
                    <span>
                      检测到上次登录的账号：<strong>{{ savedUserInfo.username }}</strong>
                    </span>
                    <v-btn
                      size="x-small"
                      variant="text"
                      color="primary"
                      @click="clearSavedAccount"
                    >
                      切换账号
                    </v-btn>
                  </div>
                </v-alert>
              </div>

              <!-- 登录表单 -->
              <v-form @submit.prevent="handleLogin">
                <v-text-field
                  v-model="form.username"
                  label="用户名"
                  prepend-inner-icon="mdi-account"
                  variant="outlined"
                  class="mb-4"
                  required
                  :rules="[v => !!v || '请输入用户名']"
                ></v-text-field>

                <v-text-field
                  v-model="form.password"
                  label="密码"
                  prepend-inner-icon="mdi-lock"
                  :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                  :type="showPassword ? 'text' : 'password'"
                  variant="outlined"
                  class="mb-4"
                  required
                  :rules="[v => !!v || '请输入密码']"
                  @click:append-inner="showPassword = !showPassword"
                ></v-text-field>

                <div class="mb-4">
                  <v-checkbox
                    v-model="form.remember"
                    label="记住我"
                    density="compact"
                    hide-details
                  ></v-checkbox>
                </div>

                <v-btn
                  type="submit"
                  color="primary"
                  size="large"
                  block
                  :loading="loading"
                  class="mb-4"
                >
                  登录
                </v-btn>

                <v-alert
                  v-if="errorMessage"
                  type="error"
                  variant="tonal"
                  density="compact"
                  class="mb-4"
                  rounded="lg"
                  closable
                  @click:close="errorMessage = ''"
                >
                  {{ errorMessage }}
                </v-alert>
              </v-form>

              <!-- 注册链接 -->
              <div class="text-center">
                <span class="text-body-2 text-medium-emphasis">还没有账户？</span>
                <v-btn
                  variant="text"
                  color="primary"
                  size="small"
                  class="text-none ml-1"
                  @click="goToRegister"
                >
                  立即注册
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 信息展示区域 -->
        <v-col cols="12" md="6" class="info-panel d-none d-md-flex">
          <div class="info-content">
            <v-icon size="120" color="white" class="mb-6">mdi-chart-timeline-variant</v-icon>
            <h2 class="text-h2 font-weight-bold text-white mb-6">FinLoom量化投资平台</h2>
            
            <v-list class="bg-transparent" density="comfortable">
              <v-list-item
                v-for="feature in features"
                :key="feature.text"
                class="px-0"
              >
                <template v-slot:prepend>
                  <v-icon color="#10b981" size="24">mdi-check-circle</v-icon>
                </template>
                <v-list-item-title class="text-h6 text-white font-weight-medium">
                  {{ feature.text }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </div>
        </v-col>
      </v-row>
    </v-container>
    
    <!-- 注册对话框 -->
    <v-dialog v-model="showRegisterDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-6 pb-4">
          <v-icon class="mr-2">mdi-account-plus</v-icon>
          用户注册
        </v-card-title>
        
        <v-card-text class="pa-6">
          <v-form @submit.prevent="handleRegister">
            <v-text-field
              v-model="registerForm.username"
              label="用户名"
              prepend-inner-icon="mdi-account"
              variant="outlined"
              class="mb-4"
              required
              :rules="[v => !!v || '请输入用户名', v => v.length >= 3 || '用户名长度至少为3个字符']"
            ></v-text-field>

            <v-text-field
              v-model="registerForm.email"
              label="邮箱（可选）"
              prepend-inner-icon="mdi-email"
              variant="outlined"
              class="mb-4"
              type="email"
            ></v-text-field>

            <v-text-field
              v-model="registerForm.password"
              label="密码"
              prepend-inner-icon="mdi-lock"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              :type="showPassword ? 'text' : 'password'"
              variant="outlined"
              class="mb-4"
              required
              :rules="[v => !!v || '请输入密码', v => v.length >= 6 || '密码长度至少为6个字符']"
              @click:append-inner="showPassword = !showPassword"
            ></v-text-field>

            <v-text-field
              v-model="registerForm.confirmPassword"
              label="确认密码"
              prepend-inner-icon="mdi-lock-check"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              :type="showPassword ? 'text' : 'password'"
              variant="outlined"
              class="mb-4"
              required
              :rules="[v => !!v || '请确认密码', v => v === registerForm.password || '两次输入的密码不一致']"
              @click:append-inner="showPassword = !showPassword"
            ></v-text-field>

            <v-alert
              v-if="errorMessage"
              type="error"
              variant="tonal"
              density="compact"
              class="mb-4"
              rounded="lg"
              closable
              @click:close="errorMessage = ''"
            >
              {{ errorMessage }}
            </v-alert>
          </v-form>
        </v-card-text>
        
        <v-card-actions class="pa-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="closeRegisterDialog"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            :loading="loading"
            @click="handleRegister"
          >
            注册
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '@/services'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const form = ref({
  username: '',
  password: '',
  remember: false
})

const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const showRegisterDialog = ref(false)
const savedUserInfo = ref(null)

// 页面加载时检查是否有保存的用户信息
onMounted(() => {
  const savedUser = localStorage.getItem('finloom_user')
  const savedToken = localStorage.getItem('finloom_token')
  
  if (savedUser && savedToken) {
    try {
      const userInfo = JSON.parse(savedUser)
      savedUserInfo.value = userInfo
      
      // 自动填充用户名，但不填充密码（安全考虑）
      form.value.username = userInfo.username || ''
      form.value.remember = true // 如果有保存的信息，默认勾选记住我
      
      console.log('💡 检测到保存的账号:', userInfo.username)
    } catch (error) {
      console.error('解析保存的用户信息失败:', error)
    }
  }
})

const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

const features = ref([
  { text: 'AI驱动的投资决策' },
  { text: '实时市场分析' },
  { text: '智能风险管理' },
  { text: '自动化交易执行' }
])

async function handleLogin() {
  errorMessage.value = ''
  
  // 验证输入
  if (!form.value.username || !form.value.password) {
    errorMessage.value = '请输入用户名和密码'
    return
  }
  
  loading.value = true
  
  try {
    // 调用登录API
    const response = await api.auth.login({
      username: form.value.username,
      password: form.value.password,
      remember: form.value.remember
    })
    
    console.log('登录响应:', response)
    
    // 注意：响应拦截器已经提取了 response.data，所以这里直接用 response
    if (response.status === 'success') {
      // 保存认证信息
      localStorage.setItem('finloom_auth', 'true')
      localStorage.setItem('finloom_token', response.data.token)
      localStorage.setItem('finloom_user', JSON.stringify(response.data.user))
      
      // 加载用户信息到store
      try {
        await userStore.fetchUserInfo()
        console.log('用户信息已加载到store')
      } catch (err) {
        console.warn('加载用户信息失败，将在侧边栏加载时重试:', err)
      }
      
      // 跳转到目标页面或仪表盘
      const redirect = route.query.redirect || '/dashboard'
      router.push(redirect)
    } else {
      errorMessage.value = response.message || '登录失败'
    }
  } catch (error) {
    console.error('登录错误:', error)
    // 错误处理：响应拦截器已经处理了错误格式
    errorMessage.value = error.message || error.detail || '登录失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}

function goToRegister() {
  showRegisterDialog.value = true
}

async function handleRegister() {
  errorMessage.value = ''
  
  // 验证输入
  if (!registerForm.value.username || !registerForm.value.password) {
    errorMessage.value = '请输入用户名和密码'
    return
  }
  
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }
  
  if (registerForm.value.password.length < 6) {
    errorMessage.value = '密码长度至少为6个字符'
    return
  }
  
  loading.value = true
  
  try {
    // 调用注册API
    const response = await api.auth.register({
      username: registerForm.value.username,
      password: registerForm.value.password,
      email: registerForm.value.email || null,
      display_name: registerForm.value.username
    })
    
    console.log('注册响应:', response)
    
    // 注意：响应拦截器已经提取了 response.data
    if (response.status === 'success') {
      // 注册成功，自动登录
      form.value.username = registerForm.value.username
      form.value.password = registerForm.value.password
      showRegisterDialog.value = false
      
      // 自动登录
      await handleLogin()
    } else {
      errorMessage.value = response.message || '注册失败'
    }
  } catch (error) {
    console.error('注册错误:', error)
    // 响应拦截器已经处理了错误格式
    errorMessage.value = error.message || error.detail || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function closeRegisterDialog() {
  showRegisterDialog.value = false
  registerForm.value = {
    username: '',
    password: '',
    confirmPassword: '',
    email: '',
    isAdmin: false
  }
  errorMessage.value = ''
}

// 清除保存的账号信息
function clearSavedAccount() {
  localStorage.removeItem('finloom_user')
  localStorage.removeItem('finloom_token')
  localStorage.removeItem('finloom_auth')
  savedUserInfo.value = null
  form.value.username = ''
  form.value.password = ''
  form.value.remember = false
  form.value.isAdmin = false
  console.log('✅ 已清除保存的账号信息')
}
</script>

<style lang="scss" scoped>
.login-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-container {
  max-width: 1000px;
  width: 100%;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  min-height: 600px;

  @media (max-width: 960px) {
    margin: 1rem;
    border-radius: 16px;
  }
}

.login-card {
  border-radius: 0;
  box-shadow: none;
  background: transparent;
}

.logo {
  width: 80px;
  height: 80px;
  margin: 0 auto;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-panel {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 3rem;
  color: white;

  .info-content {
    text-align: center;
    max-width: 400px;
  }
}

// 响应式调整
@media (max-width: 960px) {
  .login-view {
    padding: 1rem;
  }
  
  .login-container {
    background: transparent;
    box-shadow: none;
  }
  
  .login-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  }
}
</style>

