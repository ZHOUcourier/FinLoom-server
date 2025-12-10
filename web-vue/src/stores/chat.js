import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services'
import { nanoid } from 'nanoid'
import { extractTitle } from '@/utils/chat'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref([])
  const conversationId = ref('')
  const loading = ref(false)
  const error = ref(null)
  const conversations = ref([]) // 历史会话列表
  const favorites = ref([])      // 收藏列表
  const settings = ref({        // AI 设置（默认使用阿里云）
    model: 'qwen-plus',
    temperature: 0.7,
    riskTolerance: 'medium'
  })
  const initialized = ref(false)
  
  // 缓存时间戳
  const cacheTimestamps = ref({
    conversations: null,
    favorites: null
  })
  
  // 缓存有效期（10分钟 - 聊天历史不需要频繁更新）
  const CACHE_DURATION = 10 * 60 * 1000
  
  // 检查缓存是否有效
  function isCacheValid(type) {
    const timestamp = cacheTimestamps.value[type]
    if (!timestamp) return false
    
    const elapsed = Date.now() - timestamp
    return elapsed < CACHE_DURATION
  }
  
  // 操作
  function initializeConversation(title = '') {
    ensureLoaded()
    const id = nanoid()
    conversationId.value = id
    messages.value = []
    conversations.value.unshift({
      id,
      title: title || '新对话',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages: []
    })
    persistConversations()
  }
  
  function addMessage(message) {
    messages.value.push({
      id: nanoid(),
      timestamp: new Date(),
      ...message
    })
    // 同步到当前会话并更新标题/时间
    syncCurrentConversation()
    if (message.role === 'user') {
      maybeSetConversationTitleFrom(message.content)
    }
  }
  
  async function sendMessage(text, amount = null, riskTolerance = null, attachments = null) {
    try {
      loading.value = true
      error.value = null
      
      // 添加用户消息
      addMessage({
        role: 'user',
        content: text,
        attachments: Array.isArray(attachments) ? attachments : null
      })
      
      // ✅ 默认使用阿里云AI服务（简单、快速、稳定）
      const response = await api.chat.send(text, conversationId.value)
      
      if (response.status === 'success') {
        // ✅ 如果后端返回了新的会话ID，更新本地
        if (response.conversation_id && !conversationId.value) {
          conversationId.value = response.conversation_id
        }
        
        // 添加AI回复（阿里云返回的字段是 response）
        addMessage({
          role: 'assistant',
          content: response.response,
          raw: response
        })
      } else {
        throw new Error(response.response || '分析失败')
      }
      
      return response
    } catch (err) {
      console.error('发送消息失败:', err)
      error.value = err.message || '发送失败'
      
      // 添加错误消息
      addMessage({
        role: 'assistant',
        content: '抱歉，我现在遇到了一些问题，请稍后再试。',
        error: true
      })
      
      throw err
    } finally {
      loading.value = false
    }
  }
  
  async function sendSimpleMessage(text) {
    try {
      loading.value = true
      error.value = null
      
      // 添加用户消息
      addMessage({
        role: 'user',
        content: text
      })
      
      // 调用简化对话API
      const response = await api.chat.send(text, conversationId.value)
      
      if (response.status === 'success') {
        // 添加AI回复
        addMessage({
          role: 'assistant',
          content: response.response,
          detailedData: response.detailed_data
        })
      } else {
        throw new Error(response.response || '发送失败')
      }
      
      return response
    } catch (err) {
      console.error('发送消息失败:', err)
      error.value = err.message || '发送失败'
      
      addMessage({
        role: 'assistant',
        content: '抱歉，我现在遇到了一些问题，请稍后再试。',
        error: true
      })
      
      throw err
    } finally {
      loading.value = false
    }
  }
  
  function clearMessages() {
    messages.value = []
    error.value = null
    syncCurrentConversation()
  }

  // 会话历史与设置
  function ensureLoaded() {
    if (initialized.value) return
    try {
      const convRaw = localStorage.getItem('finloom_conversations')
      const cfgRaw = localStorage.getItem('finloom_ai_settings')
      conversations.value = convRaw ? JSON.parse(convRaw) : []
      if (cfgRaw) {
        const cfg = JSON.parse(cfgRaw)
        settings.value = {
          ...settings.value,
          ...cfg
        }
      }
    } catch (e) {
      console.warn('加载历史/设置失败', e)
    } finally {
      initialized.value = true
    }
    // 若无会话则初始化一个
    if (!conversations.value.length) {
      initializeConversation()
    } else {
      // 进入最近的会话
      const latest = conversations.value[0]
      conversationId.value = latest.id
      messages.value = Array.isArray(latest.messages) ? latest.messages.map(m => ({ ...m, timestamp: new Date(m.timestamp) })) : []
    }
  }

  function persistConversations() {
    try {
      localStorage.setItem('finloom_conversations', JSON.stringify(conversations.value))
    } catch {}
  }

  function persistSettings() {
    try {
      localStorage.setItem('finloom_ai_settings', JSON.stringify(settings.value))
    } catch {}
  }

  function syncCurrentConversation() {
    const idx = conversations.value.findIndex(c => c.id === conversationId.value)
    if (idx >= 0) {
      conversations.value[idx] = {
        ...conversations.value[idx],
        messages: messages.value,
        updatedAt: new Date().toISOString()
      }
      persistConversations()
    }
  }

  function maybeSetConversationTitleFrom(text) {
    const idx = conversations.value.findIndex(c => c.id === conversationId.value)
    if (idx >= 0 && conversations.value[idx].title === '新对话') {
      conversations.value[idx].title = extractTitle(text, 20)
      persistConversations()
    }
  }

  function newConversation(title = '') {
    initializeConversation(title)
  }

  function switchConversation(id) {
    ensureLoaded()
    const conv = conversations.value.find(c => c.id === id)
    if (!conv) return
    conversationId.value = id
    messages.value = Array.isArray(conv.messages) ? conv.messages.map(m => ({ ...m, timestamp: new Date(m.timestamp) })) : []
  }

  function deleteConversation(id) {
    const idx = conversations.value.findIndex(c => c.id === id)
    if (idx < 0) return
    conversations.value.splice(idx, 1)
    persistConversations()
    if (conversationId.value === id) {
      if (conversations.value.length) {
        switchConversation(conversations.value[0].id)
      } else {
        initializeConversation()
      }
    }
  }

  function renameConversation(id, title) {
    const idx = conversations.value.findIndex(c => c.id === id)
    if (idx < 0) return
    conversations.value[idx].title = extractTitle(title, 60)
    persistConversations()
  }

  function updateSettings(partial) {
    settings.value = { ...settings.value, ...partial }
    persistSettings()
  }
  
  // 获取会话历史列表（从服务器，带缓存）
  async function fetchConversations(force = false) {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!force && isCacheValid('conversations') && conversations.value.length > 0) {
      console.log('✅ 使用缓存的会话历史')
      return
    }
    
    try {
      loading.value = true
      const response = await api.chat.getConversations()
      conversations.value = response.data || []
      cacheTimestamps.value.conversations = Date.now()
      error.value = null
      console.log('✅ 从服务器获取会话历史')
    } catch (err) {
      console.error('获取会话历史失败:', err)
      error.value = err.message || '获取会话历史失败'
    } finally {
      loading.value = false
    }
  }
  
  // 获取收藏列表（从服务器，带缓存）
  async function fetchFavorites(force = false) {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!force && isCacheValid('favorites') && favorites.value.length > 0) {
      console.log('✅ 使用缓存的收藏列表')
      return
    }
    
    try {
      loading.value = true
      const response = await api.chat.getFavorites()
      favorites.value = response.data || []
      cacheTimestamps.value.favorites = Date.now()
      error.value = null
      console.log('✅ 从服务器获取收藏列表')
    } catch (err) {
      console.error('获取收藏列表失败:', err)
      error.value = err.message || '获取收藏列表失败'
    } finally {
      loading.value = false
    }
  }
  
  // 清除缓存
  function clearCache(type = null) {
    if (type) {
      cacheTimestamps.value[type] = null
    } else {
      cacheTimestamps.value = {
        conversations: null,
        favorites: null
      }
    }
  }
  
  return {
    // 状态
    messages,
    conversationId,
    loading,
    error,
    conversations,
    favorites,
    settings,
    cacheTimestamps,
    
    // 操作
    initializeConversation,
    addMessage,
    sendMessage,
    sendSimpleMessage,
    clearMessages,
    // 历史与设置
    ensureLoaded,
    newConversation,
    switchConversation,
    deleteConversation,
    renameConversation,
    updateSettings,
    // 缓存相关
    fetchConversations,
    fetchFavorites,
    clearCache,
    isCacheValid
  }
})

