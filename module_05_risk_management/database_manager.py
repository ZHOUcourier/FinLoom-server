"""
风险管理模块数据库管理器
"""

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from common.exceptions import DatabaseError
from common.logging_system import setup_logger

logger = setup_logger("risk_database_manager")


class RiskDatabaseManager:
    """风险管理数据库管理器"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "module05_risk_management.db")
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_database()
        logger.info(f"RiskDatabaseManager initialized with database: {db_path}")

    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Database connection failed: {e}")

    def _initialize_database(self):
        """初始化数据库表结构"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 投资组合风险表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_risk (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        var_95 REAL,
                        var_99 REAL,
                        cvar_95 REAL,
                        cvar_99 REAL,
                        max_drawdown REAL,
                        sharpe_ratio REAL,
                        sortino_ratio REAL,
                        volatility REAL,
                        correlation_risk REAL,
                        concentration_risk REAL,
                        risk_metrics_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 止损记录表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stop_loss_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        stop_price REAL NOT NULL,
                        max_loss REAL,
                        max_loss_percent REAL,
                        stop_type TEXT,
                        reason TEXT,
                        timestamp TIMESTAMP NOT NULL,
                        triggered BOOLEAN DEFAULT 0,
                        triggered_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 风险敞口表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS exposure_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        total_exposure REAL,
                        effective_leverage REAL,
                        sector_concentration REAL,
                        exposure_data_json TEXT,
                        violations_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 压力测试结果表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stress_test_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id TEXT NOT NULL,
                        scenario_name TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        expected_loss REAL,
                        max_loss REAL,
                        loss_probability REAL,
                        result_data_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # VaR回测表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS var_backtest (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id TEXT NOT NULL,
                        test_date DATE NOT NULL,
                        actual_return REAL,
                        var_estimate REAL,
                        violation BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_portfolio_risk_id_time 
                    ON portfolio_risk(portfolio_id, timestamp)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stop_loss_symbol_time 
                    ON stop_loss_records(symbol, timestamp)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_exposure_id_time 
                    ON exposure_analysis(portfolio_id, timestamp)
                """)

                conn.commit()
                logger.info("Database tables initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    # ==================== 投资组合风险 ====================

    def save_portfolio_risk(
        self, portfolio_id: str, risk_metrics: Dict[str, Any], timestamp: datetime
    ) -> bool:
        """保存投资组合风险数据

        Args:
            portfolio_id: 投资组合ID
            risk_metrics: 风险指标字典
            timestamp: 时间戳

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO portfolio_risk (
                        portfolio_id, timestamp, var_95, var_99, cvar_95, cvar_99,
                        max_drawdown, sharpe_ratio, sortino_ratio, volatility,
                        correlation_risk, concentration_risk, risk_metrics_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        portfolio_id,
                        timestamp,
                        risk_metrics.get("var_95"),
                        risk_metrics.get("var_99"),
                        risk_metrics.get("cvar_95"),
                        risk_metrics.get("cvar_99"),
                        risk_metrics.get("max_drawdown"),
                        risk_metrics.get("sharpe_ratio"),
                        risk_metrics.get("sortino_ratio"),
                        risk_metrics.get("volatility"),
                        risk_metrics.get("correlation_risk"),
                        risk_metrics.get("concentration_risk"),
                        json.dumps(risk_metrics),
                    ),
                )

                conn.commit()
                logger.info(f"Saved portfolio risk for {portfolio_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save portfolio risk: {e}")
            return False

    def get_portfolio_risk_history(
        self,
        portfolio_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """获取投资组合风险历史

        Args:
            portfolio_id: 投资组合ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            风险历史DataFrame
        """
        try:
            with self._get_connection() as conn:
                query = """
                    SELECT * FROM portfolio_risk
                    WHERE portfolio_id = ?
                """
                params = [portfolio_id]

                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)

                query += " ORDER BY timestamp DESC"

                df = pd.read_sql_query(query, conn, params=params)
                logger.info(f"Retrieved {len(df)} risk records for {portfolio_id}")
                return df

        except Exception as e:
            logger.error(f"Failed to get portfolio risk history: {e}")
            return pd.DataFrame()

    # ==================== 止损记录 ====================

    def save_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        stop_price: float,
        max_loss: float,
        max_loss_percent: float,
        stop_type: str,
        reason: str,
        timestamp: datetime,
    ) -> bool:
        """保存止损记录

        Args:
            symbol: 股票代码
            entry_price: 入场价格
            stop_price: 止损价格
            max_loss: 最大损失金额
            max_loss_percent: 最大损失百分比
            stop_type: 止损类型
            reason: 原因
            timestamp: 时间戳

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO stop_loss_records (
                        symbol, entry_price, stop_price, max_loss, max_loss_percent,
                        stop_type, reason, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        symbol,
                        entry_price,
                        stop_price,
                        max_loss,
                        max_loss_percent,
                        stop_type,
                        reason,
                        timestamp,
                    ),
                )

                conn.commit()
                logger.info(f"Saved stop loss for {symbol}")
                return True

        except Exception as e:
            logger.error(f"Failed to save stop loss: {e}")
            return False

    def get_stop_loss_history(
        self, symbol: Optional[str] = None, start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """获取止损历史

        Args:
            symbol: 股票代码（可选）
            start_date: 开始日期（可选）

        Returns:
            止损历史DataFrame
        """
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM stop_loss_records WHERE 1=1"
                params = []

                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)

                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)

                query += " ORDER BY timestamp DESC"

                df = pd.read_sql_query(query, conn, params=params)
                logger.info(f"Retrieved {len(df)} stop loss records")
                return df

        except Exception as e:
            logger.error(f"Failed to get stop loss history: {e}")
            return pd.DataFrame()

    # ==================== 风险敞口 ====================

    def save_exposure_analysis(
        self, portfolio_id: str, exposure: Dict[str, Any], timestamp: datetime
    ) -> bool:
        """保存风险敞口分析

        Args:
            portfolio_id: 投资组合ID
            exposure: 敞口数据
            timestamp: 时间戳

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO exposure_analysis (
                        portfolio_id, timestamp, total_exposure, effective_leverage,
                        sector_concentration, exposure_data_json, violations_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        portfolio_id,
                        timestamp,
                        exposure.get("total_exposure"),
                        exposure.get("effective_leverage"),
                        exposure.get("sector_concentration"),
                        json.dumps(exposure),
                        json.dumps(exposure.get("violations", [])),
                    ),
                )

                conn.commit()
                logger.info(f"Saved exposure analysis for {portfolio_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save exposure analysis: {e}")
            return False

    # ==================== 压力测试 ====================

    def save_stress_test_result(
        self,
        portfolio_id: str,
        scenario: str,
        result: Dict[str, Any],
        timestamp: datetime,
    ) -> bool:
        """保存压力测试结果

        Args:
            portfolio_id: 投资组合ID
            scenario: 情景名称
            result: 测试结果
            timestamp: 时间戳

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO stress_test_results (
                        portfolio_id, scenario_name, timestamp, expected_loss,
                        max_loss, loss_probability, result_data_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        portfolio_id,
                        scenario,
                        timestamp,
                        result.get("expected_loss"),
                        result.get("max_loss"),
                        result.get("loss_probability"),
                        json.dumps(result),
                    ),
                )

                conn.commit()
                logger.info(
                    f"Saved stress test result for {portfolio_id}, scenario={scenario}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to save stress test result: {e}")
            return False

    def get_stress_test_history(self, portfolio_id: str) -> List[Dict]:
        """获取压力测试历史

        Args:
            portfolio_id: 投资组合ID

        Returns:
            测试历史列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM stress_test_results
                    WHERE portfolio_id = ?
                    ORDER BY timestamp DESC
                """,
                    (portfolio_id,),
                )

                rows = cursor.fetchall()

                results = []
                for row in rows:
                    result = dict(row)
                    if result["result_data_json"]:
                        result["result_data"] = json.loads(result["result_data_json"])
                    results.append(result)

                logger.info(
                    f"Retrieved {len(results)} stress test records for {portfolio_id}"
                )
                return results

        except Exception as e:
            logger.error(f"Failed to get stress test history: {e}")
            return []

    # ==================== 数据库统计 ====================

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            统计信息字典
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 各表记录数
                stats = {}

                tables = [
                    "portfolio_risk",
                    "stop_loss_records",
                    "exposure_analysis",
                    "stress_test_results",
                    "var_backtest",
                ]

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()["count"]

                # 数据库大小
                db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB
                stats["database_size_mb"] = db_size

                # 唯一投资组合数
                cursor.execute(
                    "SELECT COUNT(DISTINCT portfolio_id) as count FROM portfolio_risk"
                )
                stats["unique_portfolios"] = cursor.fetchone()["count"]

                logger.info(f"Database stats: {stats}")
                return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 365) -> bool:
        """清理旧数据

        Args:
            days_to_keep: 保留天数

        Returns:
            是否成功
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            with self._get_connection() as conn:
                cursor = conn.cursor()

                tables = [
                    "portfolio_risk",
                    "stop_loss_records",
                    "exposure_analysis",
                    "stress_test_results",
                    "var_backtest",
                ]

                for table in tables:
                    cursor.execute(
                        f"""
                        DELETE FROM {table}
                        WHERE timestamp < ?
                    """,
                        (cutoff_date,),
                    )

                conn.commit()
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                return True

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False


# 全局数据库管理器实例
_risk_db_manager = None


def get_risk_database_manager(
    db_path: str = "data/module05_risk_management.db",
) -> RiskDatabaseManager:
    """获取风险数据库管理器实例（单例模式）

    Args:
        db_path: 数据库路径

    Returns:
        RiskDatabaseManager实例
    """
    global _risk_db_manager
    if _risk_db_manager is None:
        _risk_db_manager = RiskDatabaseManager(db_path)
    return _risk_db_manager
