<template>
  <div class="stat-card" :class="variant">
    <div class="stat-icon">
      <i :class="icon"></i>
    </div>
    <div class="stat-content">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">{{ formattedValue }}</div>
      <div v-if="change !== undefined" class="stat-change" :class="{ positive: change > 0, negative: change < 0 }">
        <i :class="change > 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down'"></i>
        <span>{{ Math.abs(change).toFixed(2) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  icon: {
    type: String,
    required: true
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'danger', 'warning'].includes(value)
  },
  change: {
    type: Number,
    default: undefined
  },
  format: {
    type: String,
    default: 'number',
    validator: (value) => ['number', 'currency', 'percent'].includes(value)
  }
})

const formattedValue = computed(() => {
  if (typeof props.value === 'string') return props.value
  
  switch (props.format) {
    case 'currency':
      return `¥${props.value.toLocaleString()}`
    case 'percent':
      return `${props.value.toFixed(2)}%`
    default:
      return props.value.toLocaleString()
  }
})
</script>

<style lang="scss" scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  }
}

.stat-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  font-size: 1.75rem;
  
  .primary & {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.2));
    color: #3b82f6;
  }
  
  .success & {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2));
    color: #10b981;
  }
  
  .danger & {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2));
    color: #ef4444;
  }
  
  .warning & {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.2));
    color: #f59e0b;
  }
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.25rem;
}

.stat-change {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;

  &.positive {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  &.negative {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
}
</style>

