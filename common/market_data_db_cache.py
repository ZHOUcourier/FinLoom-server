"""
市场数据数据库缓存层
提供当日市场数据的持久化存储，作为第二层缓存
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pathlib import Path

from common.logging_system import setup_logger

logger = setup_logger("market_data_db_cache")


class MarketDataDBCache:
    """市场数据数据库缓存管理器"""

    def __init__(self, db_path: str = "data/market_cache.db"):
        """初始化数据库缓存
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        
        # 确保数据目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库表
        self._init_database()
        
        logger.info(f"✅ 市场数据数据库缓存已初始化: {db_path}")

    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 市场指数缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_indices_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    indices_data TEXT NOT NULL,
                    source VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            ''')
            
            # 热门股票缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hot_stocks_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    stocks_data TEXT NOT NULL,
                    sentiment_data TEXT,
                    source VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_indices_date 
                ON market_indices_cache(date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stocks_date 
                ON hot_stocks_cache(date)
            ''')
            
            conn.commit()
            logger.info("✅ 数据库表结构已初始化")

    def save_market_indices(
        self, 
        indices: List[Dict[str, Any]], 
        source: str = "unknown",
        cache_date: Optional[date] = None
    ) -> bool:
        """保存市场指数数据到数据库
        
        Args:
            indices: 指数数据列表
            source: 数据来源
            cache_date: 缓存日期（默认今天）
            
        Returns:
            是否保存成功
        """
        try:
            if cache_date is None:
                cache_date = date.today()
            
            indices_json = json.dumps(indices, ensure_ascii=False)
            timestamp = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 使用 REPLACE 替换已存在的数据
                cursor.execute('''
                    REPLACE INTO market_indices_cache 
                    (date, timestamp, indices_data, source)
                    VALUES (?, ?, ?, ?)
                ''', (cache_date, timestamp, indices_json, source))
                
                conn.commit()
                
            logger.info(f"✅ 已保存市场指数数据到数据库: {cache_date}, 来源: {source}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存市场指数数据失败: {e}")
            return False

    def get_market_indices(
        self, 
        cache_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """从数据库获取市场指数数据
        
        Args:
            cache_date: 缓存日期（默认今天）
            
        Returns:
            市场指数数据，如果不存在则返回 None
        """
        try:
            if cache_date is None:
                cache_date = date.today()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, indices_data, source
                    FROM market_indices_cache
                    WHERE date = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (cache_date,))
                
                row = cursor.fetchone()
                
                if row:
                    timestamp_str, indices_json, source = row
                    indices = json.loads(indices_json)
                    
                    logger.info(f"✅ 从数据库读取市场指数数据: {cache_date}, 来源: {source}")
                    
                    return {
                        "data": {
                            "timestamp": timestamp_str,
                            "indices": indices,
                            "source": f"{source}_db_cache",
                        },
                        "message": "Market indices from database cache",
                        "from_db_cache": True,
                    }
                else:
                    logger.debug(f"数据库中没有 {cache_date} 的指数数据")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ 从数据库读取市场指数数据失败: {e}")
            return None

    def save_hot_stocks(
        self, 
        hot_stocks: List[Dict[str, Any]], 
        sentiment: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        cache_date: Optional[date] = None
    ) -> bool:
        """保存热门股票数据到数据库
        
        Args:
            hot_stocks: 热门股票数据列表
            sentiment: 市场情绪数据
            source: 数据来源
            cache_date: 缓存日期（默认今天）
            
        Returns:
            是否保存成功
        """
        try:
            if cache_date is None:
                cache_date = date.today()
            
            stocks_json = json.dumps(hot_stocks, ensure_ascii=False)
            sentiment_json = json.dumps(sentiment, ensure_ascii=False) if sentiment else None
            timestamp = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 使用 REPLACE 替换已存在的数据
                cursor.execute('''
                    REPLACE INTO hot_stocks_cache 
                    (date, timestamp, stocks_data, sentiment_data, source)
                    VALUES (?, ?, ?, ?, ?)
                ''', (cache_date, timestamp, stocks_json, sentiment_json, source))
                
                conn.commit()
                
            logger.info(f"✅ 已保存热门股票数据到数据库: {cache_date}, 来源: {source}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存热门股票数据失败: {e}")
            return False

    def get_hot_stocks(
        self, 
        cache_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """从数据库获取热门股票数据
        
        Args:
            cache_date: 缓存日期（默认今天）
            
        Returns:
            热门股票数据，如果不存在则返回 None
        """
        try:
            if cache_date is None:
                cache_date = date.today()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, stocks_data, sentiment_data, source
                    FROM hot_stocks_cache
                    WHERE date = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (cache_date,))
                
                row = cursor.fetchone()
                
                if row:
                    timestamp_str, stocks_json, sentiment_json, source = row
                    hot_stocks = json.loads(stocks_json)
                    sentiment = json.loads(sentiment_json) if sentiment_json else {}
                    
                    logger.info(f"✅ 从数据库读取热门股票数据: {cache_date}, 来源: {source}")
                    
                    return {
                        "data": {
                            "timestamp": timestamp_str,
                            "hot_stocks": hot_stocks,
                            "market_sentiment": sentiment,
                            "source": f"{source}_db_cache",
                        },
                        "message": "Hot stocks from database cache",
                        "from_db_cache": True,
                    }
                else:
                    logger.debug(f"数据库中没有 {cache_date} 的热门股票数据")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ 从数据库读取热门股票数据失败: {e}")
            return None

    def cleanup_old_data(self, days_to_keep: int = 7):
        """清理旧数据
        
        Args:
            days_to_keep: 保留最近几天的数据
        """
        try:
            cutoff_date = date.today()
            from datetime import timedelta
            cutoff_date = cutoff_date - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM market_indices_cache
                    WHERE date < ?
                ''', (cutoff_date,))
                
                indices_deleted = cursor.rowcount
                
                cursor.execute('''
                    DELETE FROM hot_stocks_cache
                    WHERE date < ?
                ''', (cutoff_date,))
                
                stocks_deleted = cursor.rowcount
                
                conn.commit()
                
            logger.info(f"🧹 清理旧数据: 删除 {indices_deleted} 条指数记录, {stocks_deleted} 条股票记录")
            
        except Exception as e:
            logger.error(f"❌ 清理旧数据失败: {e}")


# 全局数据库缓存实例
_db_cache: Optional[MarketDataDBCache] = None


def get_db_cache() -> MarketDataDBCache:
    """获取全局数据库缓存实例"""
    global _db_cache
    if _db_cache is None:
        _db_cache = MarketDataDBCache()
    return _db_cache


