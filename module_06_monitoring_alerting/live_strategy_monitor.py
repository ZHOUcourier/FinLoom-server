"""
实盘运行监控器 - Module 06扩展
实时监控策略运行状态、风险指标和性能
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from common.logging_system import setup_logger
from module_06_monitoring_alerting.real_time_monitoring.performance_tracker import (
    PerformanceTracker,
)

LOGGER = setup_logger("live_strategy_monitor")


@dataclass
class StrategyMetrics:
    """策略运行指标"""

    strategy_id: str
    timestamp: datetime
    # 收益指标
    total_return: float
    daily_return: float
    sharpe_ratio: float
    max_drawdown: float
    # 风险指标
    volatility: float
    var_95: float
    cvar_95: float
    beta: float
    # 交易指标
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    # 持仓指标
    position_count: int
    total_exposure: float
    cash_ratio: float
    # 状态
    health_score: float  # 0-100
    risk_level: str  # low/medium/high/critical


@dataclass
class RiskAlert:
    """风险告警"""

    alert_id: str
    strategy_id: str
    timestamp: datetime
    alert_type: str  # drawdown/loss/volatility/exposure
    severity: str  # low/medium/high/critical
    current_value: float
    threshold: float
    message: str
    requires_action: bool


class LiveStrategyMonitor:
    """实盘策略监控器

    功能:
    1. 实时监控策略运行状态
    2. 计算关键风险指标
    3. 检测异常和风险
    4. 生成告警
    """

    def __init__(self):
        """初始化监控器"""
        self.tracker = PerformanceTracker()
        self.metrics_history: Dict[str, List[StrategyMetrics]] = {}
        self.active_alerts: Dict[str, List[RiskAlert]] = {}
        LOGGER.info("📊 实盘策略监控器初始化完成")

    def monitor_strategy(
        self,
        strategy_id: str,
        account_status: Dict,
        positions: Dict,
        market_data: Optional[pd.DataFrame] = None,
    ) -> tuple[StrategyMetrics, List[RiskAlert]]:
        """监控策略状态

        Args:
            strategy_id: 策略ID
            account_status: 账户状态
            positions: 持仓信息
            market_data: 市场数据

        Returns:
            (metrics, alerts)
        """
        try:
            with self.tracker.track("monitor_strategy"):
                # 1. 计算指标
                metrics = self._calculate_metrics(
                    strategy_id, account_status, positions, market_data
                )

                # 2. 检测风险
                alerts = self._detect_risks(metrics, account_status)

                # 3. 保存历史
                if strategy_id not in self.metrics_history:
                    self.metrics_history[strategy_id] = []
                self.metrics_history[strategy_id].append(metrics)

                # 保留最近1000条
                if len(self.metrics_history[strategy_id]) > 1000:
                    self.metrics_history[strategy_id] = self.metrics_history[
                        strategy_id
                    ][-1000:]

                # 4. 保存告警
                if alerts:
                    if strategy_id not in self.active_alerts:
                        self.active_alerts[strategy_id] = []
                    self.active_alerts[strategy_id].extend(alerts)

                    LOGGER.warning(f"⚠️ 检测到 {len(alerts)} 个风险告警")

                return metrics, alerts

        except Exception as e:
            LOGGER.error(f"❌ 监控策略失败: {e}", exc_info=True)
            return None, []

    def _calculate_metrics(
        self,
        strategy_id: str,
        account_status: Dict,
        positions: Dict,
        market_data: Optional[pd.DataFrame],
    ) -> StrategyMetrics:
        """计算策略指标"""

        # 收益指标
        total_return = account_status.get("total_return", 0.0)
        daily_return = account_status.get("daily_return", 0.0)

        # 获取历史收益
        history = self.metrics_history.get(strategy_id, [])
        returns = [m.daily_return for m in history[-30:]]  # 最近30天

        if len(returns) > 1:
            returns_array = np.array(returns)

            # 夏普比率
            if np.std(returns_array) > 0:
                sharpe_ratio = (
                    np.mean(returns_array) / np.std(returns_array) * np.sqrt(252)
                )
            else:
                sharpe_ratio = 0.0

            # 最大回撤
            cumulative = (1 + returns_array).cumprod()
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = float(np.min(drawdown))

            # 波动率
            volatility = float(np.std(returns_array) * np.sqrt(252))

            # VaR和CVaR (95%置信度)
            var_95 = float(np.percentile(returns_array, 5))
            cvar_95 = float(np.mean(returns_array[returns_array <= var_95]))

        else:
            sharpe_ratio = 0.0
            max_drawdown = 0.0
            volatility = 0.0
            var_95 = 0.0
            cvar_95 = 0.0

        # Beta (简化计算，假设市场收益率为0.0001/天)
        if len(returns) > 10:
            market_returns = np.random.normal(0.0001, 0.02, len(returns))  # 模拟市场
            covariance = np.cov(returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)
            beta = covariance / market_variance if market_variance > 0 else 1.0
        else:
            beta = 1.0

        # 交易指标
        win_rate = 0.0
        profit_factor = 0.0
        avg_win = 0.0
        avg_loss = 0.0

        if history:
            wins = [m.daily_return for m in history if m.daily_return > 0]
            losses = [m.daily_return for m in history if m.daily_return < 0]

            if len(history) > 0:
                win_rate = len(wins) / len(history)

            if wins:
                avg_win = np.mean(wins)
            if losses:
                avg_loss = np.mean(losses)
                if avg_loss != 0:
                    profit_factor = abs(avg_win / avg_loss) if avg_win else 0.0

        # 持仓指标
        position_count = len(positions)
        total_assets = account_status.get("total_assets", 0)
        position_value = account_status.get("position_value", 0)
        cash = account_status.get("available_cash", 0)

        total_exposure = position_value / total_assets if total_assets > 0 else 0.0
        cash_ratio = cash / total_assets if total_assets > 0 else 1.0

        # 健康评分 (0-100)
        health_score = self._calculate_health_score(
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            volatility=volatility,
            win_rate=win_rate,
            total_exposure=total_exposure,
        )

        # 风险等级
        risk_level = self._calculate_risk_level(
            volatility=volatility,
            max_drawdown=max_drawdown,
            total_exposure=total_exposure,
            var_95=var_95,
        )

        return StrategyMetrics(
            strategy_id=strategy_id,
            timestamp=datetime.now(),
            total_return=total_return,
            daily_return=daily_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            volatility=volatility,
            var_95=var_95,
            cvar_95=cvar_95,
            beta=beta,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            position_count=position_count,
            total_exposure=total_exposure,
            cash_ratio=cash_ratio,
            health_score=health_score,
            risk_level=risk_level,
        )

    def _detect_risks(
        self, metrics: StrategyMetrics, account_status: Dict
    ) -> List[RiskAlert]:
        """检测风险"""
        alerts = []

        # 1. 回撤告警
        if metrics.max_drawdown < -0.15:  # 回撤超过15%
            severity = "critical" if metrics.max_drawdown < -0.20 else "high"
            alerts.append(
                RiskAlert(
                    alert_id=f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_drawdown",
                    strategy_id=metrics.strategy_id,
                    timestamp=datetime.now(),
                    alert_type="drawdown",
                    severity=severity,
                    current_value=metrics.max_drawdown,
                    threshold=-0.15,
                    message=f"最大回撤 {metrics.max_drawdown:.2%} 超过阈值",
                    requires_action=severity == "critical",
                )
            )

        # 2. 单日亏损告警
        if metrics.daily_return < -0.03:  # 单日亏损超过3%
            severity = "critical" if metrics.daily_return < -0.05 else "high"
            alerts.append(
                RiskAlert(
                    alert_id=f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_loss",
                    strategy_id=metrics.strategy_id,
                    timestamp=datetime.now(),
                    alert_type="loss",
                    severity=severity,
                    current_value=metrics.daily_return,
                    threshold=-0.03,
                    message=f"单日亏损 {metrics.daily_return:.2%} 超过阈值",
                    requires_action=severity == "critical",
                )
            )

        # 3. 波动率告警
        if metrics.volatility > 0.30:  # 年化波动率超过30%
            severity = "high" if metrics.volatility > 0.40 else "medium"
            alerts.append(
                RiskAlert(
                    alert_id=f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_volatility",
                    strategy_id=metrics.strategy_id,
                    timestamp=datetime.now(),
                    alert_type="volatility",
                    severity=severity,
                    current_value=metrics.volatility,
                    threshold=0.30,
                    message=f"波动率 {metrics.volatility:.2%} 过高",
                    requires_action=False,
                )
            )

        # 4. 仓位告警
        if metrics.total_exposure > 0.90:  # 仓位超过90%
            severity = "medium"
            alerts.append(
                RiskAlert(
                    alert_id=f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_exposure",
                    strategy_id=metrics.strategy_id,
                    timestamp=datetime.now(),
                    alert_type="exposure",
                    severity=severity,
                    current_value=metrics.total_exposure,
                    threshold=0.90,
                    message=f"总仓位 {metrics.total_exposure:.2%} 过高",
                    requires_action=False,
                )
            )

        # 5. VaR告警
        if metrics.var_95 < -0.05:  # VaR超过-5%
            severity = "high"
            alerts.append(
                RiskAlert(
                    alert_id=f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_var",
                    strategy_id=metrics.strategy_id,
                    timestamp=datetime.now(),
                    alert_type="var",
                    severity=severity,
                    current_value=metrics.var_95,
                    threshold=-0.05,
                    message=f"VaR(95%) {metrics.var_95:.2%} 风险过高",
                    requires_action=False,
                )
            )

        return alerts

    def _calculate_health_score(
        self,
        sharpe_ratio: float,
        max_drawdown: float,
        volatility: float,
        win_rate: float,
        total_exposure: float,
    ) -> float:
        """计算健康评分 (0-100)"""

        score = 50  # 基础分

        # 夏普比率 (+/- 20分)
        if sharpe_ratio > 2.0:
            score += 20
        elif sharpe_ratio > 1.5:
            score += 15
        elif sharpe_ratio > 1.0:
            score += 10
        elif sharpe_ratio > 0.5:
            score += 5
        elif sharpe_ratio < 0:
            score -= 20

        # 最大回撤 (+/- 20分)
        if max_drawdown > -0.05:
            score += 20
        elif max_drawdown > -0.10:
            score += 10
        elif max_drawdown > -0.15:
            score += 0
        elif max_drawdown > -0.20:
            score -= 10
        else:
            score -= 20

        # 波动率 (+/- 10分)
        if volatility < 0.15:
            score += 10
        elif volatility < 0.25:
            score += 5
        elif volatility > 0.40:
            score -= 10

        # 胜率 (+/- 10分)
        if win_rate > 0.60:
            score += 10
        elif win_rate > 0.50:
            score += 5
        elif win_rate < 0.40:
            score -= 10

        # 仓位 (+/- 5分)
        if 0.60 <= total_exposure <= 0.80:
            score += 5
        elif total_exposure > 0.95 or total_exposure < 0.20:
            score -= 5

        return max(0, min(100, score))

    def _calculate_risk_level(
        self,
        volatility: float,
        max_drawdown: float,
        total_exposure: float,
        var_95: float,
    ) -> str:
        """计算风险等级"""

        risk_score = 0

        # 波动率
        if volatility > 0.40:
            risk_score += 3
        elif volatility > 0.30:
            risk_score += 2
        elif volatility > 0.20:
            risk_score += 1

        # 最大回撤
        if max_drawdown < -0.20:
            risk_score += 3
        elif max_drawdown < -0.15:
            risk_score += 2
        elif max_drawdown < -0.10:
            risk_score += 1

        # 仓位
        if total_exposure > 0.90:
            risk_score += 2
        elif total_exposure > 0.80:
            risk_score += 1

        # VaR
        if var_95 < -0.05:
            risk_score += 2
        elif var_95 < -0.03:
            risk_score += 1

        # 判断等级
        if risk_score >= 7:
            return "critical"
        elif risk_score >= 5:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"

    def get_metrics_history(
        self, strategy_id: str, days: int = 30
    ) -> List[StrategyMetrics]:
        """获取历史指标

        Args:
            strategy_id: 策略ID
            days: 天数

        Returns:
            历史指标列表
        """
        if strategy_id not in self.metrics_history:
            return []

        return self.metrics_history[strategy_id][-days:]

    def get_active_alerts(
        self, strategy_id: str, severity: Optional[str] = None
    ) -> List[RiskAlert]:
        """获取活跃告警

        Args:
            strategy_id: 策略ID
            severity: 严重程度过滤

        Returns:
            告警列表
        """
        if strategy_id not in self.active_alerts:
            return []

        alerts = self.active_alerts[strategy_id]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    def clear_alerts(self, strategy_id: str) -> None:
        """清除告警

        Args:
            strategy_id: 策略ID
        """
        if strategy_id in self.active_alerts:
            self.active_alerts[strategy_id] = []
            LOGGER.info(f"🗑️ 已清除策略 {strategy_id} 的告警")

    def generate_report(self, strategy_id: str) -> Dict:
        """生成监控报告

        Args:
            strategy_id: 策略ID

        Returns:
            报告字典
        """
        try:
            history = self.get_metrics_history(strategy_id)
            alerts = self.get_active_alerts(strategy_id)

            if not history:
                return {
                    "strategy_id": strategy_id,
                    "status": "no_data",
                    "message": "暂无监控数据",
                }

            latest = history[-1]

            return {
                "strategy_id": strategy_id,
                "timestamp": datetime.now().isoformat(),
                "latest_metrics": asdict(latest),
                "active_alerts": [asdict(a) for a in alerts],
                "alert_count": len(alerts),
                "critical_alerts": len([a for a in alerts if a.severity == "critical"]),
                "summary": {
                    "health_score": latest.health_score,
                    "risk_level": latest.risk_level,
                    "total_return": latest.total_return,
                    "sharpe_ratio": latest.sharpe_ratio,
                    "max_drawdown": latest.max_drawdown,
                    "position_count": latest.position_count,
                },
            }

        except Exception as e:
            LOGGER.error(f"❌ 生成报告失败: {e}", exc_info=True)
            return {"strategy_id": strategy_id, "status": "error", "message": str(e)}


# 全局单例
_monitor_instance = None


def get_monitor() -> LiveStrategyMonitor:
    """获取监控器单例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = LiveStrategyMonitor()
    return _monitor_instance
