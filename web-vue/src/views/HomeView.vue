<template>
  <div class="home-view">
    <!-- 视频播放模态框 -->
    <div v-if="showVideoModal" class="video-modal" @click="closeVideoModal">
      <div class="video-modal-content" @click.stop>
        <button class="video-close-btn" @click="closeVideoModal">
          <i class="fas fa-times"></i>
        </button>
        <video 
          ref="modalVideoRef"
          controls 
          autoplay
          muted
          style="width: 100%; height: 100%; border-radius: 12px;">
          <source src="/video.mp4" type="video/mp4">
          您的浏览器不支持视频播放。
        </video>
      </div>
    </div>

    <!-- 导航栏 -->
    <nav class="navbar" :class="{ scrolled: isScrolled, docked: isDocked }">
      <div class="nav-container">
        <RouterLink to="/" class="nav-brand">
          <i class="fas fa-chart-network"></i>
          <span>FinLoom</span>
        </RouterLink>

        <div class="nav-menu">
          <a href="#features" class="nav-link">功能</a>
          <a href="#modules" class="nav-link">模块</a>
          <a href="#company" class="nav-link">关于我们</a>
          <button @click="goToDashboard" class="nav-btn">
            进入平台
            <svg
              class="nav-btn-arrow"
              viewBox="0 0 16 19"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M7 18C7 18.5523 7.44772 19 8 19C8.55228 19 9 18.5523 9 18H7ZM8.70711 0.292893C8.31658 -0.0976311 7.68342 -0.0976311 7.29289 0.292893L0.928932 6.65685C0.538408 7.04738 0.538408 7.68054 0.928932 8.07107C1.31946 8.46159 1.95262 8.46159 2.34315 8.07107L8 2.41421L13.6569 8.07107C14.0474 8.46159 14.6805 8.46159 15.0711 8.07107C15.4616 7.68054 15.4616 7.04738 15.0711 6.65685L8.70711 0.292893ZM9 18L9 1H7L7 18H9Z"
              ></path>
            </svg>
          </button>
        </div>
      </div>
    </nav>

    <!-- Hero区域 -->
    <section class="hero">
      <div class="hero-bg">
        <div class="gradient-orb gradient-orb-1"></div>
        <div class="gradient-orb gradient-orb-2"></div>
        <div class="gradient-orb gradient-orb-3"></div>
      </div>
      <div class="sky-blue-overlay"></div>
      
      <div class="hero-container">
        <div class="hero-content">
          <div class="hero-badge">
            <i class="fas fa-chart-line"></i>
            <span>FIN-R1赋能的自适应量化投资引擎</span>
          </div>
          
          <h1 class="hero-title">
            让投资决策<br>
                    <span class="gradient-text">更加智能</span>
          </h1>
          
          <p class="hero-subtitle">
            基于FIN-R1深度学习模型，整合12大专业模块，<br />
            结合前沿人工智能与深度量化分析，为专业投资者打造的下一代智能投资平台
          </p>
          
          <div class="hero-actions">
            <button class="btn-primary" @click="goToDashboard">
              立即开始
              <svg
                class="btn-arrow"
                viewBox="0 0 16 19"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M7 18C7 18.5523 7.44772 19 8 19C8.55228 19 9 18.5523 9 18H7ZM8.70711 0.292893C8.31658 -0.0976311 7.68342 -0.0976311 7.29289 0.292893L0.928932 6.65685C0.538408 7.04738 0.538408 7.68054 0.928932 8.07107C1.31946 8.46159 1.95262 8.46159 2.34315 8.07107L8 2.41421L13.6569 8.07107C14.0474 8.46159 14.6805 8.46159 15.0711 8.07107C15.4616 7.68054 15.4616 7.04738 15.0711 6.65685L8.70711 0.292893ZM9 18L9 1H7L7 18H9Z"
                ></path>
              </svg>
            </button>
            <button class="btn-secondary" @click="openVideoModal">
              <i class="fas fa-play-circle"></i>
              <span>观看演示</span>
            </button>
          </div>
          
          <div class="hero-stats">
            <div class="stat-item">
              <div class="stat-value">99.9%</div>
              <div class="stat-label">系统可用性</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">12+</div>
              <div class="stat-label">专业模块</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">&lt;10ms</div>
              <div class="stat-label">响应时间</div>
            </div>
          </div>
        </div>
        
        <div class="hero-visual">
          <div class="dashboard-mockup">
            <div class="mockup-header">
              <div class="mockup-dot red"></div>
              <div class="mockup-dot yellow"></div>
              <div class="mockup-dot green"></div>
            </div>
            <div class="mockup-chart">
              <video 
                autoplay 
                loop 
                muted
                playsinline
                style="width: 100%; height: 100%; object-fit: contain; border-radius: 12px;">
                <source src="/video.mp4" type="video/mp4">
                您的浏览器不支持视频播放。
              </video>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能特性 -->
    <section id="features" class="features-section">
      <div class="section-header">
        <h2>核心功能</h2>
        <p>强大的功能助您把握市场脉搏</p>
        <p>专业的量化工具与AI智能分析，为您的投资保驾护航</p>
      </div>

      <div class="features-grid">
        <div v-for="(feature, index) in features" :key="index" class="feature-card">
          <div class="card-content">
            <!-- 正面：显示功能名称和图标 -->
            <div class="card-front" :style="{ background: feature.background }">
              <div class="card-img">
                <div class="circle" :style="{ background: feature.color, opacity: 0.15 }"></div>
                <div class="circle circle-right" :style="{ background: feature.color, opacity: 0.2 }"></div>
                <div class="circle circle-bottom" :style="{ background: feature.color, opacity: 0.18 }"></div>
              </div>
              <div class="card-front-content">
                <div class="card-icon-wrapper" :style="{ background: feature.color }">
                  <i :class="feature.icon"></i>
                </div>
                <div class="card-front-info">
                  <h3 class="card-front-title">{{ feature.title }}</h3>
                </div>
              </div>
            </div>
            <!-- 背面：显示功能详细描述 -->
            <div class="card-back">
              <div class="card-back-content">
                <div class="card-back-header">
                  <div class="card-back-icon" :style="{ background: feature.color }">
                    <i :class="feature.icon"></i>
                  </div>
                  <strong>{{ feature.title }}</strong>
                </div>
                <p class="card-back-description">{{ feature.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 模块展示 -->
    <section id="modules" class="modules-section">
      <div class="section-header">
        <h2>完整模块化架构</h2>
        <p>12个专业模块协同工作</p>
      </div>

      <div class="modules-grid">
        <div v-for="(module, index) in modules" :key="index" class="comic-card" role="article">
          <div class="card-header">
            <div class="card-avatar" :style="{ background: module.gradient }">
              <span class="avatar-number">{{ String(index + 1).padStart(2, '0') }}</span>
            </div>
            <div class="card-user-info">
              <p class="card-username">{{ module.title }}</p>
              <p class="card-handle">MODULE-{{ String(index + 1).padStart(2, '0') }}</p>
            </div>
          </div>

          <div class="card-content">
            <div class="card-image-container">
              <i :class="module.icon" class="module-icon"></i>
            </div>
            <p class="card-caption">
              {{ module.caption }}
            </p>
          </div>

          <div class="card-actions">
            <button class="action-button like-button" :aria-label="`了解 ${module.title}`">
              <svg class="action-button-icon" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"></path>
              </svg>
            </button>
            <button class="action-button comment-button" :aria-label="`查看 ${module.title} 详情`">
              <svg class="action-button-icon" viewBox="0 0 24 24">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
            <button class="action-button share-button" :aria-label="`分享 ${module.title}`">
              <svg class="action-button-icon" viewBox="0 0 24 24">
                <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 公司信息 -->
    <section id="company" class="company-section">
      <div class="company-container">
        <div class="company-logo">
          <i class="fas fa-chart-network"></i>
        </div>
        <div class="company-logo">📊</div>
        <h2 class="company-title">关于 FinLoom</h2>
        <p class="company-desc">
          FinLoom 是新一代智能量化投资平台，致力于通过人工智能技术革新传统投资方式。
          我们相信，专业的工具和智能的分析能够帮助每一位投资者做出更明智的决策。
        </p>
        <div class="company-stats">
          <div class="company-stat">
            <div class="company-stat-value">2024</div>
            <div class="company-stat-label">成立年份</div>
          </div>
          <div class="company-stat">
            <div class="company-stat-value">10,000+</div>
            <div class="company-stat-label">活跃用户</div>
          </div>
          <div class="company-stat">
            <div class="company-stat-value">24/7</div>
            <div class="company-stat-label">全天候服务</div>
          </div>
          <div class="company-stat">
            <div class="company-stat-value">5,000+</div>
            <div class="company-stat-label">市场指标</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 回到置顶按钮 -->
    <button v-if="showBackToTop" class="back-to-top-button" @click="scrollToTop">
      <svg class="svgIcon" viewBox="0 0 384 512">
        <path
          d="M214.6 41.4c-12.5-12.5-32.8-12.5-45.3 0l-160 160c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L160 141.2V448c0 17.7 14.3 32 32 32s32-14.3 32-32V141.2L329.4 246.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3l-160-160z"
        ></path>
      </svg>
    </button>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-brand">
          <h3>
            <i class="fas fa-chart-network"></i>
            FinLoom
          </h3>
          <p>专业的智能量化投资平台，让投资决策更加智能。</p>
        </div>
        
        <div class="footer-section">
          <h4>产品</h4>
          <div class="footer-links">
            <RouterLink to="/login">智能对话</RouterLink>
            <RouterLink to="/login">策略制定</RouterLink>
            <RouterLink to="/login">数据分析</RouterLink>
            <RouterLink to="/login">风险管理</RouterLink>
          </div>
        </div>

        <div class="footer-section">
          <h4>公司</h4>
          <div class="footer-links">
            <a href="#company">关于我们</a>
            <a href="#">团队介绍</a>
            <a href="#">加入我们</a>
            <a href="#">联系方式</a>
          </div>
        </div>

        <div class="footer-section">
          <h4>资源</h4>
          <div class="footer-links">
            <a href="#">API文档</a>
            <a href="#">开发者指南</a>
            <a href="#">帮助中心</a>
            <a href="#">隐私政策</a>
          </div>
        </div>
      </div>
      
      <div class="footer-bottom">
        <p>© 2025 FinLoom. 保留所有权利。</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isScrolled = ref(false)
const isDocked = ref(false)
const showBackToTop = ref(false)
const showVideoModal = ref(false)
const modalVideoRef = ref(null)
const chartRef = ref(null)

const features = [
  { 
    icon: 'fas fa-brain', 
    title: 'FIN-R1 AI', 
    description: '采用先进的深度学习算法和神经网络模型，实时分析海量市场数据，挖掘隐藏的交易机会。通过多层次特征提取和模式识别，为您提供精准的市场预测和智能化投资建议，让AI成为您的专业投资顾问。', 
    color: 'linear-gradient(135deg, #667eea, #764ba2)',
    background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.06) 100%)',
    link: '#'
  },
  { 
    icon: 'fas fa-shield-alt', 
    title: '风险控制', 
    description: '构建全方位的风险管理体系，从VaR风险价值分析到压力测试，从仓位管理到止损策略。实时监控市场波动和组合风险指标，动态调整风险敞口，多维度风险评估确保投资安全，帮助您在追求收益的同时有效控制风险。', 
    color: 'linear-gradient(135deg, #4facfe, #00f2fe)',
    background: 'linear-gradient(135deg, rgba(79, 172, 254, 0.04) 0%, rgba(0, 242, 254, 0.07) 100%)',
    link: '#'
  },
  { 
    icon: 'fas fa-chart-area', 
    title: '市场分析', 
    description: '融合传统技术分析与AI智能算法，实时监测市场情绪变化和异常交易行为。通过新闻文本分析、社交媒体情绪追踪、成交量异常检测等多种手段，全面洞察市场动态，及时捕捉投资机会和潜在风险信号。', 
    color: 'linear-gradient(135deg, #fa709a, #fee140)',
    background: 'linear-gradient(135deg, rgba(250, 112, 154, 0.05) 0%, rgba(254, 225, 64, 0.08) 100%)',
    link: '#'
  },
  { 
    icon: 'fas fa-flask', 
    title: '策略回测', 
    description: '基于真实历史数据进行高精度策略验证，支持多因子回测、蒙特卡洛模拟和参数优化。详细的回测报告涵盖收益率、夏普比率、最大回撤等关键指标，让您全面了解策略表现，优化投资决策，确保策略的稳健性和可靠性。', 
    color: 'linear-gradient(135deg, #30cfd0, #330867)',
    background: 'linear-gradient(135deg, rgba(48, 207, 208, 0.04) 0%, rgba(51, 8, 103, 0.06) 100%)',
    link: '#'
  },
  { 
    icon: 'fas fa-comments', 
    title: '💬 智能对话模式', 
    description: '与AI助手自然交流，快速获取市场分析、个股研究和投资建议。支持实时对话，灵活交互，让投资咨询更加便捷。', 
    color: 'linear-gradient(135deg, #667eea, #764ba2)',
    background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.03) 0%, rgba(168, 85, 247, 0.07) 100%)',
    link: '/login'
  },
  { 
    icon: 'fas fa-chart-line', 
    title: '📊 完整策略模式', 
    description: '系统化构建投资策略，从需求分析到AI生成，再到回测优化和代码生成，提供全流程支持。', 
    color: 'linear-gradient(135deg, #f093fb, #f5576c)',
    background: 'linear-gradient(135deg, rgba(240, 147, 251, 0.05) 0%, rgba(245, 87, 108, 0.08) 100%)',
    link: '/login'
  },
  { 
    icon: 'fas fa-database', 
    title: '📈 多源数据融合', 
    description: '整合市场行情、财务数据、新闻情绪等多维度信息，提供全面的数据支持，让投资决策更有依据。', 
    color: 'linear-gradient(135deg, #4facfe, #00f2fe)',
    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.04) 0%, rgba(14, 165, 233, 0.07) 100%)',
    link: '#'
  },
  { 
    icon: 'fas fa-shield-alt', 
    title: '🛡️ 风险管理系统', 
    description: '实时监控组合风险，动态调整仓位配置，多层次风险控制机制，保护您的投资安全。', 
    color: 'linear-gradient(135deg, #43e97b, #38f9d7)',
    background: 'linear-gradient(135deg, rgba(67, 233, 123, 0.05) 0%, rgba(56, 249, 215, 0.08) 100%)',
    link: '#'
  }
]

const modules = [
  { 
    title: '环境管理', 
    description: '系统配置与依赖管理',
    icon: 'fas fa-cogs',
    gradient: 'linear-gradient(45deg, #667eea, #764ba2)',
    caption: '强大的系统配置管理，确保所有依赖正确运行！让您的交易系统稳如磐石！'
  },
  { 
    title: '数据管道', 
    description: '多源数据采集与存储',
    icon: 'fas fa-database',
    gradient: 'linear-gradient(45deg, #f093fb, #f5576c)',
    caption: '实时采集全球市场数据，多源数据融合，为您的决策提供最全面的信息支持！'
  },
  { 
    title: '特征工程', 
    description: '智能特征提取与生成',
    icon: 'fas fa-project-diagram',
    gradient: 'linear-gradient(45deg, #4facfe, #00f2fe)',
    caption: '自动挖掘市场特征，智能生成交易信号，发现别人看不到的投资机会！'
  },
  { 
    title: '市场分析', 
    description: '综合市场情报分析',
    icon: 'fas fa-chart-bar',
    gradient: 'linear-gradient(45deg, #43e97b, #38f9d7)',
    caption: 'AI驱动的市场分析引擎，实时解读市场情绪，把握最佳投资时机！'
  },
  { 
    title: '风险管理', 
    description: '投资组合优化',
    icon: 'fas fa-shield-alt',
    gradient: 'linear-gradient(45deg, #fa709a, #fee140)',
    caption: '多维度风险评估，智能仓位控制，在风险可控的前提下追求最大收益！'
  },
  { 
    title: '监控告警', 
    description: '实时系统监控',
    icon: 'fas fa-bell',
    gradient: 'linear-gradient(45deg, #30cfd0, #330867)',
    caption: '24/7全天候监控系统状态，异常情况即时推送，让您高枕无忧！'
  },
  { 
    title: '参数优化', 
    description: '超参数自动调优',
    icon: 'fas fa-sliders-h',
    gradient: 'linear-gradient(45deg, #a8edea, #fed6e3)',
    caption: '智能寻找最优参数组合，让您的策略性能达到巅峰状态！'
  },
  { 
    title: '交易执行', 
    description: '订单智能路由',
    icon: 'fas fa-exchange-alt',
    gradient: 'linear-gradient(45deg, #ff9a9e, #fecfef)',
    caption: '毫秒级订单执行，智能路由优化，确保每一笔交易都获得最优价格！'
  },
  { 
    title: '回测引擎', 
    description: '策略性能评估',
    icon: 'fas fa-history',
    gradient: 'linear-gradient(45deg, #ffecd2, #fcb69f)',
    caption: '高精度历史回测，全面评估策略表现，让您对策略效果心中有数！'
  },
  { 
    title: 'AI交互', 
    description: 'FIN-R1对话系统',
    icon: 'fas fa-robot',
    gradient: 'linear-gradient(45deg, #667eea, #764ba2)',
    caption: '与FIN-R1 AI对话，获取专业投资建议，像和顶级分析师交流一样简单！'
  },
  { 
    title: '可视化', 
    description: '交互式数据展示',
    icon: 'fas fa-chart-pie',
    gradient: 'linear-gradient(45deg, #fbc2eb, #a6c1ee)',
    caption: '精美的数据可视化界面，让复杂的市场数据一目了然，辅助您快速决策！'
  },
  { 
    title: 'AI模型', 
    description: '深度学习模型库',
    icon: 'fas fa-brain',
    gradient: 'linear-gradient(45deg, #fdcbf1, #e6dee9)',
    caption: '前沿深度学习模型，持续学习市场规律，为您提供最智能的交易策略！'
  }
]

function goToDashboard() {
  // 🔒 修改：不再自动登录，始终跳转到登录页
  // 让用户手动选择是否登录
  router.push('/login')
}

function scrollToFeatures() {
  document.querySelector('#features')?.scrollIntoView({ behavior: 'smooth' })
}

function openVideoModal() {
  showVideoModal.value = true
  document.body.style.overflow = 'hidden'
}

function closeVideoModal() {
  showVideoModal.value = false
  document.body.style.overflow = 'auto'
  if (modalVideoRef.value) {
    modalVideoRef.value.pause()
  }
}

function handleFeatureClick(link) {
  if (link && link !== '#') {
    router.push(link)
  }
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

function handleScroll() {
  isScrolled.value = window.scrollY > 50
  showBackToTop.value = window.scrollY > 300
  
  // 检测是否滚动到公司信息区域
  const companySection = document.querySelector('#company')
  if (companySection) {
    const rect = companySection.getBoundingClientRect()
    const windowHeight = window.innerHeight
    
    // 当公司信息区域进入视口时，导航栏吸附到顶部
    isDocked.value = rect.top <= 100 && rect.bottom > windowHeight * 0.3
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  initChart()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

function initChart() {
  const canvas = chartRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  const width = canvas.width = canvas.offsetWidth * 2
  const height = canvas.height = canvas.offsetHeight * 2
  ctx.scale(2, 2)

  const points = []
  for (let i = 0; i < 50; i++) {
    points.push({
      x: (i / 50) * (width / 2),
      y: Math.random() * (height / 2) * 0.5 + (height / 2) * 0.25
    })
  }

  function drawChart() {
    ctx.clearRect(0, 0, width / 2, height / 2)
    
    // 绘制渐变背景
    const gradient = ctx.createLinearGradient(0, 0, 0, height / 2)
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)')
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0)')
    
    // 绘制面积
    ctx.beginPath()
    ctx.moveTo(points[0].x, height / 2)
    points.forEach((point, i) => {
      if (i === 0) {
        ctx.lineTo(point.x, point.y)
      } else {
        const xc = (points[i - 1].x + point.x) / 2
        const yc = (points[i - 1].y + point.y) / 2
        ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc)
      }
    })
    ctx.lineTo(points[points.length - 1].x, height / 2)
    ctx.closePath()
    ctx.fillStyle = gradient
    ctx.fill()
    
    // 绘制线条
    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)
    points.forEach((point, i) => {
      if (i > 0) {
        const xc = (points[i - 1].x + point.x) / 2
        const yc = (points[i - 1].y + point.y) / 2
        ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc)
      }
    })
    ctx.strokeStyle = '#3b82f6'
    ctx.lineWidth = 3
    ctx.stroke()
    
    // 动画更新
    points.forEach(point => {
      point.y += (Math.random() - 0.5) * 2
      point.y = Math.max((height / 2) * 0.1, Math.min((height / 2) * 0.7, point.y))
    })
    
    requestAnimationFrame(drawChart)
  }

  drawChart()
}
</script>

<style lang="scss" scoped>
.home-view {
  min-height: 100vh;
  background: #ffffff;
}

/* 视频模态框 */
.video-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(10px);
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.video-modal-content {
  position: relative;
  width: 90%;
  max-width: 1200px;
  height: auto;
  max-height: 80vh;
  background: #000;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.video-close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  z-index: 10;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: rgba(239, 68, 68, 0.8);
    border-color: rgba(239, 68, 68, 1);
    transform: rotate(90deg) scale(1.1);
  }
}

.navbar {
  position: fixed;
  top: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 1200px;
  width: calc(100% - 4rem);
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 100px;
  box-shadow: 
    0 8px 32px 0 rgba(31, 38, 135, 0.15),
    0 4px 16px 0 rgba(0, 0, 0, 0.08),
    inset 0 1px 0 0 rgba(255, 255, 255, 0.6),
    inset 0 -1px 0 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 100px;
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.4) 0%,
      rgba(255, 255, 255, 0.1) 50%,
      rgba(255, 255, 255, 0.3) 100%
    );
    pointer-events: none;
    opacity: 0.8;
  }

  &.scrolled {
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(50px) saturate(200%);
    -webkit-backdrop-filter: blur(50px) saturate(200%);
    box-shadow: 
      0 12px 48px 0 rgba(31, 38, 135, 0.2),
      0 6px 24px 0 rgba(0, 0, 0, 0.12),
      inset 0 1px 0 0 rgba(255, 255, 255, 0.7),
      inset 0 -1px 0 0 rgba(0, 0, 0, 0.08);
    
    &::before {
      opacity: 1;
    }
  }

  &.docked {
    top: 0;
    left: 0;
    right: 0;
    transform: translateX(0);
    width: 100%;
    max-width: none;
    border-radius: 0;
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(50px) saturate(200%);
    -webkit-backdrop-filter: blur(50px) saturate(200%);
    box-shadow: 
      0 4px 20px 0 rgba(31, 38, 135, 0.15),
      inset 0 1px 0 0 rgba(255, 255, 255, 0.7);
    border-bottom: 1px solid rgba(255, 255, 255, 0.4);
    border-left: none;
    border-right: none;
    border-top: none;
    
    &::before {
      border-radius: 0;
      opacity: 0.6;
    }
  }

  @media (max-width: 768px) {
    width: calc(100% - 2rem);
    top: 1rem;

    &.docked {
      width: 100%;
      top: 0;
    }
  }
}

.nav-container {
  width: 100%;
  padding: 0.75rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
  transition: padding 0.3s ease;

  @media (max-width: 768px) {
    padding: 0.75rem 1.5rem;
  }
}

.navbar.docked .nav-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 3rem;

  @media (max-width: 768px) {
    padding: 1rem 1.5rem;
  }
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 900;
  color: #0f172a;
  text-decoration: none;
  transition: transform 0.3s ease;

  &:hover {
    transform: scale(1.05);
  }

  i {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 1.5rem;

  @media (max-width: 768px) {
    gap: 1rem;
  }
}

.nav-link {
  color: #475569;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 0;
    height: 2px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    transition: width 0.3s ease;
  }

  &:hover {
    color: #3b82f6;
    
    &::after {
      width: 100%;
    }
  }
}

.nav-btn {
  display: flex;
  justify-content: center;
  gap: 0.4rem;
  align-items: center;
  text-decoration: none;
  padding: 0.5rem 1.2rem;
  font-size: 0.95rem;
  font-weight: 600;
  background: #ffa200c1;
  color: #000000;
  border: 2px solid #ef444400;
  border-radius: 9999px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  z-index: 10;
  isolation: auto;
  transition: all 0.7s;

  &::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    background: #dc2626;
    left: -100%;
    top: 0;
    border-radius: 9999px;
    z-index: -10;
    transition: all 0.7s;
    aspect-ratio: 1;
    transform: scale(0);
  }

  &:hover {
    color: #f9fafb;

    &::before {
      left: 0;
      transform: scale(1.5);
    }
  }

  .nav-btn-arrow {
    width: 1.5rem;
    height: 1.5rem;
    padding: 0.25rem;
    background: #f9fafb;
    border: 1px solid #374151;
    border-radius: 9999px;
    transition: all 0.3s ease-in-out;
    transform: rotate(45deg);

    path {
      fill: #1f2937;
    }
  }

  &:hover .nav-btn-arrow {
    background: #f9fafb;
    border-color: transparent;
    transform: rotate(90deg);

    path {
      fill: #1f2937;
    }
  }
}

/* Hero区域 */
.hero {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  padding: 10rem 3rem 6rem;
  position: relative;
  overflow: hidden;
}

.sky-blue-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, 
    rgba(135, 206, 250, 0) 0%,
    rgba(135, 206, 250, 0.1) 20%,
    rgba(135, 206, 250, 0.2) 40%,
    rgba(135, 206, 250, 0.3) 60%,
    rgba(135, 206, 250, 0.4) 80%,
    rgba(135, 206, 250, 0.5) 100%
  );
  opacity: 0;
  animation: skyBlueWave 3s ease-out 0.5s forwards;
  pointer-events: none;
  z-index: 1;
}

@keyframes skyBlueWave {
  0% {
    opacity: 0;
    clip-path: inset(0 0 100% 0);
  }
  100% {
    opacity: 1;
    clip-path: inset(0 0 0 0);
  }
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.3;
  animation: float 20s infinite ease-in-out;
}

.gradient-orb-1 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  top: -10%;
  left: -10%;
  animation-delay: 0s;
}

.gradient-orb-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, var(--secondary), var(--accent));
  top: 40%;
  right: -5%;
  animation-delay: 7s;
}

.gradient-orb-3 {
  width: 350px;
  height: 350px;
  background: linear-gradient(135deg, var(--accent), var(--primary));
  bottom: -5%;
  left: 30%;
  animation-delay: 14s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(50px, -50px) scale(1.1);
  }
  66% {
    transform: translate(-50px, 50px) scale(0.9);
  }
}

.hero-container {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 6rem;
  align-items: center;
  position: relative;
  z-index: 2;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
}

.hero-content {
  animation: slideInLeft 1s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.25);
  border-radius: 50px;
  font-weight: 600;
  font-size: 0.95rem;
  color: #dc2626;
  margin-bottom: 2rem;
  transition: all 0.3s ease;

  i {
    font-size: 1rem;
  }

  &:hover {
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.35);
    transform: translateY(-2px);
  }
}

.hero-title {
  font-size: 5.5rem;
  font-weight: 900;
  line-height: 1.1;
  margin-bottom: 2rem;
  color: #1e293b;

  @media (max-width: 768px) {
    font-size: 3rem;
  }
}

.gradient-text {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 50%, #ef4444 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: #64748b;
  margin-bottom: 3rem;
  line-height: 1.8;

  @media (max-width: 768px) {
    font-size: 1.125rem;
  }
}

.hero-actions {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 3rem;

  @media (max-width: 768px) {
    flex-direction: column;
  }
}

.btn-primary {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  align-items: center;
  text-align: center;
  font-size: 1.2rem;
  font-weight: 600;
  padding: 1rem 2.5rem;
  background: #ffa200c1;
  color: #000000;
  border: 2px solid #ef444400;
  border-radius: 9999px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  z-index: 10;
  isolation: auto;
  transition: all 0.7s;

  &::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    background: #dc2626;
    left: -100%;
    top: 0;
    border-radius: 9999px;
    z-index: -10;
    transition: all 0.7s;
    aspect-ratio: 1;
    transform: scale(0);
  }

  &:hover {
    color: #f9fafb;

    &::before {
      left: 0;
      transform: scale(1.5);
    }
  }

  .btn-arrow {
    width: 2rem;
    height: 2rem;
    padding: 0.5rem;
    background: #f9fafb;
    border: 1px solid #374151;
    border-radius: 9999px;
    transition: all 0.3s ease-in-out;
    transform: rotate(45deg);

    path {
      fill: #1f2937;
    }
  }

  &:hover .btn-arrow {
    background: #f9fafb;
    border-color: transparent;
    transform: rotate(90deg);

    path {
      fill: #1f2937;
    }
  }
}

.btn-secondary {
  padding: 1.25rem 3rem;
  background: white;
  color: var(--dark);
  border: 2px solid #e2e8f0;
  border-radius: 50px;
  font-size: 1.2rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;

  &:hover {
    border-color: var(--primary);
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  }
}

.hero-stats {
  display: flex;
  gap: 3rem;

  @media (max-width: 768px) {
    justify-content: space-between;
    gap: 1rem;
  }
}

.stat-item {
  text-align: left;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 900;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;

  @media (max-width: 768px) {
    font-size: 1.75rem;
  }
}

.stat-label {
  color: #64748b;
  font-weight: 600;
  font-size: 0.875rem;
}

/* Hero可视化 */
.hero-visual {
  position: relative;
  animation: slideInRight 1s ease-out;
  padding: 1rem 0;

  @media (max-width: 1024px) {
    display: none;
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.dashboard-mockup {
  width: 100%;
  background: white;
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
  transform: scale(1.1);
  transform-origin: center center;
}

.mockup-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.mockup-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;

  &.red { background: #ef4444; }
  &.yellow { background: #f59e0b; }
  &.green { background: #10b981; }
}

.mockup-chart {
  width: 100%;
  height: 300px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 16px;
  position: relative;
  overflow: hidden;

  canvas {
    width: 100%;
    height: 100%;
  }
}

.features-section,
.modules-section {
  padding: 6rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 4rem;

  h2 {
    font-size: 3rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  p {
    font-size: 1.25rem;
    color: #64748b;
  }
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  justify-items: center;
  max-width: 1200px;
  margin: 0 auto;
  
  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.feature-card {
  overflow: visible;
  width: 240px;
  height: 320px;
  cursor: pointer;
  perspective: 1000px;
}

.card-content {
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: all 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-radius: 16px;
  position: relative;
}

.feature-card:hover .card-content {
  transform: rotateY(180deg) scale(1.05);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.card-front, .card-back {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  border-radius: 16px;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.card-front {
  color: #0f172a;
  transform: rotateY(0deg);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.card-back {
  width: 100%;
  height: 100%;
  justify-content: center;
  display: flex;
  align-items: center;
  overflow: hidden;
  transform: rotateY(180deg);
}

.card-back::before {
  position: absolute;
  content: ' ';
  display: block;
  width: 200px;
  height: 160%;
  background: linear-gradient(90deg, transparent, #3b82f6, #8b5cf6, #ec4899, #f59e0b, transparent);
  animation: rotation_481 5000ms infinite linear;
}

.card-back-content {
  position: absolute;
  width: 99%;
  height: 99%;
  background: linear-gradient(135deg, #ffffff 0%, #fef3c7 100%);
  border-radius: 14px;
  color: #0f172a;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 20px;
}

@keyframes rotation_481 {
  0% {
    transform: rotateZ(0deg);
  }
  100% {
    transform: rotateZ(360deg);
  }
}

/* 卡片正面样式 */
.card-front .card-front-content {
  position: absolute;
  width: 100%;
  height: 100%;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.card-icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  color: white;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.feature-card:hover .card-icon-wrapper {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
}

.card-front-info {
  text-align: center;
}

.card-front-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  transition: all 0.3s ease;
}

.feature-card:hover .card-front-title {
  transform: scale(1.05);
  color: #3b82f6;
}

/* 卡片背面样式 */
.card-back-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.1rem;
  color: #0f172a;
  margin-bottom: 10px;
}

.card-back-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.card-back-description {
  font-size: 0.85rem;
  line-height: 1.5;
  color: #475569;
  text-align: left;
  margin: 0;
  animation: fadeInUp 0.6s ease-out 0.3s both;
  overflow-y: auto;
  padding-right: 0.5rem;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-front .card-img {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.circle {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  position: absolute;
  filter: blur(30px);
  animation: floating 3s infinite ease-in-out;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform, filter, opacity;
}

.feature-card:hover .circle {
  filter: blur(45px);
  animation: floating-hover 2s infinite ease-in-out;
}

.circle-bottom {
  left: 50px;
  top: 0px;
  width: 150px;
  height: 150px;
  animation-delay: -800ms;
  transform-origin: center;
}

.circle-right {
  left: 160px;
  top: -80px;
  width: 30px;
  height: 30px;
  animation-delay: -1800ms;
  transform-origin: center;
}

@keyframes floating {
  0% {
    transform: translate(0px, 0px) rotate(0deg);
  }
  33% {
    transform: translate(5px, -8px) rotate(2deg);
  }
  66% {
    transform: translate(-5px, 8px) rotate(-2deg);
  }
  100% {
    transform: translate(0px, 0px) rotate(0deg);
  }
}

@keyframes floating-hover {
  0% {
    transform: translate(0px, 0px) scale(1) rotate(0deg);
  }
  25% {
    transform: translate(8px, -12px) scale(1.15) rotate(3deg);
  }
  50% {
    transform: translate(-8px, 5px) scale(1.2) rotate(-3deg);
  }
  75% {
    transform: translate(5px, 10px) scale(1.1) rotate(2deg);
  }
  100% {
    transform: translate(0px, 0px) scale(1) rotate(0deg);
  }
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
  justify-items: center;
}

/* 漫画风格卡片 */
.comic-card {
  --paper-white: #fefae8;
  --primary-yellow: #ffd900;
  --accent-red: #d92b2b;
  --accent-blue: #2b80d9;
  --ink-black: #212121;
  --border-stroke: 0.15em;
  --dot-color: rgba(0, 0, 0, 0.2);

  position: relative;
  display: flex;
  flex-direction: column;
  width: 18em;
  max-width: 333px;
  max-height: 500px;
  background-color: var(--paper-white);
  border: var(--border-stroke) solid var(--ink-black);
  border-radius: 0.5em;
  padding: 1em;
  box-shadow: 0.5em 0.5em 0 var(--ink-black);
  transition:
    transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.2s ease;
  transform-origin: bottom left;
  font-family: Impact, Haettenschweiler, "Arial Narrow Bold", sans-serif;
}

.comic-card:hover {
  transform: translateY(-0.6em) rotate(-2deg);
  box-shadow: 0.8em 0.8em 0 0.1em var(--accent-red);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.8em;
}

.card-avatar {
  width: 3.5em;
  height: 3.5em;
  border-radius: 50%;
  border: var(--border-stroke) solid var(--ink-black);
  flex-shrink: 0;
  transition: transform 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-number {
  font-size: 1.5em;
  font-weight: 900;
  color: white;
  text-shadow: 2px 2px 0 rgba(0, 0, 0, 0.3);
}

.comic-card:hover .card-avatar {
  transform: scale(1.1) rotate(5deg);
}

.card-user-info {
  margin-left: 0.8em;
  text-transform: uppercase;
}

.card-username {
  margin: 0;
  font-size: 1.2em;
  font-weight: 300;
  color: var(--ink-black);
  background-color: var(--primary-yellow);
  padding: 0.1em 0.5em;
  clip-path: polygon(0 0, 100% 0, 95% 100%, 5% 100%);
  letter-spacing: 1px;
}

.card-handle {
  margin: 0.2em 0 0 0;
  font-size: 0.8em;
  color: var(--ink-black);
  font-weight: 100;
  letter-spacing: 2px;
}

.card-content {
  flex-grow: 1;
}

.card-image-container {
  width: 100%;
  height: 9em;
  border-radius: 0.2em;
  border: var(--border-stroke) solid var(--ink-black);
  overflow: hidden;
  background-color: var(--accent-blue);
  background-image: radial-gradient(
    circle,
    var(--dot-color) 0.05em,
    transparent 0.05em
  );
  background-size: 0.5em 0.5em;
  background-position:
    0 0,
    0.25em 0.25em;
  transition: transform 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.module-icon {
  font-size: 4em;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 3px 3px 0 rgba(0, 0, 0, 0.2);
  transition: transform 0.3s ease;
}

.comic-card:hover .card-image-container {
  transform: skewX(-3deg) scale(1.02);
}

.comic-card:hover .module-icon {
  transform: scale(1.1) rotate(-5deg);
}

.card-caption {
  position: relative;
  margin: 0.8em 0;
  padding: 0.6em 0.8em;
  background-color: var(--paper-white);
  border: var(--border-stroke) solid var(--ink-black);
  border-radius: 0.5em;
  font-size: 0.9em;
  line-height: 1.3;
  color: var(--ink-black);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-weight: 500;
}

.card-caption::after {
  content: "";
  position: absolute;
  bottom: -0.6em;
  left: 1.5em;
  width: 0;
  height: 0;
  border: 0.5em solid var(--ink-black);
  border-color: var(--ink-black) transparent transparent transparent;
}

.card-caption::before {
  content: "";
  position: absolute;
  bottom: -0.4em;
  left: 1.6em;
  width: 0;
  height: 0;
  border: 0.4em solid var(--paper-white);
  border-color: var(--paper-white) transparent transparent transparent;
}

.card-actions {
  display: flex;
  justify-content: space-around;
  margin-top: auto;
  padding-top: 0.5em;
}

.action-button {
  background-color: var(--primary-yellow);
  border: var(--border-stroke) solid var(--ink-black);
  padding: 0.5em;
  cursor: pointer;
  border-radius: 0.5em;
  box-shadow: 0.2em 0.2em 0 var(--ink-black);
  transition:
    transform 0.1s ease,
    box-shadow 0.1s ease,
    background-color 0.2s ease;
}

.action-button:hover {
  background-color: var(--accent-red);
}

.action-button:active {
  transform: translate(0.2em, 0.2em);
  box-shadow: none;
}

.action-button-icon {
  width: 1.3em;
  height: 1.3em;
  stroke-width: 3;
  stroke: var(--ink-black);
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  display: block;
}

.action-button:hover .action-button-icon {
  stroke: var(--paper-white);
}

.like-button:hover .action-button-icon {
  fill: var(--paper-white);
}

/* 公司信息部分 */
.company-section {
  padding: 8rem 3rem;
  background: var(--dark);
  color: white;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 100%;
    height: 200%;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
    animation: rotate 30s linear infinite;
  }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.company-container {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
  text-align: center;
}

.company-logo {
  font-size: 6rem;
  margin-bottom: 2rem;
  color: #3b82f6;
}

.company-title {
  font-size: 3.5rem;
  font-weight: 900;
  margin-bottom: 1.5rem;

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
}

.company-desc {
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.8);
  max-width: 800px;
  margin: 0 auto 4rem;
  line-height: 1.8;

  @media (max-width: 768px) {
    font-size: 1.125rem;
  }
}

.company-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 3rem;
  margin-top: 5rem;

  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 2rem;
  }
}

.company-stat {
  text-align: center;
}

.company-stat-value {
  font-size: 3.5rem;
  font-weight: 900;
  background: linear-gradient(135deg, white, #94a3b8);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
}

.company-stat-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.2rem;

  @media (max-width: 768px) {
    font-size: 1rem;
  }
}

/* 页脚 */
.footer {
  background: #0a0e1a;
  color: white;
  padding: 4rem 3rem 2rem;
}

.footer-content {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 4rem;
  margin-bottom: 3rem;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 1rem;

  h3 {
    font-size: 2rem;
    font-weight: 900;
    display: flex;
    align-items: center;
    gap: 0.5rem;

    i {
      color: #3b82f6;
    }
  }

  p {
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.8;
  }
}

.footer-section {
  h4 {
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
  }
}

.footer-links {
  display: flex;
  flex-direction: column;
  gap: 1rem;

  a, .router-link {
    color: rgba(255, 255, 255, 0.6);
    text-decoration: none;
    transition: all 0.3s ease;

    &:hover {
      color: white;
      padding-left: 5px;
    }
  }
}

.footer-bottom {
  max-width: 1400px;
  margin: 0 auto;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;

  p {
    color: rgba(255, 255, 255, 0.5);
  }
}

/* 回到置顶按钮 */
.back-to-top-button {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: rgb(20, 20, 20);
  border: none;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0px 0px 0px 4px rgba(180, 160, 255, 0.253);
  cursor: pointer;
  transition-duration: 0.3s;
  overflow: hidden;
  z-index: 999;

  .svgIcon {
    width: 12px;
    transition-duration: 0.3s;

    path {
      fill: white;
    }
  }

  &:hover {
    width: 140px;
    border-radius: 50px;
    transition-duration: 0.3s;
    background-color: rgb(181, 160, 255);
    align-items: center;

    .svgIcon {
      transition-duration: 0.3s;
      transform: translateY(-200%);
    }
  }

  &::before {
    position: absolute;
    bottom: -20px;
    content: "Back to Top";
    color: white;
    font-size: 0px;
  }

  &:hover::before {
    font-size: 13px;
    opacity: 1;
    bottom: unset;
    transition-duration: 0.3s;
  }

  @media (max-width: 768px) {
    bottom: 1rem;
    right: 1rem;
  }
}
</style>

