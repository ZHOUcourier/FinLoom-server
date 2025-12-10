#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户留言系统
普通用户可以给管理员留言
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class UserMessageSystem:
    """用户留言系统"""
    
    def __init__(self, db_path: str = "data/users.db"):
        """初始化留言系统"""
        self.db_path = Path(db_path)
        self._init_table()
    
    def _init_table(self):
        """初始化留言表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 用户留言表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    message_type TEXT DEFAULT 'feedback',
                    subject TEXT,
                    content TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP,
                    replied_by INTEGER,
                    reply_content TEXT,
                    reply_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_messages_user 
                ON user_messages(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_messages_status 
                ON user_messages(status)
            """)
            
            conn.commit()
            logger.info("用户留言表初始化完成")
    
    def send_message(
        self,
        user_id: int,
        username: str,
        content: str,
        subject: Optional[str] = None,
        message_type: str = "feedback"
    ) -> bool:
        """
        发送留言给管理员
        
        Args:
            user_id: 用户ID
            username: 用户名
            content: 留言内容
            subject: 主题
            message_type: 留言类型 (feedback/bug/question/suggestion)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_messages 
                    (user_id, username, message_type, subject, content, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (user_id, username, message_type, subject, content))
                
                conn.commit()
                logger.info(f"用户 {username} 发送留言成功")
                return True
                
        except Exception as e:
            logger.error(f"发送留言失败: {e}")
            return False
    
    def get_all_messages(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取所有留言（管理员用）
        
        Args:
            status: 状态过滤 (pending/read/replied)
            limit: 返回数量限制
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if status:
                    cursor.execute("""
                        SELECT * FROM user_messages
                        WHERE status = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (status, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM user_messages
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (limit,))
                
                messages = [dict(row) for row in cursor.fetchall()]
                return messages
                
        except Exception as e:
            logger.error(f"获取留言失败: {e}")
            return []
    
    def get_user_messages(self, user_id: int) -> List[Dict]:
        """获取用户自己的留言"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM user_messages
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取用户留言失败: {e}")
            return []
    
    def mark_as_read(self, message_id: int) -> bool:
        """标记留言为已读"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE user_messages
                    SET status = 'read', read_at = CURRENT_TIMESTAMP
                    WHERE message_id = ?
                """, (message_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"标记已读失败: {e}")
            return False
    
    def reply_message(
        self,
        message_id: int,
        admin_id: int,
        reply_content: str
    ) -> bool:
        """管理员回复留言"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE user_messages
                    SET 
                        status = 'replied',
                        replied_by = ?,
                        reply_content = ?,
                        reply_at = CURRENT_TIMESTAMP
                    WHERE message_id = ?
                """, (admin_id, reply_content, message_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"回复留言失败: {e}")
            return False
    
    def get_unread_count(self) -> int:
        """获取未读留言数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM user_messages
                    WHERE status = 'pending'
                """)
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"获取未读数量失败: {e}")
            return 0


# 全局实例
message_system = UserMessageSystem()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 测试
    ms = UserMessageSystem("data/users_test.db")
    
    # 发送留言
    ms.send_message(1, "testuser", "这是一条测试留言", "测试主题", "feedback")
    
    # 获取所有留言
    messages = ms.get_all_messages()
    print(f"所有留言: {messages}")
    
    # 获取未读数量
    unread = ms.get_unread_count()
    print(f"未读留言数: {unread}")


