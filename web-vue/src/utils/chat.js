/**
 * 聊天相关工具函数
 */

import { CONVERSATION_ICONS, CONVERSATION_COLORS } from '@/constants/chat'

/**
 * 获取对话类型图标
 * @param {string} type - 对话类型
 * @returns {string} 图标名称
 */
export function getConversationIcon(type) {
  return CONVERSATION_ICONS[type] || 'mdi-chat-outline'
}

/**
 * 获取对话类型颜色
 * @param {string} type - 对话类型
 * @returns {string} 颜色名称
 */
export function getConversationColor(type) {
  return CONVERSATION_COLORS[type] || 'default'
}

/**
 * 复制对话内容到剪贴板
 * @param {Array} messages - 消息列表
 * @returns {Promise<void>}
 */
export async function copyConversationToClipboard(messages) {
  const conversationText = messages.map(msg => 
    `${msg.role === 'user' ? '用户' : 'AI'}: ${msg.content}`
  ).join('\n')
  
  try {
    await navigator.clipboard.writeText(conversationText)
    return true
  } catch (error) {
    console.error('复制失败:', error)
    return false
  }
}

/**
 * 导出对话为文本文件
 * @param {Object} conversation - 对话对象
 * @param {Array} messages - 消息列表
 */
export function exportConversation(conversation, messages) {
  const content = [
    `对话标题: ${conversation.title}`,
    `创建时间: ${new Date(conversation.createdAt).toLocaleString('zh-CN')}`,
    `更新时间: ${new Date(conversation.updatedAt).toLocaleString('zh-CN')}`,
    '\n--- 对话内容 ---\n',
    ...messages.map(msg => 
      `[${new Date(msg.timestamp).toLocaleString('zh-CN')}] ${msg.role === 'user' ? '用户' : 'AI'}:\n${msg.content}\n`
    )
  ].join('\n')
  
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${conversation.title}_${Date.now()}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 从文本中提取摘要作为标题
 * @param {string} text - 原始文本
 * @param {number} maxLength - 最大长度
 * @returns {string} 摘要
 */
export function extractTitle(text, maxLength = 20) {
  if (!text) return '新对话'
  const cleaned = String(text).replace(/\s+/g, ' ').trim()
  return cleaned ? cleaned.slice(0, maxLength) : '新对话'
}

/**
 * 筛选对话列表
 * @param {Array} conversations - 对话列表
 * @param {string} searchQuery - 搜索关键词
 * @param {string} filter - 筛选类型
 * @returns {Array} 筛选后的对话列表
 */
export function filterConversations(conversations, searchQuery = '', filter = 'all') {
  let filtered = [...conversations]
  
  // 搜索过滤
  if (searchQuery) {
    const query = searchQuery.toLowerCase()
    filtered = filtered.filter(conv => 
      conv.title.toLowerCase().includes(query) ||
      conv.lastMessage?.toLowerCase().includes(query)
    )
  }
  
  // 类型过滤
  if (filter === 'pinned') {
    filtered = filtered.filter(conv => conv.isPinned)
  } else if (filter === 'recent') {
    // 最近7天
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
    filtered = filtered.filter(conv => 
      new Date(conv.updatedAt || conv.createdAt) >= sevenDaysAgo
    )
  } else if (filter !== 'all') {
    // 按对话类型过滤
    filtered = filtered.filter(conv => conv.type === filter)
  }
  
  return filtered
}

