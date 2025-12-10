<template>
  <div id="app" class="app-root">
    <RouterView />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

onMounted(() => {
  // 初始化应用
  appStore.checkHealth()
})
</script>

<style lang="scss">
// 全局样式已在main.scss中定义
</style>

