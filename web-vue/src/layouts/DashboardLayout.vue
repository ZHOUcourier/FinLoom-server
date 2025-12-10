<template>
  <div class="dashboard-layout" :class="{ 'sidebar-expanded': !appStore.sidebarCollapsed }">
    <Sidebar />
    <div class="main-content">
      <TopNavbar />
      <div class="content-wrapper">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </div>
    </div>
    
    <!-- 用户留言按钮 -->
    <UserMessageButton />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import Sidebar from '@/components/layout/Sidebar.vue'
import TopNavbar from '@/components/layout/TopNavbar.vue'
import UserMessageButton from '@/components/UserMessageButton.vue'

const appStore = useAppStore()
const userStore = useUserStore()

// 页面加载时获取用户信息
onMounted(async () => {
  // 如果userStore中没有用户信息，尝试加载
  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
      console.log('✅ Dashboard: 用户信息已加载')
    } catch (error) {
      console.warn('⚠️ Dashboard: 加载用户信息失败', error)
    }
  }
})
</script>

<style lang="scss" scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, #FBF8F3 0%, #F5F0E8 50%, #FBF8F3 100%);
  padding-left: 110px;
  transition: padding-left 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  &.sidebar-expanded {
    padding-left: 300px;
  }

  @media (max-width: 768px) {
    padding-left: 90px;

    &.sidebar-expanded {
      padding-left: 240px;
    }
  }
}

.main-content {
  flex: 1;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.content-wrapper {
  padding: 2rem;
  min-height: calc(100vh - 70px);

  @media (max-width: 768px) {
    padding: 1rem;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

