#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员功能模块
提供用户管理、权限设置、token监控等功能
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from common.user_database import user_db
from common.user_token_tracker import token_tracker
from common.user_messages import message_system

logger = logging.getLogger(__name__)


class AdminManager:
    """管理员功能管理器"""
    
    def __init__(self, db_path: str = "data/users.db"):
        """初始化管理员管理器"""
        self.db_path = Path(db_path)
    
    def get_all_users(self, requester_permission: int) -> List[Dict]:
        """
        获取所有用户列表（管理员权限）
        
        Args:
            requester_permission: 请求者的权限等级
            
        Returns:
            用户列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取所有用户
                cursor.execute("""
                    SELECT 
                        user_id,
                        username,
                        email,
                        display_name,
                        created_at,
                        last_login,
                        is_active,
                        is_admin,
                        permission_level,
                        daily_token_limit
                    FROM users
                    WHERE is_active = 1
                    ORDER BY permission_level DESC, created_at DESC
                """)
                
                users = []
                for row in cursor.fetchall():
                    user_dict = dict(row)
                    
                    # 添加token使用情况
                    token_info = token_tracker.get_user_token_info(user_dict['user_id'])
                    user_dict.update(token_info)
                    
                    # 检查是否可以管理此用户
                    user_dict['can_manage'] = requester_permission > user_dict['permission_level']
                    
                    users.append(user_dict)
                
                return users
                
        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            return []
    
    def update_user_permission(
        self,
        admin_id: int,
        admin_permission: int,
        target_user_id: int,
        new_permission: int
    ) -> Tuple[bool, str]:
        """
        更新用户权限
        
        Args:
            admin_id: 管理员ID
            admin_permission: 管理员权限等级
            target_user_id: 目标用户ID
            new_permission: 新的权限等级
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 权限验证
            if admin_permission < 2:
                return False, "无权限修改用户权限"
            
            # 不能修改自己的权限
            if admin_id == target_user_id:
                return False, "无法修改自己的权限"
            
            # 权限等级限制：只能将用户提升到自己的权限-1
            if new_permission >= admin_permission:
                return False, f"无法将用户权限设置为 {new_permission}，你的权限等级为 {admin_permission}"
            
            # 权限范围检查
            if new_permission < 1 or new_permission > 128:
                return False, "权限等级必须在1-128之间"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取目标用户当前权限
                cursor.execute("""
                    SELECT permission_level, username
                    FROM users
                    WHERE user_id = ?
                """, (target_user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False, "目标用户不存在"
                
                current_permission, target_username = result
                
                # 验证是否可以管理此用户
                if current_permission >= admin_permission:
                    return False, f"无法管理权限等级大于等于你的用户"
                
                # 更新权限
                cursor.execute("""
                    UPDATE users
                    SET 
                        permission_level = ?,
                        is_admin = CASE WHEN ? >= 2 THEN 1 ELSE 0 END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_permission, new_permission, target_user_id))
                
                conn.commit()
                
                # 记录活动
                cursor.execute("""
                    INSERT INTO user_activities 
                    (user_id, action, description)
                    VALUES (?, 'permission_changed', ?)
                """, (admin_id, f"将用户 {target_username} 的权限从 {current_permission} 修改为 {new_permission}"))
                
                conn.commit()
                
                logger.info(f"管理员 {admin_id} 将用户 {target_username} 的权限从 {current_permission} 修改为 {new_permission}")
                return True, "权限修改成功"
                
        except Exception as e:
            logger.error(f"更新用户权限失败: {e}")
            return False, f"更新失败: {str(e)}"
    
    def update_token_limit(
        self,
        admin_id: int,
        admin_permission: int,
        target_user_id: int,
        new_limit: int
    ) -> Tuple[bool, str]:
        """
        更新用户token限额
        
        Args:
            admin_id: 管理员ID
            admin_permission: 管理员权限等级
            target_user_id: 目标用户ID
            new_limit: 新的token限额（-1表示无限）
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 权限验证
            if admin_permission < 2:
                return False, "无权限修改用户token限额"
            
            # 限额范围检查
            if new_limit < -1 or new_limit > 10000000:
                return False, "Token限额必须在0-10000000之间，或-1表示无限"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取目标用户信息
                cursor.execute("""
                    SELECT permission_level, username
                    FROM users
                    WHERE user_id = ?
                """, (target_user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False, "目标用户不存在"
                
                target_permission, target_username = result
                
                # 验证是否可以管理此用户
                if target_permission >= admin_permission:
                    return False, f"无法管理权限等级大于等于你的用户"
                
                # 更新限额
                cursor.execute("""
                    UPDATE users
                    SET daily_token_limit = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_limit, target_user_id))
                
                conn.commit()
                
                # 记录活动
                limit_text = "无限" if new_limit == -1 else f"{new_limit:,}"
                cursor.execute("""
                    INSERT INTO user_activities 
                    (user_id, action, description)
                    VALUES (?, 'token_limit_changed', ?)
                """, (admin_id, f"将用户 {target_username} 的token限额设置为 {limit_text}"))
                
                conn.commit()
                
                logger.info(f"管理员 {admin_id} 将用户 {target_username} 的token限额设置为 {new_limit}")
                return True, "Token限额设置成功"
                
        except Exception as e:
            logger.error(f"更新token限额失败: {e}")
            return False, f"更新失败: {str(e)}"
    
    def get_user_details(self, admin_permission: int, target_user_id: int) -> Optional[Dict]:
        """
        获取用户详细信息（包括使用记录、错误日志等）
        
        Args:
            admin_permission: 管理员权限等级
            target_user_id: 目标用户ID
            
        Returns:
            用户详细信息
        """
        if admin_permission < 2:
            return None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取用户基本信息
                cursor.execute("""
                    SELECT *
                    FROM users
                    WHERE user_id = ?
                """, (target_user_id,))
                
                user = cursor.fetchone()
                if not user:
                    return None
                
                user_dict = dict(user)
                
                # 获取token使用详情
                token_info = token_tracker.get_user_token_info(target_user_id)
                user_dict['token_info'] = token_info
                
                # 获取最近活动
                cursor.execute("""
                    SELECT *
                    FROM user_activities
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (target_user_id,))
                
                user_dict['recent_activities'] = [dict(row) for row in cursor.fetchall()]
                
                # 获取用户留言
                user_dict['messages'] = message_system.get_user_messages(target_user_id)
                
                return user_dict
                
        except Exception as e:
            logger.error(f"获取用户详情失败: {e}")
            return None
    
    def get_system_stats(self) -> Dict:
        """
        获取系统统计信息（管理员用）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 用户统计
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
                total_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1 AND is_active = 1")
                total_admins = cursor.fetchone()[0]
                
                # Token使用统计
                cursor.execute("""
                    SELECT SUM(tokens_used) 
                    FROM user_token_usage 
                    WHERE request_time >= datetime('now', '-30 days')
                """)
                total_tokens_30d = cursor.fetchone()[0] or 0
                
                # 今日活跃用户
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id)
                    FROM user_activities
                    WHERE created_at >= date('now')
                """)
                active_users_today = cursor.fetchone()[0]
                
                # 未读留言数
                unread_messages = message_system.get_unread_count()
                
                return {
                    'total_users': total_users,
                    'total_admins': total_admins,
                    'regular_users': total_users - total_admins,
                    'total_tokens_30d': total_tokens_30d,
                    'active_users_today': active_users_today,
                    'unread_messages': unread_messages
                }
                
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {}


# 全局实例
admin_manager = AdminManager()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 测试
    users = admin_manager.get_all_users(128)
    print(f"用户列表: {users}")
    
    stats = admin_manager.get_system_stats()
    print(f"系统统计: {stats}")


