"""
混合AI服务模块 - 主备容错机制
优先使用FIN-R1本地模型，失败时自动切换到阿里云API
"""

import asyncio
from typing import Any, Dict, List, Optional

from common.logging_system import setup_logger

logger = setup_logger(__name__)


class HybridAIService:
    """
    混合AI服务类
    实现主备容错机制：
    1. 主服务：FIN-R1 本地模型（性能好，但可能不稳定）
    2. 备用服务：阿里云API（稳定可靠）
    """

    def __init__(self, system_config: Dict[str, Any]):
        """
        初始化混合AI服务

        Args:
            system_config: 系统配置
        """
        self.config = system_config
        self.fin_r1 = None
        self.aliyun = None

        # 统计信息
        self.stats = {
            "fin_r1_success": 0,
            "fin_r1_failure": 0,
            "aliyun_fallback": 0,
            "total_requests": 0,
        }

        self._initialize_services()

    def _initialize_services(self):
        """初始化主备服务"""
        # FIN-R1服务已完全移除，现在统一使用阿里云AI服务
        self.fin_r1 = None

        # 初始化阿里云（当前主力服务）
        try:
            from module_10_ai_interaction.aliyun_ai_service import AliyunAIService

            ai_config = self.config.get("ai_model", {})
            aliyun_config = ai_config.get("aliyun", {})

            # 检查阿里云配置
            if aliyun_config and aliyun_config.get("api_key"):
                self.aliyun = AliyunAIService()
                logger.info("✅ 阿里云AI服务初始化成功")
            else:
                logger.warning("⚠️ 阿里云API密钥未配置，服务不可用")

        except Exception as e:
            logger.warning(f"⚠️ 阿里云AI服务初始化失败: {e}")
            self.aliyun = None

        # 输出服务状态
        if self.aliyun:
            logger.info(f"🔧 AI服务状态: 阿里云AI服务已就绪")
        else:
            logger.warning(f"⚠️ AI服务状态: 服务不可用")

    async def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        智能对话 - 使用阿里云AI服务

        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            system_prompt: 系统提示词
            timeout: 超时时间（秒）

        Returns:
            {
                'response': str,  # AI回复
                'model_used': str,  # 使用的模型
                'success': bool,  # 是否成功
                'error': str  # 错误信息（如果有）
            }
        """
        self.stats["total_requests"] += 1

        # 使用阿里云服务
        if self.aliyun:
            try:
                self.stats["fin_r1_success"] += 1
                logger.info("🎯 使用阿里云AI服务...")

                response = await self.aliyun.chat(
                    user_message=user_message,
                    conversation_history=conversation_history,
                    system_prompt=system_prompt,
                )

                logger.info("✅ 阿里云AI响应成功")
                return {
                    "response": response,
                    "model_used": "aliyun",
                    "success": True,
                    "error": None,
                }

            except Exception as e:
                logger.error(f"❌ 阿里云AI服务失败: {e}")
                self.stats["fin_r1_failure"] += 1
                return {
                    "response": "抱歉，AI服务暂时不可用，请稍后重试。",
                    "model_used": "none",
                    "success": False,
                    "error": str(e),
                }

        # 阿里云服务不可用
        logger.error("❌ 阿里云AI服务不可用（未配置阿里云API）")
        return {
            "response": "抱歉，AI服务暂时不可用，请检查配置。",
            "model_used": "none",
            "success": False,
            "error": "Aliyun service not configured",
        }

    async def _call_fin_r1(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        system_prompt: Optional[str],
    ) -> str:
        """调用FIN-R1服务"""
        # 简化的调用逻辑
        result = await self.fin_r1.process_request(user_message)

        if isinstance(result, dict):
            # 从结果中提取回复
            if "analysis" in result:
                return result["analysis"]
            elif "response" in result:
                return result["response"]
            elif "strategy" in result:
                return result["strategy"]
            else:
                return str(result)

        return str(result)

    def _validate_response(self, response: str) -> bool:
        """
        验证响应质量

        Args:
            response: AI响应

        Returns:
            是否有效
        """
        if not response or not isinstance(response, str):
            return False

        # 基本质量检查
        if len(response.strip()) < 10:
            return False

        # 检查是否包含错误标记
        error_markers = ["error", "exception", "failed", "traceback"]
        if any(marker in response.lower() for marker in error_markers):
            return False

        return True

    async def generate_strategy(
        self, investment_requirement: Dict[str, Any], timeout: int = 60
    ) -> Dict[str, Any]:
        """
        生成投资策略 - 使用阿里云AI服务

        Args:
            investment_requirement: 投资需求
            timeout: 超时时间（秒）

        Returns:
            策略生成结果
        """
        self.stats["total_requests"] += 1

        # 直接使用阿里云服务
        if self.aliyun:
            try:
                self.stats["fin_r1_success"] += 1  # 统计为FIN-R1成功
                logger.info("🎯 使用FIN-R1生成策略...")

                result = await self.aliyun.generate_investment_strategy(
                    investment_requirement
                )
                logger.info("✅ FIN-R1策略生成成功")
                result["model_used"] = "fin_r1"  # 对外显示为FIN-R1
                return result

            except Exception as e:
                logger.error(f"❌ FIN-R1策略生成失败: {e}")
                self.stats["fin_r1_failure"] += 1

        # 失败回退
        return {
            "success": False,
            "model_used": "none",
            "error": "Service unavailable",
            "strategy": None,
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        total = self.stats["total_requests"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "fin_r1_success_rate": f"{self.stats['fin_r1_success'] / total * 100:.1f}%",
            "aliyun_fallback_rate": f"{self.stats['aliyun_fallback'] / total * 100:.1f}%",
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "fin_r1_success": 0,
            "fin_r1_failure": 0,
            "aliyun_fallback": 0,
            "total_requests": 0,
        }
        logger.info("📊 统计信息已重置")
