#!/usr/bin/env python3
"""实盘交易管理器 - 管理策略的实盘运行状态"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from common.logging_system import setup_logger

LOGGER = setup_logger("live_trading_manager")


class StrategyStatus(Enum):
    """策略状态"""

    INACTIVE = "inactive"  # 未激活
    ACTIVE = "active"  # 运行中
    PAUSED = "paused"  # 已暂停
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误状态


@dataclass
class LiveTradingConfig:
    """实盘交易配置"""

    strategy_id: str
    strategy_name: str
    initial_capital: float  # 初始资金
    max_position_per_stock: float  # 单只股票最大仓位（比例）
    max_total_position: float  # 总仓位上限（比例）
    max_daily_loss: float  # 单日最大亏损（比例）
    max_drawdown: float  # 最大回撤限制（比例）
    stop_loss: float  # 止损线（比例）
    take_profit: float  # 止盈线（比例）
    risk_level: str  # 风险等级: low/medium/high
    notification_channels: List[str]  # 通知渠道: email/wechat/dingtalk/sms
    trading_hours: Dict[str, str]  # 交易时间: {"start": "09:30", "end": "15:00"}

    # 可选配置
    max_stocks: int = 10  # 最大持仓股票数
    min_position_size: float = 0.05  # 最小仓位（比例）
    rebalance_freq: str = "daily"  # 调仓频率: daily/weekly/monthly
    enable_short: bool = False  # 是否允许做空
    enable_leverage: bool = False  # 是否使用杠杆
    leverage_ratio: float = 1.0  # 杠杆倍数


@dataclass
class AccountStatus:
    """账户状态"""

    strategy_id: str
    total_assets: float  # 总资产
    available_cash: float  # 可用资金
    position_value: float  # 持仓市值
    frozen_cash: float  # 冻结资金
    total_pnl: float  # 总盈亏
    total_return: float  # 总收益率
    daily_pnl: float  # 当日盈亏
    daily_return: float  # 当日收益率
    positions: Dict[str, Any]  # 持仓明细
    pending_orders: List[Any]  # 挂单列表
    last_update: str  # 最后更新时间


@dataclass
class TradingSignal:
    """交易信号"""

    signal_id: str
    strategy_id: str
    timestamp: str
    signal_type: str  # buy/sell/hold
    stock_code: str
    stock_name: str
    current_price: float
    target_price: Optional[float]
    position_size: float  # 仓位大小（比例）
    confidence: float  # 置信度
    reason: str  # 理由
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    expected_return: Optional[float]
    risk_score: float  # 风险评分

    # 可选字段
    technical_indicators: Optional[Dict] = None
    market_regime: Optional[str] = None
    model_prediction: Optional[Dict] = None


class LiveTradingManager:
    """实盘交易管理器

    功能:
    1. 激活/停用策略
    2. 管理账户状态
    3. 记录交易信号
    4. 监控风险指标
    5. 策略运行状态管理
    """

    def __init__(self, base_dir: str = "ai_strategy_system/live_trading"):
        """初始化实盘管理器

        Args:
            base_dir: 实盘数据保存目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 子目录
        self.configs_dir = self.base_dir / "configs"
        self.accounts_dir = self.base_dir / "accounts"
        self.signals_dir = self.base_dir / "signals"
        self.logs_dir = self.base_dir / "logs"

        for dir_path in [
            self.configs_dir,
            self.accounts_dir,
            self.signals_dir,
            self.logs_dir,
        ]:
            dir_path.mkdir(exist_ok=True)

        LOGGER.info(f"📁 实盘管理器初始化完成: {self.base_dir.absolute()}")

    def activate_strategy(
        self,
        strategy_id: str,
        config: Optional[LiveTradingConfig] = None,
        strategy_name: Optional[str] = None,
        initial_capital: Optional[float] = None,
        risk_level: str = "medium",
        **kwargs,
    ) -> bool:
        """激活策略到实盘

        Args:
            strategy_id: 策略ID
            config: 实盘配置对象（可选，如果提供则使用此配置）
            strategy_name: 策略名称（仅当config为None时使用）
            initial_capital: 初始资金（仅当config为None时使用）
            risk_level: 风险等级 (low/medium/high)
            **kwargs: 其他配置参数

        Returns:
            是否激活成功
        """
        try:
            # 检查策略是否已保存在数据库中
            from ai_strategy_system.utils.strategy_database import get_strategy_database

            strategy_db = get_strategy_database()
            saved_strategies = strategy_db.list_strategies(user_id=None)
            strategy_exists = any(
                s["strategy_id"] == strategy_id for s in saved_strategies
            )

            if not strategy_exists:
                LOGGER.warning(f"⚠️ 策略未在数据库中找到: {strategy_id}，尝试继续激活")

            # 如果没有提供config，创建一个
            if config is None:
                if strategy_name is None or initial_capital is None:
                    LOGGER.error(
                        "❌ 必须提供config对象或strategy_name和initial_capital参数"
                    )
                    return False

                # 根据风险等级设置默认参数
                risk_params = self._get_risk_params(risk_level)

                # 创建配置
                config = LiveTradingConfig(
                    strategy_id=strategy_id,
                    strategy_name=strategy_name,
                    initial_capital=initial_capital,
                    risk_level=risk_level,
                    **risk_params,
                    **kwargs,
                )

            # 保存配置
            config_path = self.configs_dir / f"{strategy_id}.json"
            config_dict = asdict(config)
            config_dict["status"] = StrategyStatus.ACTIVE.value
            config_dict["activation_time"] = datetime.now().isoformat()

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)

            # 初始化账户
            account = AccountStatus(
                strategy_id=strategy_id,
                total_assets=config.initial_capital,
                available_cash=config.initial_capital,
                position_value=0.0,
                frozen_cash=0.0,
                total_pnl=0.0,
                total_return=0.0,
                daily_pnl=0.0,
                daily_return=0.0,
                positions={},
                pending_orders=[],
                last_update=datetime.now().isoformat(),
            )

            # 保存账户状态
            self._save_account_status(account)

            # 记录日志
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "activate",
                "strategy_id": strategy_id,
                "initial_capital": config.initial_capital,
                "risk_level": config.risk_level,
                "status": "success",
            }
            self._append_log(strategy_id, log_entry)

            LOGGER.info(f"✅ 策略已激活到实盘: {strategy_id}")
            LOGGER.info(f"   策略名称: {config.strategy_name}")
            LOGGER.info(f"   初始资金: ¥{config.initial_capital:,.2f}")
            LOGGER.info(f"   风险等级: {config.risk_level}")
            LOGGER.info(
                f"   止损: {config.stop_loss * 100:.1f}%, 止盈: {config.take_profit * 100:.1f}%"
            )
            LOGGER.info(f"   最大回撤: {config.max_drawdown * 100:.1f}%")

            return True

        except Exception as e:
            LOGGER.error(f"❌ 激活策略失败: {e}", exc_info=True)
            return False

    def deactivate_strategy(self, strategy_id: str, reason: str = "") -> bool:
        """停用策略

        Args:
            strategy_id: 策略ID
            reason: 停用原因

        Returns:
            是否停用成功
        """
        try:
            config_path = self.configs_dir / f"{strategy_id}.json"

            if not config_path.exists():
                LOGGER.error(f"❌ 策略未激活: {strategy_id}")
                return False

            # 读取配置
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 更新状态
            config["status"] = StrategyStatus.STOPPED.value
            config["stop_time"] = datetime.now().isoformat()
            config["stop_reason"] = reason

            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # 记录日志
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "deactivate",
                "strategy_id": strategy_id,
                "reason": reason,
                "status": "success",
            }
            self._append_log(strategy_id, log_entry)

            LOGGER.info(f"✅ 策略已停用: {strategy_id}")
            if reason:
                LOGGER.info(f"   停用原因: {reason}")

            return True

        except Exception as e:
            LOGGER.error(f"❌ 停用策略失败: {e}", exc_info=True)
            return False

    def pause_strategy(self, strategy_id: str, reason: str = "") -> bool:
        """暂停策略

        Args:
            strategy_id: 策略ID
            reason: 暂停原因

        Returns:
            是否暂停成功
        """
        try:
            config_path = self.configs_dir / f"{strategy_id}.json"

            if not config_path.exists():
                LOGGER.error(f"❌ 策略未激活: {strategy_id}")
                return False

            # 读取配置
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 更新状态
            config["status"] = StrategyStatus.PAUSED.value
            config["pause_time"] = datetime.now().isoformat()
            config["pause_reason"] = reason

            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # 记录日志
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "pause",
                "strategy_id": strategy_id,
                "reason": reason,
                "status": "success",
            }
            self._append_log(strategy_id, log_entry)

            LOGGER.info(f"⏸️  策略已暂停: {strategy_id}")
            if reason:
                LOGGER.info(f"   暂停原因: {reason}")

            return True

        except Exception as e:
            LOGGER.error(f"❌ 暂停策略失败: {e}", exc_info=True)
            return False

    def resume_strategy(self, strategy_id: str) -> bool:
        """恢复策略运行

        Args:
            strategy_id: 策略ID

        Returns:
            是否恢复成功
        """
        try:
            config_path = self.configs_dir / f"{strategy_id}.json"

            if not config_path.exists():
                LOGGER.error(f"❌ 策略未激活: {strategy_id}")
                return False

            # 读取配置
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 更新状态
            config["status"] = StrategyStatus.ACTIVE.value
            config["resume_time"] = datetime.now().isoformat()

            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # 记录日志
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "resume",
                "strategy_id": strategy_id,
                "status": "success",
            }
            self._append_log(strategy_id, log_entry)

            LOGGER.info(f"▶️  策略已恢复运行: {strategy_id}")

            return True

        except Exception as e:
            LOGGER.error(f"❌ 恢复策略失败: {e}", exc_info=True)
            return False

    def get_active_strategies(self) -> List[Dict]:
        """获取所有活跃策略

        Returns:
            活跃策略列表
        """
        active_strategies = []

        for config_file in self.configs_dir.glob("*.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                status = config.get("status", StrategyStatus.ACTIVE.value)

                if status == StrategyStatus.ACTIVE.value:
                    active_strategies.append(config)

            except Exception as e:
                LOGGER.error(f"❌ 读取配置失败 {config_file}: {e}")
                continue

        return active_strategies

    def get_strategy_config(self, strategy_id: str) -> Optional[Dict]:
        """获取策略配置

        Args:
            strategy_id: 策略ID

        Returns:
            策略配置字典，如果不存在返回None
        """
        config_path = self.configs_dir / f"{strategy_id}.json"

        if not config_path.exists():
            return None

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            LOGGER.error(f"❌ 读取策略配置失败: {e}")
            return None

    def update_account_status(
        self,
        strategy_id: str,
        positions: Optional[Dict] = None,
        pnl_update: Optional[Dict] = None,
    ) -> bool:
        """更新账户状态

        Args:
            strategy_id: 策略ID
            positions: 持仓更新
            pnl_update: 盈亏更新

        Returns:
            是否更新成功
        """
        try:
            # 读取当前状态
            account = self._load_account_status(strategy_id)

            if not account:
                LOGGER.error(f"❌ 账户不存在: {strategy_id}")
                return False

            # 更新持仓
            if positions is not None:
                account["positions"] = positions

                # 计算持仓市值
                position_value = sum(
                    pos.get("market_value", 0) for pos in positions.values()
                )
                account["position_value"] = position_value

                # 更新总资产
                account["total_assets"] = (
                    account["available_cash"]
                    + position_value
                    + account.get("frozen_cash", 0)
                )

            # 更新盈亏
            if pnl_update is not None:
                account.update(pnl_update)

            # 更新时间
            account["last_update"] = datetime.now().isoformat()

            # 保存状态
            self._save_account_status(account)

            return True

        except Exception as e:
            LOGGER.error(f"❌ 更新账户状态失败: {e}", exc_info=True)
            return False

    def get_account_status(self, strategy_id: str) -> Optional[Dict]:
        """获取账户状态

        Args:
            strategy_id: 策略ID

        Returns:
            账户状态字典，如果不存在返回None
        """
        return self._load_account_status(strategy_id)

    def save_signal(self, signal: TradingSignal) -> bool:
        """保存交易信号

        Args:
            signal: 交易信号对象

        Returns:
            是否保存成功
        """
        try:
            # 创建信号目录
            signal_dir = self.signals_dir / signal.strategy_id
            signal_dir.mkdir(exist_ok=True)

            # 按日期组织
            date_str = datetime.now().strftime("%Y%m%d")
            signal_file = signal_dir / f"{date_str}.json"

            # 读取当天的信号列表
            if signal_file.exists():
                with open(signal_file, "r", encoding="utf-8") as f:
                    signals = json.load(f)
            else:
                signals = []

            # 添加新信号
            signals.append(asdict(signal))

            # 保存
            with open(signal_file, "w", encoding="utf-8") as f:
                json.dump(signals, f, ensure_ascii=False, indent=2)

            LOGGER.info(f"💾 交易信号已保存: {signal.signal_id}")

            return True

        except Exception as e:
            LOGGER.error(f"❌ 保存交易信号失败: {e}", exc_info=True)
            return False

    def get_signals(
        self, strategy_id: str, date: Optional[str] = None, days: int = 1
    ) -> List[Dict]:
        """获取交易信号

        Args:
            strategy_id: 策略ID
            date: 日期（YYYYMMDD格式），None表示今天
            days: 获取最近几天的信号

        Returns:
            信号列表
        """
        signals = []
        signal_dir = self.signals_dir / strategy_id

        if not signal_dir.exists():
            return signals

        # 如果指定日期
        if date:
            signal_file = signal_dir / f"{date}.json"
            if signal_file.exists():
                try:
                    with open(signal_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    LOGGER.error(f"❌ 读取信号失败: {e}")
        else:
            # 获取最近N天的信号
            signal_files = sorted(signal_dir.glob("*.json"), reverse=True)[:days]

            for signal_file in signal_files:
                try:
                    with open(signal_file, "r", encoding="utf-8") as f:
                        day_signals = json.load(f)
                        signals.extend(day_signals)
                except Exception as e:
                    LOGGER.error(f"❌ 读取信号失败 {signal_file}: {e}")
                    continue

        return signals

    def check_risk_limits(self, strategy_id: str) -> Dict[str, Any]:
        """检查风险限制

        Args:
            strategy_id: 策略ID

        Returns:
            风险检查结果
        """
        result = {"passed": True, "warnings": [], "violations": []}

        try:
            # 获取配置和账户状态
            config = self.get_strategy_config(strategy_id)
            account = self.get_account_status(strategy_id)

            if not config or not account:
                result["passed"] = False
                result["violations"].append("配置或账户状态不存在")
                return result

            initial_capital = config.get("initial_capital", 0)
            max_daily_loss = config.get("max_daily_loss", 0.1)
            max_drawdown = config.get("max_drawdown", 0.2)

            # 检查单日亏损
            daily_return = account.get("daily_return", 0)
            if daily_return < -max_daily_loss:
                result["passed"] = False
                result["violations"].append(
                    f"单日亏损 {daily_return:.2%} 超过限制 {max_daily_loss:.2%}"
                )
            elif daily_return < -max_daily_loss * 0.8:
                result["warnings"].append(f"单日亏损 {daily_return:.2%} 接近限制")

            # 检查最大回撤
            total_return = account.get("total_return", 0)
            if total_return < -max_drawdown:
                result["passed"] = False
                result["violations"].append(
                    f"总回撤 {total_return:.2%} 超过限制 {max_drawdown:.2%}"
                )
            elif total_return < -max_drawdown * 0.8:
                result["warnings"].append(f"总回撤 {total_return:.2%} 接近限制")

            # 检查总仓位
            max_total_position = config.get("max_total_position", 0.95)
            total_assets = account.get("total_assets", 1)
            position_value = account.get("position_value", 0)
            position_ratio = position_value / total_assets if total_assets > 0 else 0

            if position_ratio > max_total_position:
                result["warnings"].append(
                    f"总仓位 {position_ratio:.2%} 超过限制 {max_total_position:.2%}"
                )

        except Exception as e:
            LOGGER.error(f"❌ 风险检查失败: {e}", exc_info=True)
            result["passed"] = False
            result["violations"].append(f"风险检查异常: {str(e)}")

        return result

    def _get_risk_params(self, risk_level: str) -> Dict:
        """根据风险等级获取默认参数"""
        risk_profiles = {
            "low": {
                "max_position_per_stock": 0.15,
                "max_total_position": 0.60,
                "max_daily_loss": 0.02,
                "max_drawdown": 0.10,
                "stop_loss": -0.05,
                "take_profit": 0.10,
                "notification_channels": ["email", "wechat"],
                "trading_hours": {"start": "09:30", "end": "14:30"},
            },
            "medium": {
                "max_position_per_stock": 0.20,
                "max_total_position": 0.80,
                "max_daily_loss": 0.03,
                "max_drawdown": 0.15,
                "stop_loss": -0.07,
                "take_profit": 0.15,
                "notification_channels": ["email", "wechat"],
                "trading_hours": {"start": "09:30", "end": "15:00"},
            },
            "high": {
                "max_position_per_stock": 0.30,
                "max_total_position": 0.95,
                "max_daily_loss": 0.05,
                "max_drawdown": 0.20,
                "stop_loss": -0.10,
                "take_profit": 0.20,
                "notification_channels": ["email", "wechat", "sms"],
                "trading_hours": {"start": "09:30", "end": "15:00"},
            },
        }

        return risk_profiles.get(risk_level, risk_profiles["medium"])

    def _save_account_status(self, account: Dict) -> None:
        """保存账户状态"""
        strategy_id = account["strategy_id"]
        account_file = self.accounts_dir / f"{strategy_id}.json"

        with open(account_file, "w", encoding="utf-8") as f:
            json.dump(account, f, ensure_ascii=False, indent=2)

    def _load_account_status(self, strategy_id: str) -> Optional[Dict]:
        """加载账户状态"""
        account_file = self.accounts_dir / f"{strategy_id}.json"

        if not account_file.exists():
            return None

        try:
            with open(account_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            LOGGER.error(f"❌ 读取账户状态失败: {e}")
            return None

    def _append_log(self, strategy_id: str, log_entry: Dict) -> None:
        """追加日志"""
        log_file = self.logs_dir / f"{strategy_id}.log"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# CLI工具
if __name__ == "__main__":
    import sys

    manager = LiveTradingManager()

    if len(sys.argv) < 2:
        print("用法:")
        print(
            "  python live_trading_manager.py activate <strategy_id> <capital> [risk_level]"
        )
        print("  python live_trading_manager.py deactivate <strategy_id>")
        print("  python live_trading_manager.py pause <strategy_id>")
        print("  python live_trading_manager.py resume <strategy_id>")
        print("  python live_trading_manager.py list")
        print("  python live_trading_manager.py status <strategy_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "activate":
        if len(sys.argv) < 4:
            print("❌ 缺少参数: strategy_id capital")
            sys.exit(1)

        strategy_id = sys.argv[2]
        capital = float(sys.argv[3])
        risk_level = sys.argv[4] if len(sys.argv) > 4 else "medium"

        success = manager.activate_strategy(
            strategy_id=strategy_id,
            strategy_name=f"策略_{strategy_id}",
            initial_capital=capital,
            risk_level=risk_level,
        )

        if success:
            print(f"✅ 策略已激活: {strategy_id}")
        else:
            print(f"❌ 激活失败")

    elif command == "deactivate":
        if len(sys.argv) < 3:
            print("❌ 缺少参数: strategy_id")
            sys.exit(1)

        strategy_id = sys.argv[2]
        success = manager.deactivate_strategy(strategy_id)

        if success:
            print(f"✅ 策略已停用: {strategy_id}")
        else:
            print(f"❌ 停用失败")

    elif command == "pause":
        if len(sys.argv) < 3:
            print("❌ 缺少参数: strategy_id")
            sys.exit(1)

        strategy_id = sys.argv[2]
        success = manager.pause_strategy(strategy_id)

        if success:
            print(f"⏸️  策略已暂停: {strategy_id}")
        else:
            print(f"❌ 暂停失败")

    elif command == "resume":
        if len(sys.argv) < 3:
            print("❌ 缺少参数: strategy_id")
            sys.exit(1)

        strategy_id = sys.argv[2]
        success = manager.resume_strategy(strategy_id)

        if success:
            print(f"▶️  策略已恢复: {strategy_id}")
        else:
            print(f"❌ 恢复失败")

    elif command == "list":
        strategies = manager.get_active_strategies()

        if not strategies:
            print("📋 暂无活跃策略")
        else:
            print(f"📋 活跃策略列表 ({len(strategies)}个):\n")

            for i, strategy in enumerate(strategies, 1):
                print(f"{i}. {strategy['strategy_id']}")
                print(f"   名称: {strategy['strategy_name']}")
                print(f"   资金: ¥{strategy['initial_capital']:,.2f}")
                print(f"   风险: {strategy['risk_level']}")
                print()

    elif command == "status":
        if len(sys.argv) < 3:
            print("❌ 缺少参数: strategy_id")
            sys.exit(1)

        strategy_id = sys.argv[2]
        config = manager.get_strategy_config(strategy_id)
        account = manager.get_account_status(strategy_id)

        if not config:
            print(f"❌ 策略不存在: {strategy_id}")
            sys.exit(1)

        print(f"📊 策略状态: {strategy_id}\n")
        print(f"名称: {config['strategy_name']}")
        print(f"状态: {config.get('status', 'active')}")
        print(f"风险等级: {config['risk_level']}")
        print(f"\n💰 账户信息:")

        if account:
            print(f"总资产: ¥{account['total_assets']:,.2f}")
            print(f"可用资金: ¥{account['available_cash']:,.2f}")
            print(f"持仓市值: ¥{account['position_value']:,.2f}")
            print(f"总收益: {account['total_return']:.2%}")
            print(f"当日收益: {account['daily_return']:.2%}")
            print(f"持仓数量: {len(account.get('positions', {}))}")
        else:
            print("  (暂无账户数据)")

    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)
