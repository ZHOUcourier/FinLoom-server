"""
回测引擎模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from common.data_structures import Position, Signal
from common.exceptions import QuantSystemError
from common.logging_system import setup_logger

from .database_manager import get_backtest_database_manager

logger = setup_logger("backtest_engine")


@dataclass
class BacktestConfig:
    """回测配置"""

    start_date: datetime
    end_date: datetime
    initial_capital: float
    commission_rate: float = 0.001
    slippage_bps: float = 5.0
    benchmark_symbol: Optional[str] = None
    rebalance_frequency: str = "daily"  # daily, weekly, monthly
    save_to_db: bool = True  # 是否保存到数据库
    strategy_name: str = "Unknown Strategy"  # 策略名称


@dataclass
class BacktestResult:
    """回测结果"""

    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    win_loss_ratio: float = 0.0  # 盈亏比
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    daily_returns: pd.Series = field(default_factory=pd.Series)
    drawdown_series: pd.Series = field(default_factory=pd.Series)
    trades: List[Dict[str, Any]] = field(default_factory=list)


class BacktestEngine:
    """回测引擎类"""

    def __init__(
        self,
        config: BacktestConfig,
        strategy_func: Optional[Callable] = None,
        risk_controller: Optional[Any] = None,
    ):
        """初始化回测引擎

        Args:
            config: 回测配置
            strategy_func: 策略函数
            risk_controller: 风险控制器（可选）
        """
        self.config = config
        self.strategy_func = strategy_func
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.risk_controller = risk_controller  # 新增：风险控制器

        # 生成唯一的backtest_id
        import uuid

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        self.backtest_id = (
            f"{config.strategy_name.replace(' ', '_')}_{timestamp}_{unique_id}"
        )

        # 回测状态
        self.current_capital = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict] = []

        # 进度回调
        self.progress_callback = None

        # 数据库管理器（可选）
        self.db_manager = None
        if config.save_to_db:
            self.db_manager = get_backtest_database_manager()

    def load_market_data(self, symbols: List[str], data: Dict[str, pd.DataFrame]):
        """加载市场数据

        Args:
            symbols: 股票代码列表
            data: 市场数据字典
        """
        try:
            for symbol in symbols:
                if symbol in data:
                    df = data[symbol].copy()

                    # 确保索引是datetime类型
                    if not isinstance(df.index, pd.DatetimeIndex):
                        if "date" in df.columns:
                            df["date"] = pd.to_datetime(df["date"])
                            df.set_index("date", inplace=True)
                        else:
                            df.index = pd.to_datetime(df.index)

                    # 确保数据按时间排序
                    df = df.sort_index()

                    # 过滤日期范围 - 只比较日期部分
                    start_date = (
                        self.config.start_date.date()
                        if hasattr(self.config.start_date, "date")
                        else self.config.start_date
                    )
                    end_date = (
                        self.config.end_date.date()
                        if hasattr(self.config.end_date, "date")
                        else self.config.end_date
                    )

                    df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]
                    self.market_data[symbol] = df
                    logger.info(
                        f"Loaded {len(df)} records for {symbol} between {start_date} and {end_date}"
                    )
                else:
                    logger.warning(f"No data found for {symbol}")

        except Exception as e:
            logger.error(f"Failed to load market data: {e}")
            raise QuantSystemError(f"Market data loading failed: {e}")

    def set_strategy(self, strategy_func: Callable):
        """设置策略函数

        Args:
            strategy_func: 策略函数
        """
        self.strategy_func = strategy_func
        logger.info("Strategy function set")

    def set_progress_callback(self, callback):
        """设置进度回调函数

        Args:
            callback: 异步回调函数 async def callback(current: int, total: int, message: str)
        """
        self.progress_callback = callback

    def run(self) -> BacktestResult:
        """运行回测

        Returns:
            回测结果
        """
        try:
            if not self.strategy_func:
                raise QuantSystemError("Strategy function not set")

            if not self.market_data:
                raise QuantSystemError("Market data not loaded")

            logger.info(
                f"Starting backtest from {self.config.start_date} to {self.config.end_date}"
            )

            # 生成交易日期
            trading_dates = self._generate_trading_dates()
            logger.info(f"🔍 Generated {len(trading_dates)} trading dates")

            # 逐日回测
            for i, date in enumerate(trading_dates):
                if i % 50 == 0:  # 每50天打印一次
                    logger.info(
                        f"🔍 Processing trading day {i + 1}/{len(trading_dates)}: {date}"
                    )

                    # 调用进度回调
                    if self.progress_callback:
                        self._call_progress_callback(
                            i + 1,
                            len(trading_dates),
                            f"处理交易日 {date.strftime('%Y-%m-%d')}",
                        )

                self._process_trading_day(date)

            # 计算回测结果
            result = self._calculate_results()

            # 保存到数据库
            if self.config.save_to_db:
                self._save_to_database(result)

            # 最终进度回调
            if self.progress_callback:
                self._call_progress_callback(
                    len(trading_dates), len(trading_dates), "回测完成"
                )

            logger.info(
                f"Backtest completed. Final capital: {result.final_capital:.2f}"
            )
            return result

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise QuantSystemError(f"Backtest execution failed: {e}")

    def _generate_trading_dates(self) -> List[datetime]:
        """生成交易日期

        Returns:
            交易日期列表
        """
        dates = []
        # 统一转换为日期（去掉时间部分）
        start_date = (
            self.config.start_date.date()
            if hasattr(self.config.start_date, "date")
            else self.config.start_date
        )
        end_date = (
            self.config.end_date.date()
            if hasattr(self.config.end_date, "date")
            else self.config.end_date
        )

        current_date = start_date

        while current_date <= end_date:
            # 检查是否有市场数据
            has_data = False
            for symbol, data in self.market_data.items():
                # 比较日期部分
                if any(idx.date() == current_date for idx in data.index):
                    has_data = True
                    break

            if has_data:
                # 将日期转换回datetime以保持一致性
                dates.append(datetime.combine(current_date, datetime.min.time()))

            current_date += timedelta(days=1)

        return dates

    def _process_trading_day(self, date: datetime):
        """处理单个交易日

        Args:
            date: 交易日期
        """
        try:
            # 获取当日市场数据 - 只比较日期部分
            current_data = {}
            target_date = date.date() if hasattr(date, "date") else date

            for symbol, data in self.market_data.items():
                # 查找匹配的日期
                matching_dates = [
                    idx for idx in data.index if idx.date() == target_date
                ]
                if matching_dates:
                    current_data[symbol] = data.loc[matching_dates[0]]

            if not current_data:
                return

            # 更新持仓市值
            self._update_positions_value(current_data)

            # 计算当前总资产
            total_equity = self._calculate_total_equity()
            self.equity_curve.append(
                {"date": date, "equity": total_equity, "cash": self.current_capital}
            )

            # 风险控制检查
            if self.risk_controller:
                # 计算当日损益
                daily_pnl = None
                if len(self.equity_curve) >= 2:
                    daily_pnl = total_equity - self.equity_curve[-2]["equity"]

                # 构建持仓信息
                positions_info = {}
                for symbol, pos in self.positions.items():
                    if symbol in current_data:
                        current_price = float(current_data[symbol]["close"])
                    else:
                        current_price = pos.avg_cost
                    positions_info[symbol] = {
                        "quantity": pos.quantity,
                        "avg_cost": pos.avg_cost,
                        "current_price": current_price,
                    }

                # 执行风险检查
                risk_action = self.risk_controller.check_risk_limits(
                    current_equity=total_equity,
                    positions=positions_info,
                    daily_pnl=daily_pnl,
                    recent_trades=self.trades[-10:] if len(self.trades) > 0 else [],
                )

                # 处理风险动作
                if risk_action.action == "CLOSE_ALL":
                    logger.warning(f"⚠️ 触发CLOSE_ALL: {risk_action.message}")
                    # 清空所有持仓
                    from common.data_structures import Signal

                    for symbol, pos in list(self.positions.items()):
                        if symbol in current_data:
                            close_price = float(current_data[symbol]["close"])
                            sell_signal = Signal(
                                signal_id=f"risk_close_all_{symbol}_{date}",
                                symbol=symbol,
                                action="SELL",
                                price=close_price,
                                quantity=pos.quantity,
                                confidence=1.0,
                                timestamp=date,
                                strategy_name="风险控制",
                                metadata={
                                    "reason": "CLOSE_ALL",
                                    "message": risk_action.message,
                                },
                            )
                            self._execute_sell(sell_signal, close_price, date)
                    return  # 停止交易

                elif risk_action.action == "STOP_TRADING":
                    logger.warning(f"⚠️ 触发STOP_TRADING: {risk_action.message}")
                    return  # 不生成新信号

                elif risk_action.action == "REDUCE_POSITION":
                    logger.warning(f"⚠️ 触发REDUCE_POSITION: {risk_action.message}")
                    # 减仓（这里可以选择部分平仓）
                    from common.data_structures import Signal

                    for symbol, pos in list(self.positions.items()):
                        if symbol in current_data:
                            close_price = float(current_data[symbol]["close"])
                            reduce_qty = int(pos.quantity * 0.3)  # 减仓30%
                            if reduce_qty > 0:
                                sell_signal = Signal(
                                    signal_id=f"risk_reduce_{symbol}_{date}",
                                    symbol=symbol,
                                    action="SELL",
                                    price=close_price,
                                    quantity=reduce_qty,
                                    confidence=1.0,
                                    timestamp=date,
                                    strategy_name="风险控制",
                                    metadata={
                                        "reason": "REDUCE_POSITION",
                                        "message": risk_action.message,
                                    },
                                )
                                self._execute_sell(sell_signal, close_price, date)

            # 生成交易信号
            if self.strategy_func:
                logger.debug(
                    f"🔍 Calling strategy for {date} with {len(current_data)} symbols"
                )
                signals = self.strategy_func(
                    current_data, self.positions, self.current_capital
                )
                logger.debug(
                    f"🔍 Strategy returned {len(signals) if signals else 0} signals"
                )
                if signals:
                    self._execute_signals(signals, current_data, date)
            else:
                logger.warning(f"⚠️ No strategy function set for {date}")

        except Exception as e:
            logger.error(f"Error processing trading day {date}: {e}")

    def _update_positions_value(self, current_data: Dict[str, pd.Series]):
        """更新持仓市值

        Args:
            current_data: 当前市场数据
        """
        for symbol, position in self.positions.items():
            if symbol in current_data:
                current_price = current_data[symbol]["close"]
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = position.market_value - (
                    position.quantity * position.avg_cost
                )
                position.last_update = datetime.now()

    def _calculate_total_equity(self) -> float:
        """计算总资产

        Returns:
            总资产
        """
        total_equity = self.current_capital
        for position in self.positions.values():
            total_equity += position.market_value
        return total_equity

    def _execute_signals(
        self,
        signals: List[Signal],
        current_data: Dict[str, pd.Series],
        trading_date: datetime,
    ):
        """执行交易信号

        Args:
            signals: 交易信号列表
            current_data: 当前市场数据
            trading_date: 交易日期
        """
        for signal in signals:
            try:
                if signal.symbol not in current_data:
                    logger.warning(f"No data for {signal.symbol}, skipping signal")
                    continue

                current_price = current_data[signal.symbol]["close"]

                if signal.action == "BUY":
                    self._execute_buy(signal, current_price, trading_date)
                elif signal.action == "SELL":
                    self._execute_sell(signal, current_price, trading_date)

            except Exception as e:
                logger.error(f"Error executing signal {signal.signal_id}: {e}")

    def _execute_buy(
        self, signal: Signal, current_price: float, trading_date: datetime
    ):
        """执行买入操作

        Args:
            signal: 买入信号
            current_price: 当前价格
            trading_date: 交易日期
        """
        # 计算实际价格（考虑滑点）
        slippage = current_price * (self.config.slippage_bps / 10000)
        execution_price = current_price + slippage

        # 计算交易成本
        trade_value = signal.quantity * execution_price
        commission = trade_value * self.config.commission_rate
        total_cost = trade_value + commission

        # 检查资金是否足够
        if total_cost > self.current_capital:
            logger.warning(f"Insufficient capital for buy order: {signal.signal_id}")
            return

        # 更新资金
        self.current_capital -= total_cost

        # 更新持仓
        if signal.symbol in self.positions:
            position = self.positions[signal.symbol]
            # 计算新的平均成本
            total_quantity = position.quantity + signal.quantity
            total_cost_basis = (position.quantity * position.avg_cost) + trade_value
            position.avg_cost = total_cost_basis / total_quantity
            position.quantity = total_quantity
        else:
            # 新建持仓
            self.positions[signal.symbol] = Position(
                position_id=f"pos_{signal.symbol}_{trading_date.strftime('%Y%m%d_%H%M%S')}",
                symbol=signal.symbol,
                quantity=signal.quantity,
                avg_cost=execution_price,
                current_price=execution_price,
                market_value=trade_value,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                open_time=trading_date,
                last_update=trading_date,
            )

        # 记录交易
        self.trades.append(
            {
                "date": trading_date,
                "symbol": signal.symbol,
                "action": "BUY",
                "quantity": signal.quantity,
                "price": execution_price,
                "value": trade_value,
                "commission": commission,
                "signal_id": signal.signal_id,
            }
        )

        logger.info(
            f"Executed buy: {signal.quantity} {signal.symbol} at {execution_price:.2f}"
        )

    def _execute_sell(
        self, signal: Signal, current_price: float, trading_date: datetime
    ):
        """执行卖出操作

        Args:
            signal: 卖出信号
            current_price: 当前价格
            trading_date: 交易日期
        """
        if signal.symbol not in self.positions:
            logger.warning(f"No position for {signal.symbol}, skipping sell signal")
            return

        position = self.positions[signal.symbol]

        # 检查持仓数量
        sell_quantity = min(signal.quantity, position.quantity)
        if sell_quantity <= 0:
            logger.warning(f"No quantity to sell for {signal.symbol}")
            return

        # 计算实际价格（考虑滑点）
        slippage = current_price * (self.config.slippage_bps / 10000)
        execution_price = current_price - slippage

        # 计算交易金额
        trade_value = sell_quantity * execution_price
        commission = trade_value * self.config.commission_rate
        net_proceeds = trade_value - commission

        # 更新资金
        self.current_capital += net_proceeds

        # 计算已实现盈亏
        realized_pnl = (execution_price - position.avg_cost) * sell_quantity
        position.realized_pnl += realized_pnl

        # 更新持仓
        position.quantity -= sell_quantity
        if position.quantity <= 0:
            del self.positions[signal.symbol]

        # 记录交易
        self.trades.append(
            {
                "date": trading_date,
                "symbol": signal.symbol,
                "action": "SELL",
                "quantity": sell_quantity,
                "price": execution_price,
                "value": trade_value,
                "commission": commission,
                "realized_pnl": realized_pnl,
                "signal_id": signal.signal_id,
            }
        )

        logger.info(
            f"Executed sell: {sell_quantity} {signal.symbol} at {execution_price:.2f}"
        )

    def _calculate_results(self) -> BacktestResult:
        """计算回测结果

        Returns:
            回测结果
        """
        try:
            # 计算基本指标
            final_capital = self._calculate_total_equity()
            total_return = (
                final_capital - self.config.initial_capital
            ) / self.config.initial_capital

            # 计算年化收益率
            days = (self.config.end_date - self.config.start_date).days
            annualized_return = (1 + total_return) ** (365 / days) - 1

            # 计算权益曲线
            equity_df = pd.DataFrame(self.equity_curve)
            if not equity_df.empty:
                equity_df.set_index("date", inplace=True)
                equity_returns = equity_df["equity"].pct_change().dropna()

                # 计算波动率
                volatility = equity_returns.std() * np.sqrt(252)

                # 计算夏普比率
                sharpe_ratio = (
                    equity_returns.mean() / equity_returns.std() * np.sqrt(252)
                    if equity_returns.std() > 0
                    else 0
                )

                # 计算最大回撤
                cumulative_returns = (1 + equity_returns).cumprod()
                running_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - running_max) / running_max
                max_drawdown = drawdown.min()
            else:
                volatility = 0.0
                sharpe_ratio = 0.0
                max_drawdown = 0.0

            # 计算交易统计
            total_trades = len(self.trades)
            winning_trades = len(
                [t for t in self.trades if t.get("realized_pnl", 0) > 0]
            )
            win_rate = winning_trades / total_trades if total_trades > 0 else 0

            # 计算盈亏比
            total_profit = sum(
                [
                    t.get("realized_pnl", 0)
                    for t in self.trades
                    if t.get("realized_pnl", 0) > 0
                ]
            )
            total_loss = abs(
                sum(
                    [
                        t.get("realized_pnl", 0)
                        for t in self.trades
                        if t.get("realized_pnl", 0) < 0
                    ]
                )
            )
            profit_factor = (
                total_profit / total_loss if total_loss > 0 else float("inf")
            )

            # 计算盈亏比 (平均盈利/平均亏损)
            winning_pnls = [
                t.get("realized_pnl", 0)
                for t in self.trades
                if t.get("realized_pnl", 0) > 0
            ]
            losing_pnls = [
                abs(t.get("realized_pnl", 0))
                for t in self.trades
                if t.get("realized_pnl", 0) < 0
            ]
            avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
            avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

            # 性能指标
            performance_metrics = {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "win_loss_ratio": win_loss_ratio,
                "total_trades": total_trades,
                "final_capital": final_capital,
            }

            return BacktestResult(
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                initial_capital=self.config.initial_capital,
                final_capital=final_capital,
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                win_loss_ratio=win_loss_ratio,
                total_trades=total_trades,
                performance_metrics=performance_metrics,
                equity_curve=equity_df,
                trades=self.trades,
            )

        except Exception as e:
            logger.error(f"Failed to calculate results: {e}")
            raise QuantSystemError(f"Results calculation failed: {e}")

    def _call_progress_callback(self, current: int, total: int, message: str):
        """调用进度回调

        Args:
            current: 当前进度
            total: 总进度
            message: 进度消息
        """
        if not self.progress_callback:
            return

        try:
            # 直接调用回调（包装器已在strategy_workflow中处理异步/同步）
            self.progress_callback(current, total, message)
        except Exception as e:
            # 忽略进度回调错误，不影响回测主流程
            logger.debug(f"Progress callback error: {e}")

    def _save_to_database(self, result: BacktestResult):
        """保存回测结果到数据库

        Args:
            result: 回测结果
        """
        try:
            # 保存主结果
            metadata = {
                "strategy_name": self.config.strategy_name,
                "commission_rate": self.config.commission_rate,
                "slippage_bps": self.config.slippage_bps,
                "rebalance_frequency": self.config.rebalance_frequency,
            }

            self.db_manager.save_backtest_result(self.backtest_id, result, metadata)

            # 保存交易记录
            if self.trades:
                self.db_manager.save_trades(self.backtest_id, self.trades)

            # 保存权益曲线
            if not result.equity_curve.empty:
                self.db_manager.save_equity_curve(self.backtest_id, result.equity_curve)

            # 保存性能指标
            if result.performance_metrics:
                self.db_manager.save_performance_metrics(
                    self.backtest_id, result.performance_metrics
                )

            logger.info(
                f"Saved backtest results to database with ID: {self.backtest_id}"
            )

        except Exception as e:
            logger.error(f"Failed to save backtest to database: {e}")


# 便捷函数
def create_backtest_engine(config_dict: Dict[str, Any]) -> BacktestEngine:
    """创建回测引擎的便捷函数

    Args:
        config_dict: 配置字典

    Returns:
        回测引擎实例
    """
    config = BacktestConfig(**config_dict)
    return BacktestEngine(config)
