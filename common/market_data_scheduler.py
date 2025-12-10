"""
市场数据定时更新调度器
在交易时间定期后台更新市场数据，避免用户请求时实时抓取
"""

import asyncio
import threading
import time
from datetime import datetime, time as dt_time
from typing import Optional, Callable
import traceback

from common.logging_system import setup_logger
from common.cache_manager import get_market_data_cache

logger = setup_logger("market_data_scheduler")


class MarketDataScheduler:
    """市场数据定时更新调度器"""

    def __init__(
        self,
        update_interval: int = 180,  # 默认3分钟更新一次
        enable_trading_hours_only: bool = True,  # 是否仅在交易时间更新
    ):
        """初始化调度器
        
        Args:
            update_interval: 更新间隔（秒）
            enable_trading_hours_only: 是否仅在交易时间更新
        """
        self.update_interval = update_interval
        self.enable_trading_hours_only = enable_trading_hours_only
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.market_cache = get_market_data_cache()
        
        # 数据更新回调函数
        self.indices_updater: Optional[Callable] = None
        self.hot_stocks_updater: Optional[Callable] = None
        
        logger.info(f"✅ 市场数据调度器已初始化（更新间隔: {update_interval}秒）")

    def set_indices_updater(self, updater: Callable):
        """设置指数数据更新函数
        
        Args:
            updater: 异步更新函数，返回指数数据
        """
        self.indices_updater = updater
        logger.info("✅ 已设置指数数据更新函数")

    def set_hot_stocks_updater(self, updater: Callable):
        """设置热门股票数据更新函数
        
        Args:
            updater: 异步更新函数，返回热门股票数据
        """
        self.hot_stocks_updater = updater
        logger.info("✅ 已设置热门股票数据更新函数")

    def is_trading_hours(self) -> bool:
        """判断当前是否为交易时间"""
        now = datetime.now()
        day_of_week = now.weekday()
        current_time = now.time()

        # 周末不是交易时间
        if day_of_week >= 5:
            return False

        # 定义交易时间段
        morning_start = dt_time(9, 15)  # 提前15分钟开始更新
        morning_end = dt_time(11, 35)   # 延后5分钟停止更新
        afternoon_start = dt_time(12, 55)  # 提前5分钟开始更新
        afternoon_end = dt_time(15, 5)     # 延后5分钟停止更新

        # 判断是否在交易时间段内
        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end

        return is_morning or is_afternoon

    async def update_market_data(self):
        """更新市场数据"""
        try:
            logger.info("🔄 开始更新市场数据...")
            
            # 检查是否应该更新（交易时间检查）
            if self.enable_trading_hours_only and not self.is_trading_hours():
                logger.info("⏸️ 当前非交易时间，跳过更新")
                return

            # 更新指数数据
            if self.indices_updater:
                try:
                    logger.info("📊 更新市场指数数据...")
                    indices_data = await self.indices_updater()
                    if indices_data:
                        # 缓存到内存（2分钟有效期）
                        self.market_cache.set_market_indices(indices_data, ttl=120)
                        logger.info(f"✅ 市场指数数据已更新并缓存")
                except Exception as e:
                    logger.error(f"❌ 更新指数数据失败: {e}")
                    traceback.print_exc()

            # 添加小延迟，避免请求过于密集
            await asyncio.sleep(2)

            # 更新热门股票数据
            if self.hot_stocks_updater:
                try:
                    logger.info("🔥 更新热门股票数据...")
                    hot_stocks_data = await self.hot_stocks_updater()
                    if hot_stocks_data:
                        # 缓存到内存（2分钟有效期）
                        self.market_cache.set_hot_stocks(hot_stocks_data, ttl=120)
                        logger.info(f"✅ 热门股票数据已更新并缓存")
                except Exception as e:
                    logger.error(f"❌ 更新热门股票数据失败: {e}")
                    traceback.print_exc()

            logger.info("✅ 市场数据更新完成")

        except Exception as e:
            logger.error(f"❌ 更新市场数据时发生错误: {e}")
            traceback.print_exc()

    def _run_scheduler_loop(self, preload=True):
        """调度器主循环（在独立线程中运行）
        
        Args:
            preload: 是否在启动时立即执行首次数据加载
        """
        logger.info("🚀 市场数据调度器已启动")
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 首次预加载数据（不等待定时器）
        if preload:
            try:
                logger.info("🔥 启动时预加载市场数据...")
                loop.run_until_complete(self.update_market_data())
                logger.info("✅ 预加载完成，等待下次定时更新")
            except Exception as e:
                logger.error(f"❌ 预加载失败: {e}")
                traceback.print_exc()

        while self.is_running:
            try:
                # 等待指定时间后再更新
                logger.info(f"⏰ 下次更新将在 {self.update_interval} 秒后")
                time.sleep(self.update_interval)
                
                # 运行更新任务
                loop.run_until_complete(self.update_market_data())

            except Exception as e:
                logger.error(f"❌ 调度器循环出错: {e}")
                traceback.print_exc()
                # 出错后等待一段时间再继续
                time.sleep(60)

        loop.close()
        logger.info("🛑 市场数据调度器已停止")

    def start(self, preload=True):
        """启动调度器
        
        Args:
            preload: 是否在启动时立即执行首次数据加载
        """
        if self.is_running:
            logger.warning("⚠️ 调度器已经在运行")
            return

        if not self.indices_updater and not self.hot_stocks_updater:
            logger.error("❌ 未设置任何数据更新函数，无法启动调度器")
            return

        self.is_running = True
        self.thread = threading.Thread(
            target=self._run_scheduler_loop, 
            args=(preload,),
            daemon=True
        )
        self.thread.start()
        logger.info("✅ 市场数据调度器已启动")

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("⚠️ 调度器未在运行")
            return

        logger.info("🛑 正在停止市场数据调度器...")
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=10)
        
        logger.info("✅ 市场数据调度器已停止")

    def get_status(self) -> dict:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "update_interval": self.update_interval,
            "trading_hours_only": self.enable_trading_hours_only,
            "is_trading_time": self.is_trading_hours(),
            "has_indices_updater": self.indices_updater is not None,
            "has_hot_stocks_updater": self.hot_stocks_updater is not None,
        }


# 全局调度器实例
_scheduler: Optional[MarketDataScheduler] = None


def get_scheduler() -> MarketDataScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = MarketDataScheduler(
            update_interval=180,  # 3分钟更新一次
            enable_trading_hours_only=True  # 仅在交易时间更新
        )
    return _scheduler


def start_market_data_scheduler(preload=True):
    """启动市场数据定时更新
    
    Args:
        preload: 是否在启动时立即执行首次数据加载（默认True）
    """
    scheduler = get_scheduler()
    scheduler.start(preload=preload)
    logger.info("✅ 市场数据定时更新已启动")


def stop_market_data_scheduler():
    """停止市场数据定时更新"""
    scheduler = get_scheduler()
    scheduler.stop()
    logger.info("🛑 市场数据定时更新已停止")

