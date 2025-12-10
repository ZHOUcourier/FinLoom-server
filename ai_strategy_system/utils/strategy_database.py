#!/usr/bin/env python3
"""策略数据库管理器 - 管理策略元数据"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from common.logging_system import setup_logger

LOGGER = setup_logger("strategy_database")


class StrategyDatabase:
    """策略数据库管理器

    管理策略的元数据，包括:
    - 策略ID、名称、描述
    - 创建时间、更新时间
    - 策略状态(草稿、已保存、已激活)
    - 用户ID
    - 回测结果摘要
    - 策略文件路径
    """

    def __init__(self, db_path: str = "data/strategy_metadata.db"):
        """初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        LOGGER.info(f"📊 策略数据库初始化: {self.db_path.absolute()}")

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    model_type TEXT,
                    stock_symbols TEXT,  -- JSON array
                    user_requirement TEXT,
                    
                    -- 状态
                    status TEXT DEFAULT 'draft',  -- draft, saved, activated
                    
                    -- 回测结果摘要
                    backtest_id TEXT,
                    total_return REAL,
                    annual_return REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    win_rate REAL,
                    
                    -- 文件路径
                    strategy_dir TEXT,
                    
                    -- 时间戳
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- 额外元数据(JSON)
                    metadata TEXT
                )
            """)

            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON strategies(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON strategies(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON strategies(created_at DESC)
            """)

            conn.commit()

    def save_strategy(
        self,
        strategy_id: str,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        model_type: Optional[str] = None,
        stock_symbols: Optional[List[str]] = None,
        user_requirement: Optional[str] = None,
        strategy_dir: Optional[str] = None,
        status: str = "saved",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存策略元数据

        Args:
            strategy_id: 策略唯一标识
            user_id: 用户ID
            name: 策略名称
            description: 策略描述
            model_type: 模型类型
            stock_symbols: 股票代码列表
            user_requirement: 用户需求
            strategy_dir: 策略文件目录
            status: 策略状态
            metadata: 额外元数据

        Returns:
            是否成功
        """
        import json

        try:
            with sqlite3.connect(self.db_path) as conn:
                # 检查是否已存在
                cursor = conn.execute(
                    "SELECT strategy_id FROM strategies WHERE strategy_id = ?",
                    (strategy_id,),
                )
                exists = cursor.fetchone() is not None

                if exists:
                    # 更新
                    conn.execute(
                        """
                        UPDATE strategies
                        SET user_id = ?,
                            name = ?,
                            description = ?,
                            model_type = ?,
                            stock_symbols = ?,
                            user_requirement = ?,
                            strategy_dir = ?,
                            status = ?,
                            metadata = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE strategy_id = ?
                    """,
                        (
                            user_id,
                            name or f"策略_{strategy_id}",
                            description,
                            model_type,
                            json.dumps(stock_symbols) if stock_symbols else None,
                            user_requirement,
                            strategy_dir,
                            status,
                            json.dumps(metadata) if metadata else None,
                            strategy_id,
                        ),
                    )
                    LOGGER.info(f"✅ 策略元数据已更新: {strategy_id}")
                else:
                    # 插入
                    conn.execute(
                        """
                        INSERT INTO strategies (
                            strategy_id, user_id, name, description,
                            model_type, stock_symbols, user_requirement,
                            strategy_dir, status, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            strategy_id,
                            user_id,
                            name or f"策略_{strategy_id}",
                            description,
                            model_type,
                            json.dumps(stock_symbols) if stock_symbols else None,
                            user_requirement,
                            strategy_dir,
                            status,
                            json.dumps(metadata) if metadata else None,
                        ),
                    )
                    LOGGER.info(f"✅ 策略元数据已保存: {strategy_id}")

                conn.commit()
                return True

        except Exception as e:
            LOGGER.error(f"❌ 保存策略元数据失败: {e}", exc_info=True)
            return False

    def update_backtest_result(
        self,
        strategy_id: str,
        backtest_id: str,
        total_return: float,
        annual_return: float,
        sharpe_ratio: float,
        max_drawdown: float,
        win_rate: float,
    ) -> bool:
        """更新策略的回测结果

        Args:
            strategy_id: 策略ID
            backtest_id: 回测ID
            total_return: 总收益率
            annual_return: 年化收益率
            sharpe_ratio: 夏普比率
            max_drawdown: 最大回撤
            win_rate: 胜率

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE strategies
                    SET backtest_id = ?,
                        total_return = ?,
                        annual_return = ?,
                        sharpe_ratio = ?,
                        max_drawdown = ?,
                        win_rate = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE strategy_id = ?
                """,
                    (
                        backtest_id,
                        total_return,
                        annual_return,
                        sharpe_ratio,
                        max_drawdown,
                        win_rate,
                        strategy_id,
                    ),
                )
                conn.commit()
                LOGGER.info(f"✅ 回测结果已更新: {strategy_id}")
                return True

        except Exception as e:
            LOGGER.error(f"❌ 更新回测结果失败: {e}", exc_info=True)
            return False

    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取策略信息

        Args:
            strategy_id: 策略ID

        Returns:
            策略信息字典，不存在返回None
        """
        import json

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,)
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                result = dict(row)

                # 解析JSON字段
                if result.get("stock_symbols"):
                    result["stock_symbols"] = json.loads(result["stock_symbols"])
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])

                return result

        except Exception as e:
            LOGGER.error(f"❌ 获取策略失败: {e}", exc_info=True)
            return None

    def list_strategies(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出策略

        Args:
            user_id: 用户ID过滤(可选)
            status: 状态过滤(可选)
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            策略列表
        """
        import json

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # 构建查询
                query = "SELECT * FROM strategies WHERE 1=1"
                params: List[Any] = []

                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)

                if status:
                    query += " AND status = ?"
                    params.append(status)

                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    result = dict(row)

                    # 解析JSON字段
                    if result.get("stock_symbols"):
                        result["stock_symbols"] = json.loads(result["stock_symbols"])
                    if result.get("metadata"):
                        result["metadata"] = json.loads(result["metadata"])

                    results.append(result)

                return results

        except Exception as e:
            LOGGER.error(f"❌ 列出策略失败: {e}", exc_info=True)
            return []

    def delete_strategy(self, strategy_id: str) -> bool:
        """删除策略

        Args:
            strategy_id: 策略ID

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM strategies WHERE strategy_id = ?", (strategy_id,)
                )
                conn.commit()
                LOGGER.info(f"✅ 策略已删除: {strategy_id}")
                return True

        except Exception as e:
            LOGGER.error(f"❌ 删除策略失败: {e}", exc_info=True)
            return False

    def update_strategy_status(
        self,
        strategy_id: str,
        status: str,
    ) -> bool:
        """更新策略状态

        Args:
            strategy_id: 策略ID
            status: 新状态 (draft, saved, activated)

        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE strategies
                    SET status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE strategy_id = ?
                """,
                    (status, strategy_id),
                )
                conn.commit()
                LOGGER.info(f"✅ 策略状态已更新: {strategy_id} -> {status}")
                return True

        except Exception as e:
            LOGGER.error(f"❌ 更新策略状态失败: {e}", exc_info=True)
            return False


# 全局单例
_strategy_db: Optional[StrategyDatabase] = None


def get_strategy_database() -> StrategyDatabase:
    """获取策略数据库单例

    Returns:
        StrategyDatabase实例
    """
    global _strategy_db
    if _strategy_db is None:
        _strategy_db = StrategyDatabase()
    return _strategy_db
