"""
监控告警模块数据库管理器
负责监控数据的持久化存储
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from common.logging_system import setup_logger

logger = setup_logger("monitoring_database")


class MonitoringDatabaseManager:
    """监控数据库管理器类"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "module06_monitoring.db")
        self.db_path = db_path
        self._ensure_database_exists()
        self._initialize_tables()
        logger.info(f"Initialized monitoring database at {db_path}")

    def _ensure_database_exists(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接

        Returns:
            数据库连接对象
        """
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 系统健康状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                network_sent_mb REAL,
                network_recv_mb REAL,
                active_threads INTEGER,
                python_memory_mb REAL,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 性能指标表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                operation TEXT NOT NULL,
                duration REAL,
                success BOOLEAN,
                error_message TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 告警记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                rule_id TEXT,
                timestamp DATETIME NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                metric_value REAL,
                threshold_value REAL,
                status TEXT,
                acknowledged_by TEXT,
                acknowledged_at DATETIME,
                resolved_at DATETIME,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 市场事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                timestamp DATETIME NOT NULL,
                symbol TEXT,
                event_type TEXT NOT NULL,
                severity REAL,
                description TEXT,
                affected_symbols TEXT,
                data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 投资组合快照表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                total_value REAL,
                cash_balance REAL,
                positions_value REAL,
                daily_pnl REAL,
                daily_return REAL,
                unrealized_pnl REAL,
                realized_pnl REAL,
                total_pnl REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                current_drawdown REAL,
                var_95 REAL,
                leverage REAL,
                num_positions INTEGER,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 通知记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT UNIQUE NOT NULL,
                timestamp DATETIME NOT NULL,
                type TEXT NOT NULL,
                priority TEXT NOT NULL,
                channel TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                sent_at DATETIME,
                delivered BOOLEAN,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 报告生成记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                report_type TEXT NOT NULL,
                period_start DATETIME,
                period_end DATETIME,
                generated_at DATETIME NOT NULL,
                format TEXT NOT NULL,
                file_path TEXT,
                status TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_health_timestamp 
            ON system_health(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp 
            ON performance_metrics(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
            ON alerts(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_events_timestamp 
            ON market_events(timestamp)
        """)

        conn.commit()
        conn.close()
        logger.info("Database tables initialized")

    def save_health_status(
        self,
        timestamp: datetime,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
        network_sent_mb: float = 0.0,
        network_recv_mb: float = 0.0,
        active_threads: int = 0,
        python_memory_mb: float = 0.0,
        status: str = "normal",
    ) -> bool:
        """保存系统健康状态

        Args:
            timestamp: 时间戳
            cpu_usage: CPU使用率
            memory_usage: 内存使用率
            disk_usage: 磁盘使用率
            network_sent_mb: 网络发送MB
            network_recv_mb: 网络接收MB
            active_threads: 活跃线程数
            python_memory_mb: Python内存使用MB
            status: 状态

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO system_health 
                (timestamp, cpu_usage, memory_usage, disk_usage, network_sent_mb, 
                 network_recv_mb, active_threads, python_memory_mb, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    cpu_usage,
                    memory_usage,
                    disk_usage,
                    network_sent_mb,
                    network_recv_mb,
                    active_threads,
                    python_memory_mb,
                    status,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to save health status: {e}")
            return False

    def save_performance_metrics(
        self,
        timestamp: datetime,
        operation: str,
        duration: float,
        success: bool,
        error_message: str = None,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """保存性能指标

        Args:
            timestamp: 时间戳
            operation: 操作名称
            duration: 持续时间
            success: 是否成功
            error_message: 错误消息
            metadata: 元数据

        Returns:
            是否保存成功
        """
        try:
            import json

            conn = self._get_connection()
            cursor = conn.cursor()

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute(
                """
                INSERT INTO performance_metrics 
                (timestamp, operation, duration, success, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, operation, duration, success, error_message, metadata_json),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")
            return False

    def save_alert(
        self,
        alert_id: str,
        rule_id: str,
        timestamp: datetime,
        severity: str,
        category: str,
        title: str,
        message: str,
        metric_value: float = None,
        threshold_value: float = None,
        status: str = "triggered",
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """保存告警记录

        Args:
            alert_id: 告警ID
            rule_id: 规则ID
            timestamp: 时间戳
            severity: 严重级别
            category: 类别
            title: 标题
            message: 消息
            metric_value: 指标值
            threshold_value: 阈值
            status: 状态
            metadata: 元数据

        Returns:
            是否保存成功
        """
        try:
            import json

            conn = self._get_connection()
            cursor = conn.cursor()

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute(
                """
                INSERT OR REPLACE INTO alerts 
                (alert_id, rule_id, timestamp, severity, category, title, message, 
                 metric_value, threshold_value, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert_id,
                    rule_id,
                    timestamp,
                    severity,
                    category,
                    title,
                    message,
                    metric_value,
                    threshold_value,
                    status,
                    metadata_json,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to save alert: {e}")
            return False

    def save_market_event(
        self,
        event_id: str,
        timestamp: datetime,
        symbol: str,
        event_type: str,
        severity: float,
        description: str,
        affected_symbols: List[str] = None,
        data: Dict[str, Any] = None,
    ) -> bool:
        """保存市场事件

        Args:
            event_id: 事件ID
            timestamp: 时间戳
            symbol: 股票代码
            event_type: 事件类型
            severity: 严重程度
            description: 描述
            affected_symbols: 影响的股票列表
            data: 事件数据

        Returns:
            是否保存成功
        """
        try:
            import json

            conn = self._get_connection()
            cursor = conn.cursor()

            affected_symbols_json = (
                json.dumps(affected_symbols) if affected_symbols else None
            )
            data_json = json.dumps(data) if data else None

            cursor.execute(
                """
                INSERT OR REPLACE INTO market_events 
                (event_id, timestamp, symbol, event_type, severity, description, 
                 affected_symbols, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    timestamp,
                    symbol,
                    event_type,
                    severity,
                    description,
                    affected_symbols_json,
                    data_json,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to save market event: {e}")
            return False

    def save_portfolio_snapshot(
        self, timestamp: datetime, metrics: Dict[str, Any]
    ) -> bool:
        """保存投资组合快照

        Args:
            timestamp: 时间戳
            metrics: 指标字典

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO portfolio_snapshots 
                (timestamp, total_value, cash_balance, positions_value, daily_pnl, 
                 daily_return, unrealized_pnl, realized_pnl, total_pnl, sharpe_ratio, 
                 max_drawdown, current_drawdown, var_95, leverage, num_positions, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    metrics.get("total_value", 0),
                    metrics.get("cash_balance", 0),
                    metrics.get("positions_value", 0),
                    metrics.get("daily_pnl", 0),
                    metrics.get("daily_return", 0),
                    metrics.get("unrealized_pnl", 0),
                    metrics.get("realized_pnl", 0),
                    metrics.get("total_pnl", 0),
                    metrics.get("sharpe_ratio", 0),
                    metrics.get("max_drawdown", 0),
                    metrics.get("current_drawdown", 0),
                    metrics.get("var_95", 0),
                    metrics.get("leverage", 0),
                    metrics.get("num_positions", 0),
                    metrics.get("status", "normal"),
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to save portfolio snapshot: {e}")
            return False

    def save_notification(
        self,
        notification_id: str,
        timestamp: datetime,
        type: str,
        priority: str,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
        sent_at: datetime = None,
        delivered: bool = False,
        retry_count: int = 0,
        error_message: str = None,
    ) -> bool:
        """保存通知记录

        Args:
            notification_id: 通知ID
            timestamp: 时间戳
            type: 类型
            priority: 优先级
            channel: 渠道
            recipient: 接收者
            subject: 主题
            message: 消息
            sent_at: 发送时间
            delivered: 是否已送达
            retry_count: 重试次数
            error_message: 错误消息

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO notifications 
                (notification_id, timestamp, type, priority, channel, recipient, 
                 subject, message, sent_at, delivered, retry_count, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notification_id,
                    timestamp,
                    type,
                    priority,
                    channel,
                    recipient,
                    subject,
                    message,
                    sent_at,
                    delivered,
                    retry_count,
                    error_message,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to save notification: {e}")
            return False

    def save_report(
        self,
        report_id: str,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        generated_at: datetime,
        format: str,
        file_path: str,
        status: str = "completed",
        error_message: str = None,
    ) -> bool:
        """保存报告记录

        Args:
            report_id: 报告ID
            report_type: 报告类型
            period_start: 周期开始
            period_end: 周期结束
            generated_at: 生成时间
            format: 格式
            file_path: 文件路径
            status: 状态
            error_message: 错误消息

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO reports 
                (report_id, report_type, period_start, period_end, generated_at, 
                 format, file_path, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    report_type,
                    period_start,
                    period_end,
                    generated_at,
                    format,
                    file_path,
                    status,
                    error_message,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return False

    def get_health_history(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """获取健康状态历史

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量

        Returns:
            健康状态数据框
        """
        try:
            conn = self._get_connection()

            query = "SELECT * FROM system_health WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            return df

        except Exception as e:
            logger.error(f"Failed to get health history: {e}")
            return pd.DataFrame()

    def get_performance_history(
        self,
        operation: str = None,
        start_date: datetime = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """获取性能历史

        Args:
            operation: 操作名称
            start_date: 开始日期
            limit: 限制数量

        Returns:
            性能数据框
        """
        try:
            conn = self._get_connection()

            query = "SELECT * FROM performance_metrics WHERE 1=1"
            params = []

            if operation:
                query += " AND operation = ?"
                params.append(operation)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            return df

        except Exception as e:
            logger.error(f"Failed to get performance history: {e}")
            return pd.DataFrame()

    def get_alerts(
        self,
        severity: str = None,
        category: str = None,
        status: str = None,
        start_date: datetime = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取告警列表

        Args:
            severity: 严重级别
            category: 类别
            status: 状态
            start_date: 开始日期
            limit: 限制数量

        Returns:
            告警列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM alerts WHERE 1=1"
            params = []

            if severity:
                query += " AND severity = ?"
                params.append(severity)

            if category:
                query += " AND category = ?"
                params.append(category)

            if status:
                query += " AND status = ?"
                params.append(status)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    def get_market_events(
        self,
        symbol: str = None,
        event_type: str = None,
        start_date: datetime = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取市场事件

        Args:
            symbol: 股票代码
            event_type: 事件类型
            start_date: 开始日期
            limit: 限制数量

        Returns:
            事件列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM market_events WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get market events: {e}")
            return []

    def get_portfolio_snapshots(
        self, start_date: datetime = None, end_date: datetime = None, limit: int = 1000
    ) -> pd.DataFrame:
        """获取投资组合快照

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量

        Returns:
            快照数据框
        """
        try:
            conn = self._get_connection()

            query = "SELECT * FROM portfolio_snapshots WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            return df

        except Exception as e:
            logger.error(f"Failed to get portfolio snapshots: {e}")
            return pd.DataFrame()

    def get_alert_statistics(self, start_date: datetime = None) -> Dict[str, int]:
        """获取告警统计

        Args:
            start_date: 开始日期

        Returns:
            统计字典
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT severity, COUNT(*) as count FROM alerts WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            query += " GROUP BY severity"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            stats = {row["severity"]: row["count"] for row in rows}

            # 获取总数
            cursor.execute(
                f"SELECT COUNT(*) as total FROM alerts WHERE 1=1{' AND timestamp >= ?' if start_date else ''}",
                params[:1] if start_date else [],
            )
            stats["total"] = cursor.fetchone()["total"]

            conn.close()

            return stats

        except Exception as e:
            logger.error(f"Failed to get alert statistics: {e}")
            return {}

    def get_performance_summary(self, start_date: datetime = None) -> Dict[str, Any]:
        """获取性能摘要

        Args:
            start_date: 开始日期

        Returns:
            摘要字典
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    operation,
                    COUNT(*) as count,
                    AVG(duration) as avg_duration,
                    MAX(duration) as max_duration,
                    MIN(duration) as min_duration,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                FROM performance_metrics 
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            query += " GROUP BY operation"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            summary = {
                row["operation"]: {
                    "count": row["count"],
                    "avg_duration": row["avg_duration"],
                    "max_duration": row["max_duration"],
                    "min_duration": row["min_duration"],
                    "success_rate": row["success_count"] / row["count"]
                    if row["count"] > 0
                    else 0,
                }
                for row in rows
            }

            conn.close()

            return summary

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}

    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """清理旧数据

        Args:
            days: 保留天数

        Returns:
            删除统计
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days)
            deleted = {}

            # 清理各表数据
            tables = [
                "system_health",
                "performance_metrics",
                "alerts",
                "market_events",
                "portfolio_snapshots",
                "notifications",
            ]

            for table in tables:
                cursor.execute(
                    f"DELETE FROM {table} WHERE timestamp < ?", (cutoff_date,)
                )
                deleted[table] = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(f"Cleaned up old data: {deleted}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {}


# 全局实例
_global_monitoring_db: Optional[MonitoringDatabaseManager] = None


def get_monitoring_database_manager(
    db_path: str = "data/module06_monitoring.db",
) -> MonitoringDatabaseManager:
    """获取全局监控数据库管理器实例

    Args:
        db_path: 数据库路径

    Returns:
        数据库管理器实例
    """
    global _global_monitoring_db
    if _global_monitoring_db is None:
        _global_monitoring_db = MonitoringDatabaseManager(db_path)
    return _global_monitoring_db
