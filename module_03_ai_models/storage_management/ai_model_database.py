"""
AI模型数据库管理器

用于管理AI模型的训练结果、预测结果、模型参数和性能指标的存储
"""

import json
import os
import pickle
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from common.exceptions import DatabaseError
from common.logging_system import setup_logger

logger = setup_logger("ai_model_database")


class AIModelDatabaseManager:
    """AI模型数据库管理器"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器"""
        if db_path is None:
            import os
            db_path = os.path.join("data", "module03_ai_models.db")
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 模型信息表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_info (
                    model_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    config_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'created'
                )
                """)

                # 训练历史表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    epoch INTEGER,
                    train_loss REAL,
                    val_loss REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES model_info (model_id)
                )
                """)

                # 模型预测结果表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    prediction_date DATE NOT NULL,
                    prediction_value REAL,
                    confidence REAL,
                    actual_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES model_info (model_id)
                )
                """)

                # 模型性能评估表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    evaluation_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES model_info (model_id)
                )
                """)

                # 模型参数存储表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_parameters (
                    model_id TEXT PRIMARY KEY,
                    parameters_blob BLOB,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES model_info (model_id)
                )
                """)

                conn.commit()
                logger.info("AI Model database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    def save_model_info(
        self, model_id: str, model_type: str, model_name: str, config: Dict[str, Any]
    ) -> bool:
        """保存模型基本信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                INSERT OR REPLACE INTO model_info 
                (model_id, model_type, model_name, config_json)
                VALUES (?, ?, ?, ?)
                """,
                    (model_id, model_type, model_name, json.dumps(config)),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save model info: {e}")
            return False

    def save_training_history(
        self, model_id: str, epoch: int, train_loss: float, val_loss: float = None
    ) -> bool:
        """保存训练历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                INSERT INTO training_history 
                (model_id, epoch, train_loss, val_loss)
                VALUES (?, ?, ?, ?)
                """,
                    (model_id, epoch, train_loss, val_loss),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save training history: {e}")
            return False

    def save_model_prediction(
        self,
        model_id: str,
        symbol: str,
        prediction_date: str,
        prediction_value: float,
        confidence: float = None,
    ) -> bool:
        """保存模型预测结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                INSERT INTO model_predictions 
                (model_id, symbol, prediction_date, prediction_value, confidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                    (model_id, symbol, prediction_date, prediction_value, confidence),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save model prediction: {e}")
            return False

    def save_model_performance(
        self, model_id: str, metric_name: str, metric_value: float
    ) -> bool:
        """保存模型性能指标"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                INSERT INTO model_performance 
                (model_id, metric_name, metric_value, evaluation_date)
                VALUES (?, ?, ?, DATE('now'))
                """,
                    (model_id, metric_name, metric_value),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save model performance: {e}")
            return False

    def save_model_parameters(self, model_id: str, parameters: Any) -> bool:
        """保存模型参数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                params_blob = (
                    pickle.dumps(parameters) if parameters is not None else None
                )
                cursor.execute(
                    """
                INSERT OR REPLACE INTO model_parameters 
                (model_id, parameters_blob)
                VALUES (?, ?)
                """,
                    (model_id, params_blob),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save model parameters: {e}")
            return False

    def get_model_predictions(self, model_id: str, symbol: str = None) -> pd.DataFrame:
        """获取模型预测结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT symbol, prediction_date, prediction_value, confidence, actual_value
                FROM model_predictions WHERE model_id = ?
                """
                params = [model_id]
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                query += " ORDER BY prediction_date DESC"
                return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            logger.error(f"Failed to get model predictions: {e}")
            return pd.DataFrame()

    def get_model_performance(self, model_id: str) -> pd.DataFrame:
        """获取模型性能指标"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT metric_name, metric_value, evaluation_date
                FROM model_performance WHERE model_id = ?
                ORDER BY evaluation_date DESC
                """
                return pd.read_sql_query(query, conn, params=(model_id,))
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            return pd.DataFrame()

    def load_model_parameters(self, model_id: str) -> Any:
        """加载模型参数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT parameters_blob FROM model_parameters WHERE model_id = ?",
                    (model_id,),
                )
                result = cursor.fetchone()
                if result and result[0]:
                    return pickle.loads(result[0])
                return None
        except Exception as e:
            logger.error(f"Failed to load model parameters: {e}")
            return None

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                stats = {}

                cursor.execute(
                    "SELECT model_type, COUNT(*) FROM model_info GROUP BY model_type"
                )
                stats["model_counts"] = dict(cursor.fetchall())

                cursor.execute("SELECT COUNT(*) FROM model_predictions")
                stats["total_predictions"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM training_history")
                stats["total_training_records"] = cursor.fetchone()[0]

                return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


# 全局数据库管理器实例
_ai_model_db_manager = None


def get_ai_model_database_manager(
    db_path: str = "data/module03_ai_models.db",
) -> AIModelDatabaseManager:
    """获取AI模型数据库管理器的全局实例"""
    global _ai_model_db_manager
    if _ai_model_db_manager is None:
        _ai_model_db_manager = AIModelDatabaseManager(db_path)
    return _ai_model_db_manager
