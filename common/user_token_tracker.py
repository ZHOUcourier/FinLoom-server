#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户Token使用追踪模块
追踪每个用户的API token使用情况
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class UserTokenTracker:
    """用户Token使用追踪器"""
    
    def __init__(self, db_path: str = "data/users.db"):
        """
        初始化Token追踪器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._init_table()
    
    def _init_table(self):
        """初始化token使用记录表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Token使用记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    api_endpoint TEXT,
                    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    month TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 月度统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_monthly_stats (
                    user_id INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    total_tokens INTEGER DEFAULT 0,
                    request_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, month),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_token_usage_user 
                ON user_token_usage(user_id, month)
            """)
            
            conn.commit()
            logger.info("Token追踪表初始化完成")
    
    def record_token_usage(
        self,
        user_id: int,
        tokens_used: int,
        api_endpoint: str = "chat"
    ):
        """
        记录token使用
        
        Args:
            user_id: 用户ID
            tokens_used: 使用的token数量
            api_endpoint: API端点
        """
        try:
            current_month = datetime.now().strftime("%Y-%m")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 记录使用明细
                cursor.execute("""
                    INSERT INTO user_token_usage (user_id, tokens_used, api_endpoint, month)
                    VALUES (?, ?, ?, ?)
                """, (user_id, tokens_used, api_endpoint, current_month))
                
                # 更新月度统计
                cursor.execute("""
                    INSERT INTO user_monthly_stats (user_id, month, total_tokens, request_count)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(user_id, month) DO UPDATE SET
                        total_tokens = total_tokens + ?,
                        request_count = request_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (user_id, current_month, tokens_used, tokens_used))
                
                conn.commit()
                logger.info(f"记录用户 {user_id} 使用了 {tokens_used} tokens")
                
        except Exception as e:
            logger.error(f"记录token使用失败: {e}")
    
    def get_monthly_usage(self, user_id: int, month: Optional[str] = None) -> int:
        """
        获取用户当月token使用量
        
        Args:
            user_id: 用户ID
            month: 月份（格式：YYYY-MM），默认当前月
            
        Returns:
            int: 已使用的token数量
        """
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT total_tokens FROM user_monthly_stats
                    WHERE user_id = ? AND month = ?
                """, (user_id, month))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"获取月度使用量失败: {e}")
            return 0
    
    def get_user_token_info(self, user_id: int) -> Dict:
        """获取用户token使用信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取今日使用量
                cursor.execute("""
                    SELECT COALESCE(SUM(tokens_used), 0)
                    FROM user_token_usage
                    WHERE user_id = ? AND DATE(request_time) = DATE('now')
                """, (user_id,))
                
                today_usage = cursor.fetchone()[0]
                
                # 获取月度使用量
                monthly_usage = self.get_monthly_usage(user_id)
                
                # 获取用户限额
                cursor.execute("""
                    SELECT daily_token_limit
                    FROM users
                    WHERE user_id = ?
                """, (user_id,))
                
                limit_result = cursor.fetchone()
                daily_limit = limit_result[0] if limit_result else 30000
            
            return {
                'today_usage': today_usage,
                'monthly_usage': monthly_usage,
                'daily_limit': daily_limit,
                'is_over_limit': daily_limit != -1 and today_usage >= daily_limit
            }
            
        except Exception as e:
            logger.error(f"获取用户token信息失败: {e}")
            return {
                'today_usage': 0,
                'monthly_usage': 0,
                'daily_limit': 30000,
                'is_over_limit': False
            }
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        获取用户统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 统计信息
        """
        current_month = datetime.now().strftime("%Y-%m")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取当月统计
                cursor.execute("""
                    SELECT total_tokens, request_count, last_updated
                    FROM user_monthly_stats
                    WHERE user_id = ? AND month = ?
                """, (user_id, current_month))
                
                current = cursor.fetchone()
                
                # 获取总计
                cursor.execute("""
                    SELECT 
                        SUM(total_tokens) as total_tokens,
                        SUM(request_count) as total_requests
                    FROM user_monthly_stats
                    WHERE user_id = ?
                """, (user_id,))
                
                total = cursor.fetchone()
                
                return {
                    'user_id': user_id,
                    'current_month': current_month,
                    'monthly_tokens': current['total_tokens'] if current else 0,
                    'monthly_requests': current['request_count'] if current else 0,
                    'total_tokens': total['total_tokens'] if total and total['total_tokens'] else 0,
                    'total_requests': total['total_requests'] if total and total['total_requests'] else 0,
                    'last_updated': current['last_updated'] if current else None
                }
                
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return {
                'user_id': user_id,
                'current_month': current_month,
                'monthly_tokens': 0,
                'monthly_requests': 0,
                'total_tokens': 0,
                'total_requests': 0
            }


# 创建全局实例
token_tracker = UserTokenTracker()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    tracker = UserTokenTracker("data/users_test.db")
    
    # 测试记录使用
    tracker.record_token_usage(1, 1500, "chat")
    tracker.record_token_usage(1, 2000, "chat")
    tracker.record_token_usage(1, 500, "strategy")
    
    # 测试获取使用量
    usage = tracker.get_monthly_usage(1)
    print(f"用户1本月使用: {usage} tokens")
    
    # 测试获取统计
    stats = tracker.get_user_stats(1)
    print(f"用户1统计: {stats}")

