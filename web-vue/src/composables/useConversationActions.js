/**
 * 对话操作组合式函数
 */

import { copyConversationToClipboard, exportConversation } from '@/utils/chat'
import { useChatStore } from '@/stores/chat'

export function useConversationActions() {
  const chatStore = useChatStore()
  
  /**
   * 置顶/取消置顶对话
   */
  function pinConversation(id) {
    const conv = chatStore.conversations.find(c => c.id === id)
    if (conv) {
      conv.isPinned = !conv.isPinned
    }
  }
  
  /**
   * 重命名对话
   */
  function renameConversation(id) {
    const newName = prompt('请输入新的对话名称:')
    if (newName) {
      chatStore.renameConversation(id, newName)
    }
  }
  
  /**
   * 导出对话
   */
  function exportConversationHandler(id) {
    const conv = chatStore.conversations.find(c => c.id === id)
    if (conv) {
      const messages = conv.messages || []
      exportConversation(conv, messages)
    }
  }
  
  /**
   * 复制对话内容
   */
  async function copyConversation() {
    const success = await copyConversationToClipboard(chatStore.messages)
    if (success) {
      console.log('对话已复制到剪贴板')
    }
    return success
  }
  
  return {
    pinConversation,
    renameConversation,
    exportConversation: exportConversationHandler,
    copyConversation
  }
}

