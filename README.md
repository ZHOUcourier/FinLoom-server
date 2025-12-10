# FinLoom 量化投资引擎

FinLoom ("金融（Fin）+ 编织（Loom）") 是一个FIN-R1赋能的自适应量化投资引擎，旨在将数据、因子、模型、用户需求等元素编织成个性化的投资组合。

## 🚀 快速启动

**一键启动完整系统（包含前端构建和后端服务）：**

### Windows 系统

**PowerShell（推荐）**：
```powershell
.\quickstart.ps1
```

**CMD / 双击运行**：
```cmd
quickstart.bat
```

**快速启动（前端已构建）**：
```cmd
启动服务.bat
```

### Linux/macOS 系统
```bash
./quickstart.sh
```

脚本会自动完成：
- ✅ 环境检查（Python & Node.js）
- ✅ 安装后端依赖
- ✅ 构建前端（Vue3）
- ✅ 启动服务并打开浏览器

访问地址：http://localhost:8000

📖 **从这里开始**: [START_HERE.md](START_HERE.md)  
📖 **详细说明**: [快速启动指南](QUICKSTART_快速启动指南.md)  
📖 **使用说明**: [🚀使用说明.md](🚀使用说明.md)

---

## 项目概述

FinLoom系统以 **FIN-R1 模型** 作为自然语言理解入口，支持用户通过文本输入表达投资需求（如"找高成长性中小盘股"），系统自动解析并生成对应的量化策略。

整体流程为：
```
用户输入 → NLP 解析 → 策略生成 → 数据处理 → 回测/实盘 → 风控校验 → 交易执行
```

## 核心功能模块

1. **环境模块 (module_00_environment)** - 系统环境检测和配置管理
2. **数据管道模块 (module_01_data_pipeline)** - 数据采集、处理和存储
3. **特征工程模块 (module_02_feature_engineering)** - 特征提取和因子发现
4. **AI模型模块 (module_03_ai_models)** - 机器学习模型集成
5. **市场分析模块 (module_04_market_analysis)** - 市场趋势和情绪分析
6. **风险管理模块 (module_05_risk_management)** - 风险控制和仓位管理
7. **监控告警模块 (module_06_monitoring_alerting)** - 系统监控和告警
8. **优化模块 (module_07_optimization)** - 参数优化和组合优化
9. **执行模块 (module_08_execution)** - 交易执行和订单管理
10. **回测模块 (module_09_backtesting)** - 策略回测和性能分析
11. **AI交互模块 (module_10_ai_interaction)** - 自然语言处理和需求解析
12. **可视化模块 (module_11_visualization)** - 图表展示和报告生成

每个模块的目录下都有各自的API调用文档，可供查阅。
功能上，比如想使用市场分析功能，则调用`module4`；
想进行投资策略生成和回测，可使用`ai_strategy_system/intelligent_strategy_ai.py`等。

## 技术栈

- **Python**
- **SQLite**: 本地数据存储
- **Akshare**: 中国金融市场数据获取
- **FastAPI**: RESTful API服务，与前端交互
- **Vue3**: 前端框架（正在完善）

## 运行

运行系统

```bash
python3 main.py
```

系统启动后可通过以下端点访问:

- `http://localhost:8000/` - 系统网页
- `http://localhost:8000/health` - 健康检查
- `http://localhost:8000/api/v1/analyze` - 投资需求分析
- `http://localhost:8000/docs` - api文档

## 一些若有若无的示例

### 1. AI智能策略系统（示例）

用自然语言描述需求，系统自动完成策略生成和回测：

```bash
cd ai_strategy_system
python intelligent_strategy_ai.py "我想要稳健收益的策略"
```

系统自动：理解需求 → 市场分析 → 智能选股 → AI模型选择 → 策略生成 → 回测报告

详见 `ai_strategy_system/使用说明.md`

### 2. Web API服务

启动FastAPI服务：

```bash
python main.py
```

访问 `http://localhost:8000/docs` 查看API文档

### 3. 模块测试

```bash
# 测试各模块功能
python tests/module01_data_pipeline_test.py
python tests/module03_ai_models_test.py
python tests/module09_backtesting_test.py
```

### 配置文件

- `config/system_config.yaml` - 系统配置
- `config/model_config.yaml` - 模型配置
- `config/trading_config.yaml` - 交易配置