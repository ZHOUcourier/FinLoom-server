/**
 * 聊天功能组合式函数
 */

import { ref, computed, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { filterConversations } from '@/utils/chat'

export function useChat() {
  const chatStore = useChatStore()
  const inputMessage = ref('')
  const messagesRef = ref(null)
  const searchQuery = ref('')
  const activeFilter = ref('all')
  
  // 计算属性：筛选后的对话列表
  const filteredConversations = computed(() => {
    return filterConversations(
      chatStore.conversations,
      searchQuery.value,
      activeFilter.value
    )
  })
  
  // 发送消息
  async function sendMessage() {
    if (!inputMessage.value.trim() || chatStore.loading) return
    
    await chatStore.sendMessage(inputMessage.value)
    inputMessage.value = ''
    await nextTick()
    scrollToBottom()
  }
  
  // 滚动到底部
  function scrollToBottom() {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  }
  
  // 快速提问
  function askQuestion(text) {
    inputMessage.value = text
    sendMessage()
  }
  
  // 创建新对话
  function newConversation() {
    chatStore.newConversation()
  }
  
  // 切换对话
  function switchConversation(id) {
    chatStore.switchConversation(id)
  }
  
  // 删除对话
  function deleteConversation(id) {
    chatStore.deleteConversation(id)
  }
  
  // 清空当前对话消息
  function clearMessages() {
    chatStore.clearMessages()
  }
  
  // 刷新聊天
  function refreshChat() {
    // 可以实现刷新逻辑
    console.log('刷新聊天')
  }
  
  return {
    // 状态
    inputMessage,
    messagesRef,
    searchQuery,
    activeFilter,
    filteredConversations,
    
    // Store状态
    messages: computed(() => chatStore.messages),
    conversations: computed(() => chatStore.conversations),
    conversationId: computed(() => chatStore.conversationId),
    loading: computed(() => chatStore.loading),
    error: computed(() => chatStore.error),
    
    // 方法
    sendMessage,
    scrollToBottom,
    askQuestion,
    newConversation,
    switchConversation,
    deleteConversation,
    clearMessages,
    refreshChat
  }
}

