<template>
  <header class="top-navbar">
    <div class="navbar-content">
      <div class="navbar-left">
        <div class="page-title">
          <h1>Hi, FinLoom</h1>
          <p class="subtitle">让我们看看今日的活动吧</p>
        </div>
      </div>

      <div class="navbar-right">
        <!-- 搜索栏 -->
        <form class="search-form">
          <button type="button">
            <svg width="17" height="16" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="search">
              <path d="M7.667 12.667A5.333 5.333 0 107.667 2a5.333 5.333 0 000 10.667zM14.334 14l-2.9-2.9" stroke="currentColor" stroke-width="1.333" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </button>
          <input class="search-input" placeholder="搜索..." required="" type="text">
          <button class="reset" type="reset">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </form>

        <!-- 系统状态指示器 -->
        <div class="status-indicator" :class="appStore.appStatus" @mouseenter="showModuleStatus = true" @mouseleave="showModuleStatus = false">
          <div class="status-dot"></div>
          <div class="status-content">
            <span class="status-text">{{ statusText }}</span>
            <span class="status-time">{{ currentTime }}</span>
          </div>
          
          <!-- 模块状态弹窗 -->
          <Transition name="module-status">
            <div v-if="showModuleStatus" class="module-status-popup">
              <div class="popup-header">
                <h4>系统模块状态</h4>
                <span class="popup-time">{{ currentTime }}</span>
              </div>
              <div class="module-list">
                <div v-for="module in moduleStatusList" :key="module.name" class="module-item" :class="module.status">
                  <div class="module-icon">
                    <i :class="module.icon"></i>
                  </div>
                  <div class="module-dot"></div>
                  <span class="module-name">{{ module.name }}</span>
                  <span class="module-status-text">{{ module.statusText }}</span>
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <button class="icon-btn" @click="refreshData" title="刷新数据">
          <i class="fas fa-sync-alt" :class="{ spinning: refreshing }"></i>
        </button>

        <!-- 用户菜单 -->
        <div class="user-menu" @click="toggleUserMenu" @mouseleave="showUserMenu = false">
          <div class="user-avatar">
            <i class="fas fa-user"></i>
          </div>
          <div class="user-info">
            <span class="user-name">{{ userStore.displayName }}</span>
            <span class="user-role-badge" :class="getRoleClass()">
              <i :class="getRoleIcon()"></i>
              {{ getRoleText() }}
            </span>
          </div>
          <i class="fas fa-chevron-down dropdown-icon" :class="{ rotated: showUserMenu }"></i>

          <!-- 用户下拉菜单 -->
          <Transition name="user-menu">
            <div v-if="showUserMenu" class="user-dropdown">
              <div class="dropdown-header">
                <div class="dropdown-avatar">
                  <i class="fas fa-user-circle"></i>
                </div>
                <div class="dropdown-user-info">
                  <strong>{{ userStore.displayName }}</strong>
                  <span>{{ userStore.username }}</span>
                </div>
              </div>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item" @click="goToProfile">
                <i class="fas fa-user-cog"></i>
                <span>个人信息</span>
              </button>
              <button class="dropdown-item" @click="goToSettings">
                <i class="fas fa-cog"></i>
                <span>系统设置</span>
              </button>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item warning" @click="switchAccount">
                <i class="fas fa-exchange-alt"></i>
                <span>切换账号</span>
              </button>
              <button class="dropdown-item danger" @click="logout">
                <i class="fas fa-sign-out-alt"></i>
                <span>退出登录</span>
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useDashboardStore } from '@/stores/dashboard'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const appStore = useAppStore()
const dashboardStore = useDashboardStore()
const userStore = useUserStore()

const showUserMenu = ref(false)

const showModuleStatus = ref(false)
const refreshing = ref(false)
const currentTime = ref('')

let timeInterval = null

const statusText = computed(() => {
  const status = appStore.appStatus
  return {
    healthy: '系统正常',
    unhealthy: '服务异常',
    loading: '加载中...',
    ready: '就绪'
  }[status] || '未知'
})

// 12个模块的状态数据，包含图标
const moduleStatusList = ref([
  { name: '数据管道', status: 'healthy', statusText: '正常', icon: 'fas fa-database' },
  { name: '特征工程', status: 'healthy', statusText: '正常', icon: 'fas fa-project-diagram' },
  { name: 'AI模型', status: 'healthy', statusText: '正常', icon: 'fas fa-brain' },
  { name: '市场分析', status: 'healthy', statusText: '正常', icon: 'fas fa-chart-bar' },
  { name: '风险管理', status: 'healthy', statusText: '正常', icon: 'fas fa-shield-alt' },
  { name: '监控告警', status: 'healthy', statusText: '正常', icon: 'fas fa-bell' },
  { name: '策略优化', status: 'healthy', statusText: '正常', icon: 'fas fa-sliders-h' },
  { name: '交易执行', status: 'healthy', statusText: '正常', icon: 'fas fa-exchange-alt' },
  { name: '回测系统', status: 'healthy', statusText: '正常', icon: 'fas fa-history' },
  { name: 'AI交互', status: 'healthy', statusText: '正常', icon: 'fas fa-robot' },
  { name: '可视化', status: 'healthy', statusText: '正常', icon: 'fas fa-chart-pie' },
  { name: '环境管理', status: 'healthy', statusText: '正常', icon: 'fas fa-cogs' }
])

// 更新时间显示
function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})

async function refreshData() {
  refreshing.value = true
  try {
    await dashboardStore.refreshAll()
  } finally {
    setTimeout(() => {
      refreshing.value = false
    }, 1000)
  }
}

// 切换用户菜单显示
function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value
}

// 跳转到个人信息页面
function goToProfile() {
  showUserMenu.value = false
  router.push('/dashboard/settings')
}

// 跳转到系统设置
function goToSettings() {
  showUserMenu.value = false
  router.push('/dashboard/settings')
}

// 切换账号
function switchAccount() {
  showUserMenu.value = false
  
  // 清除当前登录信息
  localStorage.removeItem('finloom_token')
  localStorage.removeItem('finloom_user')
  localStorage.removeItem('finloom_auth')
  
  // 清除用户store
  userStore.clearUserInfo()
  
  console.log('🔄 切换账号，跳转到登录页')
  
  // 跳转到登录页
  router.push('/login')
}

// 退出登录
function logout() {
  showUserMenu.value = false
  
  // 清除所有登录信息
  localStorage.removeItem('finloom_token')
  localStorage.removeItem('finloom_user')
  localStorage.removeItem('finloom_auth')
  
  // 清除用户store
  userStore.clearUserInfo()
  
  console.log('👋 退出登录，跳转到登录页')
  
  // 跳转到登录页
  router.push('/login')
}

// 获取用户角色样式类
function getRoleClass() {
  const level = userStore.permissionLevel
  if (level >= 3) return 'role-vip'  // VIP用户
  if (level >= 2) return 'role-admin'  // 管理员
  return 'role-normal'  // 普通用户
}

// 获取用户角色图标
function getRoleIcon() {
  const level = userStore.permissionLevel
  if (level >= 3) return 'fas fa-crown'  // VIP图标
  if (level >= 2) return 'fas fa-shield-alt'  // 管理员图标
  return 'fas fa-user'  // 普通用户图标
}

// 获取用户角色文本
function getRoleText() {
  const level = userStore.permissionLevel
  if (level >= 3) return 'VIP'
  if (level >= 2) return '管理员'
  return '普通用户'
}
</script>

<style lang="scss" scoped>
.top-navbar {
  height: 70px;
  background: transparent;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-content {
  height: 100%;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-left {
  .page-title {
    h1 {
      font-size: 1.5rem;
      font-weight: 700;
      color: #0f172a;
      margin: 0;
      line-height: 1.2;
    }
    
    .subtitle {
      font-size: 0.875rem;
      color: #64748b;
      margin: 0;
      font-weight: 400;
    }
  }
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

/* 搜索栏样式 */
.search-form {
  --timing: 0.3s;
  --width-of-input: 200px;
  --height-of-input: 40px;
  --border-height: 2px;
  --input-bg: #fff;
  --border-color: #2f2ee9;
  --border-radius: 30px;
  --after-border-radius: 1px;
  position: relative;
  width: var(--width-of-input);
  height: var(--height-of-input);
  display: flex;
  align-items: center;
  padding-inline: 0.8em;
  border-radius: var(--border-radius);
  transition: border-radius 0.5s ease;
  background: var(--input-bg, #fff);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.search-form button {
  border: none;
  background: none;
  color: #8b8ba7;
  cursor: pointer;
}

.search-input {
  font-size: 0.9rem;
  background-color: transparent;
  width: 100%;
  height: 100%;
  padding-inline: 0.5em;
  padding-block: 0.7em;
  border: none;
}

.search-form:before {
  content: "";
  position: absolute;
  background: var(--border-color);
  transform: scaleX(0);
  transform-origin: center;
  width: 100%;
  height: var(--border-height);
  left: 0;
  bottom: 0;
  border-radius: 1px;
  transition: transform var(--timing) ease;
}

.search-form:focus-within {
  border-radius: var(--after-border-radius);
}

.search-input:focus {
  outline: none;
}

.search-form:focus-within:before {
  transform: scale(1);
}

.reset {
  border: none;
  background: none;
  opacity: 0;
  visibility: hidden;
  cursor: pointer;
}

.search-input:not(:placeholder-shown) ~ .reset {
  opacity: 1;
  visibility: visible;
}

.search-form svg {
  width: 17px;
  margin-top: 3px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(103, 80, 164, 0.08);
  border: 1px solid rgba(103, 80, 164, 0.12);
  border-radius: 16px;
  font-size: 0.875rem;
  font-weight: 500;
  position: relative;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);

  &:hover {
    background: rgba(103, 80, 164, 0.12);
    border-color: rgba(103, 80, 164, 0.2);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
    flex-shrink: 0;
  }

  .status-content {
    display: flex;
    flex-direction: column;
    gap: 0.0625rem;
  }

  .status-text {
    font-weight: 500;
    color: #1d1b20;
    font-size: 0.8125rem;
    line-height: 1.2;
  }

  .status-time {
    font-size: 0.6875rem;
    color: #49454f;
    font-weight: 400;
    line-height: 1.2;
  }

  &.ready .status-dot,
  &.healthy .status-dot {
    background: #10b981;
  }

  &.loading .status-dot {
    background: #f59e0b;
  }

  &.unhealthy .status-dot {
    background: #ef4444;
  }

  /* Material 3 模块状态弹窗 */
  .module-status-popup {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    min-width: 320px;
    background: #fefbff;
    border: 1px solid #e7e0ec;
    border-radius: 28px;
    box-shadow: 
      0 1px 3px rgba(0, 0, 0, 0.1),
      0 1px 2px rgba(0, 0, 0, 0.06),
      0 4px 6px -1px rgba(0, 0, 0, 0.1),
      0 2px 4px -1px rgba(0, 0, 0, 0.06);
    padding: 1.5rem;
    z-index: 1000;

    .popup-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid #e7e0ec;

      h4 {
        margin: 0;
        font-size: 1.125rem;
        font-weight: 500;
        color: #1d1b20;
        letter-spacing: 0.00938em;
      }

      .popup-time {
        font-size: 0.75rem;
        color: #49454f;
        font-weight: 400;
      }
    }

    .module-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .module-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem;
      border-radius: 16px;
      transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
      position: relative;

      &:hover {
        background: rgba(103, 80, 164, 0.08);
        transform: translateY(-1px);
      }

      .module-icon {
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #49454f;
        font-size: 0.875rem;
        flex-shrink: 0;
      }

      .module-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
      }

      .module-name {
        font-weight: 500;
        color: #1d1b20;
        flex: 1;
        font-size: 0.875rem;
      }

      .module-status-text {
        font-size: 0.75rem;
        color: #49454f;
        font-weight: 400;
      }

      &.healthy .module-dot {
        background: #10b981;
      }

      &.loading .module-dot {
        background: #f59e0b;
      }

      &.unhealthy .module-dot {
        background: #ef4444;
      }
    }
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes crownGlow {
  0%, 100% {
    filter: drop-shadow(0 0 6px rgba(255, 215, 0, 1)) 
            drop-shadow(0 0 10px rgba(255, 215, 0, 0.5));
  }
  50% {
    filter: drop-shadow(0 0 10px rgba(255, 215, 0, 1)) 
            drop-shadow(0 0 15px rgba(255, 215, 0, 0.7))
            drop-shadow(0 0 20px rgba(255, 215, 0, 0.3));
  }
}

@keyframes goldShimmer {
  0%, 100% {
    filter: drop-shadow(0 0 4px rgba(255, 215, 0, 0.8));
  }
  50% {
    filter: drop-shadow(0 0 6px rgba(255, 215, 0, 1))
            drop-shadow(0 0 10px rgba(255, 215, 0, 0.5));
  }
}

@keyframes vipGlow {
  0%, 100% {
    box-shadow: 
      0 0 20px rgba(255, 215, 0, 0.5),
      0 0 40px rgba(255, 215, 0, 0.2),
      inset 0 1px 0 rgba(255, 215, 0, 0.3),
      inset 0 -1px 0 rgba(255, 215, 0, 0.1);
  }
  50% {
    box-shadow: 
      0 0 25px rgba(255, 215, 0, 0.6),
      0 0 50px rgba(255, 215, 0, 0.3),
      inset 0 1px 0 rgba(255, 215, 0, 0.4),
      inset 0 -1px 0 rgba(255, 215, 0, 0.2);
  }
}

@keyframes borderRotate {
  0% {
    filter: hue-rotate(0deg);
  }
  100% {
    filter: hue-rotate(360deg);
  }
}

.icon-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: rgba(103, 80, 164, 0.08);
  color: #6750a4;
  border: 1px solid rgba(103, 80, 164, 0.12);
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  font-size: 1.125rem;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(103, 80, 164, 0.12);
    opacity: 0;
    transition: opacity 0.2s cubic-bezier(0.2, 0, 0, 1);
  }

  &:hover {
    background: rgba(103, 80, 164, 0.12);
    border-color: rgba(103, 80, 164, 0.2);
    transform: translateY(-1px);
    box-shadow: 
      0 1px 3px rgba(0, 0, 0, 0.1),
      0 1px 2px rgba(0, 0, 0, 0.06);

    &::before {
      opacity: 1;
    }
  }

  &:active {
    transform: translateY(0);
    box-shadow: 
      0 1px 2px rgba(0, 0, 0, 0.1);
  }

  i.spinning {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 模块状态弹窗过渡动画 */
.module-status-enter-active,
.module-status-leave-active {
  transition: all 0.3s ease;
}

.module-status-enter-from,
.module-status-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 用户菜单样式 */
.user-menu {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background: rgba(103, 80, 164, 0.08);
  border: 1px solid rgba(103, 80, 164, 0.12);
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  position: relative;

  &:hover {
    background: rgba(103, 80, 164, 0.12);
    border-color: rgba(103, 80, 164, 0.2);
  }

  .user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1rem;
    flex-shrink: 0;
  }

  .user-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;

    .user-name {
      font-weight: 600;
      color: #1d1b20;
      font-size: 0.875rem;
      line-height: 1.2;
    }

    .user-role-badge {
      font-size: 0.75rem;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.125rem 0.5rem;
      border-radius: 8px;
      width: fit-content;
      transition: all 0.3s ease;

      i {
        font-size: 0.65rem;
      }

      &.role-normal {
        color: #49454f;
        background: rgba(73, 69, 79, 0.1);
      }

      &.role-admin {
        color: #ffd700;
        background: linear-gradient(135deg, 
          #000000 0%, 
          #1a1612 25%,
          #2d2416 50%,
          #1a1612 75%,
          #000000 100%
        );
        border: 1.5px solid transparent;
        background-clip: padding-box;
        position: relative;
        box-shadow: 
          0 0 15px rgba(255, 215, 0, 0.3),
          inset 0 1px 0 rgba(255, 215, 0, 0.2);
        
        &::before {
          content: '';
          position: absolute;
          inset: -1.5px;
          border-radius: inherit;
          padding: 1.5px;
          background: linear-gradient(135deg, 
            #ffd700 0%,
            #ffed4e 25%, 
            #d4af37 50%,
            #ffed4e 75%,
            #ffd700 100%
          );
          -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
          -webkit-mask-composite: xor;
          mask-composite: exclude;
          z-index: -1;
        }
        
        i {
          color: #ffd700;
          filter: drop-shadow(0 0 4px rgba(255, 215, 0, 0.8));
          animation: goldShimmer 3s ease-in-out infinite;
        }
      }

      &.role-vip {
        color: #ffd700;
        background: linear-gradient(135deg, 
          #000000 0%,
          #1a1410 15%,
          #2d2214 30%,
          #3d2e1a 50%,
          #2d2214 70%,
          #1a1410 85%,
          #000000 100%
        );
        border: 2px solid transparent;
        background-clip: padding-box;
        position: relative;
        box-shadow: 
          0 0 20px rgba(255, 215, 0, 0.5),
          0 0 40px rgba(255, 215, 0, 0.2),
          inset 0 1px 0 rgba(255, 215, 0, 0.3),
          inset 0 -1px 0 rgba(255, 215, 0, 0.1);
        animation: vipGlow 3s ease-in-out infinite;
        
        &::before {
          content: '';
          position: absolute;
          inset: -2px;
          border-radius: inherit;
          padding: 2px;
          background: linear-gradient(135deg, 
            #ffd700 0%,
            #ffed4e 20%,
            #d4af37 40%,
            #b8941f 50%,
            #d4af37 60%,
            #ffed4e 80%,
            #ffd700 100%
          );
          -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
          -webkit-mask-composite: xor;
          mask-composite: exclude;
          z-index: -1;
          animation: borderRotate 4s linear infinite;
        }
        
        i {
          color: #ffd700;
          filter: drop-shadow(0 0 6px rgba(255, 215, 0, 1)) 
                  drop-shadow(0 0 10px rgba(255, 215, 0, 0.5));
          animation: crownGlow 2s ease-in-out infinite;
        }
      }
    }
  }

  .dropdown-icon {
    font-size: 0.75rem;
    color: #49454f;
    transition: transform 0.3s ease;

    &.rotated {
      transform: rotate(180deg);
    }
  }
}

/* 用户下拉菜单 */
.user-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 260px;
  background: #fefbff;
  border: 1px solid #e7e0ec;
  border-radius: 20px;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 0.75rem;
  z-index: 1000;

  .dropdown-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(103, 80, 164, 0.05);
    border-radius: 12px;
    margin-bottom: 0.5rem;

    .dropdown-avatar {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea, #764ba2);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.5rem;
      flex-shrink: 0;
    }

    .dropdown-user-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;

      strong {
        font-size: 0.9375rem;
        font-weight: 600;
        color: #1d1b20;
      }

      span {
        font-size: 0.8125rem;
        color: #49454f;
      }
    }
  }

  .dropdown-divider {
    height: 1px;
    background: #e7e0ec;
    margin: 0.5rem 0;
  }

  .dropdown-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: none;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
    font-size: 0.875rem;
    font-weight: 500;
    color: #1d1b20;
    text-align: left;

    i {
      font-size: 1rem;
      color: #49454f;
      width: 20px;
      flex-shrink: 0;
    }

    &:hover {
      background: rgba(103, 80, 164, 0.08);
    }

    &.warning {
      color: #f59e0b;

      i {
        color: #f59e0b;
      }

      &:hover {
        background: rgba(245, 158, 11, 0.1);
      }
    }

    &.danger {
      color: #ef4444;

      i {
        color: #ef4444;
      }

      &:hover {
        background: rgba(239, 68, 68, 0.1);
      }
    }
  }
}

/* 用户菜单过渡动画 */
.user-menu-enter-active,
.user-menu-leave-active {
  transition: all 0.3s ease;
}

.user-menu-enter-from,
.user-menu-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>

