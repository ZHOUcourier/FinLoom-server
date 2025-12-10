"""
VaR (Value at Risk) 计算器
计算投资组合的风险价值
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from scipy import stats

from common.logging_system import setup_logger

LOGGER = setup_logger("var_calculator")


class VaRMethod(Enum):
    """VaR计算方法"""

    HISTORICAL = "historical"  # 历史模拟法
    PARAMETRIC = "parametric"  # 参数法(方差-协方差)
    MONTE_CARLO = "monte_carlo"  # 蒙特卡洛模拟


class VaRCalculator:
    """VaR计算器

    计算不同置信水平下的风险价值(VaR)和条件风险价值(CVaR)
    """

    def __init__(self):
        """初始化VaR计算器"""
        LOGGER.info("📊 VaR计算器初始化完成")

    def calculate_var(
        self,
        returns: Union[pd.Series, np.ndarray, List[float]],
        confidence_level: float = 0.95,
        method: VaRMethod = VaRMethod.HISTORICAL,
        portfolio_value: float = 1.0,
        time_horizon: int = 1,
    ) -> Dict[str, float]:
        """计算VaR

        Args:
            returns: 收益率序列
            confidence_level: 置信水平 (0.90, 0.95, 0.99)
            method: 计算方法
            portfolio_value: 投资组合价值
            time_horizon: 时间跨度（天）

        Returns:
            包含VaR和CVaR的字典
        """
        try:
            # 转换为numpy数组
            if isinstance(returns, (pd.Series, list)):
                returns = np.array(returns)

            # 过滤无效值
            returns = returns[~np.isnan(returns)]

            if len(returns) < 30:
                LOGGER.warning("⚠️ 数据点过少，VaR计算可能不准确")

            # 根据方法计算VaR
            if method == VaRMethod.HISTORICAL:
                var = self._historical_var(returns, confidence_level)
            elif method == VaRMethod.PARAMETRIC:
                var = self._parametric_var(returns, confidence_level)
            elif method == VaRMethod.MONTE_CARLO:
                var = self._monte_carlo_var(returns, confidence_level)
            else:
                raise ValueError(f"不支持的方法: {method}")

            # 计算CVaR (条件VaR)
            cvar = self._calculate_cvar(returns, var)

            # 调整时间跨度
            var_adjusted = var * np.sqrt(time_horizon)
            cvar_adjusted = cvar * np.sqrt(time_horizon)

            # 转换为金额
            var_amount = portfolio_value * abs(var_adjusted)
            cvar_amount = portfolio_value * abs(cvar_adjusted)

            result = {
                "var": var,  # VaR (比例)
                "cvar": cvar,  # CVaR (比例)
                "var_adjusted": var_adjusted,  # 调整时间跨度后的VaR
                "cvar_adjusted": cvar_adjusted,  # 调整时间跨度后的CVaR
                "var_amount": var_amount,  # VaR金额
                "cvar_amount": cvar_amount,  # CVaR金额
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "method": method.value,
                "portfolio_value": portfolio_value,
            }

            LOGGER.info(
                f"✅ VaR计算完成: "
                f"VaR={var:.4f} ({var_amount:,.2f}), "
                f"CVaR={cvar:.4f} ({cvar_amount:,.2f})"
            )

            return result

        except Exception as e:
            LOGGER.error(f"❌ VaR计算失败: {e}", exc_info=True)
            return {"var": 0.0, "cvar": 0.0, "error": str(e)}

    def _historical_var(self, returns: np.ndarray, confidence_level: float) -> float:
        """历史模拟法计算VaR

        最简单直观的方法，直接使用历史收益率的分位数
        """
        percentile = (1 - confidence_level) * 100
        var = np.percentile(returns, percentile)
        return float(var)

    def _parametric_var(self, returns: np.ndarray, confidence_level: float) -> float:
        """参数法计算VaR

        假设收益率服从正态分布
        """
        mean = np.mean(returns)
        std = np.std(returns)

        # 获取置信水平对应的z值
        z_score = stats.norm.ppf(1 - confidence_level)

        # VaR = μ + z*σ
        var = mean + z_score * std
        return float(var)

    def _monte_carlo_var(
        self, returns: np.ndarray, confidence_level: float, n_simulations: int = 10000
    ) -> float:
        """蒙特卡洛模拟法计算VaR

        通过大量模拟生成收益率分布
        """
        mean = np.mean(returns)
        std = np.std(returns)

        # 生成模拟收益率
        simulated_returns = np.random.normal(mean, std, n_simulations)

        # 计算VaR
        percentile = (1 - confidence_level) * 100
        var = np.percentile(simulated_returns, percentile)
        return float(var)

    def _calculate_cvar(self, returns: np.ndarray, var: float) -> float:
        """计算CVaR (条件VaR / 期望损失)

        CVaR是损失超过VaR的条件期望
        """
        # 找出所有损失超过VaR的情况
        tail_losses = returns[returns <= var]

        if len(tail_losses) > 0:
            cvar = np.mean(tail_losses)
        else:
            cvar = var

        return float(cvar)

    def calculate_marginal_var(
        self,
        portfolio_returns: pd.DataFrame,
        weights: np.ndarray,
        confidence_level: float = 0.95,
    ) -> Dict[str, float]:
        """计算边际VaR

        衡量每个资产对组合VaR的贡献

        Args:
            portfolio_returns: 各资产收益率 (DataFrame)
            weights: 资产权重
            confidence_level: 置信水平

        Returns:
            各资产的边际VaR
        """
        try:
            # 计算组合收益率
            portfolio_return = np.dot(portfolio_returns, weights)

            # 计算组合VaR
            portfolio_var = self.calculate_var(
                portfolio_return, confidence_level, VaRMethod.HISTORICAL
            )["var"]

            # 计算每个资产的边际VaR
            marginal_vars = {}

            for i, column in enumerate(portfolio_returns.columns):
                # 微小扰动
                delta = 0.01
                new_weights = weights.copy()
                new_weights[i] += delta
                new_weights = new_weights / np.sum(new_weights)  # 重新归一化

                # 计算新的VaR
                new_return = np.dot(portfolio_returns, new_weights)
                new_var = self.calculate_var(
                    new_return, confidence_level, VaRMethod.HISTORICAL
                )["var"]

                # 边际VaR
                marginal_var = (new_var - portfolio_var) / delta
                marginal_vars[column] = float(marginal_var)

            LOGGER.info(f"✅ 边际VaR计算完成: {len(marginal_vars)}个资产")

            return marginal_vars

        except Exception as e:
            LOGGER.error(f"❌ 边际VaR计算失败: {e}", exc_info=True)
            return {}

    def calculate_component_var(
        self,
        portfolio_returns: pd.DataFrame,
        weights: np.ndarray,
        confidence_level: float = 0.95,
    ) -> Dict[str, float]:
        """计算成分VaR

        将组合VaR分解为各资产的贡献

        Args:
            portfolio_returns: 各资产收益率 (DataFrame)
            weights: 资产权重
            confidence_level: 置信水平

        Returns:
            各资产的成分VaR
        """
        try:
            # 计算协方差矩阵
            cov_matrix = portfolio_returns.cov()

            # 计算组合标准差
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)

            # 获取z值
            z_score = abs(stats.norm.ppf(1 - confidence_level))

            # 组合VaR
            portfolio_var = z_score * portfolio_std

            # 计算每个资产的成分VaR
            component_vars = {}

            for i, column in enumerate(portfolio_returns.columns):
                # 资产i对组合方差的贡献
                marginal_contribution = (
                    np.dot(cov_matrix.iloc[i], weights) / portfolio_std
                )

                # 成分VaR = 权重 * 边际贡献 * VaR
                component_var = weights[i] * marginal_contribution * portfolio_var
                component_vars[column] = float(component_var)

            LOGGER.info(f"✅ 成分VaR计算完成: {len(component_vars)}个资产")

            return component_vars

        except Exception as e:
            LOGGER.error(f"❌ 成分VaR计算失败: {e}", exc_info=True)
            return {}

    def backtest_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        window_size: int = 252,
        method: VaRMethod = VaRMethod.HISTORICAL,
    ) -> Dict:
        """回测VaR模型

        检验VaR模型的准确性

        Args:
            returns: 收益率序列
            confidence_level: 置信水平
            window_size: 滚动窗口大小
            method: 计算方法

        Returns:
            回测结果
        """
        try:
            violations = 0
            total_obs = 0
            var_series = []

            for i in range(window_size, len(returns)):
                # 使用历史数据计算VaR
                historical_returns = returns[i - window_size : i].values

                var_result = self.calculate_var(
                    historical_returns, confidence_level, method
                )
                var = var_result["var"]
                var_series.append(var)

                # 检查是否违反VaR
                actual_return = returns.iloc[i]
                if actual_return < var:
                    violations += 1

                total_obs += 1

            # 计算违反率
            violation_rate = violations / total_obs if total_obs > 0 else 0
            expected_violation_rate = 1 - confidence_level

            # Kupiec检验 (似然比检验)
            if violations > 0 and violations < total_obs:
                lr_stat = -2 * (
                    np.log(
                        (expected_violation_rate**violations)
                        * ((1 - expected_violation_rate) ** (total_obs - violations))
                    )
                    - np.log(
                        (violation_rate**violations)
                        * ((1 - violation_rate) ** (total_obs - violations))
                    )
                )
                p_value = 1 - stats.chi2.cdf(lr_stat, df=1)
            else:
                lr_stat = 0
                p_value = 1

            result = {
                "violations": violations,
                "total_observations": total_obs,
                "violation_rate": violation_rate,
                "expected_violation_rate": expected_violation_rate,
                "kupiec_lr_stat": lr_stat,
                "kupiec_p_value": p_value,
                "model_adequate": p_value > 0.05,  # 5%显著性水平
                "var_series": var_series,
            }

            LOGGER.info(
                f"✅ VaR回测完成: "
                f"违反率={violation_rate:.2%} (预期={expected_violation_rate:.2%}), "
                f"模型{'充分' if result['model_adequate'] else '不充分'}"
            )

            return result

        except Exception as e:
            LOGGER.error(f"❌ VaR回测失败: {e}", exc_info=True)
            return {"error": str(e)}


# 全局单例
_calculator_instance = None


def get_var_calculator() -> VaRCalculator:
    """获取VaR计算器单例"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = VaRCalculator()
    return _calculator_instance
