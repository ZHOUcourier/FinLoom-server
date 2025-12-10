<template>
  <div class="loading-spinner" :class="size">
    <div class="spinner"></div>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  text: {
    type: String,
    default: ''
  }
})
</script>

<style lang="scss" scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.spinner {
  border-radius: 50%;
  border-style: solid;
  border-color: rgba(59, 130, 246, 0.2);
  border-top-color: #3b82f6;
  animation: spin 0.8s linear infinite;
}

.small .spinner {
  width: 24px;
  height: 24px;
  border-width: 2px;
}

.medium .spinner {
  width: 40px;
  height: 40px;
  border-width: 3px;
}

.large .spinner {
  width: 64px;
  height: 64px;
  border-width: 4px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0;
}
</style>

