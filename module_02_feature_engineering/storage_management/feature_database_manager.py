"""
特征数据库管理器
专门用于存储和管理特征工程数据
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from common.exceptions import DataError
from common.logging_system import setup_logger

logger = setup_logger("feature_database_manager")


class FeatureDatabaseManager:
    """特征数据库管理器类"""

    def __init__(self, db_path: str = None):
        """初始化特征数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "module02_features.db")
        self.db_path = db_path
        self._ensure_database_exists()
        self._init_tables()

    def _ensure_database_exists(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _safe_float_convert(self, value) -> float:
        """安全转换为浮点数"""
        if pd.isna(value):
            return None
        if isinstance(value, pd.Timestamp):
            return None  # Skip timestamp values
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _init_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        try:
            # 技术指标表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    indicator_name TEXT NOT NULL,
                    indicator_value REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date, indicator_name)
                )
            """)

            # 因子数据表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS factor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factor_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    factor_value REAL,
                    factor_type TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(factor_id, symbol, date)
                )
            """)

            # 神经因子表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS neural_factors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factor_id TEXT UNIQUE NOT NULL,
                    factor_name TEXT NOT NULL,
                    formula TEXT,
                    importance_score REAL,
                    ic_score REAL,
                    ir_score REAL,
                    stability_score REAL,
                    weights BLOB,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 图特征表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    feature_type TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    feature_value REAL,
                    graph_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date, feature_type, feature_name)
                )
            """)

            # 时间序列特征表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS time_series_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    feature_name TEXT NOT NULL,
                    feature_value REAL,
                    window_size INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date, feature_name, window_size)
                )
            """)

            # 图嵌入表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    embedding_dim INTEGER NOT NULL,
                    embedding_vector BLOB NOT NULL,
                    graph_config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, embedding_dim)
                )
            """)

            # 创建索引
            self._create_indexes(conn)

            conn.commit()
            logger.info("Feature database tables initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")
            raise DataError(f"Database initialization failed: {e}")
        finally:
            conn.close()

    def _create_indexes(self, conn: sqlite3.Connection):
        """创建数据库索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tech_symbol_date ON technical_indicators(symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_factor_symbol_date ON factor_data(symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_graph_symbol_date ON graph_features(symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_ts_symbol_date ON time_series_features(symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_embedding_symbol ON graph_embeddings(symbol)",
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

    # 技术指标相关方法
    def save_technical_indicators(
        self, symbol: str, indicators_df: pd.DataFrame
    ) -> bool:
        """保存技术指标数据

        Args:
            symbol: 股票代码
            indicators_df: 技术指标DataFrame

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()

            for date, row in indicators_df.iterrows():
                for indicator_name, value in row.items():
                    if pd.notna(value) and indicator_name not in [
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    ]:
                        # 处理日期格式
                        if hasattr(date, "strftime"):
                            date_str = date.strftime("%Y-%m-%d")
                        else:
                            date_str = str(date)[:10]  # 假设是YYYY-MM-DD格式的字符串

                        # 安全转换数值
                        float_value = self._safe_float_convert(value)
                        if float_value is None:
                            continue  # 跳过无效数值

                        conn.execute(
                            """
                            INSERT OR REPLACE INTO technical_indicators 
                            (symbol, date, indicator_name, indicator_value, metadata)
                            VALUES (?, ?, ?, ?, ?)
                        """,
                            (
                                symbol,
                                date_str,
                                indicator_name,
                                float_value,
                                json.dumps({"source": "technical_indicators"}),
                            ),
                        )

            conn.commit()
            conn.close()

            logger.info(
                f"Saved technical indicators for {symbol}: {len(indicators_df)} records"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save technical indicators for {symbol}: {e}")
            return False

    def get_technical_indicators(
        self, symbol: str, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """获取技术指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            技术指标DataFrame
        """
        try:
            conn = self._get_connection()

            query = """
                SELECT date, indicator_name, indicator_value 
                FROM technical_indicators 
                WHERE symbol = ?
            """
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date, indicator_name"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                return pd.DataFrame()

            # 透视表转换
            result_df = df.pivot(
                index="date", columns="indicator_name", values="indicator_value"
            )
            result_df.index = pd.to_datetime(result_df.index)

            return result_df

        except Exception as e:
            logger.error(f"Failed to get technical indicators for {symbol}: {e}")
            return pd.DataFrame()

    # 因子数据相关方法
    def save_factor_data(
        self,
        factor_id: str,
        symbol: str,
        factor_values: pd.Series,
        factor_type: str = "custom",
    ) -> bool:
        """保存因子数据

        Args:
            factor_id: 因子ID
            symbol: 股票代码
            factor_values: 因子值Series (index为日期)
            factor_type: 因子类型

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()

            for date, value in factor_values.items():
                if pd.notna(value):
                    # 处理日期格式
                    if hasattr(date, "strftime"):
                        date_str = date.strftime("%Y-%m-%d")
                    else:
                        date_str = str(date)[:10]

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO factor_data 
                        (factor_id, symbol, date, factor_value, factor_type, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            factor_id,
                            symbol,
                            date_str,
                            float(value),
                            factor_type,
                            json.dumps({"source": "factor_analyzer"}),
                        ),
                    )

            conn.commit()
            conn.close()

            logger.info(
                f"Saved factor data {factor_id} for {symbol}: {len(factor_values)} records"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save factor data {factor_id} for {symbol}: {e}")
            return False

    def get_factor_data(
        self,
        factor_id: str,
        symbol: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """获取因子数据

        Args:
            factor_id: 因子ID
            symbol: 股票代码 (可选)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            因子数据DataFrame
        """
        try:
            conn = self._get_connection()

            query = """
                SELECT symbol, date, factor_value 
                FROM factor_data 
                WHERE factor_id = ?
            """
            params = [factor_id]

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY symbol, date"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"])
            return df

        except Exception as e:
            logger.error(f"Failed to get factor data {factor_id}: {e}")
            return pd.DataFrame()

    # 神经因子相关方法
    def save_neural_factor(self, factor_result) -> bool:
        """保存神经因子

        Args:
            factor_result: DiscoveredFactor对象

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()

            # 序列化权重
            weights_blob = factor_result.weights.tobytes()
            metadata_json = json.dumps(factor_result.metadata)

            conn.execute(
                """
                INSERT OR REPLACE INTO neural_factors 
                (factor_id, factor_name, formula, importance_score, ic_score, ir_score, 
                 stability_score, weights, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    factor_result.factor_id,
                    factor_result.name,
                    factor_result.formula,
                    factor_result.importance_score,
                    factor_result.ic_score,
                    factor_result.ir_score,
                    factor_result.stability_score,
                    weights_blob,
                    metadata_json,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"Saved neural factor: {factor_result.factor_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save neural factor {factor_result.factor_id}: {e}")
            return False

    def get_neural_factors(self, factor_id: str = None) -> List[Dict[str, Any]]:
        """获取神经因子

        Args:
            factor_id: 因子ID (可选)

        Returns:
            神经因子列表
        """
        try:
            conn = self._get_connection()

            if factor_id:
                query = "SELECT * FROM neural_factors WHERE factor_id = ?"
                params = [factor_id]
            else:
                query = "SELECT * FROM neural_factors ORDER BY created_at DESC"
                params = []

            cursor = conn.execute(query, params)
            factors = []

            for row in cursor.fetchall():
                factor_dict = {
                    "factor_id": row[1],
                    "factor_name": row[2],
                    "formula": row[3],
                    "importance_score": row[4],
                    "ic_score": row[5],
                    "ir_score": row[6],
                    "stability_score": row[7],
                    "weights": np.frombuffer(row[8], dtype=np.float64)
                    if row[8]
                    else None,
                    "metadata": json.loads(row[9]) if row[9] else {},
                    "created_at": row[10],
                }
                factors.append(factor_dict)

            conn.close()
            return factors

        except Exception as e:
            logger.error(f"Failed to get neural factors: {e}")
            return []

    # 图特征相关方法
    def save_graph_features(
        self, symbol: str, date: str, features: Dict[str, Any]
    ) -> bool:
        """保存图特征数据

        Args:
            symbol: 股票代码
            date: 日期
            features: 图特征字典

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()

            for feature_type, feature_data in features.items():
                if isinstance(feature_data, dict):
                    for feature_name, value in feature_data.items():
                        if isinstance(value, (int, float)):
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO graph_features 
                                (symbol, date, feature_type, feature_name, feature_value, graph_metadata)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    symbol,
                                    date,
                                    feature_type,
                                    feature_name,
                                    float(value),
                                    json.dumps({"source": "graph_analyzer"}),
                                ),
                            )
                elif isinstance(feature_data, (int, float)):
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO graph_features 
                        (symbol, date, feature_type, feature_name, feature_value, graph_metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            symbol,
                            date,
                            feature_type,
                            feature_type,
                            float(feature_data),
                            json.dumps({"source": "graph_analyzer"}),
                        ),
                    )

            conn.commit()
            conn.close()

            logger.info(f"Saved graph features for {symbol} on {date}")
            return True

        except Exception as e:
            logger.error(f"Failed to save graph features for {symbol}: {e}")
            return False

    def get_graph_features(
        self, symbol: str, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """获取图特征数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            图特征DataFrame
        """
        try:
            conn = self._get_connection()

            query = """
                SELECT date, feature_type, feature_name, feature_value 
                FROM graph_features 
                WHERE symbol = ?
            """
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date, feature_type, feature_name"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                return pd.DataFrame()

            df["date"] = pd.to_datetime(df["date"])
            return df

        except Exception as e:
            logger.error(f"Failed to get graph features for {symbol}: {e}")
            return pd.DataFrame()

    # 时间序列特征相关方法
    def save_time_series_features(
        self, symbol: str, features_dict: Dict[str, Any]
    ) -> bool:
        """保存时间序列特征

        Args:
            symbol: 股票代码
            features_dict: 时间序列特征字典

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()

            for feature_name, feature_obj in features_dict.items():
                if hasattr(feature_obj, "values") and hasattr(
                    feature_obj, "description"
                ):
                    # 从特征名中提取窗口大小
                    window_size = None
                    if "_" in feature_name:
                        parts = feature_name.split("_")
                        if parts[-1].isdigit():
                            window_size = int(parts[-1])

                    for date, value in feature_obj.values.items():
                        if pd.notna(value):
                            # 处理日期格式
                            if hasattr(date, "strftime"):
                                date_str = date.strftime("%Y-%m-%d")
                            else:
                                date_str = str(date)[:10]

                            conn.execute(
                                """
                                INSERT OR REPLACE INTO time_series_features 
                                (symbol, date, feature_name, feature_value, window_size, description)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    symbol,
                                    date_str,
                                    feature_name,
                                    float(value),
                                    window_size,
                                    feature_obj.description,
                                ),
                            )

            conn.commit()
            conn.close()

            logger.info(
                f"Saved time series features for {symbol}: {len(features_dict)} features"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save time series features for {symbol}: {e}")
            return False

    def get_time_series_features(
        self, symbol: str, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        """获取时间序列特征

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            时间序列特征DataFrame
        """
        try:
            conn = self._get_connection()

            query = """
                SELECT date, feature_name, feature_value 
                FROM time_series_features 
                WHERE symbol = ?
            """
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date, feature_name"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                return pd.DataFrame()

            # 透视表转换
            result_df = df.pivot(
                index="date", columns="feature_name", values="feature_value"
            )
            result_df.index = pd.to_datetime(result_df.index)

            return result_df

        except Exception as e:
            logger.error(f"Failed to get time series features for {symbol}: {e}")
            return pd.DataFrame()

    # 图嵌入相关方法
    def save_graph_embeddings(
        self, symbol: str, embeddings: np.ndarray, graph_config: Dict[str, Any] = None
    ) -> bool:
        """保存图嵌入

        Args:
            symbol: 股票代码
            embeddings: 嵌入向量
            graph_config: 图配置

        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()

            embedding_blob = embeddings.tobytes()
            config_json = json.dumps(graph_config) if graph_config else None

            conn.execute(
                """
                INSERT OR REPLACE INTO graph_embeddings 
                (symbol, embedding_dim, embedding_vector, graph_config)
                VALUES (?, ?, ?, ?)
            """,
                (symbol, embeddings.shape[0], embedding_blob, config_json),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Saved graph embeddings for {symbol}: dim={embeddings.shape[0]}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save graph embeddings for {symbol}: {e}")
            return False

    def get_graph_embeddings(self, symbol: str) -> Optional[np.ndarray]:
        """获取图嵌入

        Args:
            symbol: 股票代码

        Returns:
            嵌入向量
        """
        try:
            conn = self._get_connection()

            cursor = conn.execute(
                """
                SELECT embedding_dim, embedding_vector 
                FROM graph_embeddings 
                WHERE symbol = ?
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (symbol,),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                embedding_dim, embedding_blob = row
                embeddings = np.frombuffer(embedding_blob, dtype=np.float64)
                return embeddings.reshape(-1)  # 确保是一维数组

            return None

        except Exception as e:
            logger.error(f"Failed to get graph embeddings for {symbol}: {e}")
            return None

    # 数据库统计和管理方法
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            统计信息字典
        """
        try:
            conn = self._get_connection()

            stats = {}

            # 各表记录数统计
            tables = [
                "technical_indicators",
                "factor_data",
                "neural_factors",
                "graph_features",
                "time_series_features",
                "graph_embeddings",
            ]

            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # 数据库大小
            cursor = conn.execute(
                "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
            )
            db_size = cursor.fetchone()[0]
            stats["database_size_mb"] = db_size / (1024 * 1024)

            # 唯一股票数量
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT symbol) FROM technical_indicators"
            )
            stats["unique_symbols"] = cursor.fetchone()[0]

            conn.close()
            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 365) -> bool:
        """清理旧数据

        Args:
            days_to_keep: 保留数据天数

        Returns:
            是否清理成功
        """
        try:
            conn = self._get_connection()

            cutoff_date = (datetime.now() - pd.Timedelta(days=days_to_keep)).strftime(
                "%Y-%m-%d"
            )

            tables = [
                "technical_indicators",
                "factor_data",
                "graph_features",
                "time_series_features",
            ]

            total_deleted = 0
            for table in tables:
                cursor = conn.execute(
                    f"DELETE FROM {table} WHERE date < ?", (cutoff_date,)
                )
                total_deleted += cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(
                f"Cleaned up {total_deleted} old records (older than {days_to_keep} days)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False


# 全局数据库管理器实例
_feature_db_manager = None


def get_feature_database_manager(
    db_path: str = "data/module02_features.db",
) -> FeatureDatabaseManager:
    """获取全局特征数据库管理器实例

    Args:
        db_path: 数据库文件路径

    Returns:
        特征数据库管理器实例
    """
    global _feature_db_manager
    if _feature_db_manager is None:
        _feature_db_manager = FeatureDatabaseManager(db_path)
    return _feature_db_manager
