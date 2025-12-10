<template>
  <v-card-text class="pa-4">
    <div class="d-flex justify-space-between align-center">
      <div class="d-flex align-center">
        <v-avatar color="primary" variant="tonal" size="40" class="mr-3">
          <v-icon size="24">mdi-robot-outline</v-icon>
        </v-avatar>
        <div>
          <div class="text-h6 font-weight-medium">FIN-R1 AI助手</div>
          <div class="text-caption text-medium-emphasis">
            <v-chip 
              size="x-small" 
              color="success" 
              variant="tonal" 
              class="mr-2"
              rounded="lg"
            >
              <v-icon start size="12">mdi-circle</v-icon>
              在线
            </v-chip>
            智能投资顾问
          </div>
        </div>
      </div>
      <div class="d-flex gap-1">
        <v-btn 
          icon="mdi-refresh" 
          variant="text" 
          size="small" 
          @click="$emit('refresh')" 
          color="primary"
          :loading="loading"
          rounded="lg"
        ></v-btn>
        <v-btn 
          icon="mdi-content-copy" 
          variant="text" 
          size="small" 
          @click="$emit('copy')" 
          color="primary"
          rounded="lg"
        ></v-btn>
        <v-btn 
          icon="mdi-delete-outline" 
          variant="text" 
          size="small" 
          @click="$emit('clear')" 
          color="primary"
          rounded="lg"
        ></v-btn>
      </div>
    </div>
  </v-card-text>
</template>

<script setup>
defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['refresh', 'copy', 'clear'])
</script>

