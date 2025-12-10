#!/usr/bin/env python3
"""自适应参数管理器 - 根据市场状态动态调整策略参数"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from common.logging_system import setup_logger

LOGGER = setup_logger("adaptive_parameter_manager")


class MarketRegime(Enum):
    """市场状态枚举"""

    BULL = "BULL"  # 牛市
    BEAR = "BEAR"  # 熊市
    VOLATILE = "VOLATILE"  # 震荡市
    NEUTRAL = "NEUTRAL"  # 中性市场


@dataclass
class AdaptiveParameters:
    """自适应参数"""

    buy_threshold: float
    sell_threshold: float
    confidence_threshold: float
    max_position: float
    max_drawdown_limit: float
    daily_loss_limit: float
    regime: str
    reason: str


class AdaptiveParameterManager:
    """自适应参数管理器

    根据市场状态、波动率、回测表现等因素动态调整策略参数
    """

    def __init__(self):
        self.parameter_history = []

    def adjust_parameters(
        self,
        market_context: Optional[Dict[str, Any]] = None,
        backtest_performance: Optional[Dict[str, float]] = None,
        risk_level: str = "MODERATE",
    ) -> AdaptiveParameters:
        """根据市场状态和回测表现动态调整参数

        Args:
            market_context: 市场上下文，包含regime、volatility等
            backtest_performance: 回测表现指标
            risk_level: 风险偏好 (CONSERVATIVE/MODERATE/AGGRESSIVE)

        Returns:
            调整后的参数
        """

        # 1. 识别市场状态
        regime = self._identify_regime(market_context)
        volatility = self._get_volatility(market_context)

        # 2. 基础参数（根据风险偏好）
        base_params = self._get_base_parameters(risk_level)

        # 3. 根据市场状态调整
        regime_adjusted = self._adjust_for_regime(base_params, regime)

        # 4. 根据波动率调整
        volatility_adjusted = self._adjust_for_volatility(regime_adjusted, volatility)

        # 5. 根据回测表现调整
        if backtest_performance:
            final_params = self._adjust_for_performance(
                volatility_adjusted, backtest_performance
            )
        else:
            final_params = volatility_adjusted

        # 6. 记录参数历史
        self.parameter_history.append(final_params)

        LOGGER.info(f"📊 Adjusted parameters for {regime.value} market:")
        LOGGER.info(f"   buy_threshold: {final_params['buy_threshold']:.4f}")
        LOGGER.info(f"   confidence: {final_params['confidence_threshold']:.2f}")
        LOGGER.info(f"   max_position: {final_params['max_position']:.2f}")
        LOGGER.info(f"   Reason: {final_params.get('reason', 'N/A')}")

        return final_params

    def _identify_regime(self, market_context: Optional[Dict]) -> MarketRegime:
        """识别市场状态"""
        if not market_context or "regime" not in market_context:
            return MarketRegime.NEUTRAL

        regime_str = market_context["regime"].get("state", "NEUTRAL").upper()

        try:
            return MarketRegime(regime_str)
        except ValueError:
            LOGGER.warning(f"Unknown regime: {regime_str}, using NEUTRAL")
            return MarketRegime.NEUTRAL

    def _get_volatility(self, market_context: Optional[Dict]) -> float:
        """获取市场波动率"""
        if not market_context:
            return 0.02  # 默认2%

        return market_context.get("volatility", 0.02)

    def _get_base_parameters(self, risk_level: str) -> Dict[str, float]:
        """根据风险偏好获取基础参数"""

        if risk_level == "CONSERVATIVE":
            return {
                "buy_threshold": 0.005,
                "sell_threshold": -0.02,
                "confidence_threshold": 0.65,
                "max_position": 0.2,
                "max_drawdown_limit": 0.08,
                "daily_loss_limit": 0.02,
            }
        elif risk_level == "AGGRESSIVE":
            return {
                "buy_threshold": -0.005,
                "sell_threshold": -0.08,
                "confidence_threshold": 0.35,
                "max_position": 0.5,
                "max_drawdown_limit": 0.25,
                "daily_loss_limit": 0.05,
            }
        else:  # MODERATE
            return {
                "buy_threshold": 0.001,  # 修复：从0.0改为0.001，确保能产生买入信号
                "sell_threshold": -0.03,
                "confidence_threshold": 0.5,
                "max_position": 0.3,
                "max_drawdown_limit": 0.15,
                "daily_loss_limit": 0.03,
            }

    def _adjust_for_regime(
        self, params: Dict[str, float], regime: MarketRegime
    ) -> Dict[str, float]:
        """根据市场状态调整参数"""

        adjusted = params.copy()
        reason_parts = []

        if regime == MarketRegime.BULL:
            # 牛市：更激进
            adjusted["buy_threshold"] -= 0.01  # 更容易买入
            adjusted["sell_threshold"] -= 0.02  # 止损放宽
            adjusted["confidence_threshold"] -= 0.1  # 降低门槛
            adjusted["max_position"] += 0.1  # 提高仓位
            reason_parts.append("牛市环境，采用激进策略")

        elif regime == MarketRegime.BEAR:
            # 熊市：更保守
            adjusted["buy_threshold"] += 0.015  # 更谨慎买入
            adjusted["sell_threshold"] += 0.01  # 止损收紧
            adjusted["confidence_threshold"] += 0.15  # 提高门槛
            adjusted["max_position"] -= 0.15  # 降低仓位
            adjusted["max_drawdown_limit"] -= 0.05  # 更严格的回撤控制
            reason_parts.append("熊市环境，采用保守策略")

        elif regime == MarketRegime.VOLATILE:
            # 震荡市：平衡但更注重风险控制
            adjusted["confidence_threshold"] += 0.05  # 提高确定性要求
            adjusted["max_position"] -= 0.05  # 稍微降低仓位
            adjusted["sell_threshold"] += 0.005  # 止损稍微收紧
            reason_parts.append("震荡市场，注重风险控制")

        else:  # NEUTRAL
            reason_parts.append("中性市场，使用基础参数")

        return adjusted

    def _adjust_for_volatility(
        self, params: Dict[str, float], volatility: float
    ) -> Dict[str, float]:
        """根据波动率调整参数"""

        adjusted = params.copy()

        if volatility > 0.04:  # 高波动（>4%）
            # 高波动时降低仓位，收紧止损
            adjusted["max_position"] *= 0.8
            adjusted["sell_threshold"] = max(adjusted["sell_threshold"], -0.025)
            adjusted["confidence_threshold"] += 0.05
            LOGGER.info(f"⚠️  High volatility ({volatility:.2%}), reducing risk")

        elif volatility < 0.01:  # 低波动（<1%）
            # 低波动时可以适当放松
            adjusted["max_position"] = min(adjusted["max_position"] * 1.1, 0.5)
            adjusted["confidence_threshold"] -= 0.03
            LOGGER.info(
                f"✅ Low volatility ({volatility:.2%}), slightly more aggressive"
            )

        return adjusted

    def _adjust_for_performance(
        self,
        params: Dict[str, float],
        performance: Dict[str, float],
    ) -> AdaptiveParameters:
        """根据回测表现调整参数"""

        adjusted = params.copy()
        reason_parts = []

        sharpe = performance.get("sharpe_ratio", 0)
        win_rate = performance.get("win_rate", 0.5)
        max_drawdown = performance.get("max_drawdown", 0)

        # 1. 根据夏普比率调整
        if sharpe < 0:
            # 夏普比率为负，策略失效
            adjusted["confidence_threshold"] += 0.15
            adjusted["max_position"] *= 0.7
            reason_parts.append(f"负夏普比率({sharpe:.2f}), 大幅收紧参数")

        elif sharpe < 0.5:
            # 夏普比率偏低
            adjusted["confidence_threshold"] += 0.08
            adjusted["max_position"] *= 0.85
            reason_parts.append(f"低夏普比率({sharpe:.2f}), 收紧参数")

        elif sharpe > 1.5:
            # 夏普比率很高，可以稍微放松
            adjusted["confidence_threshold"] = max(
                0.3, adjusted["confidence_threshold"] - 0.05
            )
            reason_parts.append(f"高夏普比率({sharpe:.2f}), 保持策略")

        # 2. 根据胜率调整
        if win_rate < 0.45:
            # 胜率太低
            adjusted["buy_threshold"] += 0.005
            adjusted["confidence_threshold"] += 0.08
            reason_parts.append(f"低胜率({win_rate:.1%}), 提高买入门槛")

        elif win_rate > 0.60:
            # 胜率很高
            adjusted["confidence_threshold"] = max(
                0.35, adjusted["confidence_threshold"] - 0.03
            )
            reason_parts.append(f"高胜率({win_rate:.1%}), 略微放松")

        # 3. 根据最大回撤调整
        if abs(max_drawdown) > 0.15:
            # 回撤过大
            adjusted["max_drawdown_limit"] = 0.12
            adjusted["daily_loss_limit"] = 0.025
            adjusted["max_position"] *= 0.8
            reason_parts.append(f"大回撤({max_drawdown:.1%}), 加强风控")

        # 构建完整的原因说明
        full_reason = "; ".join(reason_parts) if reason_parts else "基于回测表现的优化"

        return AdaptiveParameters(
            buy_threshold=adjusted["buy_threshold"],
            sell_threshold=adjusted["sell_threshold"],
            confidence_threshold=adjusted["confidence_threshold"],
            max_position=adjusted["max_position"],
            max_drawdown_limit=adjusted["max_drawdown_limit"],
            daily_loss_limit=adjusted["daily_loss_limit"],
            regime=str(self._identify_regime(None).value),
            reason=full_reason,
        )

    def get_parameter_summary(self) -> str:
        """获取参数调整历史摘要"""
        if not self.parameter_history:
            return "No parameter history"

        latest = self.parameter_history[-1]
        return f"""
参数调整摘要:
- 市场状态: {latest.regime}
- 买入阈值: {latest.buy_threshold:.4f}
- 置信度阈值: {latest.confidence_threshold:.2f}
- 最大仓位: {latest.max_position:.2f}
- 最大回撤限制: {latest.max_drawdown_limit:.1%}
- 调整原因: {latest.reason}
"""


def create_adaptive_parameter_manager() -> AdaptiveParameterManager:
    """工厂函数：创建自适应参数管理器"""
    return AdaptiveParameterManager()
