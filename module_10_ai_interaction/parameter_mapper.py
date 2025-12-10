"""
参数映射器模块
负责将用户需求映射到系统参数
"""

from typing import Any, Dict, List, Optional

from common.logging_system import setup_logger
from module_10_ai_interaction.requirement_parser import (
    InvestmentHorizon,
    ParsedRequirement,
    RiskTolerance,
)

logger = setup_logger("parameter_mapper")


class ParameterMapper:
    """参数映射器类"""

    # 风险参数映射表
    RISK_PARAMETER_MAP = {
        RiskTolerance.CONSERVATIVE: {
            "max_drawdown": 0.08,
            "position_limit": 0.05,
            "leverage": 1.0,
            "stop_loss": 0.03,
            "max_position_count": 30,
            "min_position_count": 20,
            "concentration_limit": 0.15,
        },
        RiskTolerance.MODERATE: {
            "max_drawdown": 0.15,
            "position_limit": 0.1,
            "leverage": 1.0,
            "stop_loss": 0.05,
            "max_position_count": 25,
            "min_position_count": 15,
            "concentration_limit": 0.25,
        },
        RiskTolerance.AGGRESSIVE: {
            "max_drawdown": 0.25,
            "position_limit": 0.15,
            "leverage": 1.5,
            "stop_loss": 0.08,
            "max_position_count": 20,
            "min_position_count": 10,
            "concentration_limit": 0.35,
        },
        RiskTolerance.VERY_AGGRESSIVE: {
            "max_drawdown": 0.35,
            "position_limit": 0.2,
            "leverage": 2.0,
            "stop_loss": 0.10,
            "max_position_count": 15,
            "min_position_count": 5,
            "concentration_limit": 0.50,
        },
    }

    # 策略参数映射表
    STRATEGY_PARAMETER_MAP = {
        RiskTolerance.CONSERVATIVE: {
            "strategy_mix": {
                "value": 0.5,
                "mean_reversion": 0.3,
                "trend_following": 0.1,
                "momentum": 0.1,
            },
            "rebalance_frequency": "monthly",
            "trading_frequency": "low",
        },
        RiskTolerance.MODERATE: {
            "strategy_mix": {
                "value": 0.3,
                "mean_reversion": 0.3,
                "trend_following": 0.2,
                "momentum": 0.2,
            },
            "rebalance_frequency": "weekly",
            "trading_frequency": "medium",
        },
        RiskTolerance.AGGRESSIVE: {
            "strategy_mix": {
                "momentum": 0.35,
                "trend_following": 0.35,
                "mean_reversion": 0.2,
                "value": 0.1,
            },
            "rebalance_frequency": "daily",
            "trading_frequency": "high",
        },
        RiskTolerance.VERY_AGGRESSIVE: {
            "strategy_mix": {
                "momentum": 0.5,
                "trend_following": 0.3,
                "mean_reversion": 0.15,
                "value": 0.05,
            },
            "rebalance_frequency": "intraday",
            "trading_frequency": "very_high",
        },
    }

    # 时间参数映射表
    HORIZON_PARAMETER_MAP = {
        InvestmentHorizon.SHORT_TERM: {
            "min_holding_period": 1,
            "max_holding_period": 60,
            "optimization_horizon": 60,
            "lookback_period": 20,
        },
        InvestmentHorizon.MEDIUM_TERM: {
            "min_holding_period": 5,
            "max_holding_period": 252,
            "optimization_horizon": 252,
            "lookback_period": 60,
        },
        InvestmentHorizon.LONG_TERM: {
            "min_holding_period": 20,
            "max_holding_period": 1260,
            "optimization_horizon": 504,
            "lookback_period": 120,
        },
        InvestmentHorizon.VERY_LONG_TERM: {
            "min_holding_period": 60,
            "max_holding_period": 2520,
            "optimization_horizon": 1260,
            "lookback_period": 252,
        },
    }

    def __init__(self):
        """初始化参数映射器"""
        pass

    def map_to_system_parameters(
        self, parsed_requirement: ParsedRequirement
    ) -> Dict[str, Any]:
        """将解析后的需求映射到系统参数

        Args:
            parsed_requirement: 解析后的需求

        Returns:
            系统参数字典
        """
        system_params = {
            "risk_params": {},
            "strategy_params": {},
            "horizon_params": {},
            "optimization_params": {},
            "execution_params": {},
            "asset_params": {},
        }

        # 映射风险参数
        if parsed_requirement.risk_tolerance:
            system_params["risk_params"] = self._map_risk_parameters(
                parsed_requirement.risk_tolerance
            )

            # 映射策略参数
            system_params["strategy_params"] = self._map_strategy_parameters(
                parsed_requirement.risk_tolerance
            )

        # 映射时间参数
        if parsed_requirement.investment_horizon:
            system_params["horizon_params"] = self._map_horizon_parameters(
                parsed_requirement.investment_horizon
            )

        # 映射优化目标
        system_params["optimization_params"] = self._map_optimization_parameters(
            parsed_requirement
        )

        # 映射执行参数
        system_params["execution_params"] = self._map_execution_parameters(
            parsed_requirement
        )

        # 映射资产偏好
        system_params["asset_params"] = self._map_asset_parameters(parsed_requirement)

        # 应用约束
        self._apply_constraints(system_params, parsed_requirement)

        # 应用投资金额
        if parsed_requirement.investment_amount:
            system_params["investment_amount"] = parsed_requirement.investment_amount

        # 应用回测日期
        if parsed_requirement.backtest_start_date:
            system_params["backtest_start_date"] = (
                parsed_requirement.backtest_start_date
            )
        if parsed_requirement.backtest_end_date:
            system_params["backtest_end_date"] = parsed_requirement.backtest_end_date

        logger.info("Mapped user requirements to system parameters")

        return system_params

    def map_to_module_parameters(
        self, system_params: Dict[str, Any], target_module: str
    ) -> Dict[str, Any]:
        """将系统参数映射到特定模块的参数

        Args:
            system_params: 系统参数
            target_module: 目标模块名称

        Returns:
            模块参数字典
        """
        if target_module == "module_03_ai_models":
            return self._map_to_ai_model_params(system_params)
        elif target_module == "module_05_risk_management":
            return self._map_to_risk_management_params(system_params)
        elif target_module == "module_07_optimization":
            return self._map_to_optimization_params(system_params)
        elif target_module == "module_08_execution":
            return self._map_to_execution_params(system_params)
        elif target_module == "module_09_backtesting":
            return self._map_to_backtest_params(system_params)
        else:
            logger.warning(f"Unknown target module: {target_module}")
            return system_params

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证参数有效性

        Args:
            parameters: 参数字典

        Returns:
            (是否有效, 问题列表)
        """
        issues = []

        # 检查风险参数
        risk_params = parameters.get("risk_params", {})
        if risk_params.get("max_drawdown", 0) > 0.5:
            issues.append("最大回撤限制过高（>50%）")

        if risk_params.get("leverage", 1) > 3:
            issues.append("杠杆倍数过高（>3倍）")

        # 检查策略参数
        strategy_params = parameters.get("strategy_params", {})
        strategy_mix = strategy_params.get("strategy_mix", {})
        total_weight = sum(strategy_mix.values())
        if abs(total_weight - 1.0) > 0.01:
            issues.append(f"策略权重之和不为1: {total_weight:.3f}")

        # 检查时间参数
        horizon_params = parameters.get("horizon_params", {})
        min_holding = horizon_params.get("min_holding_period", 0)
        max_holding = horizon_params.get("max_holding_period", float("inf"))
        if min_holding > max_holding:
            issues.append("最小持仓期限大于最大持仓期限")

        is_valid = len(issues) == 0
        return is_valid, issues

    def _map_risk_parameters(self, risk_tolerance: RiskTolerance) -> Dict[str, Any]:
        """映射风险参数

        Args:
            risk_tolerance: 风险承受能力

        Returns:
            风险参数字典
        """
        return self.RISK_PARAMETER_MAP.get(
            risk_tolerance, self.RISK_PARAMETER_MAP[RiskTolerance.MODERATE]
        ).copy()

    def _map_strategy_parameters(self, risk_tolerance: RiskTolerance) -> Dict[str, Any]:
        """映射策略参数

        Args:
            risk_tolerance: 风险承受能力

        Returns:
            策略参数字典
        """
        return self.STRATEGY_PARAMETER_MAP.get(
            risk_tolerance, self.STRATEGY_PARAMETER_MAP[RiskTolerance.MODERATE]
        ).copy()

    def _map_horizon_parameters(
        self, investment_horizon: InvestmentHorizon
    ) -> Dict[str, Any]:
        """映射时间参数

        Args:
            investment_horizon: 投资期限

        Returns:
            时间参数字典
        """
        return self.HORIZON_PARAMETER_MAP.get(
            investment_horizon,
            self.HORIZON_PARAMETER_MAP[InvestmentHorizon.MEDIUM_TERM],
        ).copy()

    def _map_optimization_parameters(
        self, parsed_requirement: ParsedRequirement
    ) -> Dict[str, Any]:
        """映射优化参数

        Args:
            parsed_requirement: 解析后的需求

        Returns:
            优化参数字典
        """
        # 根据投资目标设置优化目标
        primary_objective = "sharpe_ratio"  # 默认

        if parsed_requirement.investment_goals:
            first_goal = parsed_requirement.investment_goals[0]
            if first_goal.goal_type == "wealth_growth":
                primary_objective = "return"
            elif first_goal.goal_type == "income":
                primary_objective = "dividend_yield"
            elif first_goal.goal_type == "preservation":
                primary_objective = "volatility"

        return {
            "primary_objective": primary_objective,
            "secondary_objectives": ["max_drawdown", "volatility"],
            "constraints": {
                "max_turnover": 2.0,
                "max_concentration": 0.3,
            },
        }

    def _map_execution_parameters(
        self, parsed_requirement: ParsedRequirement
    ) -> Dict[str, Any]:
        """映射执行参数

        Args:
            parsed_requirement: 解析后的需求

        Returns:
            执行参数字典
        """
        # 根据流动性要求设置执行参数
        has_liquidity_constraint = any(
            c.constraint_type == "liquidity" for c in parsed_requirement.constraints
        )

        return {
            "order_type": "limit" if has_liquidity_constraint else "market",
            "execution_algo": "vwap",
            "urgency": "low" if has_liquidity_constraint else "normal",
            "max_participation_rate": 0.05 if has_liquidity_constraint else 0.1,
            "slippage_tolerance": 0.001,
        }

    def _map_asset_parameters(
        self, parsed_requirement: ParsedRequirement
    ) -> Dict[str, Any]:
        """映射资产参数

        Args:
            parsed_requirement: 解析后的需求

        Returns:
            资产参数字典
        """
        return {
            "preferred_assets": parsed_requirement.preferred_assets,
            "excluded_assets": parsed_requirement.excluded_assets,
            "target_sectors": parsed_requirement.target_sectors,
            "excluded_sectors": parsed_requirement.excluded_sectors,
            "market": "A股",  # 默认A股
            "asset_types": ["stock"],  # 默认股票
        }

    def _apply_constraints(
        self, system_params: Dict[str, Any], parsed_requirement: ParsedRequirement
    ):
        """应用约束条件

        Args:
            system_params: 系统参数
            parsed_requirement: 解析后的需求
        """
        for constraint in parsed_requirement.constraints:
            if constraint.constraint_type == "leverage":
                system_params["risk_params"]["leverage"] = constraint.constraint_value

            elif constraint.constraint_type == "liquidity":
                system_params["execution_params"]["min_liquidity"] = (
                    constraint.constraint_value
                )

            elif constraint.constraint_type == "esg":
                system_params["asset_params"]["esg_filter"] = (
                    constraint.constraint_value
                )

            elif constraint.constraint_type == "exclusion":
                if "exclusions" not in system_params:
                    system_params["exclusions"] = []
                system_params["exclusions"].append(constraint.constraint_value)

        # 应用最大回撤限制
        if parsed_requirement.max_drawdown:
            system_params["risk_params"]["max_drawdown"] = (
                parsed_requirement.max_drawdown
            )

    def _map_to_ai_model_params(self, system_params: Dict[str, Any]) -> Dict[str, Any]:
        """映射到AI模型参数"""
        return {
            "lookback_period": system_params.get("horizon_params", {}).get(
                "lookback_period", 60
            ),
            "prediction_horizon": 5,
            "features": [
                "price",
                "volume",
                "technical_indicators",
                "fundamental_factors",
            ],
        }

    def _map_to_risk_management_params(
        self, system_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """映射到风险管理参数"""
        return {
            "risk_limits": system_params.get("risk_params", {}),
            "portfolio_constraints": {
                "max_position_count": system_params.get("risk_params", {}).get(
                    "max_position_count", 20
                ),
                "concentration_limit": system_params.get("risk_params", {}).get(
                    "concentration_limit", 0.25
                ),
            },
        }

    def _map_to_optimization_params(
        self, system_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """映射到优化参数"""
        return system_params.get("optimization_params", {})

    def _map_to_execution_params(self, system_params: Dict[str, Any]) -> Dict[str, Any]:
        """映射到执行参数"""
        return system_params.get("execution_params", {})

    def _map_to_backtest_params(self, system_params: Dict[str, Any]) -> Dict[str, Any]:
        """映射到回测参数"""
        return {
            "start_date": system_params.get("backtest_start_date"),  # 从用户需求提取
            "end_date": system_params.get("backtest_end_date"),  # 从用户需求提取
            "initial_capital": system_params.get("investment_amount", 1000000),
            "benchmark": "000300",  # 沪深300
            "commission": 0.0003,
            "slippage": 0.001,
        }


# 模块级别函数
def create_parameter_mapper() -> ParameterMapper:
    """创建参数映射器实例

    Returns:
        参数映射器实例
    """
    return ParameterMapper()


def map_requirement_to_parameters(
    parsed_requirement: ParsedRequirement,
) -> Dict[str, Any]:
    """映射需求到参数的便捷函数

    Args:
        parsed_requirement: 解析后的需求

    Returns:
        系统参数字典
    """
    mapper = ParameterMapper()
    return mapper.map_to_system_parameters(parsed_requirement)
