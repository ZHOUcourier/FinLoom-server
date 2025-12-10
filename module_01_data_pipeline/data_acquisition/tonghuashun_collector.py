# -*- coding: utf-8 -*-
"""
同花顺数据采集器
支持研报、快讯、资金流向、龙虎榜等数据
使用代理IP池和反爬虫策略
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup

from common.logging_system import setup_logger
from module_01_data_pipeline.data_acquisition.proxy_pool_manager import get_proxy_pool_manager

logger = setup_logger("tonghuashun_collector")


class TongHuaShunCollector:
    """
    同花顺数据采集器
    
    功能：
    - 研报数据采集
    - 快讯数据采集
    - 资金流向数据
    - 龙虎榜数据
    - 机构评级
    - 概念题材
    """

    def __init__(
        self,
        use_proxy: bool = False,
        proxy_api_url: Optional[str] = None,
        rate_limit: tuple = (2, 5),
    ):
        """
        初始化同花顺采集器

        Args:
            use_proxy: 是否使用代理IP
            proxy_api_url: 代理API URL
            rate_limit: 请求间隔(最小, 最大)秒
        """
        self.base_url = "http://www.10jqka.com.cn"
        self.rate_limit = rate_limit
        self.use_proxy = use_proxy
        
        # 初始化代理池（如果启用）
        if use_proxy and proxy_api_url:
            self.proxy_manager = get_proxy_pool_manager(proxy_api_url=proxy_api_url)
        else:
            self.proxy_manager = None
        
        # User-Agent池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        logger.info(f"TongHuaShunCollector initialized (proxy={use_proxy})")

    def _get_headers(self) -> Dict[str, str]:
        """生成请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'http://www.10jqka.com.cn/',
        }

    async def _make_request(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> Optional[str]:
        """
        发起HTTP请求（带重试和代理）

        Args:
            url: 请求URL
            method: 请求方法
            **kwargs: 其他请求参数

        Returns:
            响应文本，失败返回None
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 随机延迟（反爬虫）
                await asyncio.sleep(random.uniform(*self.rate_limit))
                
                headers = self._get_headers()
                proxy = None
                
                # 获取代理（如果启用）
                if self.proxy_manager:
                    proxy = await self.proxy_manager.get_proxy()
                    if proxy:
                        proxy = f"http://{proxy}"
                
                # 发起请求
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        headers=headers,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=10),
                        **kwargs
                    ) as response:
                        if response.status == 200:
                            text = await response.text()
                            logger.debug(f"Successfully fetched {url}")
                            return text
                        elif response.status == 403:
                            logger.warning(f"Access forbidden (403) for {url}, retrying with new proxy...")
                            if proxy and self.proxy_manager:
                                await self.proxy_manager.mark_proxy_failed(proxy)
                        else:
                            logger.warning(f"Request failed with status {response.status} for {url}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries} for {url}")
                if proxy and self.proxy_manager:
                    await self.proxy_manager.mark_proxy_failed(proxy)
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}/{max_retries} for {url}: {e}")
                if proxy and self.proxy_manager:
                    await self.proxy_manager.mark_proxy_failed(proxy)
        
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None

    async def fetch_research_reports(self, limit: int = 20) -> pd.DataFrame:
        """
        获取研报数据

        Args:
            limit: 获取数量限制

        Returns:
            研报数据DataFrame
        """
        logger.info(f"Fetching research reports (limit={limit})...")
        
        url = f"{self.base_url}/yanbao/"
        html = await self._make_request(url)
        
        if not html:
            logger.warning("Failed to fetch research reports page")
            return pd.DataFrame()
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            reports = []
            # 解析研报列表（需要根据实际HTML结构调整）
            report_items = soup.select('.list-item, .report-item')[:limit]
            
            for item in report_items:
                try:
                    title_elem = item.select_one('.title, a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        # 提取其他信息
                        summary_elem = item.select_one('.summary, .content')
                        summary = summary_elem.get_text(strip=True) if summary_elem else ""
                        
                        date_elem = item.select_one('.date, .time')
                        date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")
                        
                        institution_elem = item.select_one('.institution, .source')
                        institution = institution_elem.get_text(strip=True) if institution_elem else "未知"
                        
                        reports.append({
                            'title': title,
                            'summary': summary[:200] if summary else title,
                            'link': link if link.startswith('http') else f"{self.base_url}{link}",
                            'institution': institution,
                            'date': date_str,
                            'type': 'research_report',
                            'source': '同花顺',
                        })
                except Exception as e:
                    logger.debug(f"Error parsing report item: {e}")
                    continue
            
            df = pd.DataFrame(reports)
            logger.info(f"Successfully fetched {len(df)} research reports")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing research reports: {e}")
            return pd.DataFrame()

    async def fetch_flash_news(self, limit: int = 50) -> pd.DataFrame:
        """
        获取快讯数据

        Args:
            limit: 获取数量限制

        Returns:
            快讯数据DataFrame
        """
        logger.info(f"Fetching flash news (limit={limit})...")
        
        url = f"{self.base_url}/news/cj/"
        html = await self._make_request(url)
        
        if not html:
            logger.warning("Failed to fetch flash news page")
            return pd.DataFrame()
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            news_list = []
            # 解析快讯列表（需要根据实际HTML结构调整）
            news_items = soup.select('.news-item, .flash-item')[:limit]
            
            for item in news_items:
                try:
                    time_elem = item.select_one('.time')
                    content_elem = item.select_one('.content, .text')
                    
                    if time_elem and content_elem:
                        time_str = time_elem.get_text(strip=True)
                        content = content_elem.get_text(strip=True)
                        
                        news_list.append({
                            'title': content[:50] + '...' if len(content) > 50 else content,
                            'content': content,
                            'time': time_str,
                            'date': datetime.now().strftime("%Y-%m-%d"),
                            'type': 'flash',
                            'source': '同花顺',
                        })
                except Exception as e:
                    logger.debug(f"Error parsing news item: {e}")
                    continue
            
            df = pd.DataFrame(news_list)
            logger.info(f"Successfully fetched {len(df)} flash news")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing flash news: {e}")
            return pd.DataFrame()

    async def fetch_capital_flow(self, symbol: str = None) -> pd.DataFrame:
        """
        获取资金流向数据

        Args:
            symbol: 股票代码（可选，不提供则获取市场整体）

        Returns:
            资金流向数据DataFrame
        """
        logger.info(f"Fetching capital flow data (symbol={symbol})...")
        
        if symbol:
            url = f"{self.base_url}/hq/{symbol}/flow/"
        else:
            url = f"{self.base_url}/zhuli/"
        
        html = await self._make_request(url)
        
        if not html:
            logger.warning("Failed to fetch capital flow page")
            return pd.DataFrame()
        
        try:
            # 解析资金流向数据
            # 这里需要根据同花顺实际页面结构解析
            # 通常包括主力净流入、超大单、大单、中单、小单等
            
            # 返回空DataFrame，实际实现需要根据页面结构调整
            logger.info("Capital flow parsing not fully implemented yet")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error parsing capital flow: {e}")
            return pd.DataFrame()

    async def fetch_dragon_tiger_list(self, date: str = None) -> pd.DataFrame:
        """
        获取龙虎榜数据

        Args:
            date: 日期（YYYY-MM-DD格式，不提供则获取最新）

        Returns:
            龙虎榜数据DataFrame
        """
        logger.info(f"Fetching dragon tiger list (date={date})...")
        
        url = f"{self.base_url}/data/longhu/"
        html = await self._make_request(url)
        
        if not html:
            logger.warning("Failed to fetch dragon tiger list page")
            return pd.DataFrame()
        
        try:
            # 解析龙虎榜数据
            # 实际实现需要根据页面结构调整
            logger.info("Dragon tiger list parsing not fully implemented yet")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error parsing dragon tiger list: {e}")
            return pd.DataFrame()


# 全局实例
_global_collector: Optional[TongHuaShunCollector] = None


def get_tonghuashun_collector(
    use_proxy: bool = False,
    proxy_api_url: Optional[str] = None,
) -> TongHuaShunCollector:
    """获取同花顺采集器实例（单例模式）"""
    global _global_collector
    if _global_collector is None:
        _global_collector = TongHuaShunCollector(
            use_proxy=use_proxy,
            proxy_api_url=proxy_api_url,
        )
    return _global_collector

