"""
回测数据库管理模块
负责回测结果、性能指标和交易记录的SQLite存储
"""

import json
import pickle
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from common.exceptions import QuantSystemError
from common.logging_system import setup_logger

logger = setup_logger("backtest_database")


class BacktestDatabaseManager:
    """回测数据库管理器"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os

            db_path = os.path.join("data", "module09_backtest.db")
        self.db_path = db_path

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._initialize_database()

        logger.info(f"Backtest database initialized at {db_path}")

    def _initialize_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()

        # 创建回测结果主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                backtest_id TEXT PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                final_capital REAL NOT NULL,
                total_return REAL,
                annualized_return REAL,
                volatility REAL,
                sharpe_ratio REAL,
                sortino_ratio REAL,
                calmar_ratio REAL,
                max_drawdown REAL,
                max_drawdown_duration INTEGER,
                win_rate REAL,
                profit_factor REAL,
                total_trades INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        # 创建交易记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                value REAL NOT NULL,
                commission REAL DEFAULT 0,
                slippage REAL DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                trade_date TEXT NOT NULL,
                signal_id TEXT,
                metadata TEXT,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(backtest_id)
            )
        """)

        # 创建每日权益曲线表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL,
                date TEXT NOT NULL,
                equity REAL NOT NULL,
                cash REAL NOT NULL,
                positions_value REAL DEFAULT 0,
                daily_return REAL,
                cumulative_return REAL,
                drawdown REAL,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(backtest_id),
                UNIQUE(backtest_id, date)
            )
        """)

        # 创建性能指标表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_category TEXT,
                calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(backtest_id)
            )
        """)

        # 创建持仓记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                exit_date TEXT,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity INTEGER NOT NULL,
                side TEXT NOT NULL,
                realized_pnl REAL DEFAULT 0,
                holding_period INTEGER,
                max_profit REAL DEFAULT 0,
                max_loss REAL DEFAULT 0,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(backtest_id)
            )
        """)

        # 创建风险指标表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL,
                var_95 REAL,
                var_99 REAL,
                cvar_95 REAL,
                cvar_99 REAL,
                downside_deviation REAL,
                beta REAL,
                alpha REAL,
                information_ratio REAL,
                tracking_error REAL,
                calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(backtest_id)
            )
        """)

        # 创建索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_backtest_date ON backtest_results(start_date, end_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trades_backtest ON trades(backtest_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(trade_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_equity_backtest ON equity_curve(backtest_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_positions_backtest ON positions(backtest_id)"
        )

        conn.commit()
        conn.close()

    def save_backtest_result(
        self, backtest_id: str, result: Any, metadata: Optional[Dict] = None
    ) -> bool:
        """保存回测结果

        Args:
            backtest_id: 回测ID
            result: 回测结果对象
            metadata: 额外的元数据

        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # 准备数据
                metadata_json = json.dumps(metadata or {})

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO backtest_results (
                        backtest_id, strategy_name, start_date, end_date,
                        initial_capital, final_capital, total_return,
                        annualized_return, volatility, sharpe_ratio,
                        sortino_ratio, calmar_ratio, max_drawdown,
                        max_drawdown_duration, win_rate, profit_factor,
                        total_trades, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        backtest_id,
                        metadata.get("strategy_name", "Unknown")
                        if metadata
                        else "Unknown",
                        result.start_date.strftime("%Y-%m-%d"),
                        result.end_date.strftime("%Y-%m-%d"),
                        result.initial_capital,
                        result.final_capital,
                        result.total_return,
                        result.annualized_return,
                        result.volatility,
                        result.sharpe_ratio,
                        getattr(result, "sortino_ratio", None),
                        getattr(result, "calmar_ratio", None),
                        result.max_drawdown,
                        getattr(result, "max_drawdown_duration", None),
                        result.win_rate,
                        result.profit_factor,
                        result.total_trades,
                        metadata_json,
                    ),
                )

                conn.commit()

            logger.info(f"Saved backtest result: {backtest_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save backtest result: {e}")
            return False

    def save_trades(self, backtest_id: str, trades: List[Dict]) -> bool:
        """保存交易记录

        Args:
            backtest_id: 回测ID
            trades: 交易记录列表

        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                for trade in trades:
                    metadata = {
                        k: v
                        for k, v in trade.items()
                        if k
                        not in [
                            "symbol",
                            "action",
                            "quantity",
                            "price",
                            "value",
                            "commission",
                            "realized_pnl",
                            "date",
                            "signal_id",
                        ]
                    }

                    cursor.execute(
                        """
                        INSERT INTO trades (
                            backtest_id, symbol, side, quantity, price,
                            value, commission, slippage, realized_pnl,
                            trade_date, signal_id, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            backtest_id,
                            trade.get("symbol"),
                            trade.get("action", trade.get("side")),
                            trade.get("quantity"),
                            trade.get("price"),
                            trade.get("value"),
                            trade.get("commission", 0),
                            trade.get("slippage", 0),
                            trade.get("realized_pnl", 0),
                            trade.get("date", datetime.now()).strftime("%Y-%m-%d")
                            if isinstance(trade.get("date"), datetime)
                            else str(trade.get("date")),
                            trade.get("signal_id"),
                            json.dumps(metadata),
                        ),
                    )

                conn.commit()

            logger.info(f"Saved {len(trades)} trades for backtest {backtest_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save trades: {e}")
            return False

    def save_equity_curve(self, backtest_id: str, equity_curve: pd.DataFrame) -> bool:
        """保存权益曲线

        Args:
            backtest_id: 回测ID
            equity_curve: 权益曲线DataFrame

        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # 计算每日收益率和回撤
                equity_series = (
                    equity_curve["equity"]
                    if "equity" in equity_curve.columns
                    else equity_curve.iloc[:, 0]
                )
                daily_returns = equity_series.pct_change()
                cumulative_returns = (1 + daily_returns).cumprod() - 1

                running_max = equity_series.expanding().max()
                drawdown = (equity_series - running_max) / running_max

                for idx, row in equity_curve.iterrows():
                    date_str = (
                        idx.strftime("%Y-%m-%d")
                        if isinstance(idx, pd.Timestamp)
                        else str(idx)
                    )

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO equity_curve (
                            backtest_id, date, equity, cash, positions_value,
                            daily_return, cumulative_return, drawdown
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            backtest_id,
                            date_str,
                            row.get("equity", equity_series.loc[idx]),
                            row.get("cash", 0),
                            row.get("positions_value", 0),
                            daily_returns.loc[idx]
                            if idx in daily_returns.index
                            else None,
                            cumulative_returns.loc[idx]
                            if idx in cumulative_returns.index
                            else None,
                            drawdown.loc[idx] if idx in drawdown.index else None,
                        ),
                    )

                conn.commit()

            logger.info(f"Saved equity curve for backtest {backtest_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save equity curve: {e}")
            return False

    def save_performance_metrics(
        self, backtest_id: str, metrics: Dict[str, float], category: str = "general"
    ) -> bool:
        """保存性能指标

        Args:
            backtest_id: 回测ID
            metrics: 指标字典
            category: 指标类别

        Returns:
            是否保存成功
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                for metric_name, metric_value in metrics.items():
                    cursor.execute(
                        """
                        INSERT INTO performance_metrics (
                            backtest_id, metric_name, metric_value, metric_category
                        ) VALUES (?, ?, ?, ?)
                    """,
                        (backtest_id, metric_name, float(metric_value), category),
                    )

                conn.commit()

            logger.info(
                f"Saved {len(metrics)} performance metrics for backtest {backtest_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")
            return False

    def get_backtest_result(self, backtest_id: str) -> Optional[Dict]:
        """获取回测结果

        Args:
            backtest_id: 回测ID

        Returns:
            回测结果字典
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM backtest_results WHERE backtest_id = ?",
                    (backtest_id,),
                )
                row = cursor.fetchone()

                if row:
                    result = dict(row)
                    result["metadata"] = json.loads(result.get("metadata", "{}"))
                    return result

                return None

        except Exception as e:
            logger.error(f"Failed to get backtest result: {e}")
            return None

    def get_trades(self, backtest_id: str) -> pd.DataFrame:
        """获取交易记录

        Args:
            backtest_id: 回测ID

        Returns:
            交易记录DataFrame
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                query = "SELECT * FROM trades WHERE backtest_id = ? ORDER BY trade_date"
                df = pd.read_sql_query(query, conn, params=(backtest_id,))
                return df

        except Exception as e:
            logger.error(f"Failed to get trades: {e}")
            return pd.DataFrame()

    def get_equity_curve(self, backtest_id: str) -> pd.DataFrame:
        """获取权益曲线

        Args:
            backtest_id: 回测ID

        Returns:
            权益曲线DataFrame
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                query = "SELECT * FROM equity_curve WHERE backtest_id = ? ORDER BY date"
                df = pd.read_sql_query(query, conn, params=(backtest_id,))
                if not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    df.set_index("date", inplace=True)
                return df

        except Exception as e:
            logger.error(f"Failed to get equity curve: {e}")
            return pd.DataFrame()

    def get_performance_metrics(
        self, backtest_id: str, category: Optional[str] = None
    ) -> Dict[str, float]:
        """获取性能指标

        Args:
            backtest_id: 回测ID
            category: 指标类别（可选）

        Returns:
            指标字典
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                if category:
                    cursor.execute(
                        """
                        SELECT metric_name, metric_value 
                        FROM performance_metrics 
                        WHERE backtest_id = ? AND metric_category = ?
                    """,
                        (backtest_id, category),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT metric_name, metric_value 
                        FROM performance_metrics 
                        WHERE backtest_id = ?
                    """,
                        (backtest_id,),
                    )

                metrics = {row[0]: row[1] for row in cursor.fetchall()}
                return metrics

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}

    def list_backtests(self, limit: int = 100) -> pd.DataFrame:
        """列出所有回测

        Args:
            limit: 返回数量限制

        Returns:
            回测列表DataFrame
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                query = """
                    SELECT backtest_id, strategy_name, start_date, end_date,
                           total_return, sharpe_ratio, max_drawdown, total_trades,
                           created_at
                    FROM backtest_results
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(limit,))
                return df

        except Exception as e:
            logger.error(f"Failed to list backtests: {e}")
            return pd.DataFrame()

    def delete_backtest(self, backtest_id: str) -> bool:
        """删除回测及相关数据

        Args:
            backtest_id: 回测ID

        Returns:
            是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # 删除相关表数据
                cursor.execute(
                    "DELETE FROM trades WHERE backtest_id = ?", (backtest_id,)
                )
                cursor.execute(
                    "DELETE FROM equity_curve WHERE backtest_id = ?", (backtest_id,)
                )
                cursor.execute(
                    "DELETE FROM performance_metrics WHERE backtest_id = ?",
                    (backtest_id,),
                )
                cursor.execute(
                    "DELETE FROM positions WHERE backtest_id = ?", (backtest_id,)
                )
                cursor.execute(
                    "DELETE FROM risk_metrics WHERE backtest_id = ?", (backtest_id,)
                )
                cursor.execute(
                    "DELETE FROM backtest_results WHERE backtest_id = ?", (backtest_id,)
                )

                conn.commit()

            logger.info(f"Deleted backtest: {backtest_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backtest: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                stats = {}

                # 回测数量
                cursor.execute("SELECT COUNT(*) FROM backtest_results")
                stats["total_backtests"] = cursor.fetchone()[0]

                # 交易数量
                cursor.execute("SELECT COUNT(*) FROM trades")
                stats["total_trades"] = cursor.fetchone()[0]

                # 平均夏普比率
                cursor.execute(
                    "SELECT AVG(sharpe_ratio) FROM backtest_results WHERE sharpe_ratio IS NOT NULL"
                )
                result = cursor.fetchone()
                stats["avg_sharpe_ratio"] = result[0] if result[0] else 0

                # 平均最大回撤
                cursor.execute(
                    "SELECT AVG(max_drawdown) FROM backtest_results WHERE max_drawdown IS NOT NULL"
                )
                result = cursor.fetchone()
                stats["avg_max_drawdown"] = result[0] if result[0] else 0

                # 数据库大小
                cursor.execute(
                    "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
                )
                result = cursor.fetchone()
                stats["database_size_mb"] = result[0] / (1024 * 1024) if result else 0

                return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# 全局数据库管理器实例
_database_manager: Optional[BacktestDatabaseManager] = None


def get_backtest_database_manager(
    db_path: str = "data/module09_backtest.db",
) -> BacktestDatabaseManager:
    """获取全局数据库管理器实例

    Args:
        db_path: 数据库路径

    Returns:
        数据库管理器实例
    """
    global _database_manager
    if _database_manager is None:
        _database_manager = BacktestDatabaseManager(db_path)
    return _database_manager
