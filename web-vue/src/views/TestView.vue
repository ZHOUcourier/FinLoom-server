<template>
  <div class="test-view">
    <h1>Vue3版本测试页</h1>
    <div class="info">
      <p>✅ 如果你能看到这个页面，说明正在使用Vue3版本</p>
      <p>⚠️ 如果看不到这个页面或显示404，说明还在使用旧版HTML</p>
      <p>当前时间: {{ currentTime }}</p>
    </div>
    <div class="actions">
      <button @click="$router.push('/')">返回首页</button>
      <button @click="$router.push('/dashboard')">进入仪表盘</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const currentTime = ref('')

onMounted(() => {
  currentTime.value = new Date().toLocaleString('zh-CN')
})
</script>

<style lang="scss" scoped>
.test-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  text-align: center;

  h1 {
    font-size: 3rem;
    margin-bottom: 2rem;
  }

  .info {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    padding: 2rem;
    border-radius: 20px;
    margin-bottom: 2rem;

    p {
      font-size: 1.25rem;
      margin-bottom: 1rem;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  .actions {
    display: flex;
    gap: 1rem;

    button {
      padding: 1rem 2rem;
      font-size: 1rem;
      font-weight: 700;
      background: white;
      color: #667eea;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
      }
    }
  }
}
</style>

