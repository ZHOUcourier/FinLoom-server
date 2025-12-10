"""
反爬虫工具模块
提供User-Agent轮换、代理IP、重试机制、Cookie管理、动态延迟等功能
"""

import random
import time
from functools import wraps
from typing import Callable, Dict, List, Optional
from datetime import datetime
import http.cookiejar

from common.logging_system import setup_logger

logger = setup_logger("anti_spider_utils")


# User-Agent池
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


def get_random_user_agent() -> str:
    """获取随机User-Agent"""
    return random.choice(USER_AGENTS)


def random_delay(min_delay: float = 0.5, max_delay: float = 2.0):
    """随机延迟，避免请求过于规律

    Args:
        min_delay: 最小延迟时间（秒）
        max_delay: 最大延迟时间（秒）
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,),
):
    """重试装饰器，使用指数退避策略

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        max_delay: 最大延迟时间（秒）
        exceptions: 需要捕获的异常类型
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(
                            f"重试 {func.__name__}，第 {attempt}/{max_retries} 次"
                        )

                    result = func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(f"{func.__name__} 在第 {attempt} 次重试后成功")

                    return result

                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # 添加随机性，避免多个请求同时重试
                        actual_delay = delay * (0.5 + random.random())
                        logger.warning(
                            f"{func.__name__} 失败: {str(e)}，"
                            f"{actual_delay:.2f}秒后重试（{attempt + 1}/{max_retries}）"
                        )
                        time.sleep(actual_delay)

                        # 指数退避
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"{func.__name__} 在 {max_retries} 次重试后仍然失败: {str(e)}"
                        )

            raise last_exception

        return wrapper

    return decorator


class AntiSpiderSession:
    """增强的反爬虫会话管理器"""

    def __init__(
        self,
        min_delay: float = 0.5,
        max_delay: float = 2.0,
        rotate_user_agent: bool = True,
        use_dynamic_delay: bool = True,
    ):
        """初始化反爬虫会话

        Args:
            min_delay: 最小请求间隔（秒）
            max_delay: 最大请求间隔（秒）
            rotate_user_agent: 是否轮换User-Agent
            use_dynamic_delay: 是否使用动态延迟（根据时间段自适应）
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.rotate_user_agent = rotate_user_agent
        self.use_dynamic_delay = use_dynamic_delay
        self.last_request_time = 0
        self.request_count = 0
        self.current_user_agent = get_random_user_agent()
        self.cookies: Dict[str, str] = {}
        self.referer_url = None
        
        # 失败计数，用于自适应延迟
        self.failure_count = 0
        self.success_count = 0

    def get_headers(self, url: Optional[str] = None) -> Dict[str, str]:
        """获取增强的请求头
        
        Args:
            url: 请求的URL，用于设置Referer
            
        Returns:
            增强的请求头
        """
        if self.rotate_user_agent and self.request_count % 5 == 0:
            # 每5次请求更换一次User-Agent
            self.current_user_agent = get_random_user_agent()

        headers = {
            "User-Agent": self.current_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "DNT": "1",  # Do Not Track
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }
        
        # 添加 Referer（模拟真实浏览器行为）
        if self.referer_url:
            headers["Referer"] = self.referer_url
        elif url:
            # 使用同域名的首页作为 Referer
            if "eastmoney.com" in str(url):
                headers["Referer"] = "http://www.eastmoney.com/"
            elif "xueqiu.com" in str(url):
                headers["Referer"] = "https://xueqiu.com/"
        
        # 添加 Cookie（如果有）
        if self.cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            headers["Cookie"] = cookie_str

        return headers
    
    def set_cookie(self, key: str, value: str):
        """设置Cookie"""
        self.cookies[key] = value
        logger.debug(f"设置Cookie: {key}={value}")
    
    def set_referer(self, url: str):
        """设置Referer"""
        self.referer_url = url
        logger.debug(f"设置Referer: {url}")
    
    def get_dynamic_delay(self) -> float:
        """根据当前时间和请求情况动态计算延迟
        
        Returns:
            动态延迟时间（秒）
        """
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        day_of_week = now.weekday()
        
        # 基础延迟
        base_delay = self.min_delay
        
        # 1. 根据交易时间调整（交易时间加大延迟）
        is_trading_time = False
        if day_of_week < 5:  # 周一到周五
            # 上午: 9:30-11:30
            if (hour == 9 and minute >= 30) or (hour == 10) or (hour == 11 and minute <= 30):
                is_trading_time = True
            # 下午: 13:00-15:00
            elif (hour == 13) or (hour == 14) or (hour == 15 and minute == 0):
                is_trading_time = True
        
        if is_trading_time:
            # 交易时间延迟加倍
            base_delay = self.min_delay * 2
            logger.debug("⏰ 当前为交易时间，延迟加倍")
        
        # 2. 根据失败率自适应调整
        if self.request_count > 10:
            failure_rate = self.failure_count / self.request_count
            if failure_rate > 0.3:  # 失败率超过30%
                base_delay *= (1 + failure_rate)  # 按失败率增加延迟
                logger.debug(f"⚠️ 失败率 {failure_rate:.2%}，增加延迟")
        
        # 3. 添加随机抖动
        actual_delay = base_delay + random.uniform(0, self.max_delay - self.min_delay)
        
        return actual_delay

    def throttle(self, url: Optional[str] = None):
        """智能请求节流
        
        Args:
            url: 请求的URL
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 计算需要等待的时间
        if self.use_dynamic_delay:
            required_delay = self.get_dynamic_delay()
        else:
            required_delay = self.min_delay

        if time_since_last < required_delay:
            sleep_time = required_delay - time_since_last
            logger.debug(f"⏸️ 请求节流，等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1
        
        # 更新 Referer
        if url:
            self.referer_url = url
    
    def mark_success(self):
        """标记请求成功"""
        self.success_count += 1
        # 成功后逐渐降低失败计数
        if self.failure_count > 0:
            self.failure_count = max(0, self.failure_count - 1)
    
    def mark_failure(self):
        """标记请求失败"""
        self.failure_count += 1
        logger.warning(f"请求失败，当前失败计数: {self.failure_count}")
    
    def get_stats(self) -> Dict[str, any]:
        """获取会话统计信息"""
        total = self.request_count
        if total == 0:
            return {
                "total_requests": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0
            }
        
        return {
            "total_requests": total,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / total if total > 0 else 0
        }


class ProxyPool:
    """代理IP池（可扩展）"""

    def __init__(self, proxies: Optional[List[str]] = None):
        """初始化代理池

        Args:
            proxies: 代理列表，格式如 ["http://ip:port", ...]
        """
        self.proxies = proxies or []
        self.current_index = 0
        self.failed_proxies = set()

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """获取下一个可用代理"""
        if not self.proxies:
            return None

        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]

        if not available_proxies:
            # 所有代理都失败了，重置失败列表
            logger.warning("所有代理都已失败，重置代理池")
            self.failed_proxies.clear()
            available_proxies = self.proxies

        proxy = available_proxies[self.current_index % len(available_proxies)]
        self.current_index += 1

        return {"http": proxy, "https": proxy}

    def mark_failed(self, proxy: str):
        """标记代理失败"""
        self.failed_proxies.add(proxy)
        logger.warning(f"代理 {proxy} 已标记为失败")

    def add_proxy(self, proxy: str):
        """添加新代理"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logger.info(f"添加新代理: {proxy}")

    def remove_proxy(self, proxy: str):
        """移除代理"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.info(f"移除代理: {proxy}")


def patch_akshare_headers():
    """为akshare打补丁，使其使用增强的反爬虫策略

    注意：这是一个实验性功能，可能随akshare版本变化而失效
    """
    try:
        import requests

        # 保存原始的get方法
        original_get = requests.Session.get
        original_post = requests.Session.post

        # 使用增强的会话管理器
        session = AntiSpiderSession(
            min_delay=1.0,  # 增加最小延迟到1秒
            max_delay=3.0,  # 最大延迟3秒
            use_dynamic_delay=True  # 启用动态延迟
        )

        def patched_get(self, url, **kwargs):
            """打补丁的get方法"""
            # 添加智能节流
            session.throttle(url)

            # 使用增强的请求头
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"].update(session.get_headers(url))

            try:
                result = original_get(self, url, **kwargs)
                session.mark_success()
                return result
            except Exception as e:
                session.mark_failure()
                raise

        def patched_post(self, url, **kwargs):
            """打补丁的post方法"""
            # 添加智能节流
            session.throttle(url)

            # 使用增强的请求头
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"].update(session.get_headers(url))

            try:
                result = original_post(self, url, **kwargs)
                session.mark_success()
                return result
            except Exception as e:
                session.mark_failure()
                raise

        # 应用补丁
        requests.Session.get = patched_get
        requests.Session.post = patched_post

        logger.info("✅ 已为akshare应用增强的反爬虫补丁（动态延迟、Referer、Cookie）")
        return True

    except Exception as e:
        logger.warning(f"无法为akshare打补丁: {e}")
        return False


# 全局代理池实例
_proxy_pool: Optional[ProxyPool] = None


def init_proxy_pool(proxies: List[str]):
    """初始化全局代理池

    Args:
        proxies: 代理列表
    """
    global _proxy_pool
    _proxy_pool = ProxyPool(proxies)
    logger.info(f"初始化代理池，共 {len(proxies)} 个代理")


def get_proxy_pool() -> Optional[ProxyPool]:
    """获取全局代理池"""
    return _proxy_pool
