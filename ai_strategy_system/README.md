# FinLoom AI策略系统

## 🎯 系统架构（清晰版）

```
ai_strategy_system/
│
├── 📌 main.py ⭐                    # 主入口文件（从这里开始）
├── 📌 intelligent_strategy_ai.py    # 智能策略AI（7步完整流程）
├── 📌 strategy_api.py               # HTTP API接口
├── 📄 README.md                     # 本文件
│
├── 📁 core/                         # 核心模块
│   ├── strategy_workflow.py        # 策略工作流（9个Service类）
│   ├── strategy_code_generator.py  # 策略代码生成器
│   └── enhanced_strategy_generator.py # 增强策略生成器（多信号确认）
│
├── 📁 services/                     # 服务模块
│   ├── daily_runner.py             # 每日定时运行
│   ├── live_trading_manager.py     # 实盘交易管理
│   ├── signal_generator.py         # 交易信号生成
│   ├── notification_system.py      # 通知系统（邮件/微信/钉钉/短信）
│   ├── risk_controller.py          # 风险控制器
│   └── adaptive_parameter_manager.py # 自适应参数管理
│
└── 📁 utils/                        # 工具模块
    └── strategy_persistence.py     # 策略持久化存储
```

---

## 🚀 快速开始

### 从这里开始 ⭐

```bash
# 生成AI投资策略（一行命令）
python ai_strategy_system/main.py \
    --requirement "中等风险，追求稳健收益" \
    --capital 100000

# 激活策略到实盘
python ai_strategy_system/main.py --activate STRATEGY_ID

# 立即执行一次
python ai_strategy_system/main.py --run

# 启动定时调度（09:00, 14:00, 21:00自动运行）
python ai_strategy_system/main.py --schedule
```

---

## 📚 目录说明

### 📌 主入口

| 文件 | 说明 | 用途 |
|------|------|------|
| **main.py** ⭐ | 主入口文件 | **从这里开始！** 命令行工具 |
| intelligent_strategy_ai.py | 智能策略AI | 7步完整流程，生成策略 |
| strategy_api.py | HTTP API | Web接口 |

### 📁 core/ - 核心模块

| 文件 | 说明 | 功能 |
|------|------|------|
| strategy_workflow.py | 策略工作流 | 9个Service类，完整流程 |
| strategy_code_generator.py | 代码生成器 | 生成可执行策略函数 |
| enhanced_strategy_generator.py | 增强生成器 | 多重信号确认机制 |

### 📁 services/ - 服务模块

| 文件 | 说明 | 功能 |
|------|------|------|
| daily_runner.py | 每日运行 | 定时调度，自动执行 |
| live_trading_manager.py | 交易管理 | 激活策略，管理账户 |
| signal_generator.py | 信号生成 | AI预测，生成信号 |
| notification_system.py | 通知系统 | 邮件/微信/钉钉/短信 |
| risk_controller.py | 风险控制 | 实时风险检查 |
| adaptive_parameter_manager.py | 参数管理 | 自适应调整参数 |

### 📁 utils/ - 工具模块

| 文件 | 说明 | 功能 |
|------|------|------|
| strategy_persistence.py | 持久化存储 | 保存/加载策略 |

---

## 🎯 核心流程

### 1️⃣ 策略生成（7步）

```
main.py
  ↓
intelligent_strategy_ai.py
  ├─ Step1: AI理解用户需求
  ├─ Step2: 分析市场环境
  ├─ Step3: AI智能选股
  ├─ Step4: AI选择最佳模型
  ├─ Step5: 训练模型
  ├─ Step6: 生成策略代码
  └─ Step7: 回测验证
  ↓
策略ID
```

### 2️⃣ 策略运行

```
main.py --run
  ↓
services/daily_runner.py
  ├─ services/signal_generator.py (生成信号)
  ├─ services/risk_controller.py (风险检查)
  ├─ services/live_trading_manager.py (交易管理)
  └─ services/notification_system.py (发送通知)
  ↓
实盘运行
```

---

## 💡 使用示例

### 示例1: 快速生成策略

```bash
# 一行命令
python ai_strategy_system/main.py --requirement "低风险稳健型" --capital 100000
```

### 示例2: Python调用

```python
from ai_strategy_system.main import FinLoomAISystem

system = FinLoomAISystem()

# 生成策略
strategy_id = await system.generate_strategy(
    requirement="中等风险追求稳健收益",
    initial_capital=100000
)

# 激活策略
system.activate_strategy(strategy_id)

# 执行任务
system.run_daily_task()
```

### 示例3: 完整流程

```python
from ai_strategy_system.intelligent_strategy_ai import IntelligentStrategyAI

# 创建AI实例
ai = IntelligentStrategyAI(
    user_requirement="高风险激进型，关注科技板块",
    initial_capital=1_000_000
)

# 执行完整工作流
await ai.execute_full_workflow()

# 获取结果
if ai.workflow_result.success:
    print(f"策略ID: {ai.workflow_result.strategy_id}")
    print(f"回测收益: {ai.backtest_summary['total_return']:.2%}")
    print(f"夏普比率: {ai.backtest_summary['sharpe_ratio']:.2f}")
```

---

## 📊 架构优势

### ✅ 清晰的入口

**之前（混乱）**：
```
14个文件平铺，不知道从哪个开始
intelligent_strategy_ai.py?
strategy_generator.py?
daily_runner.py?
还是live_trading_manager.py?
```

**现在（清晰）**：
```
main.py ⭐  ← 从这里开始！
```

### ✅ 模块化设计

```
core/      - 核心业务逻辑
services/  - 具体服务实现
utils/     - 工具函数
```

### ✅ 职责清晰

- **main.py**: 入口和命令行工具
- **intelligent_strategy_ai.py**: 策略生成主流程
- **core/**: 策略工作流、代码生成、信号确认
- **services/**: 实盘运行、信号生成、风险控制、通知
- **utils/**: 存储管理

---

## 🔍 详细功能

### main.py - 主入口 ⭐

**命令行工具**：
```bash
# 生成策略
python main.py --requirement "..." --capital 100000

# 激活策略
python main.py --activate STRATEGY_ID

# 执行任务
python main.py --run

# 启动调度
python main.py --schedule
```

**Python API**：
```python
system = FinLoomAISystem()
await system.generate_strategy(...)
system.activate_strategy(...)
system.run_daily_task()
system.start_scheduler()
```

---

### intelligent_strategy_ai.py - 智能AI

**7步完整流程**：

```python
ai = IntelligentStrategyAI(user_requirement, initial_capital)

# 逐步执行
await ai.step1_understand_requirement()  # NLP理解
await ai.step2_analyze_market()          # 市场分析
await ai.step3_ai_select_stocks()        # AI选股
await ai.step4_ai_select_model()         # 选择模型
await ai.step5_train_selected_model()    # 训练模型
await ai.step6_generate_strategy()       # 生成代码
await ai.step7_run_backtest()            # 回测验证

# 或一键执行
await ai.execute_full_workflow()
```

---

### core/strategy_workflow.py - 工作流

**9个专业Service类**：

1. **RequirementService** - NLP需求理解
2. **MarketContextService** - 市场环境分析
3. **UniverseService** - 股票池选择
4. **FeatureEngineeringService** - 特征工程
5. **ModelService** - 模型训练（LSTM/Ensemble/PPO/Online）
6. **StrategyDesignService** - 策略设计
7. **PortfolioService** - 组合优化
8. **ExecutionPlanningService** - 执行计划
9. **BacktestService** - 回测验证

```python
workflow = StrategyWorkflow()

# 使用各个服务
requirement_ctx = await workflow.requirement_service.process(text)
market_ctx = await workflow.market_service.get_current_context()
universe = await workflow.universe_service.select(requirement_ctx)
features = await workflow.feature_service.engineer(data, universe)
model = await workflow.model_service.train_lstm(features)
# ...
```

---

### core/strategy_code_generator.py - 代码生成

**生成可执行策略函数**：

```python
generator = StrategyCodeGenerator()

# 生成策略
strategy_code = generator.generate_strategy_code(
    model_type="lstm",  # lstm/ensemble/online/ppo
    model_instance=trained_model,
    strategy_params=params,
    feature_columns=features
)

# 执行策略
signals = strategy_code.strategy_function(
    current_data, positions, capital, feature_data
)
```

---

### services/daily_runner.py - 每日运行

```python
runner = DailyRunner()

# 立即执行
runner.run_daily_task()

# 定时调度
runner.start_scheduler()  # 09:00, 14:00, 21:00自动运行
```

---

### services/notification_system.py - 通知系统

```python
notifier = NotificationSystem()

# 邮件
notifier.send_email_notification(data)

# 微信
notifier.send_wechat_notification(data)

# 钉钉
notifier.send_dingtalk_notification(data)

# 短信
notifier.send_sms_notification(data)

# 风险告警
notifier.send_risk_alert(strategy_id, violations)

# 每日摘要
notifier.send_daily_summary(summary_data)
```

---

## 🚀 快速参考

### 生成策略

```bash
python ai_strategy_system/main.py --requirement "你的需求" --capital 100000
```

### 运行策略

```bash
python ai_strategy_system/main.py --run
```

### 定时调度

```bash
python ai_strategy_system/main.py --schedule
```

---

## 📝 总结

**现在的结构非常清晰**：

1. ✅ **main.py是唯一入口** - 一眼就看出来从哪里开始
2. ✅ **core/核心逻辑** - 策略工作流、代码生成
3. ✅ **services/服务实现** - 实盘运行、信号生成、通知
4. ✅ **utils/工具函数** - 存储管理
5. ✅ **保留所有功能** - 没有删减任何功能

**不再混乱，结构清晰！** ⭐

---

**从 main.py 开始使用！**
