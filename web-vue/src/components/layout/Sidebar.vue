<template>
  <aside 
    class="floating-sidebar" 
    :class="{ expanded: isExpanded, pinned: isPinned }"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
      <!-- Logo -->
    <div class="sidebar-logo">
      <div class="logo-icon">
      <!-- 纯色图形方案（保留，已注释）
      <i class="fas fa-chart-network"></i>
      -->
      <!-- Emoji 方案（当前生效） -->
      <span class="logo-emoji" role="img" aria-label="logo">📈</span>
      <!-- 图片 Logo 方案（示例，未启用）
      <img class="logo-img" src="@/assets/logo.png" alt="FinLoom Logo" />
      -->
      </div>
      <Transition name="fade-slide">
        <span v-if="isExpanded" class="logo-text">FinLoom</span>
        </Transition>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar-nav">
      <!-- 主要功能组 -->
      <div class="menu-group main-group">
        <template v-for="item in mainMenuItems" :key="item.path">
          <!-- 普通菜单项 -->
          <RouterLink
            v-if="!item.children"
            :to="item.path"
            class="nav-item"
            :class="{ 'is-active': isExactActive(item.path, item.exact) }"
            active-class="none"
            exact-active-class="none"
            exact
          >
            <div class="nav-icon">
              <i :class="item.icon"></i>
            </div>
            <Transition name="fade-slide">
              <span v-if="isExpanded" class="nav-label">{{ item.label }}</span>
            </Transition>
          </RouterLink>
          
          <!-- 带子菜单的项 -->
          <div v-else class="nav-item-group">
            <div
              class="nav-item nav-item-parent"
              :class="{ 'is-active': isParentActive(item.path) }"
            >
              <RouterLink
                :to="item.path"
                class="nav-item-link"
                active-class="none"
                exact-active-class="none"
              >
                <div class="nav-icon">
                  <i :class="item.icon"></i>
                </div>
                <Transition name="fade-slide">
                  <span v-if="isExpanded" class="nav-label">{{ item.label }}</span>
                </Transition>
              </RouterLink>
              <Transition name="fade-slide">
                <i
                  v-if="isExpanded"
                  class="submenu-arrow fas"
                  :class="expandedMenus[item.path] ? 'fa-chevron-down' : 'fa-chevron-right'"
                  @click.stop="toggleSubmenu(item.path)"
                ></i>
              </Transition>
            </div>
            
            <!-- 子菜单 -->
            <Transition name="submenu">
              <div v-if="isExpanded && expandedMenus[item.path]" class="nav-submenu">
                <RouterLink
                  v-for="child in item.children"
                  :key="child.path"
                  :to="child.path"
                  class="nav-subitem"
                >
                  <div class="submenu-dot"></div>
                  <span class="nav-label">{{ child.label }}</span>
                </RouterLink>
              </div>
            </Transition>
          </div>
        </template>
      </div>

      <!-- 系统功能组 -->
      <div class="menu-group system-group">
        <template v-for="item in systemMenuItems" :key="item.path">
      <RouterLink
        :to="item.path"
        class="nav-item"
        :class="{ 'is-active': isExactActive(item.path, item.exact) }"
        active-class="none"
        exact-active-class="none"
      >
            <div class="nav-icon">
        <i :class="item.icon"></i>
            </div>
            <Transition name="fade-slide">
              <span v-if="isExpanded" class="nav-label">{{ item.label }}</span>
        </Transition>
      </RouterLink>
        </template>
      </div>
    </nav>

    <!-- 底部操作区 -->
    <div class="sidebar-footer">
      <div class="footer-actions">
        <!-- 工具组 -->
        <div class="menu-group tools-group">
          <!-- 主题切换 -->
          <label class="theme-switch" title="切换主题">
            <input type="checkbox" class="theme-switch__checkbox" v-model="isDarkMode">
          <div class="theme-switch__container">
            <div class="theme-switch__clouds"></div>
            <div class="theme-switch__stars-container">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 144 55" fill="none">
                <path fill-rule="evenodd" clip-rule="evenodd" d="M135.831 3.00688C135.055 3.85027 134.111 4.29946 133 4.35447C134.111 4.40947 135.055 4.85867 135.831 5.71123C136.607 6.55462 136.996 7.56303 136.996 8.72727C136.996 7.95722 137.172 7.25134 137.525 6.59129C137.886 5.93124 138.372 5.39954 138.98 5.00535C139.598 4.60199 140.268 4.39114 141 4.35447C139.88 4.2903 138.936 3.85027 138.16 3.00688C137.384 2.16348 136.996 1.16425 136.996 0C136.996 1.16425 136.607 2.16348 135.831 3.00688ZM31 23.3545C32.1114 23.2995 33.0551 22.8503 33.8313 22.0069C34.6075 21.1635 34.9956 20.1642 34.9956 19C34.9956 20.1642 35.3837 21.1635 36.1599 22.0069C36.9361 22.8503 37.8798 23.2903 39 23.3545C38.2679 23.3911 37.5976 23.602 36.9802 24.0053C36.3716 24.3995 35.8864 24.9312 35.5248 25.5913C35.172 26.2513 34.9956 26.9572 34.9956 27.7273C34.9956 26.563 34.6075 25.5546 33.8313 24.7112C33.0551 23.8587 32.1114 23.4095 31 23.3545ZM0 36.3545C1.11136 36.2995 2.05513 35.8503 2.83131 35.0069C3.6075 34.1635 3.99559 33.1642 3.99559 32C3.99559 33.1642 4.38368 34.1635 5.15987 35.0069C5.93605 35.8503 6.87982 36.2903 8 36.3545C7.26792 36.3911 6.59757 36.602 5.98015 37.0053C5.37155 37.3995 4.88644 37.9312 4.52481 38.5913C4.172 39.2513 3.99559 39.9572 3.99559 40.7273C3.99559 39.563 3.6075 38.5546 2.83131 37.7112C2.05513 36.8587 1.11136 36.4095 0 36.3545ZM56.8313 24.0069C56.0551 24.8503 55.1114 25.2995 54 25.3545C55.1114 25.4095 56.0551 25.8587 56.8313 26.7112C57.6075 27.5546 57.9956 28.563 57.9956 29.7273C57.9956 28.9572 58.172 28.2513 58.5248 27.5913C58.8864 26.9312 59.3716 26.3995 59.9802 26.0053C60.5976 25.602 61.2679 25.3911 62 25.3545C60.8798 25.2903 59.9361 24.8503 59.1599 24.0069C58.3837 23.1635 57.9956 22.1642 57.9956 21C57.9956 22.1642 57.6075 23.1635 56.8313 24.0069ZM81 25.3545C82.1114 25.2995 83.0551 24.8503 83.8313 24.0069C84.6075 23.1635 84.9956 22.1642 84.9956 21C84.9956 22.1642 85.3837 23.1635 86.1599 24.0069C86.9361 24.8503 87.8798 25.2903 89 25.3545C88.2679 25.3911 87.5976 25.602 86.9802 26.0053C86.3716 26.3995 85.8864 26.9312 85.5248 27.5913C85.172 28.2513 84.9956 28.9572 84.9956 29.7273C84.9956 28.563 84.6075 27.5546 83.8313 26.7112C83.0551 25.8587 82.1114 25.4095 81 25.3545ZM136 36.3545C137.111 36.2995 138.055 35.8503 138.831 35.0069C139.607 34.1635 139.996 33.1642 139.996 32C139.996 33.1642 140.384 34.1635 141.16 35.0069C141.936 35.8503 142.88 36.2903 144 36.3545C143.268 36.3911 142.598 36.602 141.98 37.0053C141.372 37.3995 140.886 37.9312 140.525 38.5913C140.172 39.2513 139.996 39.9572 139.996 40.7273C139.996 39.563 139.607 38.5546 138.831 37.7112C138.055 36.8587 137.111 36.4095 136 36.3545ZM101.831 49.0069C101.055 49.8503 100.111 50.2995 99 50.3545C100.111 50.4095 101.055 50.8587 101.831 51.7112C102.607 52.5546 102.996 53.563 102.996 54.7273C102.996 53.9572 103.172 53.2513 103.525 52.5913C103.886 51.9312 104.372 51.3995 104.98 51.0053C105.598 50.602 106.268 50.3911 107 50.3545C105.88 50.2903 104.936 49.8503 104.16 49.0069C103.384 48.1635 102.996 47.1642 102.996 46C102.996 47.1642 102.607 48.1635 101.831 49.0069Z" fill="currentColor"></path>
              </svg>
            </div>
            <div class="theme-switch__circle-container">
              <div class="theme-switch__sun-moon-container">
                <div class="theme-switch__moon">
                  <div class="theme-switch__spot"></div>
                  <div class="theme-switch__spot"></div>
                  <div class="theme-switch__spot"></div>
                </div>
              </div>
            </div>
          </div>
            <Transition name="fade-slide">
              <span v-if="isExpanded" class="action-label">{{ isDarkMode ? '深色' : '浅色' }}</span>
            </Transition>
          </label>
          
          <!-- 固定/取消固定按钮 -->
          <div class="action-btn pin-btn" :class="{ active: isPinned }" @click="togglePin" :title="isPinned ? '取消固定' : '固定侧边栏'">
            <input type="checkbox" :id="'menu-checkbox'" v-model="isPinned" style="display: none;">
            <label :for="'menu-checkbox'" class="toggle">
              <div class="bars" id="bar1"></div>
              <div class="bars" id="bar2"></div>
              <div class="bars" id="bar3"></div>
            </label>
            <Transition name="fade-slide">
              <span v-if="isExpanded" class="action-label">切换折叠与展开</span>
            </Transition>
          </div>
          
          <!-- 用户头像 -->
          <button class="action-btn avatar-btn" title="个人资料" @click="goToProfile">
            <div class="avatar-icon">
              <i class="fas fa-user"></i>
            </div>
            <Transition name="fade-slide">
              <div v-if="isExpanded" class="avatar-info">
                <span class="action-label">{{ userStore.displayName }}</span>
                <span class="action-sublabel">{{ userStore.email }}</span>
              </div>
            </Transition>
      </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { api } from '@/services'

const appStore = useAppStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const isExpanded = ref(false)
const isPinned = ref(false)
const isDarkMode = ref(false)
const expandedMenus = reactive({})
const currentPath = computed(() => route.path)

// 初始化时设置侧边栏状态为折叠
appStore.sidebarCollapsed = true

// 主要功能组
const mainMenuItems = [
  { path: '/dashboard', icon: 'fas fa-home', label: '仪表板', exact: true },
  { path: '/dashboard/market', icon: 'fas fa-chart-area', label: '智能分析' },
  { 
    path: '/dashboard/chat', 
    icon: 'fas fa-comments', 
    label: '智能对话',
    children: [
      { path: '/dashboard/chat/new', label: '新对话' },
      { path: '/dashboard/chat/history', label: '历史记录' },
      { path: '/dashboard/chat/favorites', label: '收藏对话' }
    ]
  },
  { 
    path: '/dashboard/strategy', 
    icon: 'fas fa-brain', 
    label: '策略制定',
    children: [
      { path: '/dashboard/strategy/create', label: '创建策略' },
      { path: '/dashboard/strategy/library', label: '策略库' },
      { path: '/dashboard/strategy/templates', label: '策略模板' },
      { path: '/dashboard/strategy/live', label: '实盘运行' }
    ]
  },
  { path: '/dashboard/portfolio', icon: 'fas fa-briefcase', label: '投资组合' },
  { path: '/dashboard/backtest', icon: 'fas fa-flask', label: '策略回测' },
  { path: '/dashboard/data', icon: 'fas fa-database', label: '数据管理' },
  { path: '/dashboard/reports', icon: 'fas fa-file-alt', label: '报告中心' }
]

// 系统功能组
const systemMenuItems = ref([
  { path: '/dashboard/notifications', icon: 'fas fa-bell', label: '通知中心' },
  { path: '/dashboard/settings', icon: 'fas fa-cog', label: '系统设置' }
])

// 管理员菜单项
const adminMenuItem = { 
  path: '/dashboard/admin', 
  icon: 'fas fa-shield-alt', 
  label: '管理员中心',
  badge: true  // 显示徽章
}

// 检查是否为管理员并添加管理员菜单
onMounted(async () => {
  try {
    // 获取用户信息
    await userStore.fetchUserInfo()
    
    // 如果是管理员（权限>=2），添加管理员菜单
    if (userStore.isAdmin) {
      // 在系统设置之前插入管理员菜单
      systemMenuItems.value.splice(1, 0, adminMenuItem)
    }
  } catch (error) {
    console.error('检查管理员权限失败:', error)
  }
})

const handleMouseEnter = () => {
  if (!isPinned.value) {
    isExpanded.value = true
  }
}

const handleMouseLeave = () => {
  if (!isPinned.value) {
    isExpanded.value = false
  }
}

const togglePin = () => {
  isPinned.value = !isPinned.value
  if (isPinned.value) {
    isExpanded.value = true
  }
  appStore.sidebarCollapsed = !isPinned.value
}

const toggleSubmenu = (path) => {
  expandedMenus[path] = !expandedMenus[path]
}

const isParentActive = (parentPath) => {
  return currentPath.value.startsWith(parentPath) && currentPath.value !== '/dashboard'
}

const isExactActive = (itemPath, exact = false) => {
  if (exact) {
    return currentPath.value === itemPath
  }
  return currentPath.value.startsWith(itemPath) && currentPath.value !== '/dashboard'
}

// 路由变化时，自动展开当前路由所属的父级分组（不强制关闭其它分组）
watch(
  () => currentPath.value,
  (newPath) => {
    for (const item of mainMenuItems) {
      if (item.children && newPath.startsWith(item.path)) {
        expandedMenus[item.path] = true
      }
    }
  },
  { immediate: true }
)

// 跳转到个人信息页面
const goToProfile = () => {
  router.push({ path: '/dashboard/settings', query: { tab: 'profile' } })
}
</script>

<style lang="scss" scoped>
.floating-sidebar {
  position: fixed;
  left: 1.5rem;
  top: 1.5rem;
  bottom: 1.5rem;
  width: 80px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  border-radius: 24px;
  border: none;
  box-shadow: none;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;

  &::before {
    content: none;
  }

  &::after {
    content: none;
  }

  &.expanded {
    width: 270px;
  }

  &.pinned {
    width: 270px;
  }
}

// ===== Logo 区域 =====
.sidebar-logo {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.5rem;
  padding: 1.25rem 0.5rem;
  border-bottom: none;
  min-height: 80px;
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 
    0 4px 16px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  margin: 1rem 0.5rem 0;
  position: relative;

  .logo-icon {
    width: 48px;
    height: 48px;
    min-width: 48px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 
      0 4px 12px rgba(102, 126, 234, 0.25),
      0 0 0 1px rgba(15, 23, 42, 0.05);
    transition: all 0.3s ease;
    flex-shrink: 0;

    i {
      font-size: 1.4rem;
      color: white;
    }

    .logo-emoji {
      font-size: 1.35rem;
      line-height: 1;
    }

    .logo-img {
      width: 26px;
      height: 26px;
      object-fit: contain;
    }
  }

  .logo-text {
    font-size: 1.35rem;
    font-weight: 800;
    color: #1e293b;
    white-space: nowrap;
    opacity: 0;
    transition: opacity 0.3s ease;
    flex: 1;
  }

  &:hover .logo-icon {
    transform: scale(1.05) rotate(5deg);
    box-shadow: 
      0 6px 16px rgba(102, 126, 234, 0.35),
      0 0 0 1px rgba(15, 23, 42, 0.08);
  }
}

.floating-sidebar.expanded .sidebar-logo .logo-text,
.floating-sidebar.pinned .sidebar-logo .logo-text {
  opacity: 1;
}

// ===== 导航区域 =====
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 1.25rem 0.5rem;
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 10px;

    &:hover {
      background: rgba(0, 0, 0, 0.15);
    }
  }
}

// ===== 菜单组样式 =====
.menu-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.35rem;
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(12px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 
    0 4px 16px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.75rem;
  padding: 0.5rem 0.35rem;
  border-radius: 18px;
  text-decoration: none;
  color: #475569;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-height: 46px;
  cursor: pointer;

  &.nav-item-parent {
    text-decoration: none;
  }

  .nav-icon {
    width: 40px;
    height: 40px;
    min-width: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 11px;
    background: rgba(15, 23, 42, 0.06);
    transition: all 0.3s ease;
    box-shadow: 
      inset 0 1px 2px rgba(15, 23, 42, 0.08),
      0 1px 0 rgba(255, 255, 255, 0.6);
    flex-shrink: 0;

    i {
      font-size: 1.15rem;
      color: #475569;
      transition: all 0.3s ease;
    }
  }

  .nav-label {
    font-size: 0.95rem;
    font-weight: 500;
    white-space: nowrap;
    color: #495057;
    transition: all 0.3s ease;
    opacity: 0;
    flex: 1;
  }

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 0 4px 4px 0;
    transition: height 0.3s ease;
  }

  &:hover {
    background: rgba(102, 126, 234, 0.08);

    .nav-icon {
      background: rgba(102, 126, 234, 0.15);
      transform: scale(1.05);

      i {
        color: #667eea;
      }
    }

    .nav-label {
      color: #667eea;
    }

    &::before {
      height: 60%;
    }
  }

  &.is-active {
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);

    .nav-icon {
      background: rgba(255, 255, 255, 0.15);

      i {
        color: white;
      }
    }

    .nav-label {
      color: white;
      font-weight: 600;
    }

    &::before {
      height: 0;
    }

    &:hover {
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.16);

      .nav-icon {
        background: rgba(255, 255, 255, 0.2);
      }
    }
  }
}

.floating-sidebar.expanded .nav-item .nav-label,
.floating-sidebar.pinned .nav-item .nav-label {
  opacity: 1;
}
.nav-item-parent {
  .nav-item-link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    text-decoration: none;
    color: inherit;
    flex: 1;
  }
}

// ===== 子菜单样式 =====
.nav-item-group {
  width: 100%;
}

.submenu-arrow {
  margin-left: auto;
  font-size: 0.75rem;
  color: #94a3b8;
  transition: transform 0.3s ease;
}

.nav-submenu {
  padding-left: 0.375rem;
  margin-top: 0.125rem;
  margin-bottom: 0.125rem;
}

.nav-subitem {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.35rem;
  text-decoration: none;
  color: #64748b;
  border-radius: 16px;
  transition: all 0.3s ease;
  font-size: 0.875rem;

  .submenu-dot {
    width: 6px;
    height: 6px;
    min-width: 6px;
    border-radius: 50%;
    background: rgba(100, 116, 139, 0.3);
    transition: all 0.3s ease;
    flex-shrink: 0;
  }

  .nav-label {
    opacity: 0;
    transition: opacity 0.3s ease;
    flex: 1;
  }

  &:hover {
    background: rgba(102, 126, 234, 0.06);
    color: #667eea;

    .submenu-dot {
      background: #667eea;
      transform: scale(1.3);
    }
  }

  &.router-link-active {
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
    font-weight: 600;

    .submenu-dot {
      background: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
    }
  }
}

.floating-sidebar.expanded .nav-subitem .nav-label,
.floating-sidebar.pinned .nav-subitem .nav-label {
  opacity: 1;
}

.submenu-enter-active,
.submenu-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.submenu-enter-from,
.submenu-leave-to {
  max-height: 0;
  opacity: 0;
}

.submenu-enter-to,
.submenu-leave-from {
  max-height: 200px;
  opacity: 1;
}

// ===== 底部操作区（玻璃模糊效果）=====
.sidebar-footer {
  padding: 0.75rem 0.5rem;
  border-top: none;
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  box-shadow: none;
}

.footer-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: stretch;
  padding: 0;
}

.theme-switch {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  cursor: pointer;
  padding: 0.5rem 0.75rem;
  min-height: 46px;
  position: relative;
  --toggle-size: 15px;
  --container-width: 4em;
  --container-height: 2em;
  --container-radius: 6.25em;
  --container-light-bg: #3D7EAE;
  --container-night-bg: #1D1F2C;
  --circle-container-diameter: 2.8em;
  --sun-moon-diameter: 1.7em;
  --sun-bg: #ECCA2F;
  --moon-bg: #C4C9D1;
  --spot-color: #959DB1;
  --circle-container-offset: calc((var(--circle-container-diameter) - var(--container-height)) / 2 * -1);
  --stars-color: #fff;
  --clouds-color: #F3FDFF;
  --back-clouds-color: #AACADF;
  --transition: .5s cubic-bezier(0, -0.02, 0.4, 1.25);
  --circle-transition: .3s cubic-bezier(0, -0.02, 0.35, 1.17);

  &, *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-size: var(--toggle-size);
  }

  .theme-switch__checkbox {
    display: none;
  }

  .theme-switch__container {
    width: var(--container-width);
    height: var(--container-height);
    background-color: var(--container-light-bg);
    border-radius: var(--container-radius);
    overflow: hidden;
    cursor: pointer;
    box-shadow: 0em -0.062em 0.062em rgba(0, 0, 0, 0.25), 0em 0.062em 0.125em rgba(255, 255, 255, 0.94);
    transition: var(--transition);
    position: relative;

    &::before {
      content: "";
      position: absolute;
      z-index: 1;
      inset: 0;
      box-shadow: 0em 0.05em 0.187em rgba(0, 0, 0, 0.25) inset, 0em 0.05em 0.187em rgba(0, 0, 0, 0.25) inset;
      border-radius: var(--container-radius);
    }
  }

  .theme-switch__circle-container {
    width: var(--circle-container-diameter);
    height: var(--circle-container-diameter);
    background-color: rgba(255, 255, 255, 0.1);
    position: absolute;
    left: var(--circle-container-offset);
    top: var(--circle-container-offset);
    border-radius: var(--container-radius);
    box-shadow: inset 0 0 0 3.375em rgba(255, 255, 255, 0.1), inset 0 0 0 3.375em rgba(255, 255, 255, 0.1), 0 0 0 0.625em rgba(255, 255, 255, 0.1), 0 0 0 1.25em rgba(255, 255, 255, 0.1);
    display: flex;
    transition: var(--circle-transition);
    pointer-events: none;

    &:hover {
      left: calc(var(--circle-container-offset) + 0.187em);
    }
  }

  .theme-switch__sun-moon-container {
    pointer-events: auto;
    position: relative;
    z-index: 2;
    width: var(--sun-moon-diameter);
    height: var(--sun-moon-diameter);
    margin: auto;
    border-radius: var(--container-radius);
    background-color: var(--sun-bg);
    box-shadow: 0.062em 0.062em 0.062em 0em rgba(254, 255, 239, 0.61) inset, 0em -0.062em 0.062em 0em #a1872a inset;
    filter: drop-shadow(0.062em 0.125em 0.125em rgba(0, 0, 0, 0.25)) drop-shadow(0em 0.062em 0.125em rgba(0, 0, 0, 0.25));
    overflow: hidden;
    transition: var(--transition);
  }

  .theme-switch__moon {
    transform: translateX(100%);
    width: 100%;
    height: 100%;
    background-color: var(--moon-bg);
    border-radius: inherit;
    box-shadow: 0.062em 0.062em 0.062em 0em rgba(254, 255, 239, 0.61) inset, 0em -0.062em 0.062em 0em #969696 inset;
    transition: var(--transition);
    position: relative;
  }

  .theme-switch__spot {
    position: absolute;
    top: 0.75em;
    left: 0.312em;
    width: 0.75em;
    height: 0.75em;
    border-radius: var(--container-radius);
    background-color: var(--spot-color);
    box-shadow: 0em 0.0312em 0.062em rgba(0, 0, 0, 0.25) inset;

    &:nth-of-type(2) {
      width: 0.375em;
      height: 0.375em;
      top: 0.937em;
      left: 1.375em;
    }

    &:nth-last-of-type(3) {
      width: 0.25em;
      height: 0.25em;
      top: 0.312em;
      left: 0.812em;
    }
  }

  .theme-switch__clouds {
    width: 1.25em;
    height: 1.25em;
    background-color: var(--clouds-color);
    border-radius: var(--container-radius);
    position: absolute;
    bottom: -0.625em;
    left: 0.312em;
    box-shadow: 0.937em 0.312em var(--clouds-color), -0.312em -0.312em var(--back-clouds-color), 1.437em 0.375em var(--clouds-color), 0.5em -0.125em var(--back-clouds-color), 2.187em 0 var(--clouds-color), 1.25em -0.062em var(--back-clouds-color), 2.937em 0.312em var(--clouds-color), 2em -0.312em var(--back-clouds-color), 3.625em -0.062em var(--clouds-color), 2.625em 0em var(--back-clouds-color), 4.5em -0.312em var(--clouds-color), 3.375em -0.437em var(--back-clouds-color), 4.625em -1.75em 0 0.437em var(--clouds-color), 4em -0.625em var(--back-clouds-color), 4.125em -2.125em 0 0.437em var(--back-clouds-color);
    transition: 0.5s cubic-bezier(0, -0.02, 0.4, 1.25);
  }

  .theme-switch__stars-container {
    position: absolute;
    color: var(--stars-color);
    top: -100%;
    left: 0.312em;
    width: 2.75em;
    height: auto;
    transition: var(--transition);
  }

  .theme-switch__checkbox:checked + .theme-switch__container {
    background-color: var(--container-night-bg);

    .theme-switch__circle-container {
      left: calc(100% - var(--circle-container-offset) - var(--circle-container-diameter));

      &:hover {
        left: calc(100% - var(--circle-container-offset) - var(--circle-container-diameter) - 0.187em);
      }
    }

    .theme-switch__moon {
      transform: translate(0);
    }

    .theme-switch__clouds {
      bottom: -4.062em;
    }

    .theme-switch__stars-container {
      top: 50%;
      transform: translateY(-50%);
    }
  }

  .action-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #475569;
    white-space: nowrap;
    opacity: 0;
    transition: opacity 0.3s ease;
    flex: 1;
    margin-left: 0.75rem;
  }
}

.action-btn {
  width: 100%;
  min-height: 50px;
  padding: 0.75rem 0.75rem;
  border-radius: 13px;
    border: none;
  background: rgba(255, 255, 255, 0.8);
  color: #475569;
    cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.75rem;
  box-shadow: 
    0 2px 8px rgba(15, 23, 42, 0.08),
    0 0 0 1px rgba(15, 23, 42, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);

  i {
    font-size: 1.1rem;
    min-width: 20px;
    transition: all 0.3s ease;
  }

  .action-label {
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap;
  }

  &:hover {
    background: white;
    transform: translateY(-2px);
    box-shadow: 
      0 4px 12px rgba(15, 23, 42, 0.12),
      0 0 0 1px rgba(15, 23, 42, 0.06),
      inset 0 1px 0 rgba(255, 255, 255, 1);
  }

  &:active {
    transform: translateY(0);
  }

  &.pin-btn {
    justify-content: flex-start;
    min-height: 46px;
    padding: 0.5rem 0.75rem;
    position: relative;

    .toggle {
      position: relative;
      width: 32px;
      height: 32px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 5px;
      transition-duration: .3s;
      flex-shrink: 0;
    }

    .bars {
      width: 22px;
      height: 2.5px;
      background-color: #64748b;
      border-radius: 3px;
      transition-duration: .3s;
    }

    .action-label {
      opacity: 0;
      transition: opacity 0.3s ease;
      flex: 1;
      margin-left: 0.75rem;
    }

    &.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 
        0 4px 12px rgba(102, 126, 234, 0.3),
        0 0 0 1px rgba(102, 126, 234, 0.2);

      .bars {
        background-color: white;
      }

      #bar2 {
        transform: rotate(135deg);
        margin-left: 0;
        transform-origin: center;
        transition-duration: .3s;
      }

      #bar1 {
        transform: rotate(45deg);
        transition-duration: .3s;
        transform-origin: left center;
        margin-left: 6px;
      }

      #bar3 {
        transform: rotate(-45deg);
        transition-duration: .3s;
        transform-origin: left center;
        margin-left: 6px;
      }

      .action-label {
        color: white;
      }

      &:hover {
        box-shadow: 
          0 6px 16px rgba(102, 126, 234, 0.4),
          0 0 0 1px rgba(102, 126, 234, 0.3);
      }
    }
  }

  &.avatar-btn {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    box-shadow: 
      0 4px 12px rgba(240, 147, 251, 0.3),
      0 0 0 1px rgba(240, 147, 251, 0.2);
    padding: 0.5rem 0.375rem;
    min-height: 46px;
    justify-content: flex-start;
    position: relative;

    .avatar-icon {
      width: 40px;
      height: 40px;
      min-width: 40px;
      background: rgba(255, 255, 255, 0.25);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      flex-shrink: 0;

      i {
        font-size: 1.2rem;
        color: white;
      }
    }

    .avatar-info {
      display: flex;
      flex-direction: column;
      gap: 0.125rem;
      text-align: left;
      opacity: 0;
      transition: opacity 0.3s ease;
      flex: 1;
      margin-left: 0.375rem;

      .action-label {
        color: white;
        font-size: 0.9rem;
        font-weight: 600;
      }

      .action-sublabel {
        color: rgba(255, 255, 255, 0.75);
        font-size: 0.75rem;
        font-weight: 400;
      }
    }

    &:hover {
      box-shadow: 
        0 6px 16px rgba(240, 147, 251, 0.4),
        0 0 0 1px rgba(240, 147, 251, 0.3);

      .avatar-icon {
        background: rgba(255, 255, 255, 0.35);
        transform: scale(1.05);
      }
    }
  }
}

.floating-sidebar.expanded .avatar-btn .avatar-info,
.floating-sidebar.pinned .avatar-btn .avatar-info {
  opacity: 1;
}

.floating-sidebar.expanded .pin-btn .action-label,
.floating-sidebar.pinned .pin-btn .action-label {
  opacity: 1;
}

.floating-sidebar.expanded .theme-switch .action-label,
.floating-sidebar.pinned .theme-switch .action-label {
  opacity: 1;
}

// ===== 动画效果 =====
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

// ===== 响应式 =====
@media (max-width: 768px) {
  .floating-sidebar {
    left: 0.75rem;
    top: 0.75rem;
    bottom: 0.75rem;
    width: 60px;
    border-radius: 16px;

    &.expanded,
    &.pinned {
      width: 200px;
    }
  }

  .sidebar-logo {
    padding: 1rem 0.75rem;

    .logo-icon {
      width: 44px;
      height: 44px;
      min-width: 44px;
    }

    .logo-text {
      font-size: 1.25rem;
    }
  }

  .sidebar-nav {
    padding: 1rem 0.75rem;
  }

  .nav-item {
    padding: 0.625rem;

    .nav-icon {
      width: 36px;
      height: 36px;
      min-width: 36px;

      i {
        font-size: 1rem;
      }
    }

    .nav-label {
      font-size: 0.875rem;
    }
  }

  .action-btn {
    width: 42px;
    height: 42px;
    min-width: 42px;

    i {
      font-size: 1rem;
    }
  }
}
</style>


