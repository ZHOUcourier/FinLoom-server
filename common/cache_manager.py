"""
服务器端内存缓存管理器
提供分层缓存机制：内存缓存 + 数据库缓存
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable
from threading import Lock
import json

from common.logging_system import setup_logger

logger = setup_logger("cache_manager")


class MemoryCache:
    """内存缓存管理器（线程安全）"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        logger.info("✅ 内存缓存管理器已初始化")

    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        with self._lock:
            if key not in self._cache:
                return None

            cache_entry = self._cache[key]
            
            # 检查是否过期
            if cache_entry["expire_time"] < time.time():
                logger.debug(f"缓存 {key} 已过期，删除")
                del self._cache[key]
                return None

            logger.debug(f"✅ 命中缓存: {key}")
            return cache_entry["data"]

    def set(self, key: str, data: Any, ttl: int = 120):
        """设置缓存数据
        
        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl: 过期时间（秒），默认120秒（2分钟）
        """
        with self._lock:
            self._cache[key] = {
                "data": data,
                "expire_time": time.time() + ttl,
                "created_at": time.time()
            }
            logger.debug(f"💾 设置缓存: {key}, TTL={ttl}秒")

    def delete(self, key: str):
        """删除缓存数据
        
        Args:
            key: 缓存键
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"🗑️ 删除缓存: {key}")

    def clear(self):
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"🗑️ 清空所有缓存，共 {count} 条")

    def cleanup_expired(self):
        """清理过期的缓存条目"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry["expire_time"] < current_time
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"🧹 清理了 {len(expired_keys)} 条过期缓存")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            current_time = time.time()
            total = len(self._cache)
            expired = sum(
                1 for entry in self._cache.values()
                if entry["expire_time"] < current_time
            )
            
            return {
                "total_entries": total,
                "active_entries": total - expired,
                "expired_entries": expired
            }


class MarketDataCache:
    """市场数据专用缓存管理器"""

    def __init__(self, memory_cache: MemoryCache):
        self.memory_cache = memory_cache
        self._request_times: Dict[str, float] = {}  # 记录请求时间，用于限流
        self._lock = Lock()
        logger.info("✅ 市场数据缓存管理器已初始化")

    def get_market_indices(self) -> Optional[Dict[str, Any]]:
        """获取市场指数缓存"""
        return self.memory_cache.get("market:indices")

    def set_market_indices(self, data: Dict[str, Any], ttl: int = 120):
        """设置市场指数缓存
        
        Args:
            data: 市场指数数据
            ttl: 缓存时间（秒），默认120秒
        """
        self.memory_cache.set("market:indices", data, ttl)

    def get_hot_stocks(self) -> Optional[Dict[str, Any]]:
        """获取热门股票缓存"""
        return self.memory_cache.get("market:hot_stocks")

    def set_hot_stocks(self, data: Dict[str, Any], ttl: int = 120):
        """设置热门股票缓存
        
        Args:
            data: 热门股票数据
            ttl: 缓存时间（秒），默认120秒
        """
        self.memory_cache.set("market:hot_stocks", data, ttl)

    def get_market_overview(self) -> Optional[Dict[str, Any]]:
        """获取市场概览缓存"""
        return self.memory_cache.get("market:overview")

    def set_market_overview(self, data: Dict[str, Any], ttl: int = 120):
        """设置市场概览缓存
        
        Args:
            data: 市场概览数据
            ttl: 缓存时间（秒），默认120秒
        """
        self.memory_cache.set("market:overview", data, ttl)

    def should_fetch_from_source(self, data_type: str, min_interval: int = 60) -> bool:
        """判断是否应该从数据源获取新数据（限流）
        
        Args:
            data_type: 数据类型（如 'indices', 'hot_stocks'）
            min_interval: 最小请求间隔（秒）
            
        Returns:
            True 表示可以请求，False 表示需要等待
        """
        with self._lock:
            key = f"fetch:{data_type}"
            last_fetch_time = self._request_times.get(key, 0)
            current_time = time.time()
            
            if current_time - last_fetch_time < min_interval:
                remaining = int(min_interval - (current_time - last_fetch_time))
                logger.debug(f"⏸️ {data_type} 请求限流，还需等待 {remaining} 秒")
                return False
            
            self._request_times[key] = current_time
            return True

    def get_stock_realtime(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取个股实时数据缓存"""
        return self.memory_cache.get(f"stock:realtime:{symbol}")

    def set_stock_realtime(self, symbol: str, data: Dict[str, Any], ttl: int = 60):
        """设置个股实时数据缓存
        
        Args:
            symbol: 股票代码
            data: 实时数据
            ttl: 缓存时间（秒），默认60秒
        """
        self.memory_cache.set(f"stock:realtime:{symbol}", data, ttl)


# 全局单例
_memory_cache: Optional[MemoryCache] = None
_market_data_cache: Optional[MarketDataCache] = None


def get_memory_cache() -> MemoryCache:
    """获取全局内存缓存实例"""
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache()
    return _memory_cache


def get_market_data_cache() -> MarketDataCache:
    """获取全局市场数据缓存实例"""
    global _market_data_cache
    if _market_data_cache is None:
        _market_data_cache = MarketDataCache(get_memory_cache())
    return _market_data_cache


def cleanup_cache_daemon():
    """缓存清理守护进程（定期清理过期缓存）"""
    import threading
    
    def cleanup_loop():
        while True:
            try:
                time.sleep(300)  # 每5分钟清理一次
                cache = get_memory_cache()
                cache.cleanup_expired()
            except Exception as e:
                logger.error(f"缓存清理失败: {e}")
    
    daemon_thread = threading.Thread(target=cleanup_loop, daemon=True)
    daemon_thread.start()
    logger.info("🧹 缓存清理守护进程已启动")


