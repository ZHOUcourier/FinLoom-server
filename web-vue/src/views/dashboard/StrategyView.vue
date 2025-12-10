<template>
  <!-- 子路由视图 -->
  <router-view v-if="$route.path !== '/dashboard/strategy'" />
  
  <!-- 主策略界面 -->
  <v-container v-else fluid class="strategy-view pa-6">
    <!-- 进度条 -->
    <v-card class="mb-6" rounded="xl">
      <v-card-text class="pa-6 d-flex align-center justify-space-between">
        <v-stepper v-model="currentStep" alt-labels flat class="flex-grow-1">
          <v-stepper-header>
            <v-stepper-item 
              value="1" 
              title="需求分析"
              :complete="parseInt(currentStep) > 1"
              color="primary"
            ></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item 
              value="2" 
              title="策略生成"
              :complete="parseInt(currentStep) > 2"
              color="primary"
            ></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item 
              value="3" 
              title="回测优化"
              :complete="parseInt(currentStep) > 3"
              color="primary"
            ></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item 
              value="4" 
              title="策略保存"
              color="primary"
            ></v-stepper-item>
          </v-stepper-header>
        </v-stepper>
        
        <!-- 重新创建按钮 -->
        <v-btn
          v-if="parseInt(currentStep) > 1"
          color="secondary"
          variant="outlined"
          prepend-icon="mdi-refresh"
          rounded="pill"
          @click="resetWorkflow"
          class="ml-4"
        >
          重新创建策略
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- 步骤内容 -->
    <v-window v-model="currentStep">
      <!-- 步骤1: 需求分析 -->
      <v-window-item value="1">
        <v-card rounded="xl">
          <v-card-title class="text-h5 font-weight-medium pa-6">
            <v-icon start>mdi-chart-line</v-icon>
            投资需求分析
          </v-card-title>
          <v-card-subtitle class="px-6 pb-4">请告诉我们您的投资目标和偏好</v-card-subtitle>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <v-sheet rounded="lg" class="pa-4 mb-4" color="primary-container" style="background-color: rgba(30, 136, 229, 0.06) !important;">
                  <div class="d-flex align-center mb-4">
                    <v-icon size="24" class="mr-3 text-primary">mdi-target</v-icon>
                    <h3 class="text-h6 font-weight-medium">投资目标</h3>
                  </div>
                  <v-text-field
                    v-model.number="form.targetReturn"
                    label="收益目标 (%/年)"
                    type="number"
                    prepend-inner-icon="mdi-percent"
                    class="mb-4"
                    variant="filled"
                    density="comfortable"
                    rounded="lg"
                  ></v-text-field>
                  <v-select
                    v-model="form.investmentPeriod"
                    :items="[
                      { title: '短期 (1-3个月)', value: 'short' },
                      { title: '中期 (3-12个月)', value: 'medium' },
                      { title: '长期 (1年以上)', value: 'long' }
                    ]"
                    label="投资期限"
                    prepend-inner-icon="mdi-calendar"
                    class="mb-4"
                    variant="filled"
                    density="comfortable"
                    rounded="lg"
                  ></v-select>
                  <v-text-field
                    v-model.number="form.initialCapital"
                    label="初始资金 (万元)"
                    type="number"
                    prepend-inner-icon="mdi-currency-usd"
                    variant="filled"
                    density="comfortable"
                    rounded="lg"
                  ></v-text-field>
                </v-sheet>
              </v-col>

              <v-col cols="12" md="6">
                <v-sheet rounded="lg" class="pa-4 mb-4" color="secondary-container" style="background-color: rgba(0, 172, 193, 0.06) !important;">
                  <div class="d-flex align-center mb-4">
                    <v-icon size="24" class="mr-3 text-secondary">mdi-shield-check</v-icon>
                    <h3 class="text-h6 font-weight-medium">风险偏好</h3>
                  </div>
                  <v-chip-group
                    v-model="form.riskPreference"
                    mandatory
                    class="mb-4"
                  >
                    <v-chip 
                      value="conservative" 
                      :variant="form.riskPreference === 'conservative' ? 'elevated' : 'outlined'" 
                      :color="form.riskPreference === 'conservative' ? 'success' : undefined"
                      size="large" 
                      class="font-weight-medium"
                      rounded="lg"
                    >
                      <v-icon start>mdi-shield</v-icon>
                      保守型
                    </v-chip>
                    <v-chip 
                      value="moderate" 
                      :variant="form.riskPreference === 'moderate' ? 'elevated' : 'outlined'" 
                      :color="form.riskPreference === 'moderate' ? 'primary' : undefined"
                      size="large" 
                      class="font-weight-medium"
                      rounded="lg"
                    >
                      <v-icon start>mdi-scale-balance</v-icon>
                      稳健型
                    </v-chip>
                    <v-chip 
                      value="aggressive" 
                      :variant="form.riskPreference === 'aggressive' ? 'elevated' : 'outlined'" 
                      :color="form.riskPreference === 'aggressive' ? 'error' : undefined"
                      size="large" 
                      class="font-weight-medium"
                      rounded="lg"
                    >
                      <v-icon start>mdi-rocket-launch</v-icon>
                      进取型
                    </v-chip>
                  </v-chip-group>
                  <v-text-field
                    v-model.number="form.maxDrawdown"
                    label="最大回撤容忍度 (%)"
                    type="number"
                    prepend-inner-icon="mdi-arrow-down"
                    variant="filled"
                    density="comfortable"
                    rounded="lg"
                  ></v-text-field>
                </v-sheet>
              </v-col>

              <v-col cols="12" md="6">
                <v-sheet rounded="lg" class="pa-4 mb-4" color="tertiary-container" style="background-color: rgba(123, 97, 255, 0.06) !important;">
                  <div class="d-flex align-center mb-4">
                    <v-icon size="24" class="mr-3 text-tertiary">mdi-tag-multiple</v-icon>
                    <h3 class="text-h6 font-weight-medium">偏好行业</h3>
                  </div>
                  <v-chip-group v-model="form.preferredTags" multiple column>
                    <v-chip 
                      v-for="tag in allTags" 
                      :key="tag" 
                      :value="tag" 
                      variant="outlined"
                      color="tertiary"
                      size="large"
                      rounded="lg"
                    >
                      {{ tag }}
                    </v-chip>
                  </v-chip-group>
                </v-sheet>
              </v-col>

              <v-col cols="12" md="6">
                <v-sheet rounded="lg" class="pa-4 mb-4" color="success-container" style="background-color: rgba(0, 168, 107, 0.08) !important;">
                  <div class="d-flex align-center mb-4">
                    <v-icon size="24" class="mr-3 text-success">mdi-cog</v-icon>
                    <h3 class="text-h6 font-weight-medium">策略偏好</h3>
                  </div>
                  <v-select
                    v-model="form.strategyType"
                    :items="[
                      { title: '价值投资', value: 'value' },
                      { title: '成长投资', value: 'growth' },
                      { title: '动量策略', value: 'momentum' },
                      { title: '均值回归', value: 'mean_reversion' }
                    ]"
                    label="策略类型"
                    prepend-inner-icon="mdi-strategy"
                    class="mb-4"
                    variant="filled"
                    density="comfortable"
                    rounded="lg"
                  ></v-select>
                  <v-select
                    v-model="form.tradingFrequency"
                    :items="[
                      { title: '日内交易', value: 'daily' },
                      { title: '周级调仓', value: 'weekly' },
                      { title: '月度调仓', value: 'monthly' }
                    ]"
                    label="交易频率"
                    prepend-inner-icon="mdi-clock-outline"
                    variant="filled"
                    density="comfortable"
                    rounded="lg"
                  ></v-select>
                </v-sheet>
              </v-col>

              <v-col cols="12">
                <v-sheet rounded="lg" class="pa-4" color="warning-container" style="background-color: rgba(255, 152, 0, 0.06) !important;">
                  <div class="d-flex align-center mb-4">
                    <v-icon size="24" class="mr-3 text-warning">mdi-comment-text</v-icon>
                    <div>
                      <h3 class="text-h6 font-weight-medium">补充需求说明</h3>
                      <p class="text-caption text-medium-emphasis mb-0">提供更详细的需求可以帮助AI生成更符合您期望的策略</p>
                    </div>
                  </div>
                  <v-textarea
                    v-model="form.additionalRequirements"
                    label="其他特殊需求（可选）"
                    rows="4"
                    placeholder="例如：希望避开某些行业、关注特定市场事件、特殊的止损要求等..."
                    variant="filled"
                    density="comfortable"
                    rounded="lg"
                  ></v-textarea>
                </v-sheet>
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="px-6 pb-6">
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              size="large"
              @click="nextStep"
              prepend-icon="mdi-arrow-right"
              rounded="pill"
              variant="flat"
              :loading="isGenerating"
              :disabled="isGenerating"
            >
              下一步：生成策略
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-window-item>

      <!-- 步骤2: 策略生成 -->
      <v-window-item value="2">
        <v-card rounded="xl">
          <v-card-title class="text-h5 font-weight-medium pa-6">
            <v-icon start>mdi-brain</v-icon>
            AI策略生成
          </v-card-title>
          <v-card-subtitle class="px-6 pb-4">基于您的需求，我们正在为您生成个性化投资策略</v-card-subtitle>
          <v-card-text class="pa-10">
            <div v-if="!showResult">
              <v-sheet rounded="lg" class="pa-8 text-center" color="primary-container" style="background-color: rgba(30, 136, 229, 0.08) !important;">
                <v-icon size="64" class="mb-6 text-primary">mdi-brain</v-icon>
                <h3 class="text-h4 mb-4 font-weight-medium">AI正在分析您的需求...</h3>
                <v-progress-linear
                  v-model="generationProgress"
                  height="8"
                  color="primary"
                  rounded
                  class="mb-6"
                >
                  <strong class="text-primary">{{ generationProgress }}%</strong>
                </v-progress-linear>
                <v-chip v-if="!errorMessage" color="primary" size="large" variant="outlined" rounded="lg">
                  <v-icon start>mdi-cog</v-icon>
                  {{ statusText }}
                </v-chip>
                <v-alert
                  v-else
                  type="error"
                  variant="tonal"
                  border="start"
                  rounded="lg"
                  class="mt-6 text-left"
                >
                  <template v-slot:prepend>
                    <v-icon size="28">mdi-alert-circle</v-icon>
                  </template>
                  <div class="text-h6 font-weight-medium mb-2">策略生成失败</div>
                  <div class="mb-4">{{ errorMessage }}</div>
                  <v-btn
                    color="error"
                    variant="flat"
                    rounded="pill"
                    prepend-icon="mdi-refresh"
                    @click="retryGeneration"
                    :loading="isGenerating"
                  >
                    重新尝试
                  </v-btn>
                </v-alert>
              </v-sheet>
            </div>

            <div v-else>
              <v-alert 
                type="success" 
                variant="tonal" 
                border="start"
                class="mb-6"
                rounded="lg"
              >
                <template v-slot:prepend>
                  <v-icon size="32">mdi-check-circle</v-icon>
                </template>
                <div class="text-h6 font-weight-medium mb-2">策略生成成功！</div>
                <div>您的个性化投资策略已经准备就绪</div>
              </v-alert>
              
              <!-- 策略概览 -->
              <v-sheet rounded="lg" color="secondary-container" class="mb-6" style="background-color: rgba(0, 172, 193, 0.08) !important;">
                <v-card-title class="text-h5 pa-6 d-flex align-center">
                  <v-icon size="24" class="mr-3 text-secondary">mdi-strategy</v-icon>
                  {{ result.title }}
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-6">
                  <p class="text-body-1 mb-4">{{ result.description }}</p>
                  
                  <!-- 股票池 -->
                  <div v-if="result.recommendedStocks && result.recommendedStocks.length > 0" class="mb-4">
                    <h4 class="text-h6 mb-3 d-flex align-center">
                      <v-icon class="mr-2" color="primary">mdi-chart-box</v-icon>
                      入选股票池
                    </h4>
                    <v-chip-group>
                      <v-chip v-for="stock in result.recommendedStocks" :key="stock" color="primary" variant="outlined" size="large">
                        {{ stock }}
                      </v-chip>
                    </v-chip-group>
                  </div>

                  <!-- 策略参数 -->
                  <div v-if="result.strategyParams" class="mb-4">
                    <h4 class="text-h6 mb-3 d-flex align-center">
                      <v-icon class="mr-2" color="secondary">mdi-tune</v-icon>
                      策略参数
                    </h4>
                    <v-row>
                      <v-col cols="12" md="6">
                        <v-list density="compact" bg-color="transparent">
                          <v-list-item v-for="(value, key) in getFirstHalfParams(result.strategyParams)" :key="key">
                            <template v-slot:prepend>
                              <v-icon size="20" class="mr-2">mdi-circle-small</v-icon>
                            </template>
                            <v-list-item-title class="text-body-2">{{ formatParamKey(key) }}</v-list-item-title>
                            <v-list-item-subtitle class="font-weight-medium">{{ formatParamValue(key, value) }}</v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-col>
                      <v-col cols="12" md="6">
                        <v-list density="compact" bg-color="transparent">
                          <v-list-item v-for="(value, key) in getSecondHalfParams(result.strategyParams)" :key="key">
                            <template v-slot:prepend>
                              <v-icon size="20" class="mr-2">mdi-circle-small</v-icon>
                            </template>
                            <v-list-item-title class="text-body-2">{{ formatParamKey(key) }}</v-list-item-title>
                            <v-list-item-subtitle class="font-weight-medium">{{ formatParamValue(key, value) }}</v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-col>
                    </v-row>
                  </div>

                  <!-- 模型信息 -->
                  <div v-if="result.model && result.model.modelType" class="mb-4">
                    <h4 class="text-h6 mb-3 d-flex align-center">
                      <v-icon class="mr-2" color="success">mdi-brain</v-icon>
                      AI模型信息
                    </h4>
                    <v-chip color="success" variant="tonal" size="large" class="mr-2">
                      <v-icon start>mdi-robot</v-icon>
                      {{ result.model.modelType.toUpperCase() }}
                    </v-chip>
                    <v-chip v-if="result.model.reason" color="info" variant="text" size="small">
                      {{ result.model.reason }}
                    </v-chip>
                  </div>
                </v-card-text>
              </v-sheet>
              
              <!-- 策略代码 -->
              <v-sheet v-if="result.strategyCode" rounded="lg" color="success-container" style="background-color: rgba(0, 168, 107, 0.08) !important;">
                <v-card-title class="text-h5 pa-6 d-flex align-center">
                  <v-icon size="24" class="mr-3 text-success">mdi-code-braces</v-icon>
                  策略代码 - {{ result.strategyCode.name }}
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-6">
                  <v-expansion-panels variant="accordion">
                    <v-expansion-panel>
                      <v-expansion-panel-title>
                        <v-icon start>mdi-information</v-icon>
                        策略说明
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <pre class="text-body-2" style="white-space: pre-wrap; word-wrap: break-word;">{{ result.strategyCode.code }}</pre>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                    
                    <v-expansion-panel>
                      <v-expansion-panel-title>
                        <v-icon start>mdi-cog</v-icon>
                        策略参数
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <v-list density="compact">
                          <v-list-item v-for="(value, key) in result.strategyCode.parameters" :key="key">
                            <v-list-item-title>{{ key }}</v-list-item-title>
                            <v-list-item-subtitle>{{ value }}</v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                  
                  <v-alert type="info" variant="tonal" class="mt-4" rounded="lg">
                    <div class="text-body-2">
                      <strong>策略版本:</strong> {{ result.strategyCode.version }}<br>
                      <strong>生成时间:</strong> {{ new Date(result.strategyCode.createdAt).toLocaleString('zh-CN') }}<br>
                      <strong>策略描述:</strong> {{ result.strategyCode.description }}
                    </div>
                  </v-alert>
                </v-card-text>
              </v-sheet>
            </div>
          </v-card-text>
          <v-card-actions class="px-6 pb-6">
            <v-btn variant="text" @click="prevStep" prepend-icon="mdi-arrow-left" rounded="pill">
              上一步
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn v-if="showResult" color="primary" size="large" @click="nextStep" prepend-icon="mdi-arrow-right" rounded="pill" variant="flat">
              下一步：回测优化
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-window-item>

      <!-- 步骤3: 回测优化 -->
      <v-window-item value="3">
        <v-card rounded="xl">
          <v-card-title class="text-h5 font-weight-medium pa-6">
            <v-icon start>mdi-chart-timeline-variant</v-icon>
            回测结果
          </v-card-title>
          <v-card-subtitle class="px-6 pb-4">历史数据回测表现分析</v-card-subtitle>
          <v-card-text class="pa-6">
            <!-- 回测进度条 -->
            <div v-if="isBacktesting" class="mb-6">
              <v-progress-linear
                :model-value="backtestProgress"
                color="secondary"
                height="8"
                rounded
                striped
              ></v-progress-linear>
              <div class="text-center text-caption text-grey mt-2">
                <v-icon size="16" class="mr-1">mdi-chart-timeline-variant</v-icon>
                正在回测中... {{ backtestProgress }}%
              </div>
            </div>

            <!-- 回测错误提示 -->
            <v-alert
              v-if="backtestError"
              type="warning"
              variant="tonal"
              class="mb-6"
              closable
              @click:close="backtestError = ''"
            >
              <div class="text-body-2" style="white-space: pre-line;">{{ backtestError }}</div>
            </v-alert>

            <!-- 回测结果展示 -->
            <div v-if="!isBacktesting && result.backtest && Object.keys(result.backtest).length > 0">
              <v-row>
                <!-- 总收益率 -->
                <v-col cols="12" md="3">
                  <v-card variant="outlined" rounded="lg" class="pa-4 text-center">
                    <v-icon size="40" class="mb-3" :color="result.backtest.totalReturn > 0 ? 'success' : 'error'">
                      mdi-chart-line
                    </v-icon>
                    <div class="text-caption text-grey">总收益率</div>
                    <div class="text-h5 font-weight-bold mt-2" :class="result.backtest.totalReturn > 0 ? 'text-success' : 'text-error'">
                      {{ result.backtest.totalReturn ? (result.backtest.totalReturn * 100).toFixed(2) : '0.00' }}%
                    </div>
                  </v-card>
                </v-col>

                <!-- 年化收益率 -->
                <v-col cols="12" md="3">
                  <v-card variant="outlined" rounded="lg" class="pa-4 text-center">
                    <v-icon size="40" class="mb-3" :color="result.backtest.annualizedReturn > 0 ? 'success' : 'error'">
                      mdi-calendar-check
                    </v-icon>
                    <div class="text-caption text-grey">年化收益率</div>
                    <div class="text-h5 font-weight-bold mt-2" :class="result.backtest.annualizedReturn > 0 ? 'text-success' : 'text-error'">
                      {{ result.backtest.annualizedReturn ? (result.backtest.annualizedReturn * 100).toFixed(2) : '0.00' }}%
                    </div>
                  </v-card>
                </v-col>

                <!-- 夏普比率 -->
                <v-col cols="12" md="3">
                  <v-card variant="outlined" rounded="lg" class="pa-4 text-center">
                    <v-icon size="40" class="mb-3" color="primary">
                      mdi-shield-check
                    </v-icon>
                    <div class="text-caption text-grey">夏普比率</div>
                    <div class="text-h5 font-weight-bold mt-2 text-primary">
                      {{ result.backtest.sharpeRatio ? result.backtest.sharpeRatio.toFixed(3) : '0.000' }}
                    </div>
                  </v-card>
                </v-col>

                <!-- 最大回撤 -->
                <v-col cols="12" md="3">
                  <v-card variant="outlined" rounded="lg" class="pa-4 text-center">
                    <v-icon size="40" class="mb-3" color="warning">
                      mdi-arrow-down-bold
                    </v-icon>
                    <div class="text-caption text-grey">最大回撤</div>
                    <div class="text-h5 font-weight-bold mt-2 text-warning">
                      {{ result.backtest.maxDrawdown ? (result.backtest.maxDrawdown * 100).toFixed(2) : '0.00' }}%
                    </div>
                  </v-card>
                </v-col>
              </v-row>

              <!-- 其他指标 -->
              <v-row class="mt-4">
                <v-col cols="12" md="4">
                  <v-card variant="tonal" rounded="lg" class="pa-4">
                    <div class="d-flex align-center justify-space-between">
                      <div>
                        <div class="text-caption text-grey">交易次数</div>
                        <div class="text-h6 font-weight-bold mt-1">
                          {{ result.backtest.totalTrades || 0 }} 次
                        </div>
                      </div>
                      <v-icon size="32" color="primary">mdi-swap-horizontal</v-icon>
                    </div>
                  </v-card>
                </v-col>

                <v-col cols="12" md="4">
                  <v-card variant="tonal" rounded="lg" class="pa-4">
                    <div class="d-flex align-center justify-space-between">
                      <div>
                        <div class="text-caption text-grey">胜率</div>
                        <div class="text-h6 font-weight-bold mt-1">
                          {{ result.backtest.winRate ? (result.backtest.winRate * 100).toFixed(2) : '0.00' }}%
                        </div>
                      </div>
                      <v-icon size="32" color="success">mdi-trophy</v-icon>
                    </div>
                  </v-card>
                </v-col>

                <v-col cols="12" md="4">
                  <v-card variant="tonal" rounded="lg" class="pa-4">
                    <div class="d-flex align-center justify-space-between">
                      <div>
                        <div class="text-caption text-grey">盈亏比</div>
                        <div class="text-h6 font-weight-bold mt-1">
                          {{ result.backtest.profitFactor ? result.backtest.profitFactor.toFixed(2) : '0.00' }}
                        </div>
                      </div>
                      <v-icon size="32" color="info">mdi-scale-balance</v-icon>
                    </div>
                  </v-card>
                </v-col>
              </v-row>

              <!-- 回测说明 -->
              <v-alert type="info" variant="tonal" rounded="lg" class="mt-6">
                <template v-slot:prepend>
                  <v-icon>mdi-information</v-icon>
                </template>
                <div class="text-body-2">
                  <strong>回测说明：</strong>
                  以上数据基于历史数据模拟交易得出，仅供参考。实际收益可能因市场环境变化、交易成本、滑点等因素有所不同。
                </div>
              </v-alert>
            </div>

            <!-- 无回测结果时显示 -->
            <div v-else>
              <!-- 回测执行中 -->
              <v-sheet v-if="isBacktesting" rounded="lg" class="pa-8" color="primary-container" style="background-color: rgba(30, 136, 229, 0.08) !important;">
                <div class="text-center mb-6">
                  <v-progress-circular
                    :model-value="backtestProgress"
                    :size="100"
                    :width="10"
                    color="primary"
                    class="mb-4"
                  >
                    <span class="text-h5 font-weight-bold">{{ backtestProgress }}%</span>
                  </v-progress-circular>
                </div>
                <h3 class="text-h5 mb-4 font-weight-medium text-center">回测执行中</h3>
                <p class="text-body-1 text-center mb-6">{{ statusText || '正在执行历史数据回测...' }}</p>
                
                <!-- 进度条 -->
                <v-progress-linear
                  :model-value="backtestProgress"
                  color="primary"
                  height="8"
                  rounded
                  striped
                  class="mb-4"
                ></v-progress-linear>
                
                <v-alert type="info" variant="tonal" rounded="lg">
                  <template v-slot:prepend>
                    <v-icon>mdi-information</v-icon>
                  </template>
                  <div class="text-body-2">
                    回测可能需要几分钟时间，请耐心等待...
                  </div>
                </v-alert>
              </v-sheet>
              
              <!-- 回测准备状态 -->
              <v-sheet v-else rounded="lg" class="pa-8 text-center" color="primary-container" style="background-color: rgba(30, 136, 229, 0.08) !important;">
                <v-icon size="64" class="mb-6 text-primary">mdi-play-circle-outline</v-icon>
                <h3 class="text-h5 mb-4 font-weight-medium">准备开始回测</h3>
                <p class="text-body-1 mb-6">点击下方按钮，使用历史数据对策略进行回测验证</p>
                <v-btn 
                  color="primary" 
                  size="x-large" 
                  variant="flat" 
                  rounded="pill" 
                  @click="startBacktest"
                  :loading="isBacktesting"
                  :disabled="isBacktesting"
                >
                  <v-icon start size="24">mdi-rocket-launch</v-icon>
                  开始回测
                </v-btn>
                <v-alert v-if="backtestError" type="error" variant="tonal" class="mt-6" rounded="lg">
                  <template v-slot:prepend>
                    <v-icon>mdi-alert-circle</v-icon>
                  </template>
                  <div class="text-body-2" style="white-space: pre-wrap;">
                    <strong>回测失败：</strong>{{ backtestError }}
                  </div>
                </v-alert>
              </v-sheet>
            </div>
          </v-card-text>
          <v-card-actions class="px-6 pb-6">
            <v-btn variant="text" @click="prevStep" prepend-icon="mdi-arrow-left" rounded="pill">
              上一步
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn v-if="result.backtest && Object.keys(result.backtest).length > 0" color="primary" size="large" @click="nextStep" prepend-icon="mdi-arrow-right" rounded="pill" variant="flat">
              下一步：保存策略
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-window-item>

      <!-- 步骤4: 策略保存 -->
      <v-window-item value="4">
        <v-card rounded="xl">
          <v-card-title class="text-h5 font-weight-medium pa-6">
            <v-icon start>mdi-content-save</v-icon>
            策略保存
          </v-card-title>
          <v-card-subtitle class="px-6 pb-4">保存策略到策略库，随时可以启用实盘交易</v-card-subtitle>
          <v-card-text class="pa-6">
            <!-- 策略信息展示 -->
            <v-sheet rounded="lg" class="pa-8 mb-6" color="primary-container" style="background-color: rgba(30, 136, 229, 0.06) !important;">
              <div class="d-flex align-center mb-6">
                <v-icon size="64" class="mr-4 text-primary">mdi-strategy</v-icon>
                <div>
                  <h3 class="text-h4 font-weight-bold mb-2">{{ result.title || '智能AI策略' }}</h3>
                  <p class="text-body-1 text-medium-emphasis mb-0">{{ result.description || '策略已生成完成' }}</p>
                </div>
              </div>

              <!-- 策略表现摘要 -->
              <v-row v-if="result.backtest && Object.keys(result.backtest).length > 0">
                <v-col cols="6" md="3">
                  <v-card variant="tonal" rounded="lg" class="pa-4">
                    <div class="text-caption text-medium-emphasis mb-2">总收益率</div>
                    <div class="text-h4 font-weight-bold text-primary">
                      {{ (result.backtest.totalReturn || 0).toFixed(2) }}%
                    </div>
                  </v-card>
                </v-col>
                <v-col cols="6" md="3">
                  <v-card variant="tonal" rounded="lg" class="pa-4">
                    <div class="text-caption text-medium-emphasis mb-2">年化收益</div>
                    <div class="text-h4 font-weight-bold text-success">
                      {{ (result.backtest.annualReturn || 0).toFixed(2) }}%
                    </div>
                  </v-card>
                </v-col>
                <v-col cols="6" md="3">
                  <v-card variant="tonal" rounded="lg" class="pa-4">
                    <div class="text-caption text-medium-emphasis mb-2">夏普比率</div>
                    <div class="text-h4 font-weight-bold text-info">
                      {{ (result.backtest.sharpeRatio || 0).toFixed(2) }}
                    </div>
                  </v-card>
                </v-col>
                <v-col cols="6" md="3">
                  <v-card variant="tonal" rounded="lg" class="pa-4">
                    <div class="text-caption text-medium-emphasis mb-2">最大回撤</div>
                    <div class="text-h4 font-weight-bold text-error">
                      {{ (result.backtest.maxDrawdown || 0).toFixed(2) }}%
                    </div>
                  </v-card>
                </v-col>
              </v-row>

              <!-- 股票池信息 -->
              <v-card v-if="result.recommendedStocks && result.recommendedStocks.length > 0" variant="outlined" rounded="lg" class="mt-4 pa-4">
                <div class="d-flex align-center mb-3">
                  <v-icon start size="20" class="text-secondary">mdi-chart-box-outline</v-icon>
                  <h4 class="text-subtitle-1 font-weight-medium">股票池 ({{ result.recommendedStocks.length }}只)</h4>
                </div>
                <v-chip-group>
                  <v-chip
                    v-for="stock in result.recommendedStocks"
                    :key="stock"
                    size="small"
                    variant="outlined"
                    rounded="lg"
                  >
                    {{ stock }}
                  </v-chip>
                </v-chip-group>
              </v-card>
            </v-sheet>

            <!-- 提示信息 -->
            <v-alert type="info" variant="tonal" rounded="lg" class="mb-4">
              <div class="d-flex align-center">
                <v-icon start size="24">mdi-information</v-icon>
                <div>
                  <div class="font-weight-medium mb-1">保存策略后</div>
                  <div class="text-body-2">
                    策略将保存到您的策略库中，您可以随时在策略库中查看和管理此策略，或激活到实盘交易系统。
                  </div>
                </div>
              </div>
            </v-alert>
          </v-card-text>
          <v-card-actions class="px-6 pb-6">
            <v-btn variant="text" @click="prevStep" prepend-icon="mdi-arrow-left" rounded="pill">
              上一步
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn 
              color="primary" 
              size="large" 
              prepend-icon="mdi-play" 
              rounded="pill" 
              variant="outlined"
              class="mr-3"
              @click="activateStrategy"
              :disabled="!generatedStrategyId || isSaving"
            >
              激活到实盘
            </v-btn>
            <v-btn 
              color="success" 
              size="large" 
              prepend-icon="mdi-content-save" 
              rounded="pill" 
              variant="flat"
              @click="saveStrategy"
              :loading="isSaving"
              :disabled="!jobId"
            >
              保存策略
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { api } from '@/services'

const currentStep = ref('1')
const allTags = ['科技', '金融', '医药', '消费', '能源', '制造']

const form = ref({
  targetReturn: 15,
  investmentPeriod: 'medium',
  initialCapital: 100,
  riskPreference: 'moderate',
  maxDrawdown: 20,
  preferredTags: [],
  strategyType: 'value',
  tradingFrequency: 'weekly',
  additionalRequirements: ''
})

const showResult = ref(false)
const generationProgress = ref(0)
const statusText = ref('准备就绪，点击下一步开始生成策略')
const errorMessage = ref('')
const isGenerating = ref(false)
const isSaving = ref(false)
const isBacktesting = ref(false)
const backtestError = ref('')
const backtestProgress = ref(0)
const jobId = ref(null)
const generatedStrategyId = ref(null)

const result = ref({
  title: '',
  description: '',
  recommendedStocks: [],
  model: {},
  backtest: {},
  riskMetrics: {},
  execution: {},
  requirement: {}
})

let pollingTimer = null

const STEP_DESCRIPTIONS = {
  'AI理解用户需求': '正在解析您的投资需求...',
  'AI分析市场状态': '正在分析市场环境...',
  'AI智能选股': '正在筛选候选股票...',
  'AI选择最优模型': '正在选择最优模型...',
  '训练AI模型': '正在训练模型...',
  '生成交易策略': '正在生成策略与组合...',
  '运行智能回测': '正在执行回测...'
}

function resetResult() {
  result.value = {
    title: '',
    description: '',
    recommendedStocks: [],
    model: {},
    backtest: {},
    riskMetrics: {},
    execution: {},
    requirement: {}
  }
}

async function nextStep() {
  const step = parseInt(currentStep.value, 10)
  if (step === 1) {
    await startGeneration()
    return
  }
  if (step === 2 && !showResult.value) {
    return
  }
  if (step < 4) {
    currentStep.value = String(step + 1)
  }
}

function prevStep() {
  const step = parseInt(currentStep.value, 10)
  if (step > 1) {
    currentStep.value = String(step - 1)
  }
}

async function startGeneration() {
  if (isGenerating.value) return
  resetResult()
  showResult.value = false
  errorMessage.value = ''
  generationProgress.value = 0
  statusText.value = '正在准备策略生成...'
  isGenerating.value = true
  jobId.value = null

  try {
    const payload = {
      targetReturn: form.value.targetReturn,
      investmentPeriod: form.value.investmentPeriod,
      initialCapital: form.value.initialCapital,
      riskPreference: form.value.riskPreference,
      maxDrawdown: form.value.maxDrawdown,
      preferredTags: form.value.preferredTags,
      strategyType: form.value.strategyType,
      tradingFrequency: form.value.tradingFrequency,
      additionalRequirements: form.value.additionalRequirements
    }

    const response = await api.strategy.startWorkflow(payload)
    jobId.value = response.jobId
    updateStatus(response)
    currentStep.value = '2'
    beginPolling()
  } catch (error) {
    errorMessage.value = error?.message || '策略生成请求失败，请稍后重试。'
    statusText.value = errorMessage.value
    isGenerating.value = false
  }
}

function beginPolling() {
  stopPolling()
  pollingTimer = setInterval(async () => {
    await pollStatus()
  }, 2000)
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

async function pollStatus() {
  if (!jobId.value) return
  try {
    const status = await api.strategy.getWorkflowStatus(jobId.value)
    updateStatus(status)
  } catch (error) {
    stopPolling()
    errorMessage.value = error?.message || '获取策略状态失败，请稍后重试。'
    isGenerating.value = false
  }
}

function updateStatus(status) {
  generationProgress.value = Math.round((status.progress || 0) * 100)
  statusText.value = status.message || STEP_DESCRIPTIONS[status.stepName] || '策略正在执行中...'

  if (status.status === 'completed' && status.result) {
    stopPolling()
    showResult.value = true
    isGenerating.value = false
    result.value = formatWorkflowResult(status.result)
  } else if (status.status === 'failed') {
    stopPolling()
    isGenerating.value = false
    errorMessage.value = status.error || '策略流程执行失败'
    statusText.value = status.error || '策略流程执行失败'
  }
}

async function retryGeneration() {
  if (isGenerating.value) return
  await startGeneration()
}

function formatWorkflowResult(data) {
  return {
    title: data.title || '智能AI策略',
    description: data.description || '策略生成成功',
    recommendedStocks: data.recommendedStocks || data.universe?.symbols || [],
    model: data.model || {},
    backtest: data.backtest || {},
    riskMetrics: data.portfolio?.riskMetrics || {},
    execution: data.execution || {},
    requirement: data.requirement || {},
    strategyCode: data.strategyCode || null
  }
}

async function saveStrategy() {
  if (!jobId.value) {
    alert('未找到策略ID，请重新生成策略')
    return
  }

  isSaving.value = true
  try {
    // 构建策略保存数据
    const strategyData = {
      strategy_id: jobId.value,
      name: result.value.title || '智能AI策略',
      description: result.value.description || 'AI生成的量化交易策略'
    }

    console.log('📤 保存策略:', strategyData)
    const response = await api.strategy.save(strategyData)
    generatedStrategyId.value = response.strategyId || jobId.value
    
    console.log('✅ 策略保存成功:', response)
    alert('策略保存成功！已保存到策略库中。')
  } catch (error) {
    console.error('❌ 保存策略失败:', error)
    alert(error?.message || '保存策略失败，请稍后重试')
  } finally {
    isSaving.value = false
  }
}

async function startBacktest() {
  if (!jobId.value) {
    backtestError.value = '未找到策略ID，请重新生成策略'
    return
  }

  isBacktesting.value = true
  backtestError.value = ''
  backtestProgress.value = 0

  try {
    console.log('🚀 开始回测，策略ID:', jobId.value)
    const response = await api.strategy.startBacktest({ strategyId: jobId.value })
    
    console.log('✅ 回测响应:', response)

    // 检查是否已有缓存的回测结果
    if (response.success && response.backtest) {
      // 直接使用缓存结果
      result.value.backtest = response.backtest
      backtestProgress.value = 100
      isBacktesting.value = false
      console.log('✅ 回测完成（使用缓存结果）')
      
      // 检查回测结果是否有效
      const bt = response.backtest
      if (bt.totalReturn === 0 && bt.totalTrades === 0 && bt.winRate === 0) {
        backtestError.value = '⚠️ 回测未产生任何交易信号！\n\n可能原因：\n1. 策略参数设置过于严格\n2. 所选时间段内未达到买入条件\n3. 股票池未匹配到合适的交易机会\n\n建议：调整策略参数后重新生成策略'
      }
      return
    }

    // 启动回测任务，开始轮询进度
    if (response.success) {
      console.log('✅ 回测任务已创建，开始轮询进度')
      beginBacktestPolling()
    } else {
      backtestError.value = response.message || '回测启动失败'
      isBacktesting.value = false
    }
  } catch (error) {
    console.error('❌ 回测失败:', error)
    backtestError.value = error?.message || '回测执行失败，请稍后重试'
    isBacktesting.value = false
  }
}

// 回测轮询定时器
let backtestPollingTimer = null

function beginBacktestPolling() {
  stopBacktestPolling()
  backtestPollingTimer = setInterval(async () => {
    await pollBacktestStatus()
  }, 1000) // 每秒轮询一次
}

function stopBacktestPolling() {
  if (backtestPollingTimer) {
    clearInterval(backtestPollingTimer)
    backtestPollingTimer = null
  }
}

async function pollBacktestStatus() {
  if (!jobId.value) return
  
  try {
    const status = await api.strategy.getWorkflowStatus(jobId.value)
    
    // 更新回测进度
    if (status.status === 'running') {
      backtestProgress.value = Math.round((status.progress || 0) * 100)
      statusText.value = status.message || '回测执行中...'
      console.log(`📊 回测进度: ${backtestProgress.value}% - ${statusText.value}`)
    } else if (status.status === 'completed') {
      // 回测完成
      stopBacktestPolling()
      backtestProgress.value = 100
      isBacktesting.value = false
      
      // 更新结果
      if (status.result && status.result.backtest) {
        result.value.backtest = status.result.backtest
        console.log('✅ 回测完成，结果已更新:', status.result.backtest)
        
        // 检查回测结果是否有效
        const bt = status.result.backtest
        if (bt.totalReturn === 0 && bt.totalTrades === 0 && bt.winRate === 0) {
          backtestError.value = '⚠️ 回测未产生任何交易信号！\n\n可能原因：\n1. 策略参数设置过于严格\n2. 所选时间段内未达到买入条件\n3. 股票池未匹配到合适的交易机会\n\n建议：调整策略参数后重新生成策略'
        }
      }
    } else if (status.status === 'failed') {
      // 回测失败
      stopBacktestPolling()
      isBacktesting.value = false
      backtestProgress.value = 0
      backtestError.value = status.error || '回测执行失败'
      console.error('❌ 回测失败:', status.error)
    }
  } catch (error) {
    console.error('❌ 获取回测状态失败:', error)
    // 不停止轮询，继续尝试
  }
}

async function activateStrategy() {
  // 如果还没保存，先保存
  if (!generatedStrategyId.value) {
    await saveStrategy()
    if (!generatedStrategyId.value) {
      return
    }
  }

  try {
    // 使用用户输入的参数配置实盘
    const config = {
      strategyId: generatedStrategyId.value,
      initialCapital: form.value.initialCapital * 10000, // 转换为元
      maxPositionPerStock: 0.2, // 20%
      maxTotalPosition: 0.8, // 80%
      maxDailyLoss: 0.05, // 5%
      maxDrawdown: form.value.maxDrawdown / 100, // 用户设置的最大回撤
      stopLoss: 0.1, // 10%
      takeProfit: 0.2, // 20%
      riskLevel: form.value.riskPreference === 'conservative' ? 'low' : 
                 form.value.riskPreference === 'aggressive' ? 'high' : 'medium',
      notificationChannels: ['email']
    }

    console.log('🚀 激活实盘交易，策略ID:', generatedStrategyId.value)
    console.log('📋 实盘配置:', config)
    
    const response = await api.strategy.live.activate(config.strategyId, config)
    
    console.log('✅ 实盘激活成功:', response)
    alert('策略已成功激活到实盘！系统将开始监控市场并自动执行交易。\n\n您可以在"实时监控"页面查看交易详情。')
  } catch (error) {
    console.error('❌ 激活策略失败:', error)
    alert(error?.message || '激活策略失败，请稍后重试')
  }
}

// 格式化参数名称
function formatParamKey(key) {
  const keyMap = {
    buy_threshold: '买入阈值',
    sell_threshold: '卖出阈值',
    confidence_threshold: '置信度阈值',
    max_position: '最大持仓',
    position_size: '持仓比例',
    stop_loss: '止损',
    take_profit: '止盈',
    min_confirmations: '最少确认数',
    holding_period: '持仓周期',
    rebalance_frequency: '再平衡频率'
  }
  return keyMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// 格式化参数值
function formatParamValue(key, value) {
  if (typeof value === 'number') {
    if (key.includes('threshold') || key.includes('rate')) {
      return (value * 100).toFixed(2) + '%'
    }
    if (key.includes('capital') || key.includes('price')) {
      return '¥' + value.toLocaleString()
    }
    return value.toLocaleString()
  }
  return String(value)
}

// 获取前半部分参数
function getFirstHalfParams(params) {
  const entries = Object.entries(params)
  return Object.fromEntries(entries.slice(0, Math.ceil(entries.length / 2)))
}

// 获取后半部分参数
function getSecondHalfParams(params) {
  const entries = Object.entries(params)
  return Object.fromEntries(entries.slice(Math.ceil(entries.length / 2)))
}

// 重置工作流，重新创建策略
function resetWorkflow() {
  if (isGenerating.value || isSaving.value || isBacktesting.value) {
    alert('当前有任务正在执行，请稍后再试')
    return
  }
  
  // 确认对话框
  if (!confirm('确定要重新创建策略吗？当前进度将被清空。')) {
    return
  }
  
  // 停止所有轮询
  stopPolling()
  stopBacktestPolling()
  
  // 重置状态
  currentStep.value = '1'
  showResult.value = false
  generationProgress.value = 0
  statusText.value = '准备就绪，点击下一步开始生成策略'
  errorMessage.value = ''
  jobId.value = null
  generatedStrategyId.value = null
  resetResult()
}

onBeforeUnmount(() => {
  stopPolling()
  stopBacktestPolling()
})
</script>
