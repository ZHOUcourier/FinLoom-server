/**
 * 聊天相关常量配置
 */

// 对话筛选器
export const CONVERSATION_FILTERS = [
  { label: '全部', value: 'all' },
  { label: '置顶', value: 'pinned' },
  { label: '最近', value: 'recent' },
  { label: '投资', value: 'investment' },
  { label: '风险', value: 'risk' }
]

// 快速问题卡片
export const QUICK_QUESTIONS = [
  { 
    text: '推荐一些稳健的投资标的', 
    icon: 'mdi-chart-line', 
    color: 'primary',
    description: '基于风险偏好推荐优质股票'
  },
  { 
    text: '分析当前市场趋势', 
    icon: 'mdi-trending-up', 
    color: 'success',
    description: '深度解读市场动态和机会'
  },
  { 
    text: '帮我优化投资组合', 
    icon: 'mdi-chart-pie', 
    color: 'secondary',
    description: '智能调整资产配置比例'
  },
  { 
    text: '评估投资风险', 
    icon: 'mdi-shield-alert', 
    color: 'warning',
    description: '全面分析投资风险因素'
  },
  { 
    text: '解释技术指标', 
    icon: 'mdi-chart-areaspline', 
    color: 'info',
    description: '详细解读各类技术分析指标'
  },
  { 
    text: '制定交易策略', 
    icon: 'mdi-strategy', 
    color: 'tertiary',
    description: '量身定制个性化交易方案'
  }
]

// 对话类型图标映射
export const CONVERSATION_ICONS = {
  'investment': 'mdi-chart-line',
  'risk': 'mdi-shield-alert',
  'strategy': 'mdi-strategy',
  'general': 'mdi-chat-outline',
  'analysis': 'mdi-chart-areaspline'
}

// 对话类型颜色映射
export const CONVERSATION_COLORS = {
  'investment': 'primary',
  'risk': 'error',
  'strategy': 'secondary',
  'general': 'default',
  'analysis': 'info'
}

// AI模型选项（只保留阿里云）
export const AI_MODELS = [
  { title: '阿里云 Qwen', value: 'qwen-plus' }
]

// 风险偏好选项
export const RISK_TOLERANCE_OPTIONS = [
  { title: '保守', value: 'low' },
  { title: '中等', value: 'medium' },
  { title: '激进', value: 'high' }
]

// 默认AI设置（使用阿里云作为默认）
export const DEFAULT_AI_SETTINGS = {
  model: 'qwen-plus',
  temperature: 0.7,
  riskTolerance: 'medium'
}

