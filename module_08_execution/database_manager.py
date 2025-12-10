"""
模块08数据库管理器
负责执行模块的数据持久化
"""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from common.exceptions import DatabaseError
from common.logging_system import setup_logger

logger = setup_logger("module08_database")


class ExecutionDatabaseManager:
    """执行模块数据库管理器"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "module08_execution.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

        logger.info(f"ExecutionDatabaseManager initialized with database: {db_path}")

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # 订单表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    signal_id TEXT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL,
                    stop_price REAL,
                    status TEXT NOT NULL,
                    filled_quantity INTEGER DEFAULT 0,
                    filled_price REAL,
                    strategy_name TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    submitted_time TIMESTAMP,
                    filled_time TIMESTAMP,
                    metadata TEXT
                )
            """)

            # 成交记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    commission REAL DEFAULT 0,
                    slippage_bps REAL DEFAULT 0,
                    market_impact_bps REAL DEFAULT 0,
                    timestamp TIMESTAMP NOT NULL,
                    broker TEXT,
                    venue TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            """)

            # 信号表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    confidence REAL NOT NULL,
                    priority INTEGER,
                    strategy_name TEXT NOT NULL,
                    expected_return REAL,
                    risk_score REAL,
                    holding_period INTEGER,
                    metadata TEXT
                )
            """)

            # 执行指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_orders INTEGER DEFAULT 0,
                    filled_orders INTEGER DEFAULT 0,
                    fill_rate REAL DEFAULT 0,
                    avg_slippage_bps REAL DEFAULT 0,
                    max_slippage_bps REAL DEFAULT 0,
                    total_commission REAL DEFAULT 0,
                    market_impact_bps REAL DEFAULT 0,
                    total_volume INTEGER DEFAULT 0,
                    total_value REAL DEFAULT 0,
                    rejection_rate REAL DEFAULT 0,
                    avg_execution_time REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            """)

            # 路由决策表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routing_decisions (
                    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    priority INTEGER,
                    estimated_cost_bps REAL,
                    estimated_slippage_bps REAL,
                    estimated_execution_time INTEGER,
                    reasoning TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            """)

            # 执行算法性能表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS algorithm_performance (
                    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    algorithm_name TEXT NOT NULL,
                    date DATE NOT NULL,
                    order_count INTEGER DEFAULT 0,
                    avg_slippage_bps REAL DEFAULT 0,
                    avg_execution_time REAL DEFAULT 0,
                    fill_rate REAL DEFAULT 0,
                    total_cost_bps REAL DEFAULT 0,
                    UNIQUE(algorithm_name, date)
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_symbol 
                ON orders(symbol)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_status 
                ON orders(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_created_at 
                ON orders(created_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_symbol 
                ON trades(symbol)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp 
                ON trades(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_symbol 
                ON signals(symbol)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_timestamp 
                ON signals(timestamp)
            """)

            conn.commit()
            logger.info("Database tables initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
        finally:
            if conn:
                conn.close()

    def save_order(
        self,
        order_id: str,
        signal_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: int,
        price: Optional[float],
        status: str,
        strategy_name: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> bool:
        """保存订单记录

        Args:
            order_id: 订单ID
            signal_id: 信号ID
            symbol: 股票代码
            side: 买卖方向
            order_type: 订单类型
            quantity: 数量
            price: 价格
            status: 状态
            strategy_name: 策略名称
            timestamp: 时间戳
            **kwargs: 其他字段

        Returns:
            是否保存成功
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            created_at = timestamp or datetime.now()

            cursor.execute(
                """
                INSERT OR REPLACE INTO orders
                (order_id, signal_id, symbol, side, order_type, quantity, price,
                 stop_price, status, filled_quantity, filled_price, strategy_name,
                 created_at, updated_at, submitted_time, filled_time, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    order_id,
                    signal_id,
                    symbol,
                    side,
                    order_type,
                    quantity,
                    price,
                    kwargs.get("stop_price"),
                    status,
                    kwargs.get("filled_quantity", 0),
                    kwargs.get("filled_price"),
                    strategy_name,
                    created_at,
                    datetime.now(),
                    kwargs.get("submitted_time"),
                    kwargs.get("filled_time"),
                    str(kwargs.get("metadata", {})),
                ),
            )

            conn.commit()
            logger.debug(f"Saved order: {order_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to save order {order_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def save_trade(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        commission: float = 0.0,
        slippage_bps: float = 0.0,
        market_impact_bps: float = 0.0,
        timestamp: Optional[datetime] = None,
        broker: Optional[str] = None,
        venue: Optional[str] = None,
    ) -> bool:
        """保存成交记录

        Args:
            order_id: 订单ID
            symbol: 股票代码
            side: 买卖方向
            quantity: 数量
            price: 价格
            commission: 佣金
            slippage_bps: 滑点（基点）
            market_impact_bps: 市场冲击（基点）
            timestamp: 时间戳
            broker: 券商
            venue: 执行场所

        Returns:
            是否保存成功
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            trade_time = timestamp or datetime.now()

            cursor.execute(
                """
                INSERT INTO trades
                (order_id, symbol, side, quantity, price, commission,
                 slippage_bps, market_impact_bps, timestamp, broker, venue)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    order_id,
                    symbol,
                    side,
                    quantity,
                    price,
                    commission,
                    slippage_bps,
                    market_impact_bps,
                    trade_time,
                    broker,
                    venue,
                ),
            )

            conn.commit()
            logger.debug(f"Saved trade for order: {order_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to save trade for order {order_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def save_signal(
        self,
        signal_id: str,
        symbol: str,
        signal_type: str,
        quantity: int,
        price: float,
        confidence: float,
        strategy_name: str,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> bool:
        """保存信号记录

        Args:
            signal_id: 信号ID
            symbol: 股票代码
            signal_type: 信号类型
            quantity: 数量
            price: 价格
            confidence: 置信度
            strategy_name: 策略名称
            timestamp: 时间戳
            **kwargs: 其他字段

        Returns:
            是否保存成功
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            signal_time = timestamp or datetime.now()

            cursor.execute(
                """
                INSERT OR REPLACE INTO signals
                (signal_id, timestamp, symbol, signal_type, quantity, price,
                 confidence, priority, strategy_name, expected_return,
                 risk_score, holding_period, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    signal_id,
                    signal_time,
                    symbol,
                    signal_type,
                    quantity,
                    price,
                    confidence,
                    kwargs.get("priority"),
                    strategy_name,
                    kwargs.get("expected_return"),
                    kwargs.get("risk_score"),
                    kwargs.get("holding_period"),
                    str(kwargs.get("metadata", {})),
                ),
            )

            conn.commit()
            logger.debug(f"Saved signal: {signal_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to save signal {signal_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def save_execution_metrics(self, date: date, metrics: Dict[str, Any]) -> bool:
        """保存执行指标

        Args:
            date: 日期
            metrics: 指标字典

        Returns:
            是否保存成功
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO execution_metrics
                (date, total_orders, filled_orders, fill_rate, avg_slippage_bps,
                 max_slippage_bps, total_commission, market_impact_bps,
                 total_volume, total_value, rejection_rate, avg_execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    date,
                    metrics.get("total_orders", 0),
                    metrics.get("filled_orders", 0),
                    metrics.get("fill_rate", 0.0),
                    metrics.get("avg_slippage_bps", 0.0),
                    metrics.get("max_slippage_bps", 0.0),
                    metrics.get("total_commission", 0.0),
                    metrics.get("market_impact_bps", 0.0),
                    metrics.get("total_volume", 0),
                    metrics.get("total_value", 0.0),
                    metrics.get("rejection_rate", 0.0),
                    metrics.get("avg_execution_time", 0.0),
                ),
            )

            conn.commit()
            logger.debug(f"Saved execution metrics for {date}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to save execution metrics for {date}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """根据订单ID获取订单记录

        Args:
            order_id: 订单ID

        Returns:
            订单字典，如果不存在返回None
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_orders(
        self,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """查询订单列表

        Args:
            status: 订单状态
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大返回数量

        Returns:
            订单列表
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM orders WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)

            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Failed to query orders: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_trades(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """查询成交记录

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大返回数量

        Returns:
            成交记录DataFrame
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))

            query = "SELECT * FROM trades WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, conn, params=params)
            return df

        except Exception as e:
            logger.error(f"Failed to query trades: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()

    def get_execution_metrics(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """查询执行指标

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            执行指标DataFrame
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))

            query = "SELECT * FROM execution_metrics WHERE 1=1"
            params = []

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC"

            df = pd.read_sql_query(query, conn, params=params)
            return df

        except Exception as e:
            logger.error(f"Failed to query execution metrics: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()

    def get_execution_statistics(
        self, start_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取执行统计信息

        Args:
            start_date: 开始日期

        Returns:
            统计信息字典
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # 查询时间范围
            date_filter = ""
            params = []
            if start_date:
                date_filter = "WHERE created_at >= ?"
                params.append(start_date)

            # 总订单数
            cursor.execute(f"SELECT COUNT(*) FROM orders {date_filter}", params)
            total_orders = cursor.fetchone()[0]

            # 成交订单数
            cursor.execute(
                f"SELECT COUNT(*) FROM orders {date_filter} {'AND' if date_filter else 'WHERE'} status = 'FILLED'",
                params,
            )
            filled_orders = cursor.fetchone()[0]

            # 总成交量
            cursor.execute(
                f"SELECT SUM(quantity) FROM trades {date_filter.replace('created_at', 'timestamp')}",
                params,
            )
            total_volume = cursor.fetchone()[0] or 0

            # 平均滑点
            cursor.execute(
                f"SELECT AVG(slippage_bps) FROM trades {date_filter.replace('created_at', 'timestamp')}",
                params,
            )
            avg_slippage = cursor.fetchone()[0] or 0.0

            # 总佣金
            cursor.execute(
                f"SELECT SUM(commission) FROM trades {date_filter.replace('created_at', 'timestamp')}",
                params,
            )
            total_commission = cursor.fetchone()[0] or 0.0

            return {
                "total_orders": total_orders,
                "filled_orders": filled_orders,
                "fill_rate": filled_orders / total_orders if total_orders > 0 else 0.0,
                "total_volume": total_volume,
                "avg_slippage_bps": avg_slippage,
                "total_commission": total_commission,
            }

        except sqlite3.Error as e:
            logger.error(f"Failed to get execution statistics: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def get_database_stats(self) -> Dict[str, int]:
        """获取数据库统计信息

        Returns:
            数据库统计字典
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            stats = {}

            # 各表记录数
            for table in [
                "orders",
                "trades",
                "signals",
                "execution_metrics",
                "routing_decisions",
            ]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # 数据库文件大小
            stats["db_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)

            return stats

        except sqlite3.Error as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
        finally:
            if conn:
                conn.close()


# 全局数据库管理器实例
_global_db_manager: Optional[ExecutionDatabaseManager] = None


def get_execution_database_manager(
    db_path: str = "data/module08_execution.db",
) -> ExecutionDatabaseManager:
    """获取全局数据库管理器实例

    Args:
        db_path: 数据库路径

    Returns:
        数据库管理器实例
    """
    global _global_db_manager
    if _global_db_manager is None:
        _global_db_manager = ExecutionDatabaseManager(db_path)
    return _global_db_manager
