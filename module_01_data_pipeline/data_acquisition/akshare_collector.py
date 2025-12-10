"""
Akshare数据收集器模块
负责从Akshare获取中国金融市场数据
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd

# 尝试导入可选依赖
try:
    import akshare as ak

    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from common.data_structures import MarketData
from common.exceptions import DataError
from common.logging_system import setup_logger

logger = setup_logger("akshare_collector")


class AkshareDataCollector:
    """Akshare数据收集器类

    支持获取中国A股、港股、美股等市场的数据
    包括实时行情、历史数据、财务数据、宏观数据等
    """

    def __init__(self, rate_limit: float = 0.1):
        """初始化数据收集器

        Args:
            rate_limit: 请求间隔（秒）
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        self.session: Optional[aiohttp.ClientSession] = None

        # 检查akshare是否可用
        if not HAS_AKSHARE:
            logger.warning(
                "Akshare is not installed. Some features will use mock data."
            )
            logger.info("To install akshare: pip install akshare")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    def _rate_limit_check(self):
        """检查并执行速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def fetch_stock_list(self, market: str = "A股") -> pd.DataFrame:
        """获取股票列表

        Args:
            market: 市场类型 ("A股", "港股", "美股")

        Returns:
            股票列表DataFrame
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning mock data")
                # 返回模拟数据
                return pd.DataFrame(
                    {
                        "code": ["000001", "000002", "000003"],
                        "name": ["平安银行", "万科A", "国农科技"],
                    }
                )

            self._rate_limit_check()

            if market == "A股":
                # 获取A股股票列表
                stock_list = ak.stock_info_a_code_name()
                logger.info(f"Fetched {len(stock_list)} A-share stocks")
                return stock_list
            elif market == "港股":
                # 获取港股股票列表
                stock_list = ak.stock_hk_spot()
                logger.info(f"Fetched {len(stock_list)} Hong Kong stocks")
                return stock_list
            elif market == "美股":
                # 获取美股股票列表
                stock_list = ak.stock_us_spot_em()
                logger.info(f"Fetched {len(stock_list)} US stocks")
                return stock_list
            else:
                raise ValueError(f"Unsupported market: {market}")

        except Exception as e:
            logger.error(f"Failed to fetch stock list for {market}: {e}")
            raise DataError(f"Stock list fetch failed: {e}")

    def fetch_stock_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "daily",
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """获取股票历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            period: 周期 ("daily", "weekly", "monthly")
            adjust: 复权类型 ("qfq", "hfq", "")

        Returns:
            历史数据DataFrame
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning empty DataFrame")
                return pd.DataFrame()

            self._rate_limit_check()

            # 转换日期格式
            start_dt = datetime.strptime(start_date, "%Y%m%d")
            end_dt = datetime.strptime(end_date, "%Y%m%d")

            # 获取历史数据
            if period == "daily":
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                )
            elif period == "weekly":
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="weekly",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                )
            elif period == "monthly":
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="monthly",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                )
            else:
                raise ValueError(f"Unsupported period: {period}")

            if df.empty:
                logger.warning(
                    f"No data found for {symbol} from {start_date} to {end_date}"
                )
                return df

            # 标准化列名
            df = self._standardize_columns(df)

            # 添加股票代码
            df["symbol"] = symbol

            logger.info(f"Fetched {len(df)} records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch history for {symbol}: {e}")
            # 返回空DataFrame而不是抛出异常
            return pd.DataFrame()

    def fetch_realtime_data(
        self, symbols: List[str], max_retries: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """获取实时数据（带反爬虫策略和重试机制）

        Args:
            symbols: 股票代码列表
            max_retries: 最大重试次数

        Returns:
            实时数据字典
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning mock data")
                # 返回模拟数据
                result = {}
                for symbol in symbols:
                    result[symbol] = {
                        "symbol": symbol,
                        "name": f"股票{symbol}",
                        "price": 10.0,
                        "change": 0.05,
                        "change_amount": 0.5,
                        "volume": 100000,
                        "amount": 1000000.0,
                        "high": 10.5,
                        "low": 9.5,
                        "open": 10.0,
                        "close": 9.95,
                        "timestamp": datetime.now(),
                    }
                return result

            # 应用反爬虫补丁
            try:
                from common.anti_spider_utils import patch_akshare_headers

                patch_akshare_headers()
            except Exception as e:
                logger.debug(f"无法应用反爬虫补丁: {e}")

            # 带重试机制的数据获取
            last_exception = None
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        # 指数退避延迟
                        import random

                        delay = (2**attempt) + random.uniform(0, 1)
                        logger.info(f"等待 {delay:.2f} 秒后重试获取实时数据...")
                        time.sleep(delay)

                    self._rate_limit_check()

                    # 获取实时行情
                    realtime_data = ak.stock_zh_a_spot_em()

                    if realtime_data.empty:
                        logger.warning("获取到的实时数据为空")
                        continue

                    # 筛选指定股票
                    if symbols:
                        realtime_data = realtime_data[
                            realtime_data["代码"].isin(symbols)
                        ]

                    # 转换为字典格式
                    result = {}
                    for _, row in realtime_data.iterrows():
                        symbol = row["代码"]
                        result[symbol] = {
                            "symbol": symbol,
                            "name": row.get("名称", ""),
                            "price": float(row.get("最新价", 0.0)),
                            "change": float(row.get("涨跌幅", 0.0)),
                            "change_amount": float(row.get("涨跌额", 0.0)),
                            "volume": int(row.get("成交量", 0)),
                            "amount": float(row.get("成交额", 0.0)),
                            "high": float(row.get("最高", 0.0)),
                            "low": float(row.get("最低", 0.0)),
                            "open": float(row.get("今开", 0.0)),
                            "close": float(row.get("昨收", 0.0)),
                            "timestamp": datetime.now(),
                        }

                    logger.info(f"Fetched realtime data for {len(result)} stocks")
                    return result

                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"获取实时数据第 {attempt + 1}/{max_retries} 次失败: {e}"
                    )
                    if attempt == max_retries - 1:
                        # 最后一次尝试失败，抛出异常
                        raise DataError(
                            f"Realtime data fetch failed after {max_retries} retries: {e}"
                        )

            # 不应该到达这里，但为了安全
            if last_exception:
                raise DataError(f"Realtime data fetch failed: {last_exception}")

            return {}

        except DataError:
            # 直接抛出DataError
            raise
        except Exception as e:
            logger.error(f"Failed to fetch realtime data: {e}")
            raise DataError(f"Realtime data fetch failed: {e}")

    def fetch_financial_data(
        self, symbol: str, report_type: str = "资产负债表"
    ) -> pd.DataFrame:
        """获取财务数据

        Args:
            symbol: 股票代码
            report_type: 报表类型 ("资产负债表", "利润表", "现金流量表")

        Returns:
            财务数据DataFrame
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning empty DataFrame")
                return pd.DataFrame()

            self._rate_limit_check()

            if report_type == "资产负债表":
                df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
            elif report_type == "利润表":
                df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
            elif report_type == "现金流量表":
                df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")

            logger.info(f"Fetched {report_type} for {symbol}: {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch {report_type} for {symbol}: {e}")
            # 返回空DataFrame而不是抛出异常
            return pd.DataFrame()

    def fetch_industry_data(self, industry: str = "全部") -> pd.DataFrame:
        """获取行业数据

        Args:
            industry: 行业名称

        Returns:
            行业数据DataFrame
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning empty DataFrame")
                return pd.DataFrame()

            self._rate_limit_check()

            # 获取行业板块数据
            df = ak.stock_board_industry_cons_em()

            if industry != "全部":
                df = df[df["板块名称"].str.contains(industry, na=False)]

            logger.info(f"Fetched industry data for {industry}: {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch industry data for {industry}: {e}")
            return pd.DataFrame()

    def fetch_macro_data(self, indicator: str = "GDP") -> pd.DataFrame:
        """获取宏观经济数据

        Args:
            indicator: 指标名称 ("GDP", "CPI", "PPI", "PMI")

        Returns:
            宏观经济数据DataFrame
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning empty DataFrame")
                return pd.DataFrame()

            self._rate_limit_check()

            if indicator == "GDP":
                df = ak.macro_china_gdp()
            elif indicator == "CPI":
                df = ak.macro_china_cpi()
            elif indicator == "PPI":
                df = ak.macro_china_ppi()
            elif indicator == "PMI":
                df = ak.macro_china_pmi()
            else:
                raise ValueError(f"Unsupported macro indicator: {indicator}")

            logger.info(f"Fetched {indicator} data: {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch {indicator} data: {e}")
            return pd.DataFrame()

    def fetch_news_data(
        self, symbol: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取新闻数据

        Args:
            symbol: 股票代码（可选）
            limit: 获取数量限制

        Returns:
            新闻数据列表
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning empty list")
                return []

            self._rate_limit_check()

            # 获取财经新闻
            df = ak.stock_news_em(symbol=symbol)

            # 限制数量
            if len(df) > limit:
                df = df.head(limit)

            # 转换为字典列表
            news_list = []
            for _, row in df.iterrows():
                news_list.append(
                    {
                        "title": row.get("新闻标题", ""),
                        "content": row.get("新闻内容", ""),
                        "publish_time": row.get("发布时间", ""),
                        "source": row.get("新闻来源", ""),
                        "url": row.get("新闻链接", ""),
                        "symbol": symbol,
                    }
                )

            logger.info(f"Fetched {len(news_list)} news items")
            return news_list

        except Exception as e:
            logger.error(f"Failed to fetch news data: {e}")
            return []

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名

        Args:
            df: 原始DataFrame

        Returns:
            标准化后的DataFrame
        """
        # 列名映射
        column_mapping = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "pct_change",
            "涨跌额": "change",
            "换手率": "turnover",
        }

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保日期列是datetime类型
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        # 确保数值列是float类型
        numeric_columns = ["open", "high", "low", "close", "volume", "amount"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def convert_to_market_data(self, df: pd.DataFrame, symbol: str) -> List[MarketData]:
        """将DataFrame转换为MarketData对象列表

        Args:
            df: 数据DataFrame
            symbol: 股票代码

        Returns:
            MarketData对象列表
        """
        market_data_list = []

        for _, row in df.iterrows():
            try:
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=row.get("date", datetime.now()),
                    open=float(row.get("open", 0.0)),
                    high=float(row.get("high", 0.0)),
                    low=float(row.get("low", 0.0)),
                    close=float(row.get("close", 0.0)),
                    volume=int(row.get("volume", 0)),
                    vwap=float(row.get("amount", 0.0))
                    / max(int(row.get("volume", 1)), 1)
                    if row.get("volume", 0) > 0
                    else None,
                )
                market_data_list.append(market_data)
            except Exception as e:
                logger.warning(f"Failed to convert row to MarketData: {e}")
                continue

    def get_stock_basic_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            股票基本信息字典
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning mock data")
                return {
                    "symbol": symbol,
                    "name": f"股票{symbol}",
                    "industry": "未知行业",
                    "area": "未知地区",
                    "market": "A股",
                    "list_date": "2020-01-01",
                }

            self._rate_limit_check()

            # 获取股票基本信息
            stock_info = ak.stock_individual_info_em(symbol=symbol)

            if stock_info.empty:
                logger.warning(f"No basic info found for {symbol}")
                return {}

            # 转换为字典格式
            info_dict = {}
            for _, row in stock_info.iterrows():
                key = row.get("item", "")
                value = row.get("value", "")
                if key and value:
                    info_dict[key] = value

            result = {
                "symbol": symbol,
                "name": info_dict.get("股票简称", ""),
                "industry": info_dict.get("所属行业", ""),
                "area": info_dict.get("所属地域", ""),
                "market": info_dict.get("上市板块", ""),
                "list_date": info_dict.get("上市日期", ""),
                "total_shares": info_dict.get("总股本", ""),
                "float_shares": info_dict.get("流通股", ""),
                "pe_ratio": info_dict.get("市盈率", ""),
                "pb_ratio": info_dict.get("市净率", ""),
                "raw_info": info_dict,
            }

            logger.info(f"Fetched basic info for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch basic info for {symbol}: {e}")
            return {}

    def get_stock_holders(self, symbol: str) -> pd.DataFrame:
        """获取股东信息

        Args:
            symbol: 股票代码

        Returns:
            股东信息DataFrame
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning empty DataFrame")
                return pd.DataFrame()

            self._rate_limit_check()

            # 获取十大股东信息
            holders_df = ak.stock_top_10_holders_em(symbol=symbol)

            logger.info(f"Fetched holders info for {symbol}: {len(holders_df)} records")
            return holders_df

        except Exception as e:
            logger.error(f"Failed to fetch holders for {symbol}: {e}")
            return pd.DataFrame()

    def get_dividend_info(self, symbol: str) -> pd.DataFrame:
        """获取分红配股信息

        Args:
            symbol: 股票代码

        Returns:
            分红配股信息DataFrame
        """
        try:
            if not HAS_AKSHARE:
                logger.warning("Akshare not available, returning empty DataFrame")
                return pd.DataFrame()

            self._rate_limit_check()

            # 获取分红配股信息
            dividend_df = ak.stock_dividend_detail(symbol=symbol)

            logger.info(
                f"Fetched dividend info for {symbol}: {len(dividend_df)} records"
            )
            return dividend_df

        except Exception as e:
            logger.error(f"Failed to fetch dividend info for {symbol}: {e}")
            return pd.DataFrame()

    async def fetch_multiple_stocks(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        max_concurrent: int = 5,
    ) -> Dict[str, pd.DataFrame]:
        """并发获取多只股票数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            max_concurrent: 最大并发数

        Returns:
            股票数据字典
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_single_stock(symbol: str) -> tuple:
            async with semaphore:
                try:
                    df = self.fetch_stock_history(symbol, start_date, end_date)
                    return symbol, df
                except Exception as e:
                    logger.error(f"Failed to fetch data for {symbol}: {e}")
                    return symbol, pd.DataFrame()

        # 创建任务
        tasks = [fetch_single_stock(symbol) for symbol in symbols]

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        stock_data = {}
        for result in results:
            if isinstance(result, tuple):
                symbol, df = result
                stock_data[symbol] = df
            else:
                logger.error(f"Task failed with exception: {result}")

        logger.info(f"Fetched data for {len(stock_data)} stocks")
        return stock_data


# 便捷函数
def create_akshare_collector(rate_limit: float = 0.1) -> AkshareDataCollector:
    """创建Akshare数据收集器

    Args:
        rate_limit: 请求间隔

    Returns:
        数据收集器实例
    """
    return AkshareDataCollector(rate_limit=rate_limit)


async def fetch_stock_data_batch(
    symbols: List[str], start_date: str, end_date: str, rate_limit: float = 0.1
) -> Dict[str, pd.DataFrame]:
    """批量获取股票数据的便捷函数

    Args:
        symbols: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        rate_limit: 请求间隔

    Returns:
        股票数据字典
    """
    async with AkshareDataCollector(rate_limit=rate_limit) as collector:
        return await collector.fetch_multiple_stocks(symbols, start_date, end_date)
