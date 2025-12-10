<template>
  <button
    class="btn"
    :class="[variant, size, { loading, disabled, block }]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <span v-if="loading" class="btn-spinner"></span>
    <i v-if="icon && !loading" :class="icon"></i>
    <span v-if="$slots.default" class="btn-text">
      <slot></slot>
    </span>
  </button>
</template>

<script setup>
const emit = defineEmits(['click'])

defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'success', 'danger', 'warning', 'ghost'].includes(value)
  },
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  icon: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  block: {
    type: Boolean,
    default: false
  }
})

function handleClick(event) {
  emit('click', event)
}
</script>

<style lang="scss" scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  position: relative;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.block {
    width: 100%;
  }

  &.loading {
    pointer-events: none;
  }
}

// 尺寸变体
.small {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.medium {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

.large {
  padding: 1rem 2rem;
  font-size: 1.125rem;
}

// 颜色变体
.primary {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  }
}

.secondary {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  }
}

.success {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
  }
}

.danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
  }
}

.warning {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
  }
}

.ghost {
  background: transparent;
  color: #475569;
  border: 2px solid #e2e8f0;

  &:hover:not(:disabled) {
    background: rgba(59, 130, 246, 0.1);
    border-color: #3b82f6;
    color: #3b82f6;
  }
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

