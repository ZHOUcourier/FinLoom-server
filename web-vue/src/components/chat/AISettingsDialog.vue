<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="500">
    <v-card rounded="xl">
      <v-card-title class="d-flex align-center">
        <v-icon start>mdi-cog-outline</v-icon>
        AI 设置
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <v-select
          :model-value="settings.model"
          @update:model-value="updateSetting('model', $event)"
          :items="modelOptions"
          label="模型"
          variant="filled"
          density="comfortable"
          rounded="lg"
          class="mb-4"
        ></v-select>

        <div class="mb-4">
          <label class="text-body-2 mb-2 d-block">温度: {{ settings.temperature.toFixed(2) }}</label>
          <v-slider
            :model-value="settings.temperature"
            @update:model-value="updateSetting('temperature', $event)"
            min="0"
            max="1"
            step="0.05"
            color="primary"
          ></v-slider>
        </div>

        <v-select
          :model-value="settings.riskTolerance"
          @update:model-value="updateSetting('riskTolerance', $event)"
          :items="riskToleranceOptions"
          label="风险偏好"
          variant="filled"
          density="comfortable"
          rounded="lg"
        ></v-select>
      </v-card-text>
      <v-card-actions class="pa-6 pt-0">
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="$emit('cancel')" rounded="pill">取消</v-btn>
        <v-btn color="primary" @click="$emit('save')" rounded="pill" variant="flat">保存</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { AI_MODELS, RISK_TOLERANCE_OPTIONS } from '@/constants/chat'

defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  settings: {
    type: Object,
    required: true
  }
})

const modelOptions = AI_MODELS
const riskToleranceOptions = RISK_TOLERANCE_OPTIONS

const emit = defineEmits(['update:modelValue', 'save', 'cancel', 'update-setting'])

function updateSetting(key, value) {
  emit('update-setting', key, value)
}
</script>

