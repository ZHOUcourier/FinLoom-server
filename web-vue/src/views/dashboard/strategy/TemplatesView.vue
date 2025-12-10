<template>
  <v-container fluid class="templates-view pa-6">
    <v-card rounded="xl">
      <!-- 头部 -->
      <v-card-title class="pa-6">
        <div class="d-flex align-center">
          <v-icon start color="secondary" size="32">mdi-view-module-outline</v-icon>
          <div>
            <div class="text-h4 font-weight-bold">策略模板</div>
            <div class="text-subtitle-1 text-medium-emphasis">
              从预定义模板快速创建策略
            </div>
          </div>
        </div>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <!-- 模板列表 -->
      <v-card-text class="pa-6">
        <v-row v-if="!loading && templates.length > 0">
          <v-col
            v-for="template in templates"
            :key="template.id"
            cols="12"
            md="6"
            lg="4"
          >
            <v-card
              variant="outlined"
              rounded="xl"
              class="template-card h-100"
            >
              <v-card-text class="pa-6">
                <div class="d-flex justify-space-between align-start mb-3">
                  <v-avatar
                    :color="getCategoryColor(template.category)"
                    size="48"
                    rounded="lg"
                  >
                    <v-icon color="white" size="28">{{ getCategoryIcon(template.category) }}</v-icon>
                  </v-avatar>
                  
                  <v-chip
                    size="small"
                    :color="getRiskColor(template.risk_level)"
                    variant="tonal"
                    rounded="lg"
                  >
                    {{ getRiskLabel(template.risk_level) }}
                  </v-chip>
                </div>
                
                <div class="text-h5 font-weight-bold mb-2">
                  {{ template.name }}
                </div>
                
                <div class="text-body-2 text-medium-emphasis mb-4" style="min-height: 48px">
                  {{ template.description }}
                </div>
                
                <v-divider class="my-4"></v-divider>
                
                <!-- 特征标签 -->
                <div class="mb-4">
                  <v-chip
                    v-for="(value, key) in getTemplateFeatures(template)"
                    :key="key"
                    size="small"
                    variant="text"
                    class="mr-2 mb-2"
                  >
                    <v-icon start size="16">{{ getFeatureIcon(key) }}</v-icon>
                    {{ value }}
                  </v-chip>
                </div>
                
                <!-- 预期表现 -->
                <v-row dense class="mb-3">
                  <v-col cols="6">
                    <div class="text-caption text-medium-emphasis">预期收益</div>
                    <div class="text-subtitle-1 font-weight-medium text-success">
                      {{ template.expected_return }}
                    </div>
                  </v-col>
                  <v-col cols="6">
                    <div class="text-caption text-medium-emphasis">适用场景</div>
                    <div class="text-subtitle-1 font-weight-medium">
                      {{ template.suitable_for }}
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
              
              <v-divider></v-divider>
              
              <v-card-actions class="pa-4">
                <v-btn
                  variant="text"
                  color="primary"
                  rounded="lg"
                  prepend-icon="mdi-information-outline"
                  @click="viewTemplateDetails(template)"
                >
                  查看详情
                </v-btn>
                <v-spacer></v-spacer>
                <v-btn
                  variant="flat"
                  color="primary"
                  rounded="lg"
                  prepend-icon="mdi-plus"
                  @click="useTemplate(template)"
                >
                  使用模板
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
          <div class="text-h6 mt-4">加载模板中...</div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="!loading && templates.length === 0" class="text-center py-12">
          <v-avatar color="surface-variant" size="96" class="mb-4">
            <v-icon size="48" color="medium-emphasis">mdi-view-module-outline</v-icon>
          </v-avatar>
          <div class="text-h5 mb-2">暂无模板</div>
        </div>
      </v-card-text>
    </v-card>
    
    <!-- 模板详情对话框 -->
    <v-dialog v-model="detailsDialog" max-width="900">
      <v-card v-if="selectedTemplate" rounded="xl">
        <v-card-title class="pa-6 d-flex align-center">
          <v-avatar
            :color="getCategoryColor(selectedTemplate.category)"
            size="40"
            rounded="lg"
            class="mr-3"
          >
            <v-icon color="white">{{ getCategoryIcon(selectedTemplate.category) }}</v-icon>
          </v-avatar>
          <div>
            <div class="text-h5">{{ selectedTemplate.name }}</div>
            <div class="text-subtitle-2 text-medium-emphasis">{{ selectedTemplate.category }}</div>
          </div>
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="pa-6">
          <!-- 描述 -->
          <div class="mb-6">
            <div class="text-h6 mb-2">策略描述</div>
            <div class="text-body-1">{{ selectedTemplate.description }}</div>
          </div>
          
          <!-- 参数配置 -->
          <div class="mb-6">
            <div class="text-h6 mb-3">参数配置</div>
            <v-row>
              <v-col
                v-for="param in selectedTemplate.parameters"
                :key="param.name"
                cols="12"
                md="6"
              >
                <v-card variant="tonal">
                  <v-card-text>
                    <div class="text-subtitle-2 mb-1">{{ param.name }}</div>
                    <div class="text-caption text-medium-emphasis">
                      类型: {{ param.param_type }} | 
                      范围: {{ param.low }} - {{ param.high }}
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
          
          <!-- 回测结果 -->
          <div v-if="selectedTemplateBacktest">
            <div class="text-h6 mb-3">历史回测表现</div>
            <v-row dense>
              <v-col cols="4">
                <v-card variant="tonal" color="success">
                  <v-card-text class="text-center">
                    <div class="text-caption">年化收益</div>
                    <div class="text-h5 font-weight-bold">
                      {{ selectedTemplateBacktest.annual_return }}%
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="4">
                <v-card variant="tonal" color="info">
                  <v-card-text class="text-center">
                    <div class="text-caption">夏普比率</div>
                    <div class="text-h5 font-weight-bold">
                      {{ selectedTemplateBacktest.sharpe_ratio }}
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="4">
                <v-card variant="tonal" color="warning">
                  <v-card-text class="text-center">
                    <div class="text-caption">最大回撤</div>
                    <div class="text-h5 font-weight-bold">
                      {{ selectedTemplateBacktest.max_drawdown }}%
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <v-card-actions class="pa-6">
          <v-btn variant="text" @click="detailsDialog = false" rounded="pill">关闭</v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            rounded="pill"
            variant="flat"
            @click="useTemplate(selectedTemplate)"
          >
            使用此模板
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 自定义参数对话框 -->
    <v-dialog v-model="customizeDialog" max-width="600">
      <v-card rounded="xl">
        <v-card-title class="pa-6">
          <v-icon start>mdi-tune-variant</v-icon>
          自定义策略参数
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-text-field
            v-model="customStrategyName"
            label="策略名称"
            variant="outlined"
            rounded="lg"
            class="mb-4"
          ></v-text-field>
          
          <div class="text-body-2 text-medium-emphasis mb-2">
            您可以使用默认参数,或在创建后进行调整
          </div>
        </v-card-text>
        <v-card-actions class="pa-6 pt-0">
          <v-btn variant="text" @click="customizeDialog = false" rounded="pill">取消</v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            rounded="pill"
            variant="flat"
            :loading="creating"
            @click="createFromTemplate"
          >
            创建策略
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services'

const router = useRouter()
const templates = ref([])
const loading = ref(false)
const detailsDialog = ref(false)
const customizeDialog = ref(false)
const selectedTemplate = ref(null)
const selectedTemplateBacktest = ref(null)
const customStrategyName = ref('')
const creating = ref(false)

onMounted(async () => {
  await loadTemplates()
})

async function loadTemplates() {
  loading.value = true
  try {
    const response = await api.strategy.templates.list()
    templates.value = response.data.templates || []
  } catch (error) {
    console.error('加载模板失败:', error)
  } finally {
    loading.value = false
  }
}

async function viewTemplateDetails(template) {
  selectedTemplate.value = template
  
  try {
    const response = await api.strategy.templates.get(template.id)
    selectedTemplateBacktest.value = response.data.backtesting_results
  } catch (error) {
    console.error('获取模板详情失败:', error)
  }
  
  detailsDialog.value = true
}

function useTemplate(template) {
  selectedTemplate.value = template
  customStrategyName.value = `我的${template.name}`
  customizeDialog.value = true
  detailsDialog.value = false
}

async function createFromTemplate() {
  creating.value = true
  
  try {
    const response = await api.strategy.templates.createFrom(
      selectedTemplate.value.id,
      customStrategyName.value
    )
    
    customizeDialog.value = false
    
    // 跳转到策略库
    router.push({
      name: 'dashboard-strategy-library',
      query: { created: response.data.id }
    })
  } catch (error) {
    console.error('创建策略失败:', error)
  } finally {
    creating.value = false
  }
}

function getCategoryColor(category) {
  const colors = {
    '趋势跟踪': 'primary',
    '均值回归': 'success',
    '波动率交易': 'warning',
    '动量交易': 'error'
  }
  return colors[category] || 'secondary'
}

function getCategoryIcon(category) {
  const icons = {
    '趋势跟踪': 'mdi-trending-up',
    '均值回归': 'mdi-chart-bell-curve',
    '波动率交易': 'mdi-chart-areaspline',
    '动量交易': 'mdi-rocket-launch'
  }
  return icons[category] || 'mdi-chart-line'
}

function getRiskColor(level) {
  const colors = {
    conservative: 'success',
    moderate: 'warning',
    aggressive: 'error'
  }
  return colors[level] || 'default'
}

function getRiskLabel(level) {
  const labels = {
    conservative: '保守型',
    moderate: '稳健型',
    aggressive: '激进型'
  }
  return labels[level] || level
}

function getTemplateFeatures(template) {
  return {
    category: template.category,
    suitable: template.suitable_for
  }
}

function getFeatureIcon(key) {
  const icons = {
    category: 'mdi-tag',
    suitable: 'mdi-check-circle'
  }
  return icons[key] || 'mdi-information'
}
</script>

<style lang="scss" scoped>
.templates-view {
  max-width: 1600px;
  margin: 0 auto;
}

.template-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(var(--v-theme-secondary), 0.15);
  }
}
</style>







