/**
 * Vuetify 3 配置
 * Material Design 3 (Material You) 主题配置
 */
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { md3 } from 'vuetify/blueprints'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Material 3 自定义主题
const finloomTheme = {
  dark: false,
  colors: {
    // Material 3 色彩系统
    primary: '#1E88E5',           // 主色
    'on-primary': '#FFFFFF',
    'primary-container': '#D3E4FD',
    'on-primary-container': '#001C38',
    
    secondary: '#00ACC1',         // 次要色
    'on-secondary': '#FFFFFF',
    'secondary-container': '#C2F0F7',
    'on-secondary-container': '#002023',
    
    tertiary: '#7B61FF',          // 第三色
    'on-tertiary': '#FFFFFF',
    'tertiary-container': '#E7DEFF',
    'on-tertiary-container': '#1A0061',
    
    error: '#BA1A1A',
    'on-error': '#FFFFFF',
    'error-container': '#FFDAD6',
    'on-error-container': '#410002',
    
    success: '#00A86B',
    warning: '#FF9800',
    info: '#2196F3',
    
    background: '#FBF8F3',        // 淡淡的米色
    'on-background': '#1A1C1E',
    
    surface: '#FBF8F3',            // 淡淡的米色
    'on-surface': '#1A1C1E',
    'surface-variant': '#E1E2EC',
    'on-surface-variant': '#44474E',
    
    outline: '#74777F',
    'outline-variant': '#C4C6D0',
    
    shadow: '#000000',
    scrim: '#000000',
    
    'inverse-surface': '#2F3033',
    'inverse-on-surface': '#F1F0F4',
    'inverse-primary': '#A8C8FF',
    
    // 自定义金融色
    bullish: '#00A86B',
    bearish: '#BA1A1A',
  }
}

const finloomDarkTheme = {
  dark: true,
  colors: {
    // Material 3 深色模式
    primary: '#A8C8FF',
    'on-primary': '#003258',
    'primary-container': '#00497D',
    'on-primary-container': '#D3E4FD',
    
    secondary: '#84D8E8',
    'on-secondary': '#00363E',
    'secondary-container': '#004F58',
    'on-secondary-container': '#C2F0F7',
    
    tertiary: '#CCB9FF',
    'on-tertiary': '#330097',
    'tertiary-container': '#4A00B3',
    'on-tertiary-container': '#E7DEFF',
    
    error: '#FFB4AB',
    'on-error': '#690005',
    'error-container': '#93000A',
    'on-error-container': '#FFDAD6',
    
    success: '#4ADE80',
    warning: '#FFB74D',
    info: '#64B5F6',
    
    background: '#1A1C1E',
    'on-background': '#E3E2E6',
    
    surface: '#1A1C1E',
    'on-surface': '#E3E2E6',
    'surface-variant': '#44474E',
    'on-surface-variant': '#C4C6D0',
    
    outline: '#8E9099',
    'outline-variant': '#44474E',
    
    shadow: '#000000',
    scrim: '#000000',
    
    'inverse-surface': '#E3E2E6',
    'inverse-on-surface': '#2F3033',
    'inverse-primary': '#1E88E5',
    
    bullish: '#4ADE80',
    bearish: '#FFB4AB',
  }
}

export default createVuetify({
  // 使用 Material 3 蓝图
  blueprint: md3,
  
  components,
  directives,
  
  theme: {
    defaultTheme: 'finloomTheme',
    themes: {
      finloomTheme,
      finloomDarkTheme,
    },
  },
  
  // Material 3 默认配置
  defaults: {
    VCard: {
      elevation: 0,
      border: true,
      rounded: 'xl',  // Material 3 更圆润
    },
    VBtn: {
      rounded: 'pill',  // Material 3 药丸形状
      elevation: 0,
      style: 'text-transform: none;',  // 不全大写
    },
    VTextField: {
      variant: 'filled',  // Material 3 默认 filled
      density: 'comfortable',
      rounded: 'lg',
      color: 'primary',   // 聚焦时使用主色
      baseColor: 'on-surface-variant',  // 未聚焦时的颜色
    },
    VTextarea: {
      variant: 'filled',
      density: 'comfortable',
      rounded: 'lg',
      color: 'primary',
      baseColor: 'on-surface-variant',
    },
    VSelect: {
      variant: 'filled',
      density: 'comfortable',
      rounded: 'lg',
      color: 'primary',
      baseColor: 'on-surface-variant',
    },
    VSwitch: {
      color: 'primary',
      inset: true,
    },
    VChip: {
      rounded: 'lg',
    },
    VList: {
      rounded: 'xl',
    },
    VSheet: {
      rounded: 'xl',
    },
  },
  
  icons: {
    defaultSet: 'mdi',
  },
})

