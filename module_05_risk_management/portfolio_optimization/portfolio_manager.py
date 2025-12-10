"""
投资组合管理器模块
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import sqlite3
import json

from common.data_structures import Position, MarketData
from common.logging_system import setup_logger
from common.exceptions import QuantSystemError

logger = setup_logger("portfolio_manager")

@dataclass
class PortfolioConfig:
    """投资组合配置"""
    max_positions: int = 20
    max_position_weight: float = 0.1
    min_position_weight: float = 0.01
    rebalance_threshold: float = 0.05
    risk_free_rate: float = 0.03
    target_volatility: float = 0.15

@dataclass
class PortfolioMetrics:
    """投资组合指标"""
    total_value: float
    cash: float
    positions_value: float
    total_return: float
    daily_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float
    alpha: float
    win_rate: float
    profit_factor: float
    total_trades: int
    timestamp: datetime

class PortfolioManager:
    """投资组合管理器类"""
    
    def __init__(self, config: PortfolioConfig = None, db_path: str = None):
        """初始化投资组合管理器
        
        Args:
            config: 投资组合配置
            db_path: 数据库路径
        """
        self.config = config or PortfolioConfig()
        if db_path is None:
            import os
            db_path = os.path.join("data", "portfolio.db")
        self.db_path = db_path
        self.positions: Dict[str, Position] = {}
        self.cash = 0.0
        self.initial_capital = 0.0
        self.trade_history = []
        self.performance_history = []
        
        # 初始化数据库
        self._init_database()
        
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建持仓表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    position_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    avg_cost REAL NOT NULL,
                    current_price REAL,
                    market_value REAL,
                    unrealized_pnl REAL,
                    realized_pnl REAL,
                    open_time TEXT NOT NULL,
                    last_update TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # 创建交易历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    amount REAL NOT NULL,
                    commission REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    signal_id TEXT,
                    metadata TEXT
                )
            ''')
            
            # 创建投资组合历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_value REAL NOT NULL,
                    cash REAL NOT NULL,
                    positions_value REAL NOT NULL,
                    total_return REAL NOT NULL,
                    daily_return REAL NOT NULL,
                    volatility REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    beta REAL,
                    alpha REAL,
                    win_rate REAL,
                    profit_factor REAL,
                    total_trades INTEGER,
                    metadata TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Portfolio database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize portfolio database: {e}")
            raise QuantSystemError(f"Database initialization failed: {e}")
    
    def initialize_portfolio(self, initial_capital: float):
        """初始化投资组合
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.trade_history = []
        self.performance_history = []
        
        logger.info(f"Portfolio initialized with capital: {initial_capital}")
    
    def add_position(self, position: Position):
        """添加持仓
        
        Args:
            position: 持仓对象
        """
        self.positions[position.symbol] = position
        self._save_position_to_db(position)
        logger.info(f"Added position: {position.symbol} - {position.quantity} shares")
    
    def remove_position(self, symbol: str):
        """移除持仓
        
        Args:
            symbol: 股票代码
        """
        if symbol in self.positions:
            del self.positions[symbol]
            self._remove_position_from_db(symbol)
            logger.info(f"Removed position: {symbol}")
    
    def update_position(self, symbol: str, current_price: float):
        """更新持仓价格
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
        """
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = current_price
            position.market_value = position.quantity * current_price
            position.unrealized_pnl = position.market_value - (position.quantity * position.avg_cost)
            position.last_update = datetime.now()
            
            self._update_position_in_db(position)
    
    def execute_trade(self, symbol: str, action: str, quantity: int, price: float, 
                     commission: float = 0.001, signal_id: str = None) -> bool:
        """执行交易
        
        Args:
            symbol: 股票代码
            action: 交易动作 (BUY/SELL)
            quantity: 交易数量
            price: 交易价格
            commission: 手续费率
            signal_id: 信号ID
            
        Returns:
            是否执行成功
        """
        try:
            trade_amount = quantity * price
            commission_fee = trade_amount * commission
            total_cost = trade_amount + commission_fee
            
            if action == "BUY":
                if total_cost > self.cash:
                    logger.warning(f"Insufficient cash for buy order: {symbol}")
                    return False
                
                # 更新现金
                self.cash -= total_cost
                
                # 更新或创建持仓
                if symbol in self.positions:
                    position = self.positions[symbol]
                    # 计算新的平均成本
                    total_quantity = position.quantity + quantity
                    total_cost_basis = (position.quantity * position.avg_cost) + trade_amount
                    position.avg_cost = total_cost_basis / total_quantity
                    position.quantity = total_quantity
                else:
                    # 创建新持仓
                    position = Position(
                        position_id=f"pos_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        symbol=symbol,
                        quantity=quantity,
                        avg_cost=price,
                        current_price=price,
                        market_value=trade_amount,
                        unrealized_pnl=0.0,
                        realized_pnl=0.0,
                        open_time=datetime.now(),
                        last_update=datetime.now()
                    )
                    self.positions[symbol] = position
                
            elif action == "SELL":
                if symbol not in self.positions:
                    logger.warning(f"No position for sell order: {symbol}")
                    return False
                
                position = self.positions[symbol]
                if quantity > position.quantity:
                    logger.warning(f"Insufficient shares for sell order: {symbol}")
                    return False
                
                # 更新现金
                self.cash += trade_amount - commission_fee
                
                # 计算已实现盈亏
                realized_pnl = (price - position.avg_cost) * quantity
                position.realized_pnl += realized_pnl
                
                # 更新持仓
                position.quantity -= quantity
                if position.quantity <= 0:
                    del self.positions[symbol]
            
            # 记录交易
            trade_record = {
                'trade_id': f"trade_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'amount': trade_amount,
                'commission': commission_fee,
                'timestamp': datetime.now().isoformat(),
                'signal_id': signal_id
            }
            
            self.trade_history.append(trade_record)
            self._save_trade_to_db(trade_record)
            
            logger.info(f"Executed {action} trade: {quantity} {symbol} at {price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            return False
    
    def calculate_portfolio_metrics(self, market_data: Dict[str, float] = None) -> PortfolioMetrics:
        """计算投资组合指标
        
        Args:
            market_data: 市场数据字典 {symbol: current_price}
            
        Returns:
            投资组合指标
        """
        try:
            # 更新持仓价格
            if market_data:
                for symbol, price in market_data.items():
                    if symbol in self.positions:
                        self.update_position(symbol, price)
            
            # 计算持仓总价值
            positions_value = sum(pos.market_value for pos in self.positions.values())
            total_value = self.cash + positions_value
            
            # 计算总收益率
            total_return = (total_value - self.initial_capital) / self.initial_capital if self.initial_capital > 0 else 0.0
            
            # 计算日收益率
            daily_return = 0.0
            if len(self.performance_history) > 0:
                prev_value = self.performance_history[-1].total_value
                daily_return = (total_value - prev_value) / prev_value if prev_value > 0 else 0.0
            
            # 计算波动率
            volatility = 0.0
            if len(self.performance_history) > 10:
                returns = [p.daily_return for p in self.performance_history[-30:]]
                volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0.0
            
            # 计算夏普比率
            sharpe_ratio = 0.0
            if volatility > 0:
                excess_return = (1 + total_return) ** (1/252) - 1 - self.config.risk_free_rate/252
                sharpe_ratio = excess_return / (volatility / np.sqrt(252))
            
            # 计算最大回撤
            max_drawdown = 0.0
            if len(self.performance_history) > 1:
                values = [p.total_value for p in self.performance_history]
                peak = values[0]
                for value in values:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak
                    max_drawdown = max(max_drawdown, drawdown)
            
            # 计算交易统计
            total_trades = len(self.trade_history)
            winning_trades = len([t for t in self.trade_history if t.get('realized_pnl', 0) > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            
            # 计算盈亏比
            total_profit = sum([t.get('realized_pnl', 0) for t in self.trade_history if t.get('realized_pnl', 0) > 0])
            total_loss = abs(sum([t.get('realized_pnl', 0) for t in self.trade_history if t.get('realized_pnl', 0) < 0]))
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            metrics = PortfolioMetrics(
                total_value=total_value,
                cash=self.cash,
                positions_value=positions_value,
                total_return=total_return,
                daily_return=daily_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                beta=0.0,  # 简化计算
                alpha=0.0,  # 简化计算
                win_rate=win_rate,
                profit_factor=profit_factor,
                total_trades=total_trades,
                timestamp=datetime.now()
            )
            
            # 保存性能历史
            self.performance_history.append(metrics)
            self._save_portfolio_history_to_db(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate portfolio metrics: {e}")
            raise QuantSystemError(f"Portfolio metrics calculation failed: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取投资组合摘要
        
        Returns:
            投资组合摘要字典
        """
        try:
            metrics = self.calculate_portfolio_metrics()
            
            # 获取持仓详情
            positions_data = []
            for symbol, position in self.positions.items():
                weight = position.market_value / metrics.total_value if metrics.total_value > 0 else 0.0
                positions_data.append({
                    'symbol': symbol,
                    'quantity': position.quantity,
                    'avg_cost': position.avg_cost,
                    'current_price': position.current_price,
                    'market_value': position.market_value,
                    'unrealized_pnl': position.unrealized_pnl,
                    'pnl_rate': (position.unrealized_pnl / (position.quantity * position.avg_cost)) * 100 if position.quantity * position.avg_cost > 0 else 0.0,
                    'weight': weight,
                    'sector': '金融'  # 简化处理
                })
            
            return {
                'total_value': metrics.total_value,
                'cash': metrics.cash,
                'positions_value': metrics.positions_value,
                'total_return': metrics.total_return * 100,  # 转换为百分比
                'daily_return': metrics.daily_return * 100,
                'volatility': metrics.volatility * 100,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown * 100,
                'win_rate': metrics.win_rate * 100,
                'total_trades': metrics.total_trades,
                'positions': positions_data,
                'timestamp': metrics.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            return {}
    
    def _save_position_to_db(self, position: Position):
        """保存持仓到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO positions 
                (position_id, symbol, quantity, avg_cost, current_price, market_value, 
                 unrealized_pnl, realized_pnl, open_time, last_update, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position.position_id,
                position.symbol,
                position.quantity,
                position.avg_cost,
                position.current_price,
                position.market_value,
                position.unrealized_pnl,
                position.realized_pnl,
                position.open_time.isoformat(),
                position.last_update.isoformat(),
                json.dumps({})
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save position to database: {e}")
    
    def _update_position_in_db(self, position: Position):
        """更新数据库中的持仓"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE positions SET 
                current_price = ?, market_value = ?, unrealized_pnl = ?, 
                realized_pnl = ?, last_update = ?
                WHERE position_id = ?
            ''', (
                position.current_price,
                position.market_value,
                position.unrealized_pnl,
                position.realized_pnl,
                position.last_update.isoformat(),
                position.position_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update position in database: {e}")
    
    def _remove_position_from_db(self, symbol: str):
        """从数据库中删除持仓"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM positions WHERE symbol = ?', (symbol,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to remove position from database: {e}")
    
    def _save_trade_to_db(self, trade: Dict[str, Any]):
        """保存交易到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades 
                (trade_id, symbol, action, quantity, price, amount, commission, timestamp, signal_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['trade_id'],
                trade['symbol'],
                trade['action'],
                trade['quantity'],
                trade['price'],
                trade['amount'],
                trade['commission'],
                trade['timestamp'],
                trade.get('signal_id'),
                json.dumps({})
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save trade to database: {e}")
    
    def _save_portfolio_history_to_db(self, metrics: PortfolioMetrics):
        """保存投资组合历史到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO portfolio_history 
                (timestamp, total_value, cash, positions_value, total_return, daily_return,
                 volatility, sharpe_ratio, max_drawdown, beta, alpha, win_rate, profit_factor, total_trades, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp.isoformat(),
                metrics.total_value,
                metrics.cash,
                metrics.positions_value,
                metrics.total_return,
                metrics.daily_return,
                metrics.volatility,
                metrics.sharpe_ratio,
                metrics.max_drawdown,
                metrics.beta,
                metrics.alpha,
                metrics.win_rate,
                metrics.profit_factor,
                metrics.total_trades,
                json.dumps({})
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save portfolio history to database: {e}")

# 便捷函数
def create_portfolio_manager(config: PortfolioConfig = None) -> PortfolioManager:
    """创建投资组合管理器的便捷函数
    
    Args:
        config: 投资组合配置
        
    Returns:
        投资组合管理器实例
    """
    return PortfolioManager(config)
