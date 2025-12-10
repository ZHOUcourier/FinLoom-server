/**
 * AI设置组合式函数
 */

import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import { DEFAULT_AI_SETTINGS } from '@/constants/chat'

export function useAISettings() {
  const chatStore = useChatStore()
  const settingsOpen = ref(false)
  const localSettings = ref({ ...DEFAULT_AI_SETTINGS })
  
  /**
   * 打开设置对话框
   */
  function openSettings() {
    localSettings.value = { ...chatStore.settings }
    settingsOpen.value = true
  }
  
  /**
   * 保存设置
   */
  function saveSettings() {
    chatStore.updateSettings(localSettings.value)
    settingsOpen.value = false
  }
  
  /**
   * 取消设置
   */
  function cancelSettings() {
    settingsOpen.value = false
  }
  
  /**
   * 重置设置
   */
  function resetSettings() {
    localSettings.value = { ...DEFAULT_AI_SETTINGS }
  }
  
  return {
    settingsOpen,
    localSettings,
    openSettings,
    saveSettings,
    cancelSettings,
    resetSettings
  }
}

