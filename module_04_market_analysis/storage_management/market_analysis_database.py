"""
Market Analysis Database Manager
专门用于Module 04的数据存储管理
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from common.logging_system import setup_logger

logger = setup_logger("market_analysis_db")

# 全局数据库实例
_db_instance = None
_db_lock = threading.Lock()


class MarketAnalysisDB:
    """市场分析数据库管理器"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "module04_market_analysis.db")
        self.db_path = db_path
        self._ensure_data_dir()
        self._init_database()
        logger.info(f"Initialized market analysis database at {db_path}")

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建分析结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE NOT NULL,
                    symbols TEXT NOT NULL,  -- JSON format
                    consensus_recommendation TEXT NOT NULL,
                    consensus_confidence REAL NOT NULL,
                    consensus_reasoning TEXT,
                    key_insights TEXT,  -- JSON format
                    risk_assessment TEXT,  -- JSON format
                    individual_analyses TEXT,  -- JSON format
                    debate_result TEXT,  -- JSON format
                    execution_time REAL NOT NULL,
                    status TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建智能体分析历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT UNIQUE NOT NULL,
                    agent_name TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    symbols TEXT NOT NULL,  -- JSON format
                    recommendation_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    key_factors TEXT,  -- JSON format
                    risk_factors TEXT,  -- JSON format
                    market_outlook TEXT,
                    additional_insights TEXT,  -- JSON format
                    data_sources TEXT,  -- JSON format
                    analysis_duration REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建异常检测表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomaly_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    anomaly_score REAL NOT NULL,
                    description TEXT,
                    detection_method TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    data_point TEXT,  -- JSON format
                    threshold_values TEXT,  -- JSON format
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建相关性分析表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS correlation_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT UNIQUE NOT NULL,
                    symbols TEXT NOT NULL,  -- JSON format
                    correlation_matrix TEXT NOT NULL,  -- JSON format
                    correlation_type TEXT NOT NULL,
                    time_window INTEGER NOT NULL,
                    analysis_date DATETIME NOT NULL,
                    insights TEXT,  -- JSON format
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建市场状态检测表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regime_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detection_id TEXT UNIQUE NOT NULL,
                    market_regime TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    regime_features TEXT,  -- JSON format
                    detection_method TEXT NOT NULL,
                    symbols TEXT,  -- JSON format
                    analysis_date DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建情绪分析表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT UNIQUE NOT NULL,
                    symbol TEXT,
                    text_source TEXT NOT NULL,  -- news, social_media, reports, etc.
                    sentiment_score REAL NOT NULL,
                    sentiment_label TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    keywords TEXT,  -- JSON format
                    analysis_method TEXT NOT NULL,
                    source_data TEXT,  -- JSON format
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建辩论历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS debate_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    debate_id TEXT UNIQUE NOT NULL,
                    symbols TEXT NOT NULL,  -- JSON format
                    participants TEXT NOT NULL,  -- JSON format
                    rounds_data TEXT NOT NULL,  -- JSON format
                    final_consensus TEXT NOT NULL,  -- JSON format
                    consensus_score REAL NOT NULL,
                    debate_duration REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建性能指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT,  -- JSON format
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            self._create_indexes(cursor)

            conn.commit()
            logger.info("Database schema initialized successfully")

    def _create_indexes(self, cursor):
        """创建数据库索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_symbols ON analysis_results(symbols)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_timestamp ON analysis_results(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_agent_analyses_agent_type ON agent_analyses(agent_type)",
            "CREATE INDEX IF NOT EXISTS idx_agent_analyses_symbols ON agent_analyses(symbols)",
            "CREATE INDEX IF NOT EXISTS idx_agent_analyses_timestamp ON agent_analyses(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_anomaly_detections_symbol ON anomaly_detections(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_anomaly_detections_type ON anomaly_detections(anomaly_type)",
            "CREATE INDEX IF NOT EXISTS idx_correlation_analyses_symbols ON correlation_analyses(symbols)",
            "CREATE INDEX IF NOT EXISTS idx_regime_detections_regime ON regime_detections(market_regime)",
            "CREATE INDEX IF NOT EXISTS idx_sentiment_analyses_symbol ON sentiment_analyses(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_sentiment_analyses_source ON sentiment_analyses(text_source)",
            "CREATE INDEX IF NOT EXISTS idx_debate_history_symbols ON debate_history(symbols)",
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type)",
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.Error as e:
                logger.warning(f"Failed to create index: {e}")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def save_analysis_result(self, result_data: Dict[str, Any]) -> bool:
        """保存分析结果

        Args:
            result_data: 分析结果数据

        Returns:
            是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO analysis_results (
                        request_id, symbols, consensus_recommendation, consensus_confidence,
                        consensus_reasoning, key_insights, risk_assessment, individual_analyses,
                        debate_result, execution_time, status, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        result_data["request_id"],
                        json.dumps(result_data["symbols"]),
                        result_data["consensus_recommendation"],
                        result_data["consensus_confidence"],
                        result_data.get("consensus_reasoning", ""),
                        json.dumps(result_data.get("key_insights", [])),
                        json.dumps(result_data.get("risk_assessment", {})),
                        json.dumps(result_data.get("individual_analyses", [])),
                        json.dumps(result_data.get("debate_result", {})),
                        result_data["execution_time"],
                        result_data["status"],
                        result_data["timestamp"],
                    ),
                )

                conn.commit()
                logger.info(f"Saved analysis result {result_data['request_id']}")
                return True

        except Exception as e:
            logger.error(f"Failed to save analysis result: {e}")
            return False

    def save_agent_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """保存智能体分析结果

        Args:
            analysis_data: 智能体分析数据

        Returns:
            是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO agent_analyses (
                        analysis_id, agent_name, agent_type, symbols, recommendation_type,
                        confidence, reasoning, key_factors, risk_factors, market_outlook,
                        additional_insights, data_sources, analysis_duration, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        analysis_data["analysis_id"],
                        analysis_data["agent_name"],
                        analysis_data["agent_type"],
                        json.dumps(analysis_data["symbols"]),
                        analysis_data["recommendation_type"],
                        analysis_data["confidence"],
                        analysis_data.get("reasoning", ""),
                        json.dumps(analysis_data.get("key_factors", [])),
                        json.dumps(analysis_data.get("risk_factors", [])),
                        analysis_data.get("market_outlook", ""),
                        json.dumps(analysis_data.get("additional_insights", {})),
                        json.dumps(analysis_data.get("data_sources", [])),
                        analysis_data["analysis_duration"],
                        analysis_data["timestamp"],
                    ),
                )

                conn.commit()
                logger.info(f"Saved agent analysis {analysis_data['analysis_id']}")
                return True

        except Exception as e:
            logger.error(f"Failed to save agent analysis: {e}")
            return False

    def save_anomaly_detection(self, anomaly_data: Dict[str, Any]) -> bool:
        """保存异常检测结果

        Args:
            anomaly_data: 异常检测数据

        Returns:
            是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO anomaly_detections (
                        symbol, anomaly_type, anomaly_score, description, detection_method,
                        timestamp, data_point, threshold_values
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        anomaly_data["symbol"],
                        anomaly_data["anomaly_type"],
                        anomaly_data["anomaly_score"],
                        anomaly_data.get("description", ""),
                        anomaly_data["detection_method"],
                        anomaly_data["timestamp"],
                        json.dumps(anomaly_data.get("data_point", {})),
                        json.dumps(anomaly_data.get("threshold_values", {})),
                    ),
                )

                conn.commit()
                logger.info(f"Saved anomaly detection for {anomaly_data['symbol']}")
                return True

        except Exception as e:
            logger.error(f"Failed to save anomaly detection: {e}")
            return False

    def save_correlation_analysis(self, correlation_data: Dict[str, Any]) -> bool:
        """保存相关性分析结果

        Args:
            correlation_data: 相关性分析数据

        Returns:
            是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO correlation_analyses (
                        analysis_id, symbols, correlation_matrix, correlation_type,
                        time_window, analysis_date, insights
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        correlation_data["analysis_id"],
                        json.dumps(correlation_data["symbols"]),
                        json.dumps(correlation_data["correlation_matrix"]),
                        correlation_data["correlation_type"],
                        correlation_data["time_window"],
                        correlation_data["analysis_date"],
                        json.dumps(correlation_data.get("insights", [])),
                    ),
                )

                conn.commit()
                logger.info(
                    f"Saved correlation analysis {correlation_data['analysis_id']}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to save correlation analysis: {e}")
            return False

    def save_regime_detection(self, regime_data: Dict[str, Any]) -> bool:
        """保存市场状态检测结果

        Args:
            regime_data: 市场状态检测数据

        Returns:
            是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO regime_detections (
                        detection_id, market_regime, confidence, regime_features,
                        detection_method, symbols, analysis_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        regime_data["detection_id"],
                        regime_data["market_regime"],
                        regime_data["confidence"],
                        json.dumps(regime_data.get("regime_features", {})),
                        regime_data["detection_method"],
                        json.dumps(regime_data.get("symbols", [])),
                        regime_data["analysis_date"],
                    ),
                )

                conn.commit()
                logger.info(f"Saved regime detection {regime_data['detection_id']}")
                return True

        except Exception as e:
            logger.error(f"Failed to save regime detection: {e}")
            return False

    def save_sentiment_analysis(self, sentiment_data: Dict[str, Any]) -> bool:
        """保存情绪分析结果

        Args:
            sentiment_data: 情绪分析数据

        Returns:
            是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO sentiment_analyses (
                        analysis_id, symbol, text_source, sentiment_score, sentiment_label,
                        confidence, keywords, analysis_method, source_data, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        sentiment_data["analysis_id"],
                        sentiment_data.get("symbol", ""),
                        sentiment_data["text_source"],
                        sentiment_data["sentiment_score"],
                        sentiment_data["sentiment_label"],
                        sentiment_data["confidence"],
                        json.dumps(sentiment_data.get("keywords", [])),
                        sentiment_data["analysis_method"],
                        json.dumps(sentiment_data.get("source_data", {})),
                        sentiment_data["timestamp"],
                    ),
                )

                conn.commit()
                logger.info(f"Saved sentiment analysis {sentiment_data['analysis_id']}")
                return True

        except Exception as e:
            logger.error(f"Failed to save sentiment analysis: {e}")
            return False

    def save_debate_history(self, debate_data: Dict[str, Any]) -> bool:
        """保存辩论历史

        Args:
            debate_data: 辩论数据

        Returns:
            是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO debate_history (
                        debate_id, symbols, participants, rounds_data, final_consensus,
                        consensus_score, debate_duration, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        debate_data["debate_id"],
                        json.dumps(debate_data["symbols"]),
                        json.dumps(debate_data["participants"]),
                        json.dumps(debate_data["rounds_data"]),
                        json.dumps(debate_data["final_consensus"]),
                        debate_data["consensus_score"],
                        debate_data["debate_duration"],
                        debate_data["timestamp"],
                    ),
                )

                conn.commit()
                logger.info(f"Saved debate history {debate_data['debate_id']}")
                return True

        except Exception as e:
            logger.error(f"Failed to save debate history: {e}")
            return False

    def get_analysis_results(
        self, symbols: Optional[List[str]] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取分析结果

        Args:
            symbols: 股票代码列表（可选）
            limit: 返回数量限制

        Returns:
            分析结果列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if symbols:
                    # 构建查询条件
                    symbols_json = [json.dumps(symbols)]
                    placeholders = ",".join(["?" for _ in symbols_json])
                    query = f"""
                        SELECT * FROM analysis_results 
                        WHERE symbols IN ({placeholders})
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    cursor.execute(query, symbols_json + [limit])
                else:
                    query = """
                        SELECT * FROM analysis_results 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    cursor.execute(query, (limit,))

                rows = cursor.fetchall()
                results = []

                for row in rows:
                    result = dict(row)
                    # 解析JSON字段
                    result["symbols"] = json.loads(result["symbols"])
                    result["key_insights"] = json.loads(result["key_insights"])
                    result["risk_assessment"] = json.loads(result["risk_assessment"])
                    result["individual_analyses"] = json.loads(
                        result["individual_analyses"]
                    )
                    result["debate_result"] = json.loads(result["debate_result"])
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Failed to get analysis results: {e}")
            return []

    def get_anomaly_detections(
        self, symbol: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取异常检测结果

        Args:
            symbol: 股票代码（可选）
            limit: 返回数量限制

        Returns:
            异常检测结果列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if symbol:
                    query = """
                        SELECT * FROM anomaly_detections 
                        WHERE symbol = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    cursor.execute(query, (symbol, limit))
                else:
                    query = """
                        SELECT * FROM anomaly_detections 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    cursor.execute(query, (limit,))

                rows = cursor.fetchall()
                results = []

                for row in rows:
                    result = dict(row)
                    # 解析JSON字段
                    result["data_point"] = json.loads(result["data_point"])
                    result["threshold_values"] = json.loads(result["threshold_values"])
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Failed to get anomaly detections: {e}")
            return []

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            数据库统计信息
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # 各表记录数
                tables = [
                    "analysis_results",
                    "agent_analyses",
                    "anomaly_detections",
                    "correlation_analyses",
                    "regime_detections",
                    "sentiment_analyses",
                    "debate_history",
                    "performance_metrics",
                ]

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[f"{table}_count"] = count

                # 数据库文件大小
                import os

                if os.path.exists(self.db_path):
                    file_size = os.path.getsize(self.db_path)
                    stats["database_size_mb"] = round(file_size / (1024 * 1024), 2)
                else:
                    stats["database_size_mb"] = 0

                # 最近分析时间
                cursor.execute("SELECT MAX(timestamp) FROM analysis_results")
                last_analysis = cursor.fetchone()[0]
                stats["last_analysis_time"] = last_analysis

                return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """清理旧数据

        Args:
            days_to_keep: 保留天数

        Returns:
            是否清理成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 计算截止日期
                cutoff_date = datetime.now() - pd.Timedelta(days=days_to_keep)

                # 清理各表的旧数据
                tables = [
                    "analysis_results",
                    "agent_analyses",
                    "anomaly_detections",
                    "correlation_analyses",
                    "regime_detections",
                    "sentiment_analyses",
                    "debate_history",
                    "performance_metrics",
                ]

                total_deleted = 0
                for table in tables:
                    cursor.execute(
                        f"DELETE FROM {table} WHERE created_at < ?", (cutoff_date,)
                    )
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    logger.info(f"Deleted {deleted} old records from {table}")

                conn.commit()
                logger.info(f"Cleanup completed, deleted {total_deleted} records total")
                return True

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False


def get_market_analysis_db(
    db_path: str = "data/module04_market_analysis.db",
) -> MarketAnalysisDB:
    """获取市场分析数据库实例（单例模式）

    Args:
        db_path: 数据库文件路径

    Returns:
        MarketAnalysisDB实例
    """
    global _db_instance

    with _db_lock:
        if _db_instance is None:
            _db_instance = MarketAnalysisDB(db_path)

    return _db_instance
