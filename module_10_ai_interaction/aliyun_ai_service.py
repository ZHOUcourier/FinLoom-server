"""
阿里云AI服务模块
使用阿里云API替代FIN-R1模型，提供智能对话和策略生成功能
"""

import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from common.logging_system import setup_logger
from common.aliyun_api_client import AliyunAPIClient

logger = setup_logger(__name__)


class AliyunAIService:
    """阿里云AI服务类"""
    
    def __init__(self, config_path: str = "config/system_config.yaml"):
        """
        初始化AI服务
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.client = None
        self._initialize_client()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('ai_model', {})
            else:
                logger.warning(f"配置文件不存在: {config_path}")
                return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def _initialize_client(self):
        """初始化阿里云API客户端"""
        try:
            aliyun_config = self.config.get('aliyun', {})
            api_key = aliyun_config.get('api_key', '')
            
            if not api_key or api_key == 'YOUR_ALIYUN_API_KEY':
                logger.error("请在config/system_config.yaml中配置阿里云API密钥")
                raise ValueError("阿里云API密钥未配置")
            
            model = aliyun_config.get('model', 'qwen-plus')
            self.client = AliyunAPIClient(api_key=api_key, model=model)
            logger.info(f"阿里云AI服务初始化成功，使用模型: {model}")
            
        except Exception as e:
            logger.error(f"初始化阿里云客户端失败: {e}")
            raise
    
    async def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        智能对话功能
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            system_prompt: 系统提示词
            
        Returns:
            AI回复内容
        """
        try:
            if conversation_history:
                response = self.client.chat_with_history(
                    user_message=user_message,
                    history=conversation_history,
                    system_message=system_prompt or self._get_default_system_prompt(),
                    temperature=self.config.get('aliyun', {}).get('temperature', 0.7),
                    max_tokens=self.config.get('aliyun', {}).get('max_tokens', 2000)
                )
            else:
                response = self.client.simple_chat(
                    user_message=user_message,
                    system_message=system_prompt or self._get_default_system_prompt(),
                    temperature=self.config.get('aliyun', {}).get('temperature', 0.7),
                    max_tokens=self.config.get('aliyun', {}).get('max_tokens', 2000)
                )
            
            logger.info("智能对话完成")
            return response
            
        except Exception as e:
            logger.error(f"智能对话失败: {e}")
            raise
    
    async def parse_investment_requirement(self, user_text: str) -> Dict[str, Any]:
        """
        解析用户的投资需求
        
        Args:
            user_text: 用户输入的文本
            
        Returns:
            解析后的结构化需求
        """
        system_prompt = """你是一个专业的金融投资顾问助手，负责解析用户的投资需求。
请根据用户的描述，提取以下信息并以JSON格式返回：

{
    "investment_amount": 投资金额(数字，单位：元),
    "risk_tolerance": "风险承受能力(conservative/moderate/aggressive/very_aggressive)",
    "investment_horizon": "投资时间范围(short/medium/long)",
    "investment_goals": ["投资目标列表"],
    "constraints": ["投资约束条件列表"],
    "preferred_sectors": ["偏好的行业列表"],
    "strategy_preferences": {
        "rebalance_frequency": "调仓频率(daily/weekly/monthly)",
        "position_sizing_method": "仓位管理方法(equal_weight/kelly_criterion/risk_parity)",
        "max_drawdown": "最大回撤限制(0-1之间的小数)",
        "position_limit": "单个仓位上限(0-1之间的小数)",
        "stop_loss": "止损比例(0-1之间的小数)"
    }
}

如果用户没有明确提到某些信息，请根据常识推断合理的默认值。
只返回JSON，不要包含其他解释文字。"""

        try:
            response = await self.chat(
                user_message=user_text,
                system_prompt=system_prompt
            )
            
            # 解析JSON响应
            # 清理可能的markdown代码块标记
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.startswith('```'):
                response_clean = response_clean[3:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            
            parsed_data = json.loads(response_clean)
            
            logger.info("投资需求解析成功")
            return {
                "parsed_requirement": parsed_data,
                "strategy_params": parsed_data.get("strategy_preferences", {}),
                "risk_params": {
                    "max_drawdown": parsed_data.get("strategy_preferences", {}).get("max_drawdown", 0.2),
                    "position_limit": parsed_data.get("strategy_preferences", {}).get("position_limit", 0.1),
                    "stop_loss": parsed_data.get("strategy_preferences", {}).get("stop_loss", 0.05)
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {e}, 响应内容: {response}")
            # 返回一个默认的解析结果
            return self._get_default_requirement()
        except Exception as e:
            logger.error(f"解析投资需求失败: {e}")
            raise
    
    async def generate_strategy(
        self,
        requirement: str,
        market_data: Optional[Dict[str, Any]] = None,
        market_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成投资策略
        
        Args:
            requirement: 用户需求描述
            market_data: 市场数据
            market_analysis: 市场分析结果
            
        Returns:
            生成的策略方案
        """
        # 构建上下文信息
        context = f"用户投资需求：{requirement}\n\n"
        
        if market_data:
            context += f"当前市场数据：{json.dumps(market_data, ensure_ascii=False, indent=2)}\n\n"
        
        if market_analysis:
            context += f"市场分析：{json.dumps(market_analysis, ensure_ascii=False, indent=2)}\n\n"
        
        system_prompt = """你是一个专业的量化投资策略师。
根据用户需求和市场情况，生成一个详细的投资策略方案，包括：

1. 策略概述
2. 推荐股票列表（股票代码、名称、推荐理由）
3. 仓位配置建议
4. 风险控制措施
5. 预期收益和风险评估

请以JSON格式返回策略方案：
{
    "strategy_name": "策略名称",
    "strategy_description": "策略描述",
    "recommended_stocks": [
        {
            "symbol": "股票代码",
            "name": "股票名称",
            "reason": "推荐理由",
            "suggested_weight": 0.15
        }
    ],
    "risk_management": {
        "max_position_size": 0.15,
        "stop_loss_pct": 0.05,
        "take_profit_pct": 0.20
    },
    "expected_performance": {
        "expected_return": "预期年化收益率",
        "risk_level": "风险等级",
        "holding_period": "建议持有期限"
    },
    "key_points": ["关键要点1", "关键要点2"]
}

只返回JSON，不要包含其他解释文字。"""

        try:
            response = await self.chat(
                user_message=context,
                system_prompt=system_prompt
            )
            
            # 解析JSON响应
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.startswith('```'):
                response_clean = response_clean[3:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            
            strategy_data = json.loads(response_clean)
            
            logger.info("策略生成成功")
            return strategy_data
            
        except json.JSONDecodeError as e:
            logger.error(f"解析策略JSON失败: {e}, 响应内容: {response}")
            return self._get_default_strategy()
        except Exception as e:
            logger.error(f"生成策略失败: {e}")
            raise
    
    async def analyze_and_recommend(
        self,
        user_text: str,
        include_market_insight: bool = True
    ) -> Dict[str, Any]:
        """
        综合分析并提供投资建议
        
        Args:
            user_text: 用户输入
            include_market_insight: 是否包含市场洞察
            
        Returns:
            分析结果和建议
        """
        system_prompt = """你是FinLoom智能投资助手，一个专业的金融投资顾问。
请根据用户的问题或需求，提供专业、清晰、实用的投资建议。

回复要求：
1. 语气专业但易懂
2. 提供具体可执行的建议
3. 包含风险提示
4. 如果涉及股票推荐，请说明理由
5. 回复要有条理，使用适当的标点和换行

请直接给出自然语言回复，不需要返回JSON格式。"""

        try:
            response = await self.chat(
                user_message=user_text,
                system_prompt=system_prompt
            )
            
            return {
                "status": "success",
                "response": response,
                "model": self.client.model,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"分析推荐失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": "抱歉，我现在遇到了一些技术问题，请稍后再试。"
            }
    
    def _get_default_system_prompt(self) -> str:
        """获取默认的系统提示词"""
        return """你是FinLoom智能投资助手，一个专业的金融投资顾问。
你的任务是帮助用户进行投资决策，提供专业的市场分析和投资建议。
请用专业但易懂的语言回答用户的问题，并在适当时候提供风险提示。"""
    
    def _get_default_requirement(self) -> Dict[str, Any]:
        """获取默认的投资需求"""
        return {
            "parsed_requirement": {
                "investment_amount": 100000,
                "risk_tolerance": "moderate",
                "investment_horizon": "medium",
                "investment_goals": ["稳健增值"],
                "constraints": [],
                "preferred_sectors": []
            },
            "strategy_params": {
                "rebalance_frequency": "weekly",
                "position_sizing_method": "equal_weight",
                "max_drawdown": 0.2,
                "position_limit": 0.1,
                "stop_loss": 0.05
            },
            "risk_params": {
                "max_drawdown": 0.2,
                "position_limit": 0.1,
                "stop_loss": 0.05
            }
        }
    
    def _get_default_strategy(self) -> Dict[str, Any]:
        """获取默认的策略方案"""
        return {
            "strategy_name": "稳健均衡策略",
            "strategy_description": "基于用户需求生成的均衡投资策略",
            "recommended_stocks": [
                {
                    "symbol": "000001",
                    "name": "平安银行",
                    "reason": "金融龙头，业绩稳定",
                    "suggested_weight": 0.25
                },
                {
                    "symbol": "600036",
                    "name": "招商银行",
                    "reason": "优质银行股，分红稳定",
                    "suggested_weight": 0.25
                },
                {
                    "symbol": "600519",
                    "name": "贵州茅台",
                    "reason": "消费龙头，长期价值",
                    "suggested_weight": 0.25
                },
                {
                    "symbol": "601318",
                    "name": "中国平安",
                    "reason": "保险龙头，估值合理",
                    "suggested_weight": 0.25
                }
            ],
            "risk_management": {
                "max_position_size": 0.25,
                "stop_loss_pct": 0.05,
                "take_profit_pct": 0.20
            },
            "expected_performance": {
                "expected_return": "8-12%年化收益",
                "risk_level": "中等",
                "holding_period": "6-12个月"
            },
            "key_points": [
                "分散投资，降低单一股票风险",
                "关注业绩稳定的龙头企业",
                "设置合理的止损止盈位"
            ]
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 全局单例
_aliyun_ai_service = None


def get_aliyun_ai_service() -> AliyunAIService:
    """获取阿里云AI服务单例"""
    global _aliyun_ai_service
    if _aliyun_ai_service is None:
        _aliyun_ai_service = AliyunAIService()
    return _aliyun_ai_service

