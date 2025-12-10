/**
 * 日期时间工具函数
 */

/**
 * 格式化时间戳
 * @param {Date|string|number} timestamp - 时间戳
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(timestamp) {
  return new Date(timestamp).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 格式化完整日期时间
 * @param {Date|string|number} timestamp - 时间戳
 * @returns {string} 格式化后的日期时间字符串
 */
export function formatDateTime(timestamp) {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 获取相对时间描述
 * @param {Date|string|number} timestamp - 时间戳
 * @returns {string} 相对时间描述
 */
export function getRelativeTime(timestamp) {
  const now = new Date()
  const date = new Date(timestamp)
  const diff = now - date
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return formatTime(timestamp)
}

/**
 * 判断是否为今天
 * @param {Date|string|number} timestamp - 时间戳
 * @returns {boolean}
 */
export function isToday(timestamp) {
  const date = new Date(timestamp)
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

/**
 * 判断是否在指定天数内
 * @param {Date|string|number} timestamp - 时间戳
 * @param {number} days - 天数
 * @returns {boolean}
 */
export function isWithinDays(timestamp, days) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  return diff < days * 24 * 60 * 60 * 1000
}

