#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户上下文管理模块
用于在各个功能模块中识别和隔离用户数据
"""

from typing import Optional, Dict
from functools import wraps
from fastapi import Header, HTTPException
import logging

from common.user_database import user_db

logger = logging.getLogger(__name__)


class UserContext:
    """用户上下文类"""
    
    def __init__(self, user_id: int, username: str, user_info: Dict):
        self.user_id = user_id
        self.username = username
        self.user_info = user_info
        self.is_admin = user_info.get('is_admin', False)
    
    def __str__(self):
        return f"UserContext(user_id={self.user_id}, username={self.username})"
    
    def __repr__(self):
        return self.__str__()


async def get_current_user(authorization: Optional[str] = Header(None)) -> UserContext:
    """
    从请求头中获取当前用户上下文
    
    Args:
        authorization: 认证令牌（Bearer token）
        
    Returns:
        UserContext: 用户上下文对象
        
    Raises:
        HTTPException: 未认证或认证失败时抛出
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="未提供认证令牌"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # 验证令牌
    valid, message, user_info = user_db.verify_token(token)
    
    if not valid:
        raise HTTPException(
            status_code=401,
            detail=message
        )
    
    return UserContext(
        user_id=user_info['user_id'],
        username=user_info['username'],
        user_info=user_info
    )


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[UserContext]:
    """
    获取可选的用户上下文（用于可选认证的API）
    
    Args:
        authorization: 认证令牌（Bearer token）
        
    Returns:
        Optional[UserContext]: 用户上下文对象，如果未认证则返回None
    """
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


def require_auth(func):
    """
    装饰器：要求用户认证
    
    使用方式:
        @require_auth
        async def my_api(request: Dict, user: UserContext):
            # user参数会自动注入
            pass
    """
    @wraps(func)
    async def wrapper(*args, authorization: Optional[str] = Header(None), **kwargs):
        user = await get_current_user(authorization)
        return await func(*args, user=user, **kwargs)
    return wrapper


def require_admin(func):
    """
    装饰器：要求管理员权限
    
    使用方式:
        @require_admin
        async def admin_api(request: Dict, user: UserContext):
            # 只有管理员可以访问
            pass
    """
    @wraps(func)
    async def wrapper(*args, authorization: Optional[str] = Header(None), **kwargs):
        user = await get_current_user(authorization)
        if not user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="需要管理员权限"
            )
        return await func(*args, user=user, **kwargs)
    return wrapper


def get_user_db_filter(user_id: int) -> Dict:
    """
    获取用户数据库查询过滤条件
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict: 数据库过滤条件
        
    示例:
        filter_condition = get_user_db_filter(user.user_id)
        # 在SQL查询中使用: WHERE user_id = ?
    """
    return {"user_id": user_id}


def add_user_id_to_record(record: Dict, user_id: int) -> Dict:
    """
    向记录中添加用户ID
    
    Args:
        record: 数据记录
        user_id: 用户ID
        
    Returns:
        Dict: 添加了用户ID的记录
    """
    record['user_id'] = user_id
    return record


class UserDataManager:
    """
    用户数据管理器
    提供统一的用户数据隔离接口
    """
    
    @staticmethod
    def get_user_specific_table_name(base_table: str, user_id: int) -> str:
        """
        获取用户专属表名
        
        Args:
            base_table: 基础表名
            user_id: 用户ID
            
        Returns:
            str: 用户专属表名
            
        示例:
            get_user_specific_table_name("conversations", 123)
            # 返回: "conversations_user_123"
        """
        return f"{base_table}_user_{user_id}"
    
    @staticmethod
    def add_user_filter(query_params: Dict, user_id: int) -> Dict:
        """
        向查询参数添加用户过滤
        
        Args:
            query_params: 原始查询参数
            user_id: 用户ID
            
        Returns:
            Dict: 添加用户过滤的查询参数
        """
        query_params['user_id'] = user_id
        return query_params
    
    @staticmethod
    def verify_user_ownership(record_user_id: int, current_user_id: int) -> bool:
        """
        验证用户是否拥有某条记录
        
        Args:
            record_user_id: 记录所属用户ID
            current_user_id: 当前用户ID
            
        Returns:
            bool: 是否拥有
        """
        return record_user_id == current_user_id
    
    @staticmethod
    def require_ownership(record_user_id: int, current_user_id: int, is_admin: bool = False):
        """
        要求用户拥有某条记录（否则抛出异常）
        
        Args:
            record_user_id: 记录所属用户ID
            current_user_id: 当前用户ID
            is_admin: 是否为管理员
            
        Raises:
            HTTPException: 无权访问时抛出
        """
        if not is_admin and record_user_id != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="无权访问该资源"
            )


# 导出常用函数和类
__all__ = [
    'UserContext',
    'get_current_user',
    'get_optional_user',
    'require_auth',
    'require_admin',
    'get_user_db_filter',
    'add_user_id_to_record',
    'UserDataManager'
]


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试用户上下文
    test_user_info = {
        'user_id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'is_admin': False
    }
    
    context = UserContext(1, 'testuser', test_user_info)
    print(f"用户上下文: {context}")
    
    # 测试数据管理器
    manager = UserDataManager()
    
    table_name = manager.get_user_specific_table_name("conversations", 1)
    print(f"用户专属表名: {table_name}")
    
    params = manager.add_user_filter({"limit": 10}, 1)
    print(f"添加用户过滤后的参数: {params}")
    
    # 测试所有权验证
    print(f"验证所有权 (1, 1): {manager.verify_user_ownership(1, 1)}")
    print(f"验证所有权 (1, 2): {manager.verify_user_ownership(1, 2)}")


