#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""因子评估器模块
提供全面的因子评估和分析功能。"""

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

try:
    from scipy import stats
except ImportError:
    stats = None
    logger.warning("scipy not available. Some statistical functions will be limited.")


@dataclass
class FactorEvaluationConfig:
    """因子评估配置"""

    rolling_window: int = 252  # 滚动窗口大小
    min_periods: int = 60  # 最小有效期数
    quantiles: int = 5  # 分位数数量
    forward_periods: List[int] = field(
        default_factory=lambda: [1, 5, 10, 20]
    )  # 前向期数
    risk_free_rate: float = 0.03  # 无风险利率
    benchmark_return: float = 0.08  # 基准收益率


@dataclass
class FactorEvaluationResult:
    """因子评估结果"""

    factor_name: str
    ic: float = 0.0  # 信息系数
    rank_ic: float = 0.0  # 排序信息系数
    ir: float = 0.0  # 信息比率
    ic_std: float = 0.0  # IC标准差
    ic_ir: float = 0.0  # IC信息比率
    positive_ic_ratio: float = 0.0  # 正IC比例
    ic_decay: Dict[int, float] = field(default_factory=dict)  # IC衰减
    quantile_returns: Dict[int, float] = field(default_factory=dict)  # 分位数收益
    long_short_return: float = 0.0  # 多空收益
    hit_rate: float = 0.0  # 胜率
    cumulative_returns: Optional[pd.Series] = None  # 累积收益
    max_drawdown: float = 0.0  # 最大回撤
    sharpe_ratio: float = 0.0  # 夏普比率
    calmar_ratio: float = 0.0  # 卡尔玛比率
    sample_size: int = 0  # 样本大小
    evaluation_date: str = ""  # 评估日期


class FactorEvaluator:
    """因子评估器"""

    def __init__(self, config: Optional[FactorEvaluationConfig] = None):
        """初始化因子评估器

        Args:
            config: 评估配置
        """
        self.config = config or FactorEvaluationConfig()

    def evaluate_factor(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series,
        factor_name: str = "unnamed_factor",
    ) -> FactorEvaluationResult:
        """评估因子表现

        Args:
            factor_values: 因子值序列
            forward_returns: 前向收益率序列
            factor_name: 因子名称

        Returns:
            因子评估结果
        """
        try:
            # 数据对齐
            aligned_data = self._align_data(factor_values, forward_returns)
            if aligned_data.empty:
                logger.warning(f"No valid data for factor {factor_name}")
                return FactorEvaluationResult(factor_name=factor_name)

            factor_clean = aligned_data["factor"]
            returns_clean = aligned_data["returns"]

            # 创建结果对象
            result = FactorEvaluationResult(
                factor_name=factor_name,
                sample_size=len(factor_clean),
                evaluation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            # 基础指标计算
            result.ic = self.calculate_ic(factor_clean, returns_clean)
            result.rank_ic = self.calculate_rank_ic(factor_clean, returns_clean)

            # IC稳定性分析
            stability_metrics = self.analyze_ic_stability(factor_clean, returns_clean)
            result.ic_std = stability_metrics["ic_std"]
            result.ic_ir = stability_metrics["ic_ir"]
            result.positive_ic_ratio = stability_metrics["positive_ic_ratio"]

            # IC衰减分析
            result.ic_decay = self.analyze_ic_decay(factor_clean, returns_clean)

            # 分层分析
            quantile_analysis = self.analyze_factor_quantiles(
                factor_clean, returns_clean
            )
            result.quantile_returns = quantile_analysis["quantile_returns"]
            result.long_short_return = quantile_analysis["long_short_return"]
            result.hit_rate = quantile_analysis["hit_rate"]

            # 计算信息比率
            result.ir = result.ic / (result.ic_std + 1e-8)

            # 累积收益计算
            result.cumulative_returns = self.calculate_cumulative_returns(
                factor_clean, returns_clean
            )

            # 风险指标计算
            risk_metrics = self.calculate_risk_metrics(result.cumulative_returns)
            result.max_drawdown = risk_metrics["max_drawdown"]
            result.sharpe_ratio = risk_metrics["sharpe_ratio"]
            result.calmar_ratio = risk_metrics["calmar_ratio"]

            logger.info(
                f"Factor {factor_name} evaluation completed. IC: {result.ic:.4f}, IR: {result.ir:.4f}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to evaluate factor {factor_name}: {e}")
            return FactorEvaluationResult(factor_name=factor_name)

    def calculate_ic(self, factor_values: pd.Series, returns: pd.Series) -> float:
        """计算信息系数

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            信息系数
        """
        try:
            # 过滤无效值
            valid_mask = pd.notna(factor_values) & pd.notna(returns)
            if valid_mask.sum() < 2:
                return 0.0

            factor_clean = factor_values[valid_mask]
            returns_clean = returns[valid_mask]

            # 计算相关系数
            ic = factor_clean.corr(returns_clean)
            return ic if pd.notna(ic) else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate IC: {e}")
            return 0.0

    def calculate_rank_ic(self, factor_values: pd.Series, returns: pd.Series) -> float:
        """计算排序信息系数

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            排序信息系数
        """
        try:
            # 过滤无效值
            valid_mask = pd.notna(factor_values) & pd.notna(returns)
            if valid_mask.sum() < 2:
                return 0.0

            factor_clean = factor_values[valid_mask]
            returns_clean = returns[valid_mask]

            # 计算排序相关系数
            rank_ic = stats.spearmanr(factor_clean, returns_clean)[0]
            return rank_ic if pd.notna(rank_ic) else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate Rank IC: {e}")
            return 0.0

    def analyze_ic_stability(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> Dict[str, float]:
        """分析IC稳定性

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            IC稳定性指标
        """
        try:
            # 滚动IC计算
            window = min(self.config.rolling_window, len(factor_values) // 3)
            if window < self.config.min_periods:
                window = len(factor_values)

            rolling_ics = []

            if window >= len(factor_values):
                # 如果数据不够滚动，使用全样本
                ic = self.calculate_ic(factor_values, returns)
                rolling_ics = [ic] if pd.notna(ic) else []
            else:
                # 滚动计算IC
                for i in range(window, len(factor_values) + 1):
                    factor_window = factor_values.iloc[i - window : i]
                    returns_window = returns.iloc[i - window : i]
                    ic = self.calculate_ic(factor_window, returns_window)
                    if pd.notna(ic):
                        rolling_ics.append(ic)

            if not rolling_ics:
                return {"ic_std": 0.0, "ic_ir": 0.0, "positive_ic_ratio": 0.0}

            rolling_ics = np.array(rolling_ics)

            # 计算稳定性指标
            ic_mean = np.mean(rolling_ics)
            ic_std = np.std(rolling_ics)
            ic_ir = ic_mean / (ic_std + 1e-8)
            positive_ic_ratio = (rolling_ics > 0).mean()

            return {
                "ic_std": ic_std,
                "ic_ir": ic_ir,
                "positive_ic_ratio": positive_ic_ratio,
            }

        except Exception as e:
            logger.error(f"Failed to analyze IC stability: {e}")
            return {"ic_std": 0.0, "ic_ir": 0.0, "positive_ic_ratio": 0.0}

    def analyze_ic_decay(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> Dict[int, float]:
        """分析IC衰减

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            不同周期的IC值
        """
        try:
            ic_decay = {}

            for period in self.config.forward_periods:
                # 计算前向收益
                if period <= len(returns):
                    forward_returns = returns.shift(-period)
                    ic = self.calculate_ic(factor_values, forward_returns)
                    ic_decay[period] = ic

            return ic_decay

        except Exception as e:
            logger.error(f"Failed to analyze IC decay: {e}")
            return {}

    def analyze_factor_quantiles(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> Dict[str, Union[Dict, float]]:
        """分析因子分层表现

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            分层分析结果
        """
        try:
            # 过滤无效值
            valid_mask = pd.notna(factor_values) & pd.notna(returns)
            factor_clean = factor_values[valid_mask]
            returns_clean = returns[valid_mask]

            if len(factor_clean) < self.config.quantiles:
                return {
                    "quantile_returns": {},
                    "long_short_return": 0.0,
                    "hit_rate": 0.0,
                }

            # 分位数分组
            quantile_labels = pd.qcut(
                factor_clean, q=self.config.quantiles, labels=False, duplicates="drop"
            )

            # 计算各分位数收益
            quantile_returns = {}
            for q in range(self.config.quantiles):
                mask = quantile_labels == q
                if mask.sum() > 0:
                    q_returns = returns_clean[mask].mean()
                    quantile_returns[q + 1] = q_returns

            # 多空收益 (最高分位数 - 最低分位数)
            if len(quantile_returns) >= 2:
                max_q = max(quantile_returns.keys())
                min_q = min(quantile_returns.keys())
                long_short_return = quantile_returns[max_q] - quantile_returns[min_q]
            else:
                long_short_return = 0.0

            # 计算胜率 (因子值与收益率同方向的比例)
            factor_sign = np.sign(factor_clean)
            returns_sign = np.sign(returns_clean)
            hit_rate = (factor_sign == returns_sign).mean()

            return {
                "quantile_returns": quantile_returns,
                "long_short_return": long_short_return,
                "hit_rate": hit_rate,
            }

        except Exception as e:
            logger.error(f"Failed to analyze factor quantiles: {e}")
            return {"quantile_returns": {}, "long_short_return": 0.0, "hit_rate": 0.0}

    def calculate_cumulative_returns(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> pd.Series:
        """计算因子累积收益

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            累积收益序列
        """
        try:
            # 标准化因子值作为权重
            weights = (factor_values - factor_values.mean()) / (
                factor_values.std() + 1e-8
            )

            # 计算加权收益
            weighted_returns = weights * returns

            # 计算累积收益
            cumulative_returns = (1 + weighted_returns).cumprod() - 1

            return cumulative_returns

        except Exception as e:
            logger.error(f"Failed to calculate cumulative returns: {e}")
            return pd.Series()

    def calculate_risk_metrics(self, cumulative_returns: pd.Series) -> Dict[str, float]:
        """计算风险指标

        Args:
            cumulative_returns: 累积收益序列

        Returns:
            风险指标字典
        """
        try:
            if cumulative_returns.empty:
                return {"max_drawdown": 0.0, "sharpe_ratio": 0.0, "calmar_ratio": 0.0}

            # 计算收益率
            returns = cumulative_returns.pct_change().dropna()

            if returns.empty:
                return {"max_drawdown": 0.0, "sharpe_ratio": 0.0, "calmar_ratio": 0.0}

            # 最大回撤
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(drawdown.min())

            # 夏普比率
            excess_returns = returns - self.config.risk_free_rate / 252
            sharpe_ratio = (
                excess_returns.mean() / (excess_returns.std() + 1e-8) * np.sqrt(252)
            )

            # 卡尔玛比率
            annual_return = (1 + cumulative_returns.iloc[-1]) ** (
                252 / len(cumulative_returns)
            ) - 1
            calmar_ratio = annual_return / (max_drawdown + 1e-8)

            return {
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "calmar_ratio": calmar_ratio,
            }

        except Exception as e:
            logger.error(f"Failed to calculate risk metrics: {e}")
            return {"max_drawdown": 0.0, "sharpe_ratio": 0.0, "calmar_ratio": 0.0}

    def compare_factors(
        self, factor_results: List[FactorEvaluationResult]
    ) -> pd.DataFrame:
        """比较多个因子的表现

        Args:
            factor_results: 因子评估结果列表

        Returns:
            因子比较表
        """
        try:
            if not factor_results:
                return pd.DataFrame()

            # 提取关键指标
            comparison_data = []

            for result in factor_results:
                data = {
                    "factor_name": result.factor_name,
                    "ic": result.ic,
                    "rank_ic": result.rank_ic,
                    "ir": result.ir,
                    "ic_std": result.ic_std,
                    "positive_ic_ratio": result.positive_ic_ratio,
                    "long_short_return": result.long_short_return,
                    "hit_rate": result.hit_rate,
                    "max_drawdown": result.max_drawdown,
                    "sharpe_ratio": result.sharpe_ratio,
                    "calmar_ratio": result.calmar_ratio,
                    "sample_size": result.sample_size,
                }
                comparison_data.append(data)

            comparison_df = pd.DataFrame(comparison_data)

            # 按IC排序
            comparison_df = comparison_df.sort_values("ic", ascending=False)

            logger.info(
                f"Factor comparison completed for {len(factor_results)} factors"
            )
            return comparison_df

        except Exception as e:
            logger.error(f"Failed to compare factors: {e}")
            return pd.DataFrame()

    def _align_data(self, factor_values: pd.Series, returns: pd.Series) -> pd.DataFrame:
        """数据对齐

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            对齐后的数据
        """
        try:
            # 创建DataFrame
            df = pd.DataFrame({"factor": factor_values, "returns": returns})

            # 删除缺失值
            df = df.dropna()

            return df

        except Exception as e:
            logger.error(f"Failed to align data: {e}")
            return pd.DataFrame()

    def generate_evaluation_report(self, result: FactorEvaluationResult) -> str:
        """生成评估报告

        Args:
            result: 因子评估结果

        Returns:
            评估报告文本
        """
        try:
            report = f"""
==========================================
因子评估报告: {result.factor_name}
==========================================

基础指标:
- 信息系数 (IC): {result.ic:.4f}
- 排序信息系数 (Rank IC): {result.rank_ic:.4f}
- 信息比率 (IR): {result.ir:.4f}

稳定性分析:
- IC标准差: {result.ic_std:.4f}
- IC信息比率: {result.ic_ir:.4f}
- 正IC比例: {result.positive_ic_ratio:.2%}

分层分析:
- 多空收益: {result.long_short_return:.4f}
- 胜率: {result.hit_rate:.2%}

风险指标:
- 最大回撤: {result.max_drawdown:.2%}
- 夏普比率: {result.sharpe_ratio:.4f}
- 卡尔玛比率: {result.calmar_ratio:.4f}

数据统计:
- 样本大小: {result.sample_size}
- 评估日期: {result.evaluation_date}

"""

            # 添加IC衰减分析
            if result.ic_decay:
                report += "IC衰减分析:\n"
                for period, ic in result.ic_decay.items():
                    report += f"- {period}期IC: {ic:.4f}\n"
                report += "\n"

            # 添加分位数收益
            if result.quantile_returns:
                report += "分位数收益:\n"
                for q, ret in result.quantile_returns.items():
                    report += f"- Q{q}: {ret:.4f}\n"
                report += "\n"

            report += "==========================================\n"

            return report

        except Exception as e:
            logger.error(f"Failed to generate evaluation report: {e}")
            return f"Error generating report for factor {result.factor_name}"


# 便捷函数
def evaluate_factor(
    factor_values: pd.Series,
    forward_returns: pd.Series,
    factor_name: str = "unnamed_factor",
    config: Optional[FactorEvaluationConfig] = None,
) -> FactorEvaluationResult:
    """评估因子的便捷函数

    Args:
        factor_values: 因子值
        forward_returns: 前向收益率
        factor_name: 因子名称
        config: 评估配置

    Returns:
        因子评估结果
    """
    evaluator = FactorEvaluator(config)
    return evaluator.evaluate_factor(factor_values, forward_returns, factor_name)
