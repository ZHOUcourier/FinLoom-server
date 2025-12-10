"""
模块07优化数据库管理器
管理优化结果和历史数据的存储
"""

import json
import pickle
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from common.logging_system import setup_logger

logger = setup_logger("optimization_db_manager")


class OptimizationDatabaseManager:
    """优化数据库管理器"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "module07_optimization.db")
        self.db_path = db_path

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 优化任务表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS optimization_tasks (
                    task_id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    optimizer_type TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status TEXT NOT NULL,
                    config TEXT,
                    metadata TEXT
                )
            """
            )

            # 优化结果表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS optimization_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    best_parameters TEXT NOT NULL,
                    best_value REAL NOT NULL,
                    n_trials INTEGER NOT NULL,
                    n_successful_trials INTEGER NOT NULL,
                    total_time_seconds REAL NOT NULL,
                    convergence_history TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES optimization_tasks (task_id)
                )
            """
            )

            # 试验历史表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trial_history (
                    trial_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    trial_number INTEGER NOT NULL,
                    parameters TEXT NOT NULL,
                    objective_value REAL,
                    status TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    error_message TEXT,
                    metrics TEXT,
                    FOREIGN KEY (task_id) REFERENCES optimization_tasks (task_id)
                )
            """
            )

            # 策略优化结果表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_optimization (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT,
                    parameters TEXT NOT NULL,
                    train_performance TEXT NOT NULL,
                    test_performance TEXT,
                    optimization_date TIMESTAMP NOT NULL,
                    walk_forward_results TEXT
                )
            """
            )

            # 投资组合优化结果表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_optimization (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    optimization_name TEXT NOT NULL,
                    weights TEXT NOT NULL,
                    expected_return REAL,
                    volatility REAL,
                    sharpe_ratio REAL,
                    optimization_date TIMESTAMP NOT NULL,
                    constraints TEXT,
                    metadata TEXT
                )
            """
            )

            # 多目标优化结果表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS multi_objective_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    pareto_front TEXT NOT NULL,
                    n_solutions INTEGER NOT NULL,
                    objective_names TEXT NOT NULL,
                    optimization_date TIMESTAMP NOT NULL,
                    metadata TEXT
                )
            """
            )

            conn.commit()

        logger.info(f"Database initialized at {self.db_path}")

    def save_optimization_task(
        self,
        task_id: str,
        task_name: str,
        optimizer_type: str,
        config: Dict[str, Any],
        status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存优化任务

        Args:
            task_id: 任务ID
            task_name: 任务名称
            optimizer_type: 优化器类型
            config: 配置信息
            status: 状态
            metadata: 元数据

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO optimization_tasks
                    (task_id, task_name, optimizer_type, created_at, status, config, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        task_id,
                        task_name,
                        optimizer_type,
                        datetime.now().isoformat(),
                        status,
                        json.dumps(config),
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save optimization task: {e}")
            return False

    def update_task_status(
        self, task_id: str, status: str, completed_at: Optional[datetime] = None
    ) -> bool:
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            completed_at: 完成时间

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if completed_at:
                    cursor.execute(
                        """
                        UPDATE optimization_tasks
                        SET status = ?, completed_at = ?
                        WHERE task_id = ?
                    """,
                        (status, completed_at.isoformat(), task_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE optimization_tasks
                        SET status = ?
                        WHERE task_id = ?
                    """,
                        (status, task_id),
                    )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            return False

    def save_optimization_result(
        self,
        task_id: str,
        best_parameters: Dict[str, Any],
        best_value: float,
        n_trials: int,
        n_successful_trials: int,
        total_time_seconds: float,
        convergence_history: Optional[List[float]] = None,
    ) -> bool:
        """保存优化结果

        Args:
            task_id: 任务ID
            best_parameters: 最佳参数
            best_value: 最佳值
            n_trials: 试验次数
            n_successful_trials: 成功试验次数
            total_time_seconds: 总耗时
            convergence_history: 收敛历史

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO optimization_results
                    (task_id, best_parameters, best_value, n_trials, n_successful_trials,
                     total_time_seconds, convergence_history, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        task_id,
                        json.dumps(best_parameters),
                        best_value,
                        n_trials,
                        n_successful_trials,
                        total_time_seconds,
                        json.dumps(convergence_history)
                        if convergence_history
                        else None,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save optimization result: {e}")
            return False

    def save_trial(
        self,
        task_id: str,
        trial_id: str,
        trial_number: int,
        parameters: Dict[str, Any],
        objective_value: Optional[float],
        status: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存试验记录

        Args:
            task_id: 任务ID
            trial_id: 试验ID
            trial_number: 试验编号
            parameters: 参数
            objective_value: 目标值
            status: 状态
            start_time: 开始时间
            end_time: 结束时间
            error_message: 错误信息
            metrics: 指标

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO trial_history
                    (trial_id, task_id, trial_number, parameters, objective_value, status,
                     start_time, end_time, error_message, metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        trial_id,
                        task_id,
                        trial_number,
                        json.dumps(parameters),
                        objective_value,
                        status,
                        start_time.isoformat() if start_time else None,
                        end_time.isoformat() if end_time else None,
                        error_message,
                        json.dumps(metrics) if metrics else None,
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save trial: {e}")
            return False

    def save_strategy_optimization(
        self,
        strategy_name: str,
        parameters: Dict[str, Any],
        train_performance: Dict[str, float],
        test_performance: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
        walk_forward_results: Optional[List[Dict]] = None,
    ) -> bool:
        """保存策略优化结果

        Args:
            strategy_name: 策略名称
            parameters: 参数
            train_performance: 训练集性能
            test_performance: 测试集性能
            symbol: 股票代码
            walk_forward_results: Walk Forward结果

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO strategy_optimization
                    (strategy_name, symbol, parameters, train_performance, test_performance,
                     optimization_date, walk_forward_results)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        strategy_name,
                        symbol,
                        json.dumps(parameters),
                        json.dumps(train_performance),
                        json.dumps(test_performance) if test_performance else None,
                        datetime.now().isoformat(),
                        json.dumps(walk_forward_results)
                        if walk_forward_results
                        else None,
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save strategy optimization: {e}")
            return False

    def save_portfolio_optimization(
        self,
        optimization_name: str,
        weights: Dict[str, float],
        expected_return: float,
        volatility: float,
        sharpe_ratio: float,
        constraints: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存投资组合优化结果

        Args:
            optimization_name: 优化名称
            weights: 权重
            expected_return: 预期收益
            volatility: 波动率
            sharpe_ratio: 夏普比率
            constraints: 约束条件
            metadata: 元数据

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO portfolio_optimization
                    (optimization_name, weights, expected_return, volatility, sharpe_ratio,
                     optimization_date, constraints, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        optimization_name,
                        json.dumps(weights),
                        expected_return,
                        volatility,
                        sharpe_ratio,
                        datetime.now().isoformat(),
                        json.dumps(constraints) if constraints else None,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save portfolio optimization: {e}")
            return False

    def save_multi_objective_result(
        self,
        task_id: str,
        pareto_front: List[Dict[str, Any]],
        objective_names: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存多目标优化结果

        Args:
            task_id: 任务ID
            pareto_front: 帕累托前沿
            objective_names: 目标名称列表
            metadata: 元数据

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO multi_objective_results
                    (task_id, pareto_front, n_solutions, objective_names, optimization_date, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        task_id,
                        json.dumps(pareto_front),
                        len(pareto_front),
                        json.dumps(objective_names),
                        datetime.now().isoformat(),
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save multi-objective result: {e}")
            return False

    def get_optimization_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取优化结果

        Args:
            task_id: 任务ID

        Returns:
            优化结果
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT best_parameters, best_value, n_trials, n_successful_trials,
                           total_time_seconds, convergence_history
                    FROM optimization_results
                    WHERE task_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (task_id,),
                )

                row = cursor.fetchone()
                if row:
                    return {
                        "best_parameters": json.loads(row[0]),
                        "best_value": row[1],
                        "n_trials": row[2],
                        "n_successful_trials": row[3],
                        "total_time_seconds": row[4],
                        "convergence_history": json.loads(row[5]) if row[5] else None,
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to get optimization result: {e}")
            return None

    def get_strategy_optimization_history(
        self, strategy_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取策略优化历史

        Args:
            strategy_name: 策略名称
            limit: 结果数量限制

        Returns:
            优化历史列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, symbol, parameters, train_performance, test_performance,
                           optimization_date
                    FROM strategy_optimization
                    WHERE strategy_name = ?
                    ORDER BY optimization_date DESC
                    LIMIT ?
                """,
                    (strategy_name, limit),
                )

                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append(
                        {
                            "id": row[0],
                            "symbol": row[1],
                            "parameters": json.loads(row[2]),
                            "train_performance": json.loads(row[3]),
                            "test_performance": json.loads(row[4]) if row[4] else None,
                            "optimization_date": row[5],
                        }
                    )
                return results
        except Exception as e:
            logger.error(f"Failed to get strategy optimization history: {e}")
            return []

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = {}

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 优化任务数
                cursor.execute("SELECT COUNT(*) FROM optimization_tasks")
                stats["total_tasks"] = cursor.fetchone()[0]

                # 优化结果数
                cursor.execute("SELECT COUNT(*) FROM optimization_results")
                stats["total_results"] = cursor.fetchone()[0]

                # 试验数
                cursor.execute("SELECT COUNT(*) FROM trial_history")
                stats["total_trials"] = cursor.fetchone()[0]

                # 策略优化数
                cursor.execute("SELECT COUNT(*) FROM strategy_optimization")
                stats["total_strategy_optimizations"] = cursor.fetchone()[0]

                # 投资组合优化数
                cursor.execute("SELECT COUNT(*) FROM portfolio_optimization")
                stats["total_portfolio_optimizations"] = cursor.fetchone()[0]

                # 多目标优化数
                cursor.execute("SELECT COUNT(*) FROM multi_objective_results")
                stats["total_multi_objective_results"] = cursor.fetchone()[0]

                # 数据库大小
                db_file = Path(self.db_path)
                if db_file.exists():
                    stats["database_size_mb"] = db_file.stat().st_size / (1024 * 1024)

            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


# 全局数据库管理器实例
_global_db_manager: Optional[OptimizationDatabaseManager] = None


def get_optimization_database_manager(
    db_path: str = "data/module07_optimization.db",
) -> OptimizationDatabaseManager:
    """获取全局优化数据库管理器实例

    Args:
        db_path: 数据库路径

    Returns:
        数据库管理器实例
    """
    global _global_db_manager
    if _global_db_manager is None:
        _global_db_manager = OptimizationDatabaseManager(db_path)
    return _global_db_manager
