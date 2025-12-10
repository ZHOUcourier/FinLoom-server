#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户权限管理模块
管理用户权限、配额和限制
"""

import logging
from typing import Dict, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class UserPermissions:
    """用户权限类"""
    
    # 权限定义
    PERMISSION_STRATEGY_GENERATE = "strategy_generate"  # 策略生成权限
    PERMISSION_UNLIMITED_CHAT = "unlimited_chat"  # 无限对话权限
    PERMISSION_ADMIN = "admin"  # 管理员权限
    
    # 配额定义
    QUOTA_CHAT_TOKENS = "chat_tokens"  # 对话token配额
    
    # 默认配额
    DEFAULT_USER_CHAT_TOKEN_LIMIT = 30000  # 普通用户每月30000 tokens
    ADMIN_CHAT_TOKEN_LIMIT = -1  # 管理员无限制
    
    def __init__(self, user_info: Dict):
        """
        初始化用户权限
        
        Args:
            user_info: 用户信息字典
        """
        self.user_id = user_info.get('user_id')
        self.username = user_info.get('username')
        self.is_admin = user_info.get('is_admin', False)
        
        # 初始化权限
        self._permissions = self._load_permissions()
        
        # 初始化配额
        self._quotas = self._load_quotas()
    
    def _load_permissions(self) -> Dict[str, bool]:
        """加载用户权限"""
        if self.is_admin:
            # 管理员拥有所有权限
            return {
                self.PERMISSION_STRATEGY_GENERATE: True,
                self.PERMISSION_UNLIMITED_CHAT: True,
                self.PERMISSION_ADMIN: True
            }
        else:
            # 普通用户权限
            return {
                self.PERMISSION_STRATEGY_GENERATE: False,  # 禁止策略生成
                self.PERMISSION_UNLIMITED_CHAT: False,
                self.PERMISSION_ADMIN: False
            }
    
    def _load_quotas(self) -> Dict[str, int]:
        """加载用户配额"""
        if self.is_admin:
            return {
                self.QUOTA_CHAT_TOKENS: self.ADMIN_CHAT_TOKEN_LIMIT  # 无限制
            }
        else:
            return {
                self.QUOTA_CHAT_TOKENS: self.DEFAULT_USER_CHAT_TOKEN_LIMIT  # 30000 tokens
            }
    
    def has_permission(self, permission: str) -> bool:
        """
        检查用户是否有某个权限
        
        Args:
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        return self._permissions.get(permission, False)
    
    def require_permission(self, permission: str):
        """
        要求用户必须有某个权限（否则抛出异常）
        
        Args:
            permission: 权限名称
            
        Raises:
            HTTPException: 无权限时抛出403
        """
        if not self.has_permission(permission):
            permission_names = {
                self.PERMISSION_STRATEGY_GENERATE: "策略生成",
                self.PERMISSION_UNLIMITED_CHAT: "无限对话",
                self.PERMISSION_ADMIN: "管理员"
            }
            perm_name = permission_names.get(permission, permission)
            raise HTTPException(
                status_code=403,
                detail=f"您没有【{perm_name}】权限。请联系管理员或升级账户。"
            )
    
    def get_quota(self, quota_type: str) -> int:
        """
        获取用户配额
        
        Args:
            quota_type: 配额类型
            
        Returns:
            int: 配额值（-1表示无限制）
        """
        return self._quotas.get(quota_type, 0)
    
    def check_chat_token_limit(self, used_tokens: int = 0) -> bool:
        """
        检查对话token是否超过限制
        
        Args:
            used_tokens: 已使用的token数量
            
        Returns:
            bool: 是否在限制内
        """
        limit = self.get_quota(self.QUOTA_CHAT_TOKENS)
        
        # -1表示无限制
        if limit == -1:
            return True
        
        return used_tokens < limit
    
    def require_chat_token_quota(self, used_tokens: int = 0):
        """
        要求用户有足够的对话token配额（否则抛出异常）
        
        Args:
            used_tokens: 已使用的token数量
            
        Raises:
            HTTPException: 超过配额时抛出403
        """
        if not self.check_chat_token_limit(used_tokens):
            limit = self.get_quota(self.QUOTA_CHAT_TOKENS)
            raise HTTPException(
                status_code=403,
                detail=f"您的对话token配额已用完。本月限额：{limit} tokens，已使用：{used_tokens} tokens。请联系管理员增加配额。"
            )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'is_admin': self.is_admin,
            'permissions': self._permissions,
            'quotas': self._quotas
        }


# 便捷函数
def get_user_permissions(user_info: Dict) -> UserPermissions:
    """
    获取用户权限对象
    
    Args:
        user_info: 用户信息字典
        
    Returns:
        UserPermissions: 用户权限对象
    """
    return UserPermissions(user_info)


def require_strategy_permission(user_info: Dict):
    """要求用户有策略生成权限"""
    perms = get_user_permissions(user_info)
    perms.require_permission(UserPermissions.PERMISSION_STRATEGY_GENERATE)


def check_chat_token_quota(user_info: Dict, used_tokens: int = 0) -> bool:
    """检查对话token配额"""
    perms = get_user_permissions(user_info)
    return perms.check_chat_token_limit(used_tokens)


# 导出
__all__ = [
    'UserPermissions',
    'get_user_permissions',
    'require_strategy_permission',
    'check_chat_token_quota'
]


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 测试管理员权限
    admin_info = {
        'user_id': 1,
        'username': 'admin',
        'is_admin': True
    }
    admin_perms = UserPermissions(admin_info)
    print(f"管理员权限: {admin_perms.to_dict()}")
    print(f"管理员可以生成策略: {admin_perms.has_permission(UserPermissions.PERMISSION_STRATEGY_GENERATE)}")
    print(f"管理员对话token配额: {admin_perms.get_quota(UserPermissions.QUOTA_CHAT_TOKENS)}")
    
    # 测试普通用户权限
    user_info = {
        'user_id': 2,
        'username': 'user',
        'is_admin': False
    }
    user_perms = UserPermissions(user_info)
    print(f"\n普通用户权限: {user_perms.to_dict()}")
    print(f"普通用户可以生成策略: {user_perms.has_permission(UserPermissions.PERMISSION_STRATEGY_GENERATE)}")
    print(f"普通用户对话token配额: {user_perms.get_quota(UserPermissions.QUOTA_CHAT_TOKENS)}")
    print(f"普通用户已用25000 tokens是否超限: {user_perms.check_chat_token_limit(25000)}")
    print(f"普通用户已用35000 tokens是否超限: {user_perms.check_chat_token_limit(35000)}")


