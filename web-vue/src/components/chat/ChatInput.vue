<template>
  <div class="input-container">
    <v-card 
      variant="outlined" 
      class="input-card"
      rounded="xl"
      elevation="2"
    >
      <v-card-text class="pa-0">
        <div class="d-flex align-center">
          <v-textarea
            :model-value="modelValue"
            @update:model-value="$emit('update:modelValue', $event)"
            placeholder="描述您的投资需求..."
            variant="plain"
            rows="1"
            auto-grow
            hide-details
            density="comfortable"
            class="input-textarea centered-placeholder"
            @keydown.enter.exact.prevent="$emit('send')"
            @keydown.enter.shift.exact="$emit('update:modelValue', modelValue + '\n')"
          ></v-textarea>
          <div class="input-actions">
            <v-btn
              icon="mdi-send"
              color="primary"
              variant="flat"
              :disabled="!modelValue.trim() || loading"
              @click="$emit('send')"
              size="small"
              rounded="lg"
              class="send-btn"
            >
              <v-icon size="18">mdi-send</v-icon>
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>
    <div class="input-hint">
      <span class="text-caption text-medium-emphasis">
        按 Enter 发送，Shift + Enter 换行
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue', 'send'])
</script>

<style scoped>
.centered-placeholder :deep(.v-field__input) {
  display: flex;
  align-items: center;
  text-align: left;
}

.centered-placeholder :deep(textarea) {
  line-height: 1.5 !important;
  padding: 16px 16px;
}
</style>
