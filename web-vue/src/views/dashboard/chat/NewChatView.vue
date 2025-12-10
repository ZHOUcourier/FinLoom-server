<template>
  <v-container fluid class="new-chat-view pa-6">
    <v-card rounded="xl" class="pa-6">
      <v-card-title class="text-h4 font-weight-bold mb-2">
        <v-icon start color="primary" size="32">mdi-chat-plus-outline</v-icon>
        开始新对话
      </v-card-title>
      <v-card-subtitle class="text-h6 mb-6">与FIN-R1智能助手交流您的投资需求</v-card-subtitle>
      
      <v-divider class="mb-6"></v-divider>
      
      <!-- 快速开始卡片 -->
      <v-row>
        <v-col 
          v-for="card in quickStartCards" 
          :key="card.title"
          cols="12" 
          md="6" 
          lg="4"
        >
          <v-card 
            variant="tonal" 
            :color="card.color"
            rounded="xl"
            class="quick-start-card h-100"
            @click="startConversation(card.prompt)"
          >
            <v-card-text class="pa-6">
              <v-avatar :color="card.color" variant="flat" size="48" class="mb-4">
                <v-icon :icon="card.icon" size="28" color="white"></v-icon>
              </v-avatar>
              <div class="text-h6 font-weight-bold mb-2">{{ card.title }}</div>
              <div class="text-body-2">{{ card.description }}</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <v-divider class="my-6"></v-divider>
      
      <!-- 自定义输入 -->
      <v-card variant="outlined" rounded="xl" class="pa-6">
        <div class="text-h6 font-weight-medium mb-4">
          <v-icon start>mdi-pencil-outline</v-icon>
          或者,描述您的投资需求
        </div>
        
        <v-textarea
          v-model="customInput"
          placeholder="例如：我想投资10万元,期限3年,希望年化收益15%以上,风险适中..."
          variant="outlined"
          rows="4"
          rounded="lg"
          class="mb-4"
        ></v-textarea>
        
        <div class="d-flex justify-end">
          <v-btn
            color="primary"
            size="large"
            prepend-icon="mdi-send"
            rounded="pill"
            variant="flat"
            :disabled="!customInput.trim()"
            :loading="creating"
            @click="startConversation(customInput)"
          >
            开始对话
          </v-btn>
        </div>
      </v-card>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services'

const router = useRouter()
const customInput = ref('')
const creating = ref(false)

const quickStartCards = [
  {
    title: '投资建议',
    description: '获取个性化投资组合推荐',
    icon: 'mdi-lightbulb-on-outline',
    color: 'primary',
    prompt: '我想获取一些投资建议,请帮我分析当前市场并推荐适合的投资标的'
  },
  {
    title: '风险评估',
    description: '评估投资组合风险水平',
    icon: 'mdi-shield-check-outline',
    color: 'warning',
    prompt: '请帮我评估我的投资组合风险,并给出风险控制建议'
  },
  {
    title: '市场分析',
    description: '了解最新市场动态和趋势',
    icon: 'mdi-chart-line',
    color: 'success',
    prompt: '请分析当前A股市场的整体走势和投资机会'
  },
  {
    title: '策略优化',
    description: '优化现有投资策略',
    icon: 'mdi-tune-variant',
    color: 'secondary',
    prompt: '我想优化我的投资策略,提高收益并降低风险'
  },
  {
    title: '行业研究',
    description: '深入了解特定行业',
    icon: 'mdi-domain',
    color: 'info',
    prompt: '请帮我分析科技行业的投资价值和机会'
  },
  {
    title: '问题咨询',
    description: '解答投资相关疑问',
    icon: 'mdi-help-circle-outline',
    color: 'tertiary',
    prompt: '我想了解如何开始量化投资'
  }
]

async function startConversation(prompt) {
  if (!prompt.trim()) return
  
  creating.value = true
  
  try {
    // 创建新对话
    const response = await api.chat.createConversation()
    const conversationId = response.data.conversation_id
    
    // 发送第一条消息
    await api.chat.send(prompt, conversationId)
    
    // 跳转到对话页面
    router.push({
      name: 'dashboard-chat',
      query: { id: conversationId }
    })
  } catch (error) {
    console.error('创建对话失败:', error)
    // 即使创建失败,也可以使用默认对话
    router.push({
      name: 'dashboard-chat'
    })
  } finally {
    creating.value = false
  }
}
</script>

<style lang="scss" scoped>
.new-chat-view {
  max-width: 1400px;
  margin: 0 auto;
}

.quick-start-card {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(var(--v-theme-primary), 0.15);
  }
}
</style>







