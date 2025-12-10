# 阿里云API配置说明

## 概述

FinLoom系统已升级为使用阿里云DashScope API，以提供更强大的AI对话和策略生成功能。

## 获取API密钥

1. 访问阿里云DashScope控制台：https://dashscope.console.aliyun.com/
2. 登录您的阿里云账号
3. 在控制台中找到"API-KEY管理"
4. 创建一个新的API密钥或使用现有密钥
5. 复制API密钥（请妥善保管，不要泄露）

## 配置步骤

### 1. 编辑配置文件

打开 `config/system_config.yaml` 文件，找到 `ai_model` 配置段：

```yaml
# AI模型配置
ai_model:
  provider: aliyun  # 使用阿里云API
  aliyun:
    api_key: "YOUR_ALIYUN_API_KEY"  # 请替换为实际的API密钥
    model: "qwen-plus"  # 可选: qwen-turbo, qwen-plus, qwen-max
    temperature: 0.7
    max_tokens: 2000
```

### 2. 替换API密钥

将 `api_key: "YOUR_ALIYUN_API_KEY"` 中的 `YOUR_ALIYUN_API_KEY` 替换为您从阿里云控制台获取的实际API密钥。

示例：
```yaml
api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 3. 选择模型（可选）

阿里云提供多个模型选择：

- **qwen-turbo**: 快速响应，适合对话场景
- **qwen-plus**: 平衡性能和质量（推荐）
- **qwen-max**: 最强性能，适合复杂分析

根据您的需求修改 `model` 配置项。

### 4. 调整参数（可选）

- `temperature`: 控制输出的随机性（0-2，默认0.7）
  - 较低值：更确定性的输出
  - 较高值：更有创造性的输出

- `max_tokens`: 单次响应的最大token数（默认2000）

## 功能说明

配置完成后，以下功能将使用阿里云API：

### 1. 智能对话功能
- API端点：`POST /api/chat`
- 用户在网页端的"智能对话"页面提问，系统将通过阿里云API返回专业的投资建议

### 2. 策略生成功能
- API端点：`POST /api/v1/strategy/generate`
- 用户在"策略生成"页面输入需求，系统将自动：
  - 解析投资需求
  - 生成个性化投资策略
  - 推荐股票配置
  - 提供风险管理建议

## 验证配置

### 1. 启动服务

```bash
python main.py
```

### 2. 测试智能对话

在浏览器中打开FinLoom界面，进入"智能对话"页面，输入问题如：
```
我有10万元，想进行中等风险的投资，请给我一些建议
```

### 3. 测试策略生成

进入"策略生成"页面，输入需求如：
```
我希望建立一个稳健型的投资组合，投资期限1年，偏好科技和消费行业
```

## 常见问题

### Q: 提示"阿里云API密钥未配置"

A: 请检查 `config/system_config.yaml` 中的API密钥是否已正确配置，且不是默认值 `YOUR_ALIYUN_API_KEY`。

### Q: API调用失败

A: 可能的原因：
1. API密钥无效或过期
2. 账户余额不足
3. 网络连接问题
4. 请求频率超限

请检查日志文件 `logs/system.log` 获取详细错误信息。

### Q: 如何查看API调用日志

A: 查看 `logs/system.log` 文件，搜索"阿里云API"相关日志。

### Q: 支持哪些模型

A: 当前支持阿里云通义千问系列模型：
- qwen-turbo
- qwen-plus
- qwen-max
- qwen-max-longcontext（长文本场景）

## 安全建议

1. **不要将API密钥提交到版本控制系统**
   - 将 `config/system_config.yaml` 添加到 `.gitignore`
   - 或使用环境变量管理密钥

2. **定期轮换API密钥**
   - 建议每3-6个月更换一次API密钥

3. **监控API使用情况**
   - 在阿里云控制台查看API调用统计
   - 设置用量告警

4. **设置访问限制**
   - 为API密钥设置IP白名单（如果可能）

## 技术支持

如遇到问题，请：
1. 查看 `logs/system.log` 日志文件
2. 访问阿里云DashScope文档：https://help.aliyun.com/zh/dashscope/
3. 联系技术支持团队

## 更新日志

- **2025-10-09**: 初始版本，支持阿里云DashScope API集成

