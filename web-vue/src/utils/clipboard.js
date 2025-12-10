/**
 * 剪贴板工具函数
 */

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} 是否成功
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('复制到剪贴板失败:', error)
    // 降级方案
    return fallbackCopy(text)
  }
}

/**
 * 降级复制方案（兼容旧浏览器）
 * @param {string} text - 要复制的文本
 * @returns {boolean} 是否成功
 */
function fallbackCopy(text) {
  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const success = document.execCommand('copy')
    document.body.removeChild(textarea)
    return success
  } catch (error) {
    console.error('降级复制方案失败:', error)
    return false
  }
}

/**
 * 从剪贴板读取文本
 * @returns {Promise<string|null>} 剪贴板文本
 */
export async function readFromClipboard() {
  try {
    const text = await navigator.clipboard.readText()
    return text
  } catch (error) {
    console.error('从剪贴板读取失败:', error)
    return null
  }
}

