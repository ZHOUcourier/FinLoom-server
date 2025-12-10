# FinLoom 策略执行详解

## 📋 目录
- [系统架构概览](#系统架构概览)
- [AI模型类型](#ai模型类型)
- [策略生成流程](#策略生成流程)
- [策略执行机制](#策略执行机制)
- [回测执行流程](#回测执行流程)
- [实盘执行流程](#实盘执行流程)

---

## 🏗️ 系统架构概览

FinLoom是一个**智能量化交易系统**，核心理念是：
1. **AI驱动**：使用深度学习模型预测股票未来走势
2. **多重确认**：结合技术指标进行信号确认，避免虚假信号
3. **自适应调整**：根据市场环境动态调整策略参数
4. **风险控制**：集成仓位管理、止损止盈等风险控制机制

### 核心流程
```
用户需求 → AI理解 → 市场分析 → 特征工程 → 模型训练 → 策略生成 → 回测验证 → 实盘执行
```

---

## 🤖 AI模型类型

系统支持4种AI模型，每种模型有不同的特点和应用场景：

### 1. LSTM（长短期记忆网络）⭐⭐⭐⭐⭐ 推荐

**模型架构：**
```python
LSTMNet(
    input_size: 特征数量（如50个技术指标）
    hidden_size: 50（隐藏层神经元数量）
    num_layers: 2（LSTM层数）
    dropout: 0.2（防止过拟合）
)
输出层: Linear(hidden_size → 1) # 预测未来收益率
```

**训练数据：**
- **输入特征**（50+个）：
  - 技术指标：MA5/MA20/RSI/MACD/布林带/KDJ等
  - 动量指标：momentum_5d/momentum_10d/momentum_20d
  - 成交量指标：volume_ratio/volume_ma/成交额比
  - 波动率：收益率标准差、ATR
  - 市场情绪：涨跌比、换手率
  
- **目标变量**：
  - `future_returns`：未来5日收益率
  - 计算方式：`(price_t+5 - price_t) / price_t`

**训练过程：**
```python
1. 数据准备：
   - 时间序列切片：每10天为一个序列
   - 特征归一化：MinMaxScaler标准化
   - 滑动窗口：[t-9, t-8, ..., t] → future_returns[t+5]

2. 模型训练：
   - 损失函数：MSE（均方误差）
   - 优化器：Adam（学习率0.001）
   - 训练轮次：50 epochs
   - 批次大小：32

3. 验证：
   - 训练集/验证集分割：80%/20%
   - 早停机制：防止过拟合
```

**预测输出：**
```python
LSTMPrediction(
    predictions: [0.0123],  # 预测未来5日上涨1.23%
    confidence: 0.75,       # 置信度75%
    model_metrics: {
        "train_loss": 0.0012,
        "val_loss": 0.0015
    }
)
```

**适用场景：**
- ✅ 趋势跟踪策略
- ✅ 短期波段交易（5-10天）
- ✅ 技术面主导的市场

---

### 2. Ensemble（集成模型）⭐⭐⭐⭐⭐ 推荐

**模型架构：**
```python
EnsemblePredictor(
    models: [
        LSTM模型（权重1.0）,
        随机森林（权重0.8）,
        梯度提升树（权重0.9）
    ],
    voting_strategy: "weighted"  # 加权投票
)
```

**集成策略：**
```python
# 加权平均
final_prediction = Σ(model_i.predict() * weight_i) / Σ(weight_i)

# 示例：
LSTM预测: +2.0% (权重1.0)
RF预测:   +1.5% (权重0.8)
GBT预测:  +1.8% (权重0.9)

最终预测 = (2.0*1.0 + 1.5*0.8 + 1.8*0.9) / (1.0+0.8+0.9)
        = (2.0 + 1.2 + 1.62) / 2.7
        = 1.78%
```

**优势：**
- ✅ 降低单一模型的预测偏差
- ✅ 提高预测稳定性和鲁棒性
- ✅ 综合多种算法的优势

**适用场景：**
- ✅ 高波动市场环境
- ✅ 需要稳定收益的场景
- ✅ 长期持有策略

---

### 3. PPO（近端策略优化）⭐⭐⭐

**模型架构：**
```python
PPOAgent(
    state_dim: 10,      # 状态维度（市场特征）
    action_dim: 3,      # 动作维度（买入/持有/卖出）
    actor_network: [64, 64],  # 策略网络
    critic_network: [64, 64]  # 价值网络
)
```

**强化学习流程：**
```python
1. 环境交互：
   State_t → Agent → Action_t → Environment → Reward_t

2. 奖励设计：
   - 正奖励：收益率 > 0
   - 负奖励：亏损、回撤
   - 惩罚：频繁交易、大幅回撤

3. 策略优化：
   - 优势函数：A(s,a) = Q(s,a) - V(s)
   - 策略梯度：最大化期望收益
   - PPO-Clip：限制策略更新幅度
```

**适用场景：**
- ✅ 复杂市场环境
- ✅ 需要动态决策的场景
- ⚠️ 需要大量训练数据
- ⚠️ 训练时间较长

---

### 4. Online Learning（在线学习）⭐⭐

**模型特点：**
```python
OnlineLearner(
    learning_rate: 0.01,
    buffer_size: 500  # 保留最近500个样本
)
```

**增量学习机制：**
```python
# 每接收一个新样本立即更新模型
for new_data in market_stream:
    model.add_sample(features, target)
    model.update_weights()
```

**适用场景：**
- ✅ 高频交易
- ✅ 市场快速变化的场景
- ⚠️ 可能不稳定

---

## 🔄 策略生成流程

### 完整工作流（StrategyWorkflow）

```python
async def execute_strategy_workflow(
    objective: str,        # "短期收益最大化"
    stock_pool: List[str], # ["600519", "000858"]
    strategy_type: str,    # "ensemble"
    risk_level: str        # "medium"
):
```

#### 步骤1: 需求解析
```python
RequirementService.process()
├─ 解析用户需求文本
├─ 提取关键参数（风险偏好、投资期限、目标）
├─ 映射到系统参数
└─ 生成投资组合建议

输出:
RequirementContext(
    raw_text: "我想要短期收益最大化...",
    parsed_requirement: {
        "risk_tolerance": "medium",
        "investment_horizon": "short_term",
        "goals": ["wealth_growth"]
    },
    system_params: {...}
)
```

#### 步骤2: 市场分析
```python
MarketAnalysisService.analyze()
├─ 市场环境识别（牛市/熊市/震荡）
├─ 波动率计算
├─ 情绪指标分析
└─ 宏观经济数据

输出:
MarketContext(
    regime: {
        "trend": "upward",      # 上升趋势
        "volatility": "medium",  # 中等波动
        "confidence": 0.82
    },
    sentiment: {
        "market_mood": "optimistic",
        "fear_greed_index": 65
    }
)
```

#### 步骤3: 股票池筛选
```python
UniverseSelectionService.select()
├─ 基本面筛选（财务健康、盈利能力）
├─ 技术面筛选（趋势、成交量）
├─ 流动性筛选（日均成交额）
└─ 风险筛选（ST股票、停牌股票）

输出:
UniverseSelection(
    symbols: ["600519", "000858", "600036"],
    metadata: {
        "600519": {
            "name": "贵州茅台",
            "sector": "消费品",
            "market_cap": 2500000000000,
            "avg_volume": 50000000
        }
    }
)
```

#### 步骤4: 特征工程
```python
FeatureEngineeringService.engineer()
├─ 数据采集（AKShare）
│  ├─ 日线数据：OHLCV
│  ├─ 分钟数据（可选）
│  └─ 基本面数据
│
├─ 技术指标计算（50+个）
│  ├─ 趋势指标：sma_5, sma_20, sma_50, ema_12, ema_26
│  ├─ 动量指标：momentum_5d, momentum_10d, rsi, macd
│  ├─ 波动率指标：atr, bollinger_bands, volatility
│  ├─ 成交量指标：volume_ratio, volume_ma, obv
│  └─ 其他：kdj, cci, williams_r
│
├─ 时序特征（可选）
│  ├─ 滞后特征：lag_1, lag_5, lag_10
│  └─ 滚动统计：rolling_mean, rolling_std
│
└─ 目标变量计算
   └─ future_returns = (close_t+5 - close_t) / close_t

输出:
FeatureBundle(
    combined_features: DataFrame[
        symbol, date, close, sma_5, sma_20, rsi, 
        momentum_5d, volume_ratio, future_returns, ...
    ],
    train_data: DataFrame[2023-01-01 to 2024-09-01],
    test_data: DataFrame[2024-09-01 to 2024-10-01]
)
```

#### 步骤5: 模型训练
```python
ModelTrainingService.train()

# 以Ensemble为例
├─ 选择模型类型（基于用户偏好）
│  └─ strategy_type="ensemble" → EnsemblePredictor
│
├─ 训练基础LSTM模型
│  ├─ 数据准备：时间序列切片（10天窗口）
│  ├─ 特征归一化：MinMaxScaler
│  ├─ 模型训练：50 epochs, batch_size=32
│  └─ 验证：train_loss=0.0012, val_loss=0.0015
│
├─ 构建集成模型
│  ├─ 添加LSTM模型（权重1.0）
│  ├─ 可选添加其他模型（RF, GBT）
│  └─ 训练集成权重
│
└─ 模型验证
   └─ 测试集预测：RMSE, MAE, 方向准确率

输出:
ModelSelectionResult(
    choice: ModelChoice(
        model_type: "ensemble",
        rationale: "集成模型适合中等风险偏好"
    ),
    model: EnsemblePredictor(已训练),
    training_metadata: {
        "train_loss": 0.0012,
        "val_loss": 0.0015,
        "epochs": 50,
        "training_samples": 12000
    }
)
```

#### 步骤6: 策略代码生成
```python
# 增强版策略生成器
EnhancedStrategyGenerator.generate_enhanced_ensemble_strategy()

策略逻辑 = AI预测 + 多重技术指标确认

买入条件（必须同时满足）:
1. AI预测上涨 > buy_threshold (-0.01即可)
2. 至少1个技术指标确认：
   ├─ 趋势确认：sma_5 > sma_20
   ├─ 动量确认：momentum_5d > 0
   ├─ 成交量确认：volume_ratio > 1.2
   └─ RSI确认：30 < rsi < 70（避免超买超卖）
3. AI置信度 > confidence_threshold (0.3)
4. 加权得分 >= min_weighted_score (1.0)

卖出条件（满足2个即可）:
1. AI预测下跌 < sell_threshold (-0.05)
2. 趋势转弱：sma_5 < sma_20
3. 动量转负：momentum_5d < -0.02
4. 止损：持仓收益 < -5%

输出:
StrategyCode(
    strategy_name: "增强LSTM多重确认策略",
    strategy_function: enhanced_lstm_strategy,
    code_string: "# 策略代码...",
    parameters: {
        "buy_threshold": -0.01,
        "sell_threshold": -0.05,
        "confidence_threshold": 0.3,
        "max_position": 0.3,
        "min_confirmations": 1,
        "min_weighted_score": 1.0
    }
)
```

#### 步骤7: 策略参数优化
```python
AdaptiveParameterManager.adjust_parameters()

根据市场环境动态调整参数：

牛市环境：
├─ buy_threshold: -0.02（更激进）
├─ max_position: 0.4（提高仓位）
└─ confidence_threshold: 0.25

熊市环境：
├─ buy_threshold: 0.01（更保守）
├─ max_position: 0.2（降低仓位）
└─ confidence_threshold: 0.5（提高置信度要求）

震荡市场：
├─ buy_threshold: 0.0（中性）
├─ max_position: 0.3
└─ confidence_threshold: 0.35
```

---

## ⚙️ 策略执行机制

### 回测执行（BacktestService）

```python
async def run_backtest(
    strategy_id: str,
    backtest_config: {
        "start_date": "2024-01-01",
        "end_date": "2024-10-01",
        "initial_capital": 1000000
    }
)
```

#### 回测引擎工作流程

```python
BacktestEngine.run()

初始化：
├─ 初始资金：1,000,000元
├─ 加载历史行情数据（2024-01-01 to 2024-10-01）
├─ 加载特征数据（包含所有技术指标）
└─ 设置风险控制器

每日回测循环（共200个交易日）:
for date in trading_dates:
    
    1. 获取当日市场数据
       current_data = {
           "600519": {
               "open": 1850.0,
               "high": 1880.0,
               "low": 1840.0,
               "close": 1875.0,
               "volume": 50000000
           },
           ...
       }
    
    2. 调用策略函数
       signals = enhanced_lstm_strategy(
           current_data=current_data,
           positions=current_positions,
           capital=current_capital,
           feature_data=feature_bundle
       )
       
       # 策略内部执行：
       ├─ 提取最近10日特征序列
       ├─ AI模型预测未来收益
       │  └─ LSTM预测：+1.5%
       │  └─ 置信度：0.75
       │
       ├─ 检查技术指标确认
       │  ├─ sma_5 (1870) > sma_20 (1850) ✅ 趋势向上
       │  ├─ momentum_5d (+0.012) > 0 ✅ 动量为正
       │  ├─ volume_ratio (1.35) > 1.2 ✅ 成交量放大
       │  └─ rsi (58) in [30, 70] ✅ 未超买
       │
       ├─ 计算确认得分
       │  └─ weighted_score = 2.0(AI) + 1.5(TREND) + 1.2(MOMENTUM) + 1.0(VOLUME) = 5.7
       │
       ├─ 判断是否满足买入条件
       │  ├─ AI预测(+1.5%) > buy_threshold(-0.01) ✅
       │  ├─ 确认数(4) >= min_confirmations(1) ✅
       │  ├─ 得分(5.7) >= min_weighted_score(1.0) ✅
       │  └─ 置信度(0.75) >= confidence_threshold(0.3) ✅
       │
       └─ 生成买入信号
          signals = [
              Signal(
                  symbol="600519",
                  action="BUY",
                  price=1875.0,
                  quantity=500,  # 根据资金和仓位限制计算
                  confidence=0.75,
                  metadata={
                      "ai_prediction": 0.015,
                      "confirmations": 4,
                      "weighted_score": 5.7
                  }
              )
          ]
    
    3. 风险控制过滤
       risk_controller.filter_signals(signals)
       ├─ 检查单股最大仓位（不超过30%）
       ├─ 检查组合最大回撤（不超过15%）
       ├─ 检查单日最大亏损（不超过3%）
       └─ 调整信号数量或取消信号
    
    4. 执行交易
       order_manager.execute_orders(filtered_signals)
       ├─ 买入600519：500股 @ 1875.0元
       │  └─ 成本：937,500元（含手续费）
       ├─ 更新持仓
       │  └─ positions["600519"] = Position(
       │         symbol="600519",
       │         quantity=500,
       │         avg_cost=1875.0,
       │         current_value=937,500
       │      )
       └─ 更新资金
          └─ capital = 1,000,000 - 937,500 = 62,500
    
    5. 持仓市值更新
       for symbol, position in positions.items():
           position.current_value = position.quantity * current_data[symbol]["close"]
       
       total_value = capital + Σ(position.current_value)
                   = 62,500 + 937,500 = 1,000,000
    
    6. 记录绩效
       performance_analyzer.record_daily_performance(
           date=date,
           total_value=total_value,
           cash=capital,
           positions_value=Σ(position.current_value)
       )

回测结束后计算指标：
├─ 总收益率：(final_value - initial_capital) / initial_capital
├─ 年化收益率：total_return * (252 / trading_days)
├─ 夏普比率：(avg_return - risk_free_rate) / std_return
├─ 最大回撤：max((peak - trough) / peak)
├─ 胜率：winning_trades / total_trades
├─ 盈亏比：avg_profit / avg_loss
└─ 卡玛比率：annual_return / max_drawdown
```

#### 回测结果示例

```python
BacktestSummary(
    final_capital: 1,028,700.00,
    total_return: 0.0287,  # 2.87%
    total_trades: 15,
    win_rate: 0.60,  # 60%
    sharpe_ratio: 1.23,
    max_drawdown: 0.08,  # 8%
    profit_factor: 1.85,
    calmar_ratio: 0.36,
    sortino_ratio: 1.56
)
```

### 实盘执行（未完全实现，框架已搭建）

```python
LiveTradingEngine.run()

实时数据流：
├─ 订阅实时行情（WebSocket或轮询）
├─ 每分钟/每秒更新市场数据
└─ 触发策略计算

策略执行：
├─ 与回测相同的策略逻辑
├─ 生成交易信号
└─ 通过API发送到券商

风险监控：
├─ 实时监控持仓盈亏
├─ 自动止损止盈
└─ 异常情况告警
```

---

## 📊 关键指标说明

### 策略信号指标

| 指标 | 说明 | 计算方式 | 阈值 |
|------|------|----------|------|
| **ai_prediction** | AI模型预测的未来收益率 | LSTM/Ensemble输出 | > -0.01 |
| **confirmation_count** | 技术指标确认数量 | 满足条件的指标个数 | >= 1 |
| **weighted_score** | 加权确认得分 | Σ(indicator_weight) | >= 1.0 |
| **confidence** | AI预测置信度 | 模型输出或基于历史准确率 | >= 0.3 |

### 技术指标确认

| 确认类型 | 指标 | 条件 | 权重 |
|----------|------|------|------|
| **AI** | 模型预测 | prediction > buy_threshold | 2.0 |
| **TREND** | sma_5 vs sma_20 | sma_5 > sma_20 | 1.5 |
| **MOMENTUM** | momentum_5d | > 0 | 1.2 |
| **VOLUME** | volume_ratio | > 1.2 | 1.0 |
| **RSI** | rsi | 30 < rsi < 70 | 0.8 |

### 回测绩效指标

| 指标 | 说明 | 优秀标准 |
|------|------|----------|
| **总收益率** | (期末资金 - 期初资金) / 期初资金 | > 10% (年化) |
| **夏普比率** | 风险调整后收益 | > 1.5 |
| **最大回撤** | 最大亏损幅度 | < 15% |
| **胜率** | 盈利交易占比 | > 50% |
| **盈亏比** | 平均盈利 / 平均亏损 | > 2.0 |
| **卡玛比率** | 年化收益 / 最大回撤 | > 0.5 |

---

## 🔧 参数调优建议

### 激进策略（高风险高收益）
```python
params = {
    "buy_threshold": -0.02,      # 更宽松
    "confidence_threshold": 0.2,  # 更低置信度要求
    "min_confirmations": 1,       # 最少确认
    "max_position": 0.4,          # 更高仓位
}
```

### 稳健策略（平衡风险收益）
```python
params = {
    "buy_threshold": 0.0,
    "confidence_threshold": 0.35,
    "min_confirmations": 2,
    "max_position": 0.3,
}
```

### 保守策略（低风险稳定收益）
```python
params = {
    "buy_threshold": 0.01,       # 必须预测明确上涨
    "confidence_threshold": 0.5, # 高置信度要求
    "min_confirmations": 3,      # 多重确认
    "max_position": 0.2,         # 低仓位
}
```

---

## 📝 总结

### 策略核心逻辑
1. **AI驱动预测**：使用LSTM/Ensemble深度学习模型预测未来收益
2. **多重信号确认**：结合趋势、动量、成交量、RSI等技术指标
3. **加权评分机制**：不同指标有不同权重，避免单一指标误导
4. **自适应参数**：根据市场环境动态调整策略参数
5. **严格风控**：仓位控制、止损止盈、回撤限制

### 策略优势
- ✅ **智能化**：AI自动学习市场规律
- ✅ **稳定性**：多重确认降低虚假信号
- ✅ **灵活性**：参数可根据需求调整
- ✅ **可解释**：每个信号都有详细的决策依据

### 适用场景
- ✅ A股市场（已集成AKShare数据源）
- ✅ 中短期波段交易（5-30天持有期）
- ✅ 中等风险偏好投资者
- ✅ 量化投资组合管理

---

**文档版本**：v2.0  
**更新时间**：2025-10-14  
**作者**：FinLoom开发团队
