#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化默认管理员账户
"""

import logging
from pathlib import Path
from common.user_database import user_db

logger = logging.getLogger(__name__)


def init_default_admin():
    """
    初始化默认管理员账户
    用户名：Sycamore1024
    密码：Finloomtest
    权限等级：128（最高级）
    """
    try:
        # 检查是否已存在
        import sqlite3
        db_path = Path("data/users.db")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT user_id FROM users WHERE username = ?", ("Sycamore1024",))
            existing = cursor.fetchone()
            
            if existing:
                logger.info("默认管理员账户已存在")
                # 确保权限正确
                cursor.execute("""
                    UPDATE users 
                    SET is_admin = 1, permission_level = 128, daily_token_limit = -1
                    WHERE username = ?
                """, ("Sycamore1024",))
                conn.commit()
                logger.info("已更新默认管理员权限为128")
                return True
        
        # 创建新管理员账户
        success, message, user_id = user_db.create_user(
            username="Sycamore1024",
            password="Finloomtest",
            email="admin@finloom.com",
            display_name="系统管理员",
            is_admin=True,
            permission_level=128
        )
        
        if success:
            # 设置无限token限制
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET daily_token_limit = -1
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
            
            logger.info(f"✅ 默认管理员账户创建成功！用户名: Sycamore1024, 权限等级: 128")
            print("=" * 60)
            print("✅ 默认管理员账户已创建")
            print("   用户名: Sycamore1024")
            print("   密码: Finloomtest")
            print("   权限等级: 128 (最高级)")
            print("=" * 60)
            return True
        else:
            logger.error(f"创建默认管理员失败: {message}")
            return False
            
    except Exception as e:
        logger.error(f"初始化默认管理员失败: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_default_admin()


