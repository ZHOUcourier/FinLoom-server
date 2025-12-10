<template>
  <v-container fluid class="create-strategy-view pa-6">
    <v-card rounded="xl">
      <!-- 头部 -->
      <v-card-title class="pa-6">
        <div class="d-flex align-center">
          <v-icon start color="primary" size="32">mdi-creation</v-icon>
          <div>
            <div class="text-h4 font-weight-bold">创建投资策略</div>
            <div class="text-subtitle-1 text-medium-emphasis">
              使用AI生成个性化量化投资策略
            </div>
          </div>
        </div>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <!-- 步骤指示器 -->
      <v-card-text class="pa-6">
        <v-stepper v-model="currentStep" alt-labels flat>
          <v-stepper-header>
            <v-stepper-item value="1" title="需求分析" :complete="parseInt(currentStep) > 1" color="primary"></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item value="2" title="策略生成" :complete="parseInt(currentStep) > 2" color="primary"></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item value="3" title="参数优化" :complete="parseInt(currentStep) > 3" color="primary"></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item value="4" title="完成" color="primary"></v-stepper-item>
          </v-stepper-header>
        </v-stepper>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <!-- 步骤内容 -->
      <v-window v-model="currentStep">
        <!-- 步骤1: 需求分析 -->
        <v-window-item value="1">
          <v-card-text class="pa-6">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.strategyName"
                  label="策略名称"
                  placeholder="例如: 稳健型价值投资策略"
                  variant="outlined"
                  rounded="lg"
                  prepend-inner-icon="mdi-label-outline"
                  class="mb-4"
                ></v-text-field>
                
                <v-textarea
                  v-model="form.description"
                  label="策略描述"
                  placeholder="描述您的投资需求和期望..."
                  variant="outlined"
                  rounded="lg"
                  rows="4"
                  prepend-inner-icon="mdi-text"
                ></v-textarea>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-select
                  v-model="form.strategyType"
                  :items="strategyTypes"
                  label="策略类型"
                  variant="outlined"
                  rounded="lg"
                  prepend-inner-icon="mdi-format-list-bulleted-type"
                  class="mb-4"
                ></v-select>
                
                <v-select
                  v-model="form.riskLevel"
                  :items="riskLevels"
                  label="风险偏好"
                  variant="outlined"
                  rounded="lg"
                  prepend-inner-icon="mdi-shield-check"
                  class="mb-4"
                ></v-select>
                
                <v-text-field
                  v-model.number="form.targetReturn"
                  label="目标年化收益率 (%)"
                  type="number"
                  variant="outlined"
                  rounded="lg"
                  prepend-inner-icon="mdi-trending-up"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-card-text>
          
          <v-card-actions class="pa-6">
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              size="large"
              prepend-icon="mdi-arrow-right"
              rounded="pill"
              variant="flat"
              :disabled="!isStep1Valid"
              @click="generateStrategy"
            >
              生成策略
            </v-btn>
          </v-card-actions>
        </v-window-item>
        
        <!-- 步骤2: 策略生成 -->
        <v-window-item value="2">
          <v-card-text class="pa-10">
            <div v-if="generating" class="text-center">
              <v-progress-circular indeterminate color="primary" size="64" width="6"></v-progress-circular>
              <div class="text-h5 mt-6">AI正在生成策略...</div>
              <div class="text-body-1 text-medium-emphasis mt-2">{{ generatingStatus }}</div>
            </div>
            
            <div v-else-if="generatedStrategy">
              <v-alert type="success" variant="tonal" rounded="lg" class="mb-6">
                <template v-slot:prepend>
                  <v-icon size="32">mdi-check-circle</v-icon>
                </template>
                <div class="text-h6 mb-2">策略生成成功!</div>
                <div>已为您生成个性化投资策略</div>
              </v-alert>
              
              <v-card variant="outlined" rounded="lg" class="mb-4">
                <v-card-title class="pa-4">
                  <v-icon start color="primary">mdi-file-document-outline</v-icon>
                  {{ generatedStrategy.name }}
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-4">
                  <div class="mb-4">
                    <div class="text-subtitle-2 mb-2">策略类型</div>
                    <v-chip color="primary" variant="tonal">{{ generatedStrategy.type }}</v-chip>
                  </div>
                  
                  <div class="mb-4">
                    <div class="text-subtitle-2 mb-2">风险等级</div>
                    <v-chip :color="getRiskColor(generatedStrategy.risk_level)" variant="tonal">
                      {{ generatedStrategy.risk_level }}
                    </v-chip>
                  </div>
                  
                  <div>
                    <div class="text-subtitle-2 mb-2">策略参数</div>
                    <pre class="pa-4 rounded" style="background: rgba(var(--v-theme-surface-variant), 0.5)">{{ JSON.stringify(generatedStrategy.parameters, null, 2) }}</pre>
                  </div>
                </v-card-text>
              </v-card>
            </div>
          </v-card-text>
          
          <v-card-actions class="pa-6">
            <v-btn variant="text" @click="currentStep = '1'" rounded="pill">上一步</v-btn>
            <v-spacer></v-spacer>
            <v-btn
              v-if="generatedStrategy"
              color="primary"
              size="large"
              prepend-icon="mdi-arrow-right"
              rounded="pill"
              variant="flat"
              @click="currentStep = '3'"
            >
              继续优化
            </v-btn>
          </v-card-actions>
        </v-window-item>
        
        <!-- 步骤3: 参数优化 -->
        <v-window-item value="3">
          <v-card-text class="pa-6">
            <v-alert type="info" variant="tonal" rounded="lg" class="mb-6">
              <div class="text-body-1">
                <v-icon start>mdi-information</v-icon>
                参数优化可以提高策略性能，但需要较长时间
              </div>
            </v-alert>
            
            <v-btn
              color="secondary"
              size="large"
              prepend-icon="mdi-tune-variant"
              rounded="pill"
              variant="flat"
              :loading="optimizing"
              @click="optimizeStrategy"
            >
              开始优化
            </v-btn>
          </v-card-text>
          
          <v-card-actions class="pa-6">
            <v-btn variant="text" @click="currentStep = '2'" rounded="pill">上一步</v-btn>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              size="large"
              prepend-icon="mdi-check"
              rounded="pill"
              variant="flat"
              @click="saveStrategy"
            >
              保存策略
            </v-btn>
          </v-card-actions>
        </v-window-item>
        
        <!-- 步骤4: 完成 -->
        <v-window-item value="4">
          <v-card-text class="pa-10 text-center">
            <v-icon size="96" color="success" class="mb-6">mdi-check-circle-outline</v-icon>
            <div class="text-h4 mb-4">策略创建成功!</div>
            <div class="text-body-1 text-medium-emphasis mb-6">
              您的策略已保存到策略库
            </div>
            
            <div class="d-flex justify-center gap-4">
              <v-btn
                color="primary"
                prepend-icon="mdi-view-list"
                rounded="pill"
                variant="flat"
                size="large"
                @click="$router.push('/dashboard/strategy/library')"
              >
                查看策略库
              </v-btn>
              
              <v-btn
                color="secondary"
                prepend-icon="mdi-plus"
                rounded="pill"
                variant="outlined"
                size="large"
                @click="resetForm"
              >
                创建新策略
              </v-btn>
            </div>
          </v-card-text>
        </v-window-item>
      </v-window>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '@/services'

const currentStep = ref('1')
const generating = ref(false)
const generatingStatus = ref('分析需求中...')
const optimizing = ref(false)
const generatedStrategy = ref(null)

const form = ref({
  strategyName: '',
  description: '',
  strategyType: 'value',
  riskLevel: 'moderate',
  targetReturn: 15
})

const strategyTypes = [
  { title: '价值投资', value: 'value' },
  { title: '成长投资', value: 'growth' },
  { title: '动量策略', value: 'momentum' },
  { title: '均值回归', value: 'mean_reversion' }
]

const riskLevels = [
  { title: '保守型', value: 'conservative' },
  { title: '稳健型', value: 'moderate' },
  { title: '激进型', value: 'aggressive' }
]

const isStep1Valid = computed(() => {
  return form.value.strategyName.trim() && form.value.description.trim()
})

async function generateStrategy() {
  generating.value = true
  currentStep.value = '2'
  
  try {
    generatingStatus.value = '分析投资需求...'
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    generatingStatus.value = '生成策略参数...'
    const response = await api.strategy.generate({
      name: form.value.strategyName,
      description: form.value.description,
      strategy_type: form.value.strategyType,
      risk_level: form.value.riskLevel,
      target_return: form.value.targetReturn
    })
    
    generatingStatus.value = '完成'
    generatedStrategy.value = response.data.strategy
  } catch (error) {
    console.error('生成策略失败:', error)
  } finally {
    generating.value = false
  }
}

async function optimizeStrategy() {
  optimizing.value = true
  
  try {
    await api.strategy.optimize(generatedStrategy.value.parameters)
    // 更新优化后的参数
  } catch (error) {
    console.error('优化失败:', error)
  } finally {
    optimizing.value = false
  }
}

async function saveStrategy() {
  try {
    await api.strategy.save(generatedStrategy.value)
    currentStep.value = '4'
  } catch (error) {
    console.error('保存策略失败:', error)
  }
}

function resetForm() {
  form.value = {
    strategyName: '',
    description: '',
    strategyType: 'value',
    riskLevel: 'moderate',
    targetReturn: 15
  }
  generatedStrategy.value = null
  currentStep.value = '1'
}

function getRiskColor(level) {
  const colors = {
    conservative: 'success',
    moderate: 'warning',
    aggressive: 'error'
  }
  return colors[level] || 'default'
}
</script>

<style lang="scss" scoped>
.create-strategy-view {
  max-width: 1200px;
  margin: 0 auto;
}
</style>







