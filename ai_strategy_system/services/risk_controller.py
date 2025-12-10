#!/usr/bin/env python3
"""风险控制器 - 实时监控和控制交易风险"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from common.logging_system import setup_logger

LOGGER = setup_logger("risk_controller")


class RiskAction(Enum):
    """风险控制动作"""
    CONTINUE = "CONTINUE"  # 继续交易
    REDUCE_POSITION = "REDUCE_POSITION"  # 降低仓位
    STOP_TRADING = "STOP_TRADING"  # 停止交易
    CLOSE_ALL = "CLOSE_ALL"  # 平掉所有仓位
    WARNING = "WARNING"  # 风险警告


@dataclass
class RiskEvent:
    """风险事件"""
    timestamp: datetime
    event_type: str
    severity: str  # LOW/MEDIUM/HIGH/CRITICAL
    description: str
    action_taken: RiskAction
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class RiskControlDecision:
    """风险控制决策"""
    action: RiskAction
    reason: str
    position_adjustment_factor: float = 1.0  # 仓位调整系数
    metadata: Dict[str, Any] = field(default_factory=dict)


class RiskController:
    """风险控制器
    
    实时监控交易风险，包括：
    - 最大回撤控制
    - 单日最大亏损
    - 连续亏损控制
    - 仓位集中度
    - 波动率过滤
    """
    
    def __init__(
        self,
        max_drawdown: float = 0.15,
        max_daily_loss: float = 0.03,
        max_consecutive_losses: int = 3,
        max_single_position: float = 0.35,
        max_sector_concentration: float = 0.5,
    ):
        """初始化风险控制器
        
        Args:
            max_drawdown: 最大回撤限制（默认15%）
            max_daily_loss: 单日最大亏损限制（默认3%）
            max_consecutive_losses: 最大连续亏损次数
            max_single_position: 单个持仓最大比例
            max_sector_concentration: 单个行业最大集中度
        """
        self.max_drawdown = max_drawdown
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.max_single_position = max_single_position
        self.max_sector_concentration = max_sector_concentration
        
        # 状态追踪
        self.peak_equity = 0
        self.daily_start_equity = 0
        self.consecutive_loss_days = 0
        self.consecutive_losing_trades = 0
        self.risk_events: List[RiskEvent] = []
        self.is_trading_halted = False
        self.halt_until = None
        
        LOGGER.info("🛡️  Risk Controller initialized")
        LOGGER.info(f"   Max Drawdown: {max_drawdown:.1%}")
        LOGGER.info(f"   Max Daily Loss: {max_daily_loss:.1%}")
        LOGGER.info(f"   Max Consecutive Losses: {max_consecutive_losses}")
    
    def check_risk_limits(
        self,
        current_equity: float,
        positions: Dict[str, Any],
        daily_pnl: Optional[float] = None,
        recent_trades: Optional[List[Dict]] = None,
    ) -> RiskControlDecision:
        """检查风险限制并返回控制决策
        
        Args:
            current_equity: 当前总资产
            positions: 当前持仓字典
            daily_pnl: 当日损益
            recent_trades: 最近交易记录
            
        Returns:
            风险控制决策
        """
        
        # 检查交易是否被暂停
        if self._check_trading_halt():
            return RiskControlDecision(
                action=RiskAction.STOP_TRADING,
                reason="Trading halted due to previous risk breach",
            )
        
        # 更新峰值资产
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.consecutive_loss_days = 0
        
        # 1. 检查最大回撤
        drawdown_decision = self._check_max_drawdown(current_equity)
        if drawdown_decision.action != RiskAction.CONTINUE:
            self._log_risk_event(
                event_type="MAX_DRAWDOWN_BREACH",
                severity="CRITICAL",
                description=drawdown_decision.reason,
                action=drawdown_decision.action,
                metrics={"drawdown": (current_equity - self.peak_equity) / self.peak_equity},
            )
            return drawdown_decision
        
        # 2. 检查单日最大亏损
        if daily_pnl is not None:
            daily_loss_decision = self._check_daily_loss(daily_pnl, current_equity)
            if daily_loss_decision.action != RiskAction.CONTINUE:
                self._log_risk_event(
                    event_type="DAILY_LOSS_LIMIT",
                    severity="HIGH",
                    description=daily_loss_decision.reason,
                    action=daily_loss_decision.action,
                    metrics={"daily_pnl": daily_pnl},
                )
                return daily_loss_decision
        
        # 3. 检查连续亏损
        if recent_trades:
            consecutive_decision = self._check_consecutive_losses(recent_trades)
            if consecutive_decision.action != RiskAction.CONTINUE:
                self._log_risk_event(
                    event_type="CONSECUTIVE_LOSSES",
                    severity="MEDIUM",
                    description=consecutive_decision.reason,
                    action=consecutive_decision.action,
                    metrics={"consecutive_losses": self.consecutive_losing_trades},
                )
                return consecutive_decision
        
        # 4. 检查仓位集中度
        concentration_decision = self._check_position_concentration(positions, current_equity)
        if concentration_decision.action != RiskAction.CONTINUE:
            self._log_risk_event(
                event_type="POSITION_CONCENTRATION",
                severity="LOW",
                description=concentration_decision.reason,
                action=concentration_decision.action,
                metrics=concentration_decision.metadata,
            )
            return concentration_decision
        
        # 所有检查通过
        return RiskControlDecision(
            action=RiskAction.CONTINUE,
            reason="All risk checks passed",
        )
    
    def _check_max_drawdown(self, current_equity: float) -> RiskControlDecision:
        """检查最大回撤"""
        if self.peak_equity == 0:
            return RiskControlDecision(action=RiskAction.CONTINUE, reason="Initial state")
        
        drawdown = (current_equity - self.peak_equity) / self.peak_equity
        
        if abs(drawdown) > self.max_drawdown:
            # 超过最大回撤限制，立即平仓
            LOGGER.error(f"🚨 CRITICAL: Max drawdown exceeded! {drawdown:.2%} > {self.max_drawdown:.1%}")
            self._halt_trading(hours=24)
            return RiskControlDecision(
                action=RiskAction.CLOSE_ALL,
                reason=f"Maximum drawdown exceeded: {drawdown:.2%}",
                metadata={"drawdown": drawdown, "threshold": self.max_drawdown},
            )
        
        elif abs(drawdown) > self.max_drawdown * 0.8:
            # 接近最大回撤，降低仓位
            LOGGER.warning(f"⚠️  Approaching max drawdown: {drawdown:.2%}")
            return RiskControlDecision(
                action=RiskAction.REDUCE_POSITION,
                reason=f"Drawdown at {drawdown:.2%}, approaching limit",
                position_adjustment_factor=0.5,
                metadata={"drawdown": drawdown},
            )
        
        return RiskControlDecision(action=RiskAction.CONTINUE, reason="Drawdown within limits")
    
    def _check_daily_loss(self, daily_pnl: float, current_equity: float) -> RiskControlDecision:
        """检查单日最大亏损"""
        if self.daily_start_equity == 0:
            self.daily_start_equity = current_equity - daily_pnl
        
        daily_loss_pct = daily_pnl / self.daily_start_equity if self.daily_start_equity > 0 else 0
        
        if daily_loss_pct < -self.max_daily_loss:
            # 超过单日最大亏损，停止交易
            LOGGER.error(f"🚨 Daily loss limit exceeded! {daily_loss_pct:.2%}")
            self._halt_trading(hours=6)
            self.consecutive_loss_days += 1
            
            return RiskControlDecision(
                action=RiskAction.STOP_TRADING,
                reason=f"Daily loss limit exceeded: {daily_loss_pct:.2%}",
                metadata={"daily_pnl": daily_pnl, "limit": self.max_daily_loss},
            )
        
        elif daily_loss_pct < -self.max_daily_loss * 0.7:
            # 接近单日亏损限制，发出警告
            LOGGER.warning(f"⚠️  Approaching daily loss limit: {daily_loss_pct:.2%}")
            return RiskControlDecision(
                action=RiskAction.WARNING,
                reason=f"Daily loss at {daily_loss_pct:.2%}",
                metadata={"daily_pnl": daily_pnl},
            )
        
        # 重置单日起始资产（新的一天）
        if daily_pnl > 0:
            self.daily_start_equity = current_equity
            self.consecutive_loss_days = 0
        
        return RiskControlDecision(action=RiskAction.CONTINUE, reason="Daily loss within limits")
    
    def _check_consecutive_losses(self, recent_trades: List[Dict]) -> RiskControlDecision:
        """检查连续亏损"""
        if not recent_trades:
            return RiskControlDecision(action=RiskAction.CONTINUE, reason="No recent trades")
        
        # 统计最近的连续亏损交易
        consecutive_losses = 0
        for trade in reversed(recent_trades[-10:]):  # 检查最近10笔交易
            if trade.get("pnl", 0) < 0:
                consecutive_losses += 1
            else:
                break
        
        self.consecutive_losing_trades = consecutive_losses
        
        if consecutive_losses >= self.max_consecutive_losses:
            # 连续亏损过多，降低仓位
            LOGGER.warning(f"⚠️  {consecutive_losses} consecutive losing trades")
            
            # 根据亏损次数调整仓位
            if consecutive_losses >= self.max_consecutive_losses + 2:
                # 严重连续亏损，大幅降低仓位
                return RiskControlDecision(
                    action=RiskAction.REDUCE_POSITION,
                    reason=f"{consecutive_losses} consecutive losses",
                    position_adjustment_factor=0.3,
                    metadata={"consecutive_losses": consecutive_losses},
                )
            else:
                # 一般连续亏损，降低50%仓位
                return RiskControlDecision(
                    action=RiskAction.REDUCE_POSITION,
                    reason=f"{consecutive_losses} consecutive losses",
                    position_adjustment_factor=0.5,
                    metadata={"consecutive_losses": consecutive_losses},
                )
        
        return RiskControlDecision(action=RiskAction.CONTINUE, reason="Consecutive losses within limits")
    
    def _check_position_concentration(
        self, 
        positions: Dict[str, Any],
        current_equity: float,
    ) -> RiskControlDecision:
        """检查仓位集中度"""
        if not positions or current_equity == 0:
            return RiskControlDecision(action=RiskAction.CONTINUE, reason="No positions")
        
        # 检查单个持仓比例
        for symbol, position in positions.items():
            position_value = getattr(position, "market_value", 0)
            position_pct = position_value / current_equity
            
            if position_pct > self.max_single_position:
                LOGGER.warning(
                    f"⚠️  Single position {symbol} too large: {position_pct:.1%} > {self.max_single_position:.1%}"
                )
                return RiskControlDecision(
                    action=RiskAction.WARNING,
                    reason=f"Position {symbol} concentration too high: {position_pct:.1%}",
                    metadata={"symbol": symbol, "concentration": position_pct},
                )
        
        return RiskControlDecision(action=RiskAction.CONTINUE, reason="Position concentration OK")
    
    def _check_trading_halt(self) -> bool:
        """检查交易是否被暂停"""
        if not self.is_trading_halted:
            return False
        
        if self.halt_until and datetime.now() > self.halt_until:
            # 暂停期结束，恢复交易
            self.is_trading_halted = False
            self.halt_until = None
            LOGGER.info("✅ Trading halt lifted, resuming normal operations")
            return False
        
        return True
    
    def _halt_trading(self, hours: int):
        """暂停交易指定小时数"""
        from datetime import timedelta
        self.is_trading_halted = True
        self.halt_until = datetime.now() + timedelta(hours=hours)
        LOGGER.warning(f"🛑 Trading halted for {hours} hours until {self.halt_until}")
    
    def _log_risk_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        action: RiskAction,
        metrics: Dict[str, float],
    ):
        """记录风险事件"""
        event = RiskEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            description=description,
            action_taken=action,
            metrics=metrics,
        )
        self.risk_events.append(event)
        
        # 打印风险事件日志
        emoji = "🚨" if severity == "CRITICAL" else "⚠️" if severity in ["HIGH", "MEDIUM"] else "ℹ️"
        LOGGER.warning(f"{emoji} Risk Event [{severity}]: {description}")
        LOGGER.warning(f"   Action: {action.value}")
        LOGGER.warning(f"   Metrics: {metrics}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要"""
        return {
            "peak_equity": self.peak_equity,
            "consecutive_loss_days": self.consecutive_loss_days,
            "consecutive_losing_trades": self.consecutive_losing_trades,
            "is_trading_halted": self.is_trading_halted,
            "halt_until": self.halt_until.isoformat() if self.halt_until else None,
            "total_risk_events": len(self.risk_events),
            "critical_events": len([e for e in self.risk_events if e.severity == "CRITICAL"]),
            "recent_events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type,
                    "severity": e.severity,
                    "description": e.description,
                }
                for e in self.risk_events[-5:]  # 最近5个事件
            ],
        }
    
    def reset_daily_state(self):
        """重置每日状态（在每个交易日开始时调用）"""
        self.daily_start_equity = 0
        LOGGER.info("📅 Daily risk state reset")


def create_risk_controller(
    max_drawdown: float = 0.15,
    max_daily_loss: float = 0.03,
) -> RiskController:
    """工厂函数：创建风险控制器"""
    return RiskController(
        max_drawdown=max_drawdown,
        max_daily_loss=max_daily_loss,
    )
