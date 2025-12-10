#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理IP池管理器
用于防止爬虫被封禁
"""

import requests
import random
import time
import threading
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from common.logging_system import setup_logger

logger = setup_logger("proxy_pool_manager")


class ProxyPool:
    """代理IP池管理器"""
    
    def __init__(self, use_free=True, use_paid=False):
        """
        初始化代理池
        
        Args:
            use_free: 是否使用免费代理
            use_paid: 是否使用付费代理
        """
        self.proxies = []
        self.blacklist = set()
        self.success_count = {}
        self.fail_count = {}
        self.last_validate_time = {}
        
        self.use_free = use_free
        self.use_paid = use_paid
        
        self.lock = threading.Lock()
        
        # 免费代理来源
        self.free_proxy_apis = [
            'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            'http://www.xiladaili.com/api/?uuid=你的UUID&num=100',  # 需要注册
        ]
        
        # 付费代理配置
        self.paid_proxy_config = {
            'api_url': 'http://api.your-proxy-service.com/get',
            'api_key': 'your_api_key',
        }
        
        # 初始化代理池
        self.refresh_proxies()
        
    def refresh_proxies(self):
        """刷新代理池"""
        logger.info("正在刷新代理池...")
        
        new_proxies = []
        
        if self.use_free:
            new_proxies.extend(self.fetch_free_proxies())
        
        if self.use_paid:
            new_proxies.extend(self.fetch_paid_proxies())
        
        # 验证代理
        valid_proxies = []
        for proxy in new_proxies:
            if self.validate_proxy(proxy):
                valid_proxies.append(proxy)
        
        with self.lock:
            self.proxies = valid_proxies
            logger.info(f"代理池已刷新，可用代理: {len(self.proxies)}")
        
    def fetch_free_proxies(self) -> List[str]:
        """获取免费代理"""
        proxies = []
        
        # 方法1: 从免费API获取
        for api_url in self.free_proxy_apis:
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    # 解析代理列表
                    proxy_list = response.text.strip().split('\n')
                    for proxy in proxy_list:
                        if ':' in proxy:
                            proxies.append(f'http://{proxy.strip()}')
                    logger.info(f"从 {api_url} 获取到 {len(proxy_list)} 个代理")
            except Exception as e:
                logger.warning(f"获取免费代理失败 {api_url}: {e}")
        
        return proxies
    
    def fetch_paid_proxies(self) -> List[str]:
        """获取付费代理"""
        proxies = []
        
        try:
            response = requests.get(
                self.paid_proxy_config['api_url'],
                params={'key': self.paid_proxy_config['api_key'], 'num': 10},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                for proxy_info in data.get('proxies', []):
                    proxy = f"http://{proxy_info['ip']}:{proxy_info['port']}"
                    proxies.append(proxy)
                logger.info(f"获取到 {len(proxies)} 个付费代理")
        
        except Exception as e:
            logger.error(f"获取付费代理失败: {e}")
        
        return proxies
    
    def validate_proxy(self, proxy: str, timeout: int = 5) -> bool:
        """
        验证代理是否可用
        
        Args:
            proxy: 代理地址
            timeout: 超时时间
            
        Returns:
            是否可用
        """
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': proxy, 'https': proxy},
                timeout=timeout
            )
            return response.status_code == 200
        except:
            return False
    
    def get_proxy(self, force_validate: bool = False) -> Optional[str]:
        """
        获取可用代理
        
        Args:
            force_validate: 是否强制验证
            
        Returns:
            代理地址，如果没有可用代理返回None
        """
        with self.lock:
            if not self.proxies:
                logger.warning("代理池为空，尝试刷新...")
                self.refresh_proxies()
                
                if not self.proxies:
                    logger.error("无可用代理")
                    return None
            
            # 按成功率排序
            sorted_proxies = sorted(
                [p for p in self.proxies if p not in self.blacklist],
                key=lambda p: self.success_count.get(p, 0) / max(self.fail_count.get(p, 0) + 1, 1),
                reverse=True
            )
            
            if not sorted_proxies:
                logger.warning("所有代理都在黑名单中，清空黑名单")
                self.blacklist.clear()
                sorted_proxies = self.proxies
            
            # 获取最佳代理
            for proxy in sorted_proxies:
                # 如果最近验证过，直接返回
                last_validate = self.last_validate_time.get(proxy, datetime.min)
                if not force_validate and datetime.now() - last_validate < timedelta(minutes=5):
                    return proxy
                
                # 重新验证
                if self.validate_proxy(proxy):
                    self.last_validate_time[proxy] = datetime.now()
                    return proxy
                else:
                    self.mark_fail(proxy)
            
            # 没有可用代理
            return None
    
    def mark_success(self, proxy: str):
        """标记代理成功"""
        with self.lock:
            self.success_count[proxy] = self.success_count.get(proxy, 0) + 1
            
            # 从黑名单移除
            if proxy in self.blacklist:
                self.blacklist.remove(proxy)
    
    def mark_fail(self, proxy: str):
        """标记代理失败"""
        with self.lock:
            self.fail_count[proxy] = self.fail_count.get(proxy, 0) + 1
            
            # 失败次数过多，加入黑名单
            if self.fail_count[proxy] >= 3:
                self.blacklist.add(proxy)
                logger.warning(f"代理 {proxy} 已加入黑名单（失败{self.fail_count[proxy]}次）")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            total_proxies = len(self.proxies)
            blacklisted = len(self.blacklist)
            available = total_proxies - blacklisted
            
            total_requests = sum(self.success_count.values()) + sum(self.fail_count.values())
            success_requests = sum(self.success_count.values())
            success_rate = success_requests / max(total_requests, 1)
            
            return {
                'total_proxies': total_proxies,
                'available_proxies': available,
                'blacklisted_proxies': blacklisted,
                'total_requests': total_requests,
                'success_requests': success_requests,
                'success_rate': success_rate,
            }


class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait(self):
        """等待随机时间"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            
            # 计算需要等待的时间
            required_delay = random.uniform(self.min_delay, self.max_delay)
            
            if elapsed < required_delay:
                sleep_time = required_delay - elapsed
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()


class UARotator:
    """User-Agent轮换器"""
    
    def __init__(self):
        self.user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Chrome on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            # Safari on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
    
    def get_random_ua(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)


def get_browser_headers(ua_rotator: UARotator = None) -> Dict[str, str]:
    """
    生成浏览器请求头
    
    Args:
        ua_rotator: UA轮换器
        
    Returns:
        请求头字典
    """
    if ua_rotator is None:
        ua_rotator = UARotator()
    
    return {
        'User-Agent': ua_rotator.get_random_ua(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
    }


# 全局单例
_global_proxy_pool = None
_global_rate_limiter = None
_global_ua_rotator = None


def get_proxy_pool(use_free: bool = True, use_paid: bool = False) -> ProxyPool:
    """获取全局代理池实例"""
    global _global_proxy_pool
    if _global_proxy_pool is None:
        _global_proxy_pool = ProxyPool(use_free=use_free, use_paid=use_paid)
    return _global_proxy_pool


def get_rate_limiter(min_delay: float = 1.0, max_delay: float = 3.0) -> RateLimiter:
    """获取全局限流器实例"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(min_delay=min_delay, max_delay=max_delay)
    return _global_rate_limiter


def get_ua_rotator() -> UARotator:
    """获取全局UA轮换器实例"""
    global _global_ua_rotator
    if _global_ua_rotator is None:
        _global_ua_rotator = UARotator()
    return _global_ua_rotator

