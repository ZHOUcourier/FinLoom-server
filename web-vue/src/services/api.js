/**
 * API服务统一导出
 * 
 * 注意：此文件已重构，API模块已拆分到 services/modules/ 目录
 * 此文件保留用于向后兼容，新代码请使用 services/index.js
 */

// 从新的模块化结构导入
export { api, apiClient } from './index'
export default apiClient

