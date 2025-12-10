#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据库管理模块
管理用户账号、认证和数据隔离
"""

import hashlib
import sqlite3
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class UserDatabase:
    """用户数据库管理类"""
    
    def __init__(self, db_path: str = "data/users.db"):
        """
        初始化用户数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    display_name TEXT,
                    avatar_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    is_admin INTEGER DEFAULT 0,
                    permission_level INTEGER DEFAULT 1,
                    daily_token_limit INTEGER DEFAULT 30000
                )
            """)
            
            # 用户会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_valid INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 用户配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, setting_key),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 用户活动日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    activity_detail TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_username ON users(username)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_email ON users(email)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_token ON user_sessions(token)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_sessions ON user_sessions(user_id)
            """)
            
            conn.commit()
            logger.info("用户数据库初始化完成")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """
        使用盐值对密码进行哈希
        
        Args:
            password: 原始密码
            salt: 盐值
            
        Returns:
            哈希后的密码
        """
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
    
    def _generate_salt(self) -> str:
        """生成随机盐值"""
        return secrets.token_hex(32)
    
    def _generate_token(self) -> str:
        """生成访问令牌"""
        return secrets.token_urlsafe(48)
    
    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        is_admin: bool = False,
        permission_level: int = 1
    ) -> Tuple[bool, str, Optional[int]]:
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            display_name: 显示名称（可选）
            
        Returns:
            (成功标志, 消息, 用户ID)
        """
        # 验证用户名和密码
        if not username or len(username) < 3:
            return False, "用户名长度至少为3个字符", None
        
        if not password or len(password) < 6:
            return False, "密码长度至少为6个字符", None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查用户名是否已存在
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return False, "用户名已存在", None
                
                # 检查邮箱是否已存在
                if email:
                    cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
                    if cursor.fetchone():
                        return False, "邮箱已被注册", None
                
                # 生成盐值和密码哈希
                salt = self._generate_salt()
                password_hash = self._hash_password(password, salt)
                
                # 插入新用户
                # 权限等级：1=普通用户，2-128=管理员
                if is_admin and permission_level == 1:
                    permission_level = 2  # 默认管理员权限为2
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, salt, display_name, is_admin, permission_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (username, email, password_hash, salt, display_name or username, 1 if is_admin else 0, permission_level))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"新用户创建成功: {username} (ID: {user_id})")
                return True, "注册成功", user_id
                
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return False, f"注册失败: {str(e)}", None
    
    def verify_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        验证用户凭证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (成功标志, 消息, 用户信息字典)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取用户信息
                cursor.execute("""
                    SELECT user_id, username, email, password_hash, salt, 
                           display_name, avatar_url, is_active, is_admin, permission_level
                    FROM users 
                    WHERE username = ?
                """, (username,))
                
                user = cursor.fetchone()
                if not user:
                    return False, "用户名或密码错误", None
                
                # 检查用户是否被禁用
                if not user['is_active']:
                    return False, "账号已被禁用", None
                
                # 验证密码
                password_hash = self._hash_password(password, user['salt'])
                if password_hash != user['password_hash']:
                    return False, "用户名或密码错误", None
                
                # 更新最后登录时间
                cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                """, (user['user_id'],))
                conn.commit()
                
                # 返回用户信息
                user_info = {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'display_name': user['display_name'],
                    'avatar_url': user['avatar_url'],
                    'is_admin': bool(user['is_admin']),
                    'permission_level': user['permission_level']
                }
                
                logger.info(f"用户登录成功: {username} (ID: {user['user_id']}, 权限等级: {user['permission_level']})")
                return True, "登录成功", user_info
                
        except Exception as e:
            logger.error(f"用户验证失败: {e}")
            return False, f"登录失败: {str(e)}", None
    
    def create_session(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_hours: int = 24
    ) -> Tuple[bool, str, Optional[str]]:
        """
        创建用户会话
        
        Args:
            user_id: 用户ID
            ip_address: IP地址
            user_agent: 用户代理
            expires_hours: 过期时间（小时）
            
        Returns:
            (成功标志, 消息, 访问令牌)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 生成会话ID和令牌
                session_id = secrets.token_hex(16)
                token = self._generate_token()
                
                # 计算过期时间
                expires_at = datetime.now() + timedelta(hours=expires_hours)
                
                # 插入会话
                cursor.execute("""
                    INSERT INTO user_sessions 
                    (session_id, user_id, token, expires_at, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, user_id, token, expires_at, ip_address, user_agent))
                
                conn.commit()
                
                logger.info(f"会话创建成功: User ID {user_id}")
                return True, "会话创建成功", token
                
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return False, f"会话创建失败: {str(e)}", None
    
    def verify_token(self, token: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        验证访问令牌
        
        Args:
            token: 访问令牌
            
        Returns:
            (有效标志, 消息, 用户信息)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 查询会话信息
                cursor.execute("""
                    SELECT s.session_id, s.user_id, s.expires_at, s.is_valid,
                           u.username, u.email, u.display_name, u.avatar_url, u.is_active, u.is_admin,
                           u.permission_level, u.daily_token_limit
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.user_id
                    WHERE s.token = ?
                """, (token,))
                
                session = cursor.fetchone()
                if not session:
                    return False, "无效的令牌", None
                
                # 检查会话是否有效
                if not session['is_valid']:
                    return False, "会话已失效", None
                
                # 检查用户是否被禁用
                if not session['is_active']:
                    return False, "账号已被禁用", None
                
                # 检查是否过期
                expires_at = datetime.fromisoformat(session['expires_at'])
                if datetime.now() > expires_at:
                    # 标记会话为无效
                    cursor.execute("""
                        UPDATE user_sessions 
                        SET is_valid = 0 
                        WHERE session_id = ?
                    """, (session['session_id'],))
                    conn.commit()
                    return False, "令牌已过期", None
                
                # 更新最后活动时间
                cursor.execute("""
                    UPDATE user_sessions 
                    SET last_activity = CURRENT_TIMESTAMP 
                    WHERE session_id = ?
                """, (session['session_id'],))
                conn.commit()
                
                # 返回用户信息
                user_info = {
                    'user_id': session['user_id'],
                    'username': session['username'],
                    'email': session['email'],
                    'display_name': session['display_name'],
                    'avatar_url': session['avatar_url'],
                    'is_admin': bool(session['is_admin']),
                    'permission_level': session['permission_level'],
                    'daily_token_limit': session['daily_token_limit']
                }
                
                return True, "令牌有效", user_info
                
        except Exception as e:
            logger.error(f"令牌验证失败: {e}")
            return False, f"令牌验证失败: {str(e)}", None
    
    def invalidate_session(self, token: str) -> bool:
        """
        使会话失效（登出）
        
        Args:
            token: 访问令牌
            
        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_valid = 0 
                    WHERE token = ?
                """, (token,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"会话失效失败: {e}")
            return False
    
    def log_activity(
        self,
        user_id: int,
        activity_type: str,
        activity_detail: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """
        记录用户活动
        
        Args:
            user_id: 用户ID
            activity_type: 活动类型
            activity_detail: 活动详情
            ip_address: IP地址
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_activity_log 
                    (user_id, activity_type, activity_detail, ip_address)
                    VALUES (?, ?, ?, ?)
                """, (user_id, activity_type, activity_detail, ip_address))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"记录用户活动失败: {e}")
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        根据ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_id, username, email, display_name, 
                           avatar_url, created_at, last_login, is_admin,
                           permission_level, daily_token_limit
                    FROM users 
                    WHERE user_id = ?
                """, (user_id,))
                
                user = cursor.fetchone()
                if user:
                    return dict(user)
                return None
                
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    def update_user_profile(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        更新用户资料
        
        Args:
            user_id: 用户ID
            display_name: 显示名称
            email: 邮箱
            avatar_url: 头像URL
            
        Returns:
            (成功标志, 消息)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates = []
                params = []
                
                if display_name is not None:
                    updates.append("display_name = ?")
                    params.append(display_name)
                
                if email is not None:
                    # 检查邮箱是否被其他用户使用
                    cursor.execute("""
                        SELECT user_id FROM users 
                        WHERE email = ? AND user_id != ?
                    """, (email, user_id))
                    if cursor.fetchone():
                        return False, "邮箱已被其他用户使用"
                    
                    updates.append("email = ?")
                    params.append(email)
                
                if avatar_url is not None:
                    updates.append("avatar_url = ?")
                    params.append(avatar_url)
                
                if not updates:
                    return True, "无需更新"
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                
                sql = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                cursor.execute(sql, params)
                conn.commit()
                
                return True, "资料更新成功"
                
        except Exception as e:
            logger.error(f"更新用户资料失败: {e}")
            return False, f"更新失败: {str(e)}"
    
    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            (成功标志, 消息)
        """
        if not new_password or len(new_password) < 6:
            return False, "新密码长度至少为6个字符"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取用户当前密码和盐值
                cursor.execute("""
                    SELECT password_hash, salt 
                    FROM users 
                    WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False, "用户不存在"
                
                old_hash, old_salt = result
                
                # 验证旧密码
                if self._hash_password(old_password, old_salt) != old_hash:
                    return False, "旧密码错误"
                
                # 生成新盐值和密码哈希
                new_salt = self._generate_salt()
                new_hash = self._hash_password(new_password, new_salt)
                
                # 更新密码
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_hash, new_salt, user_id))
                
                # 使所有会话失效
                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_valid = 0 
                    WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                
                logger.info(f"用户 {user_id} 修改密码成功")
                return True, "密码修改成功"
                
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            return False, f"修改失败: {str(e)}"


# 创建全局用户数据库实例
user_db = UserDatabase()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    db = UserDatabase("data/users_test.db")
    
    # 测试创建用户
    success, msg, user_id = db.create_user("testuser", "password123", "test@example.com")
    print(f"创建用户: {success}, {msg}, ID: {user_id}")
    
    # 测试验证用户
    success, msg, user_info = db.verify_user("testuser", "password123")
    print(f"验证用户: {success}, {msg}, Info: {user_info}")
    
    # 测试创建会话
    if user_id:
        success, msg, token = db.create_session(user_id)
        print(f"创建会话: {success}, {msg}, Token: {token}")
        
        # 测试验证令牌
        if token:
            success, msg, user_info = db.verify_token(token)
            print(f"验证令牌: {success}, {msg}, Info: {user_info}")

