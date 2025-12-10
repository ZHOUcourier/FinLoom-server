"""
可视化模块数据库管理器
负责管理可视化相关的数据持久化
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from common.exceptions import DatabaseError
from common.logging_system import setup_logger

logger = setup_logger("visualization_database_manager")


class VisualizationDatabaseManager:
    """可视化数据库管理器"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "module11_visualization.db")
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_database()
        logger.info(
            f"VisualizationDatabaseManager initialized with database: {db_path}"
        )

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

                # 图表数据表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS charts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chart_id TEXT UNIQUE NOT NULL,
                        chart_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        data_source TEXT,
                        config_json TEXT,
                        html_content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 仪表板数据表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dashboards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dashboard_id TEXT UNIQUE NOT NULL,
                        dashboard_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        layout_config_json TEXT,
                        components_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 报告数据表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_id TEXT UNIQUE NOT NULL,
                        report_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        report_date DATE NOT NULL,
                        content_html TEXT,
                        content_json TEXT,
                        metadata_json TEXT,
                        file_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 可视化模板表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        template_id TEXT UNIQUE NOT NULL,
                        template_name TEXT NOT NULL,
                        template_type TEXT NOT NULL,
                        template_content TEXT NOT NULL,
                        variables_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 导出历史表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS export_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        export_id TEXT UNIQUE NOT NULL,
                        export_type TEXT NOT NULL,
                        source_type TEXT,
                        source_id TEXT,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        export_format TEXT NOT NULL,
                        metadata_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 缓存数据表（用于存储预计算的可视化数据）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS visualization_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cache_key TEXT UNIQUE NOT NULL,
                        cache_type TEXT NOT NULL,
                        data_json TEXT NOT NULL,
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_charts_type_created 
                    ON charts(chart_type, created_at DESC)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_dashboards_type_updated 
                    ON dashboards(dashboard_type, updated_at DESC)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_reports_type_date 
                    ON reports(report_type, report_date DESC)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_export_history_type_created 
                    ON export_history(export_type, created_at DESC)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cache_key_expires 
                    ON visualization_cache(cache_key, expires_at)
                """)

                conn.commit()
                logger.info("Database tables initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    # ==================== 图表管理 ====================

    def save_chart(
        self,
        chart_id: str,
        chart_type: str,
        title: str,
        data_source: str,
        config: Dict[str, Any],
        html_content: Optional[str] = None,
    ) -> bool:
        """保存图表数据

        Args:
            chart_id: 图表ID
            chart_type: 图表类型
            title: 标题
            data_source: 数据源
            config: 配置
            html_content: HTML内容

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO charts (
                        chart_id, chart_type, title, data_source, config_json, 
                        html_content, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        chart_id,
                        chart_type,
                        title,
                        data_source,
                        json.dumps(config),
                        html_content,
                        datetime.now(),
                    ),
                )

                conn.commit()
                logger.info(f"Saved chart: {chart_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save chart: {e}")
            return False

    def get_chart(self, chart_id: str) -> Optional[Dict[str, Any]]:
        """获取图表数据

        Args:
            chart_id: 图表ID

        Returns:
            图表数据字典
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM charts WHERE chart_id = ?", (chart_id,))

                row = cursor.fetchone()
                if row:
                    chart = dict(row)
                    if chart["config_json"]:
                        chart["config"] = json.loads(chart["config_json"])
                    return chart

                return None

        except Exception as e:
            logger.error(f"Failed to get chart: {e}")
            return None

    def list_charts(
        self, chart_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """列出图表

        Args:
            chart_type: 图表类型（可选）
            limit: 限制数量

        Returns:
            图表列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if chart_type:
                    cursor.execute(
                        """
                        SELECT * FROM charts 
                        WHERE chart_type = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """,
                        (chart_type, limit),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM charts 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """,
                        (limit,),
                    )

                rows = cursor.fetchall()
                charts = []
                for row in rows:
                    chart = dict(row)
                    if chart["config_json"]:
                        chart["config"] = json.loads(chart["config_json"])
                    charts.append(chart)

                return charts

        except Exception as e:
            logger.error(f"Failed to list charts: {e}")
            return []

    def delete_chart(self, chart_id: str) -> bool:
        """删除图表

        Args:
            chart_id: 图表ID

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM charts WHERE chart_id = ?", (chart_id,))
                conn.commit()
                logger.info(f"Deleted chart: {chart_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete chart: {e}")
            return False

    # ==================== 仪表板管理 ====================

    def save_dashboard(
        self,
        dashboard_id: str,
        dashboard_type: str,
        title: str,
        layout_config: Dict[str, Any],
        components: List[Dict[str, Any]],
    ) -> bool:
        """保存仪表板数据

        Args:
            dashboard_id: 仪表板ID
            dashboard_type: 仪表板类型
            title: 标题
            layout_config: 布局配置
            components: 组件列表

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO dashboards (
                        dashboard_id, dashboard_type, title, layout_config_json,
                        components_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        dashboard_id,
                        dashboard_type,
                        title,
                        json.dumps(layout_config),
                        json.dumps(components),
                        datetime.now(),
                    ),
                )

                conn.commit()
                logger.info(f"Saved dashboard: {dashboard_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save dashboard: {e}")
            return False

    def get_dashboard(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """获取仪表板数据

        Args:
            dashboard_id: 仪表板ID

        Returns:
            仪表板数据字典
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM dashboards WHERE dashboard_id = ?", (dashboard_id,)
                )

                row = cursor.fetchone()
                if row:
                    dashboard = dict(row)
                    if dashboard["layout_config_json"]:
                        dashboard["layout_config"] = json.loads(
                            dashboard["layout_config_json"]
                        )
                    if dashboard["components_json"]:
                        dashboard["components"] = json.loads(
                            dashboard["components_json"]
                        )
                    return dashboard

                return None

        except Exception as e:
            logger.error(f"Failed to get dashboard: {e}")
            return None

    # ==================== 报告管理 ====================

    def save_report(
        self,
        report_id: str,
        report_type: str,
        title: str,
        report_date: datetime,
        content_html: str,
        content_json: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
    ) -> bool:
        """保存报告数据

        Args:
            report_id: 报告ID
            report_type: 报告类型
            title: 标题
            report_date: 报告日期
            content_html: HTML内容
            content_json: JSON内容
            metadata: 元数据
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO reports (
                        report_id, report_type, title, report_date, content_html,
                        content_json, metadata_json, file_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        report_id,
                        report_type,
                        title,
                        report_date.date(),
                        content_html,
                        json.dumps(content_json) if content_json else None,
                        json.dumps(metadata) if metadata else None,
                        file_path,
                    ),
                )

                conn.commit()
                logger.info(f"Saved report: {report_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return False

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取报告数据

        Args:
            report_id: 报告ID

        Returns:
            报告数据字典
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM reports WHERE report_id = ?", (report_id,)
                )

                row = cursor.fetchone()
                if row:
                    report = dict(row)
                    if report["content_json"]:
                        report["content"] = json.loads(report["content_json"])
                    if report["metadata_json"]:
                        report["metadata"] = json.loads(report["metadata_json"])
                    return report

                return None

        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return None

    def list_reports(
        self,
        report_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """列出报告

        Args:
            report_type: 报告类型（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 限制数量

        Returns:
            报告列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM reports WHERE 1=1"
                params = []

                if report_type:
                    query += " AND report_type = ?"
                    params.append(report_type)

                if start_date:
                    query += " AND report_date >= ?"
                    params.append(start_date.date())

                if end_date:
                    query += " AND report_date <= ?"
                    params.append(end_date.date())

                query += " ORDER BY report_date DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)

                rows = cursor.fetchall()
                reports = []
                for row in rows:
                    report = dict(row)
                    if report.get("metadata_json"):
                        report["metadata"] = json.loads(report["metadata_json"])
                    reports.append(report)

                return reports

        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return []

    # ==================== 模板管理 ====================

    def save_template(
        self,
        template_id: str,
        template_name: str,
        template_type: str,
        template_content: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存模板

        Args:
            template_id: 模板ID
            template_name: 模板名称
            template_type: 模板类型
            template_content: 模板内容
            variables: 变量定义

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO templates (
                        template_id, template_name, template_type, template_content,
                        variables_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        template_id,
                        template_name,
                        template_type,
                        template_content,
                        json.dumps(variables) if variables else None,
                        datetime.now(),
                    ),
                )

                conn.commit()
                logger.info(f"Saved template: {template_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            return False

    # ==================== 导出历史 ====================

    def save_export_record(
        self,
        export_id: str,
        export_type: str,
        source_type: str,
        source_id: str,
        file_path: str,
        file_size: int,
        export_format: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存导出记录

        Args:
            export_id: 导出ID
            export_type: 导出类型
            source_type: 源类型
            source_id: 源ID
            file_path: 文件路径
            file_size: 文件大小
            export_format: 导出格式
            metadata: 元数据

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO export_history (
                        export_id, export_type, source_type, source_id, file_path,
                        file_size, export_format, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        export_id,
                        export_type,
                        source_type,
                        source_id,
                        file_path,
                        file_size,
                        export_format,
                        json.dumps(metadata) if metadata else None,
                    ),
                )

                conn.commit()
                logger.info(f"Saved export record: {export_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to save export record: {e}")
            return False

    def get_export_history(
        self, export_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取导出历史

        Args:
            export_type: 导出类型（可选）
            limit: 限制数量

        Returns:
            导出记录列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if export_type:
                    cursor.execute(
                        """
                        SELECT * FROM export_history 
                        WHERE export_type = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """,
                        (export_type, limit),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM export_history 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """,
                        (limit,),
                    )

                rows = cursor.fetchall()
                records = []
                for row in rows:
                    record = dict(row)
                    if record.get("metadata_json"):
                        record["metadata"] = json.loads(record["metadata_json"])
                    records.append(record)

                return records

        except Exception as e:
            logger.error(f"Failed to get export history: {e}")
            return []

    # ==================== 缓存管理 ====================

    def set_cache(
        self,
        cache_key: str,
        cache_type: str,
        data: Dict[str, Any],
        expires_in_seconds: Optional[int] = None,
    ) -> bool:
        """设置缓存

        Args:
            cache_key: 缓存键
            cache_type: 缓存类型
            data: 数据
            expires_in_seconds: 过期时间（秒）

        Returns:
            是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                expires_at = None
                if expires_in_seconds:
                    expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO visualization_cache (
                        cache_key, cache_type, data_json, expires_at
                    ) VALUES (?, ?, ?, ?)
                """,
                    (cache_key, cache_type, json.dumps(data), expires_at),
                )

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    def get_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存数据
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM visualization_cache 
                    WHERE cache_key = ?
                    AND (expires_at IS NULL OR expires_at > ?)
                """,
                    (cache_key, datetime.now()),
                )

                row = cursor.fetchone()
                if row:
                    return json.loads(row["data_json"])

                return None

        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None

    def clear_expired_cache(self) -> int:
        """清理过期缓存

        Returns:
            清理的记录数
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    DELETE FROM visualization_cache 
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """,
                    (datetime.now(),),
                )

                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Cleared {deleted_count} expired cache entries")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            return 0

    # ==================== 数据库统计 ====================

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            统计信息字典
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # 各表记录数
                tables = [
                    "charts",
                    "dashboards",
                    "reports",
                    "templates",
                    "export_history",
                    "visualization_cache",
                ]

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()["count"]

                # 数据库大小
                db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB
                stats["database_size_mb"] = round(db_size, 2)

                # 最近报告日期
                cursor.execute("SELECT MAX(report_date) as latest FROM reports")
                result = cursor.fetchone()
                stats["latest_report_date"] = (
                    result["latest"] if result["latest"] else None
                )

                logger.info(f"Database stats: {stats}")
                return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
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

                # 清理旧报告
                cursor.execute(
                    "DELETE FROM reports WHERE created_at < ?", (cutoff_date,)
                )

                # 清理旧导出记录
                cursor.execute(
                    "DELETE FROM export_history WHERE created_at < ?", (cutoff_date,)
                )

                # 清理过期缓存
                self.clear_expired_cache()

                conn.commit()
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                return True

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False


# 全局数据库管理器实例
_vis_db_manager = None


def get_visualization_database_manager(
    db_path: str = "data/module11_visualization.db",
) -> VisualizationDatabaseManager:
    """获取可视化数据库管理器实例（单例模式）

    Args:
        db_path: 数据库路径

    Returns:
        VisualizationDatabaseManager实例
    """
    global _vis_db_manager
    if _vis_db_manager is None:
        _vis_db_manager = VisualizationDatabaseManager(db_path)
    return _vis_db_manager
