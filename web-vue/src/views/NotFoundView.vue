<template>
  <div class="not-found-view">
    <div class="not-found-content">
      <h1>404</h1>
      <h2>页面未找到</h2>
      <p>抱歉，您访问的页面不存在</p>
      <Button size="large" @click="goHome">
        <i class="fas fa-home"></i>
        返回仪表盘
      </Button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import Button from '@/components/ui/Button.vue'

const router = useRouter()

function goHome() {
  router.push({ name: 'dashboard-overview' })
}
</script>

<style lang="scss" scoped>
.not-found-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.not-found-content {
  text-align: center;
  color: white;

  h1 {
    font-size: 8rem;
    font-weight: 900;
    margin-bottom: 1rem;
    opacity: 0.9;
  }

  h2 {
    font-size: 2rem;
    margin-bottom: 1rem;
  }

  p {
    font-size: 1.25rem;
    margin-bottom: 2rem;
    opacity: 0.8;
  }
}
</style>

