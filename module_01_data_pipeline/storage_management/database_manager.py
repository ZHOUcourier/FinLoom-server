"""
数据库管理器模块
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from common.exceptions import DataError
from common.logging_system import setup_logger

logger = setup_logger("database_manager")


class DatabaseManager:
    """数据库管理器类"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "finloom.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建股票基本信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_info (
                    symbol TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sector TEXT,
                    industry TEXT,
                    market_cap REAL,
                    pe_ratio REAL,
                    pb_ratio REAL,
                    dividend_yield REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 创建股票价格数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    amount REAL,
                    pct_change REAL,
                    created_at TEXT NOT NULL,
                    UNIQUE(symbol, date)
                )
            """)

            # 创建技术指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    sma_5 REAL,
                    sma_10 REAL,
                    sma_20 REAL,
                    sma_50 REAL,
                    ema_12 REAL,
                    ema_26 REAL,
                    rsi REAL,
                    macd REAL,
                    macd_signal REAL,
                    macd_histogram REAL,
                    bb_upper REAL,
                    bb_middle REAL,
                    bb_lower REAL,
                    atr REAL,
                    stoch_k REAL,
                    stoch_d REAL,
                    created_at TEXT NOT NULL,
                    UNIQUE(symbol, date)
                )
            """)

            # 创建宏观数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS macro_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    indicator_type TEXT NOT NULL,
                    date TEXT NOT NULL,
                    value REAL NOT NULL,
                    report_name TEXT,
                    forecast_value REAL,
                    previous_value REAL,
                    created_at TEXT NOT NULL,
                    UNIQUE(indicator_type, date)
                )
            """)

            # 创建板块数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sector_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sector_name TEXT NOT NULL,
                    company_count INTEGER,
                    avg_price REAL,
                    change_amount REAL,
                    change_pct REAL,
                    total_volume INTEGER,
                    total_amount REAL,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(sector_name, date)
                )
            """)

            # 创建新闻数据表 (新闻联播)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    sentiment TEXT,
                    source TEXT DEFAULT 'CCTV',
                    created_at TEXT NOT NULL
                )
            """)

            # 创建个股新闻数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    keyword TEXT,
                    title TEXT NOT NULL,
                    content TEXT,
                    publish_time TEXT NOT NULL,
                    source TEXT NOT NULL,
                    news_url TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # 创建每日A股市场概况表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_market_overview (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    listed_stocks INTEGER,
                    main_board_a INTEGER,
                    main_board_b INTEGER,
                    star_market INTEGER,
                    stock_buyback INTEGER,
                    total_market_value REAL,
                    circulating_market_value REAL,
                    turnover_amount REAL,
                    turnover_volume REAL,
                    avg_pe_ratio REAL,
                    turnover_rate REAL,
                    circulating_turnover_rate REAL,
                    created_at TEXT NOT NULL
                )
            """)

            # 创建个股详细信息表（完整版）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_detail_info (
                    symbol TEXT PRIMARY KEY,
                    stock_code TEXT,
                    name TEXT NOT NULL,
                    latest_price REAL,
                    total_shares REAL,
                    circulating_shares REAL,
                    total_market_value REAL,
                    circulating_market_value REAL,
                    industry TEXT,
                    listing_date TEXT,
                    
                    -- 公司基本信息
                    org_name_cn TEXT,
                    org_short_name_cn TEXT,
                    org_name_en TEXT,
                    org_short_name_en TEXT,
                    main_operation_business TEXT,
                    operating_scope TEXT,
                    org_cn_introduction TEXT,
                    
                    -- 管理层信息
                    legal_representative TEXT,
                    general_manager TEXT,
                    secretary TEXT,
                    chairman TEXT,
                    executives_nums INTEGER,
                    
                    -- 财务信息
                    established_date TEXT,
                    reg_asset REAL,
                    staff_num INTEGER,
                    currency TEXT,
                    listed_date_timestamp TEXT,
                    
                    -- 联系信息
                    telephone TEXT,
                    postcode TEXT,
                    fax TEXT,
                    email TEXT,
                    org_website TEXT,
                    reg_address_cn TEXT,
                    reg_address_en TEXT,
                    office_address_cn TEXT,
                    office_address_en TEXT,
                    
                    -- 控制权信息
                    provincial_name TEXT,
                    actual_controller TEXT,
                    classi_name TEXT,
                    pre_name_cn TEXT,
                    
                    -- 发行信息
                    actual_issue_vol REAL,
                    issue_price REAL,
                    actual_rc_net_amt REAL,
                    pe_after_issuing REAL,
                    online_success_rate_of_issue REAL,
                    
                    -- 行业信息
                    affiliate_industry_code TEXT,
                    affiliate_industry_name TEXT,
                    
                    updated_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 创建回测结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    initial_capital REAL NOT NULL,
                    final_capital REAL NOT NULL,
                    total_return REAL NOT NULL,
                    annualized_return REAL NOT NULL,
                    volatility REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    win_rate REAL NOT NULL,
                    profit_factor REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    equity_curve TEXT,
                    trades TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # 创建索引
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date ON stock_prices(symbol, date)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_date ON technical_indicators(symbol, date)"
            )
            # 创建宏观数据索引
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_macro_data_indicator_date ON macro_data(indicator_type, date)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sector_data_sector_date ON sector_data(sector_name, date)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_news_data_date ON news_data(date)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_stock_news_symbol ON stock_news(symbol)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_stock_news_publish_time ON stock_news(publish_time)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_daily_market_overview_date ON daily_market_overview(date)"
            )

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DataError(f"Database initialization failed: {e}")

    def _safe_numeric(self, value, default=0):
        """
        安全转换数值，处理NaN、None等特殊值

        Args:
            value: 要转换的值
            default: 默认值

        Returns:
            转换后的数值
        """
        try:
            if (
                pd.isna(value)
                or value is None
                or value == ""
                or str(value).lower() == "nan"
            ):
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def save_stock_info(
        self,
        symbol: str,
        name: str,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        **kwargs,
    ):
        """保存股票基本信息

        Args:
            symbol: 股票代码
            name: 股票名称
            sector: 行业板块
            industry: 细分行业
            **kwargs: 其他信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT OR REPLACE INTO stock_info 
                (symbol, name, sector, industry, market_cap, pe_ratio, pb_ratio, 
                 dividend_yield, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    symbol,
                    name,
                    sector,
                    industry,
                    kwargs.get("market_cap"),
                    kwargs.get("pe_ratio"),
                    kwargs.get("pb_ratio"),
                    kwargs.get("dividend_yield"),
                    now,
                    now,
                ),
            )

            conn.commit()
            conn.close()
            logger.info(f"Saved stock info for {symbol}")

        except Exception as e:
            logger.error(f"Failed to save stock info for {symbol}: {e}")
            raise DataError(f"Stock info save failed: {e}")

    def save_stock_prices(self, symbol: str, df: pd.DataFrame) -> bool:
        """保存股票价格数据

        Args:
            symbol: 股票代码
            df: 价格数据DataFrame

        Returns:
            是否保存成功
        """
        try:
            if df.empty:
                logger.warning(f"Empty DataFrame provided for {symbol}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            # 批量插入数据
            records = []
            for _, row in df.iterrows():
                # 处理日期字段 - 简化版本避免类型错误
                if "date" in row:
                    date_value = row["date"]
                    # 简单检查None值
                    if date_value is None:
                        continue

                    # 直接使用pandas转换
                    try:
                        date_str = pd.to_datetime(date_value).strftime("%Y-%m-%d")
                    except Exception:
                        # 如果转换失败，直接使用字符串
                        date_str = (
                            str(date_value).split()[0]
                            if " " in str(date_value)
                            else str(date_value)
                        )
                else:
                    # 使用DataFrame索引作为日期
                    index_value = df.index[_]
                    try:
                        date_str = pd.to_datetime(index_value).strftime("%Y-%m-%d")
                    except Exception:
                        date_str = (
                            str(index_value).split()[0]
                            if " " in str(index_value)
                            else str(index_value)
                        )

                record = (
                    symbol,
                    date_str,
                    float(row.get("open", 0.0) or 0.0),
                    float(row.get("high", 0.0) or 0.0),
                    float(row.get("low", 0.0) or 0.0),
                    float(row.get("close", 0.0) or 0.0),
                    int(row.get("volume", 0) or 0),
                    float(row.get("amount", 0.0) or 0.0),
                    float(row.get("pct_change", 0.0) or 0.0),
                    now,
                )
                records.append(record)

            # 使用executemany提高性能
            cursor.executemany(
                """
                INSERT OR REPLACE INTO stock_prices 
                (symbol, date, open, high, low, close, volume, amount, 
                 pct_change, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                records,
            )

            conn.commit()
            conn.close()
            logger.info(f"Saved {len(records)} price records for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to save stock prices for {symbol}: {e}")
            return False

    def save_technical_indicators(self, symbol: str, df: pd.DataFrame) -> bool:
        """保存技术指标数据

        Args:
            symbol: 股票代码
            df: 技术指标数据DataFrame

        Returns:
            是否保存成功
        """
        try:
            if df.empty:
                logger.warning(f"Empty DataFrame provided for {symbol}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            # 批量插入数据
            records = []
            for _, row in df.iterrows():
                # 处理日期字段 - 简化版本避免类型错误
                if "date" in row:
                    date_value = row["date"]
                    # 简单检查None值
                    if date_value is None:
                        continue

                    # 直接使用pandas转换
                    try:
                        date_str = pd.to_datetime(date_value).strftime("%Y-%m-%d")
                    except Exception:
                        # 如果转换失败，直接使用字符串
                        date_str = (
                            str(date_value).split()[0]
                            if " " in str(date_value)
                            else str(date_value)
                        )
                else:
                    # 使用DataFrame索引作为日期
                    index_value = df.index[_]
                    try:
                        date_str = pd.to_datetime(index_value).strftime("%Y-%m-%d")
                    except Exception:
                        date_str = (
                            str(index_value).split()[0]
                            if " " in str(index_value)
                            else str(index_value)
                        )

                # 安全地处理可能为None的值
                def safe_float(value):
                    if value is None or pd.isna(value):
                        return None
                    return float(value)

                record = (
                    symbol,
                    date_str,
                    safe_float(row.get("sma_5")),
                    safe_float(row.get("sma_10")),
                    safe_float(row.get("sma_20")),
                    safe_float(row.get("sma_50")),
                    safe_float(row.get("ema_12")),
                    safe_float(row.get("ema_26")),
                    safe_float(row.get("rsi")),
                    safe_float(row.get("macd")),
                    safe_float(row.get("macd_signal")),
                    safe_float(row.get("macd_histogram")),
                    safe_float(row.get("bb_upper")),
                    safe_float(row.get("bb_middle")),
                    safe_float(row.get("bb_lower")),
                    safe_float(row.get("atr")),
                    safe_float(row.get("stoch_k")),
                    safe_float(row.get("stoch_d")),
                    now,
                )
                records.append(record)

            # 使用executemany提高性能
            cursor.executemany(
                """
                INSERT OR REPLACE INTO technical_indicators 
                (symbol, date, sma_5, sma_10, sma_20, sma_50, ema_12, ema_26,
                 rsi, macd, macd_signal, macd_histogram, bb_upper, bb_middle, 
                 bb_lower, atr, stoch_k, stoch_d, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                records,
            )

            conn.commit()
            conn.close()
            logger.info(
                f"Saved {len(records)} technical indicator records for {symbol}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save technical indicators for {symbol}: {e}")
            return False

    def save_trading_signal(self, signal_data: Dict[str, Any]):
        """保存交易信号

        Args:
            signal_data: 信号数据字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT OR REPLACE INTO trading_signals 
                (signal_id, symbol, strategy_name, signal_type, confidence, 
                 price, quantity, timestamp, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    signal_data["signal_id"],
                    signal_data["symbol"],
                    signal_data["strategy_name"],
                    signal_data["signal_type"],
                    signal_data["confidence"],
                    signal_data["price"],
                    signal_data["quantity"],
                    signal_data["timestamp"],
                    json.dumps(signal_data.get("metadata", {})),
                    now,
                ),
            )

            conn.commit()
            conn.close()
            logger.info(f"Saved trading signal: {signal_data['signal_id']}")

        except Exception as e:
            logger.error(f"Failed to save trading signal: {e}")
            raise DataError(f"Trading signal save failed: {e}")

    def save_backtest_result(self, result_data: Dict[str, Any]):
        """保存回测结果

        Args:
            result_data: 回测结果数据字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO backtest_results 
                (strategy_name, symbol, start_date, end_date, initial_capital, 
                 final_capital, total_return, annualized_return, volatility, 
                 sharpe_ratio, max_drawdown, win_rate, profit_factor, total_trades,
                 equity_curve, trades, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result_data["strategy_name"],
                    result_data["symbol"],
                    result_data["start_date"],
                    result_data["end_date"],
                    result_data["initial_capital"],
                    result_data["final_capital"],
                    result_data["total_return"],
                    result_data["annualized_return"],
                    result_data["volatility"],
                    result_data["sharpe_ratio"],
                    result_data["max_drawdown"],
                    result_data["win_rate"],
                    result_data["profit_factor"],
                    result_data["total_trades"],
                    json.dumps(result_data.get("equity_curve", [])),
                    json.dumps(result_data.get("trades", [])),
                    now,
                ),
            )

            conn.commit()
            conn.close()
            logger.info(f"Saved backtest result for {result_data['symbol']}")

        except Exception as e:
            logger.error(f"Failed to save backtest result: {e}")
            raise DataError(f"Backtest result save failed: {e}")

    def save_macro_data(self, indicator_type: str, df: pd.DataFrame) -> bool:
        """保存宏观经济数据

        Args:
            indicator_type: 指标类型 (GDP, CPI, PMI等)
            df: 宏观数据 DataFrame

        Returns:
            是否保存成功
        """
        try:
            if df.empty:
                logger.warning(f"Empty DataFrame provided for {indicator_type}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            # 批量插入数据
            records = []
            for _, row in df.iterrows():
                # 处理日期字段
                if "日期" in row:
                    date_value = row["日期"]
                elif "date" in row:
                    date_value = row["date"]
                else:
                    continue

                if date_value is None:
                    continue

                try:
                    date_str = pd.to_datetime(date_value).strftime("%Y-%m-%d")
                except Exception:
                    date_str = (
                        str(date_value).split()[0]
                        if " " in str(date_value)
                        else str(date_value)[:10]
                    )

                # 处理值字段
                value = None
                if "今值" in row:
                    value = row["今值"]
                elif "value" in row:
                    value = row["value"]
                elif "同比增长" in row:
                    value = row["同比增长"]

                if value is None or pd.isna(value):
                    continue

                # 处理其他字段
                report_name = row.get("商品", row.get("report_name", ""))
                forecast_value = row.get("预测值", row.get("forecast_value", None))
                previous_value = row.get("前值", row.get("previous_value", None))

                records.append(
                    (
                        indicator_type,
                        date_str,
                        float(value),
                        str(report_name) if report_name else None,
                        float(forecast_value)
                        if forecast_value and not pd.isna(forecast_value)
                        else None,
                        float(previous_value)
                        if previous_value and not pd.isna(previous_value)
                        else None,
                        now,
                    )
                )

            if records:
                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO macro_data 
                    (indicator_type, date, value, report_name, forecast_value, previous_value, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    records,
                )

                conn.commit()
                logger.info(f"Saved {len(records)} {indicator_type} records")
                result = True
            else:
                logger.warning(f"No valid records found for {indicator_type}")
                result = False

            conn.close()
            return result

        except Exception as e:
            logger.error(f"Failed to save macro data for {indicator_type}: {e}")
            return False

    def save_sector_data(self, df: pd.DataFrame, date: str = None) -> bool:
        """保存板块数据

        Args:
            df: 板块数据 DataFrame
            date: 数据日期

        Returns:
            是否保存成功
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for sector data")
                return False

            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            records = []
            for _, row in df.iterrows():
                sector_name = row.get("板块", row.get("sector_name", ""))
                if not sector_name:
                    continue

                records.append(
                    (
                        str(sector_name),
                        int(row.get("公司家数", row.get("company_count", 0)))
                        if not pd.isna(row.get("公司家数", row.get("company_count", 0)))
                        else 0,
                        float(row.get("平均价格", row.get("avg_price", 0)))
                        if not pd.isna(row.get("平均价格", row.get("avg_price", 0)))
                        else 0,
                        float(row.get("涨跌额", row.get("change_amount", 0)))
                        if not pd.isna(row.get("涨跌额", row.get("change_amount", 0)))
                        else 0,
                        float(row.get("涨跌幅", row.get("change_pct", 0)))
                        if not pd.isna(row.get("涨跌幅", row.get("change_pct", 0)))
                        else 0,
                        int(row.get("总成交量", row.get("total_volume", 0)))
                        if not pd.isna(row.get("总成交量", row.get("total_volume", 0)))
                        else 0,
                        float(row.get("总成交额", row.get("total_amount", 0)))
                        if not pd.isna(row.get("总成交额", row.get("total_amount", 0)))
                        else 0,
                        date,
                        now,
                    )
                )

            if records:
                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO sector_data 
                    (sector_name, company_count, avg_price, change_amount, change_pct, 
                     total_volume, total_amount, date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    records,
                )

                conn.commit()
                logger.info(f"Saved {len(records)} sector records for {date}")
                result = True
            else:
                logger.warning("No valid sector records found")
                result = False

            conn.close()
            return result

        except Exception as e:
            logger.error(f"Failed to save sector data: {e}")
            return False

    def save_stock_news(self, symbol: str, df: pd.DataFrame) -> bool:
        """
        保存个股新闻数据

        Args:
            symbol: 股票代码
            df: 新闻数据 DataFrame

        Returns:
            是否保存成功
        """
        try:
            if df.empty:
                logger.warning(f"Empty DataFrame provided for stock news {symbol}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            records = []
            for _, row in df.iterrows():
                keyword = row.get("关键词", symbol)
                title = row.get("新闻标题", "")
                content = row.get("新闻内容", "")
                publish_time = row.get("发布时间", "")
                source = row.get("文章来源", "")
                news_url = row.get("新闻链接", "")

                if not title:
                    continue

                records.append(
                    (
                        symbol,
                        str(keyword),
                        str(title),
                        str(content),
                        str(publish_time),
                        str(source),
                        str(news_url),
                        now,
                    )
                )

            if records:
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO stock_news 
                    (symbol, keyword, title, content, publish_time, source, news_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    records,
                )

                conn.commit()
                logger.info(f"Saved {len(records)} stock news records for {symbol}")
                result = True
            else:
                logger.warning(f"No valid stock news records found for {symbol}")
                result = False

            conn.close()
            return result

        except Exception as e:
            logger.error(f"Failed to save stock news for {symbol}: {e}")
            return False

    def save_daily_market_overview(self, df: pd.DataFrame, date: str = None) -> bool:
        """
        保存每日A股市场概况数据

        数据结构说明：
        - 原始数据是8行×6列，每行代表一个指标
        - '单日情况'列包含指标名称：挂牌数、市价总值、流通市值等
        - 其他列（'股票'、'主板A'、'主板B'、'科创板'、'股票回购'）包含对应板块的数值

        Args:
            df: 市场概况数据 DataFrame
            date: 数据日期，如果为None则使用当前日期

        Returns:
            是否保存成功
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for daily market overview")
                return False

            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            elif len(str(date)) == 8:  # Convert YYYYMMDD to YYYY-MM-DD
                date_str = str(date)
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # 解析实际数据结构：8行指标数据
            # 找到各个指标对应的行
            overview_data = {
                "date": date,
                "listed_stocks": 0,
                "main_board_a": 0,
                "main_board_b": 0,
                "star_market": 0,
                "stock_buyback": 0,
                "total_market_value": 0.0,
                "circulating_market_value": 0.0,
                "turnover_amount": 0.0,
                "turnover_volume": 0.0,
                "avg_pe_ratio": 0.0,
                "turnover_rate": 0.0,
                "circulating_turnover_rate": 0.0,
            }

            # 遍历每一行，提取对应数据
            for _, row in df.iterrows():
                metric_name = row.get("单日情况", "")

                if metric_name == "挂牌数":
                    overview_data["listed_stocks"] = int(
                        self._safe_numeric(row.get("股票", 0))
                    )
                    overview_data["main_board_a"] = int(
                        self._safe_numeric(row.get("主板A", 0))
                    )
                    overview_data["main_board_b"] = int(
                        self._safe_numeric(row.get("主板B", 0))
                    )
                    overview_data["star_market"] = int(
                        self._safe_numeric(row.get("科创板", 0))
                    )
                    overview_data["stock_buyback"] = int(
                        self._safe_numeric(row.get("股票回购", 0))
                    )

                elif metric_name == "市价总值":
                    overview_data["total_market_value"] = float(
                        self._safe_numeric(row.get("股票", 0))
                    )

                elif metric_name == "流通市值":
                    overview_data["circulating_market_value"] = float(
                        self._safe_numeric(row.get("股票", 0))
                    )

                elif metric_name == "成交金额":
                    overview_data["turnover_amount"] = float(
                        self._safe_numeric(row.get("股票", 0))
                    )

                elif metric_name == "成交量":
                    overview_data["turnover_volume"] = float(
                        self._safe_numeric(row.get("股票", 0))
                    )

                elif metric_name == "平均市盈率":
                    overview_data["avg_pe_ratio"] = float(
                        self._safe_numeric(row.get("股票", 0))
                    )

                elif metric_name == "换手率":
                    overview_data["turnover_rate"] = float(
                        self._safe_numeric(row.get("股票", 0))
                    )

                elif metric_name == "流通换手率":
                    overview_data["circulating_turnover_rate"] = float(
                        self._safe_numeric(row.get("股票", 0))
                    )

            # 保存到数据库
            cursor.execute(
                """
                INSERT OR REPLACE INTO daily_market_overview 
                (date, listed_stocks, main_board_a, main_board_b, star_market, stock_buyback,
                 total_market_value, circulating_market_value, turnover_amount, turnover_volume,
                 avg_pe_ratio, turnover_rate, circulating_turnover_rate, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    overview_data["date"],
                    overview_data["listed_stocks"],
                    overview_data["main_board_a"],
                    overview_data["main_board_b"],
                    overview_data["star_market"],
                    overview_data["stock_buyback"],
                    overview_data["total_market_value"],
                    overview_data["circulating_market_value"],
                    overview_data["turnover_amount"],
                    overview_data["turnover_volume"],
                    overview_data["avg_pe_ratio"],
                    overview_data["turnover_rate"],
                    overview_data["circulating_turnover_rate"],
                    now,
                ),
            )

            conn.commit()
            conn.close()
            logger.info(f"Saved daily market overview data for {date}")
            return True

        except Exception as e:
            logger.error(f"Failed to save daily market overview: {e}")
            return False

    def save_historical_daily_market_overview(self, df: pd.DataFrame) -> bool:
        """
        保存历史每日A股市场概况数据（批量处理）

        Args:
            df: 历史市场概况数据 DataFrame，包含date列

        Returns:
            是否保存成功
        """
        try:
            if df.empty:
                logger.warning(
                    "Empty DataFrame provided for historical daily market overview"
                )
                return False

            # 按日期分组处理
            unique_dates = df["date"].unique()
            saved_count = 0

            for date_value in unique_dates:
                # 提取该日期的数据
                daily_data = df[df["date"] == date_value].copy()
                if not daily_data.empty:
                    # 移除date列，因为save_daily_market_overview会单独处理日期
                    daily_data_no_date = daily_data.drop(columns=["date"])
                    success = self.save_daily_market_overview(
                        daily_data_no_date, date=str(date_value)
                    )
                    if success:
                        saved_count += 1

            logger.info(
                f"Saved {saved_count}/{len(unique_dates)} historical market overview days"
            )
            return saved_count > 0

        except Exception as e:
            logger.error(f"Failed to save historical daily market overview: {e}")
            return False

    def save_stock_detail_info(self, symbol: str, info_dict: Dict[str, Any]) -> bool:
        """
        保存个股详细信息（完整版）

        Args:
            symbol: 股票代码
            info_dict: 股票详细信息字典

        Returns:
            是否保存成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute(
                """
                INSERT OR REPLACE INTO stock_detail_info 
                (symbol, stock_code, name, latest_price, total_shares, circulating_shares, 
                 total_market_value, circulating_market_value, industry, listing_date,
                 org_name_cn, org_short_name_cn, org_name_en, org_short_name_en,
                 main_operation_business, operating_scope, org_cn_introduction,
                 legal_representative, general_manager, secretary, chairman, executives_nums,
                 established_date, reg_asset, staff_num, currency, listed_date_timestamp,
                 telephone, postcode, fax, email, org_website, 
                 reg_address_cn, reg_address_en, office_address_cn, office_address_en,
                 provincial_name, actual_controller, classi_name, pre_name_cn,
                 actual_issue_vol, issue_price, actual_rc_net_amt, pe_after_issuing, 
                 online_success_rate_of_issue, affiliate_industry_code, affiliate_industry_name,
                 updated_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        ?, ?, ?, ?, ?)
            """,
                (
                    symbol,
                    str(info_dict.get("stock_code", "")),
                    str(info_dict.get("name", "")),
                    self._safe_numeric(info_dict.get("latest_price", 0)),
                    self._safe_numeric(info_dict.get("total_shares", 0)),
                    self._safe_numeric(info_dict.get("circulating_shares", 0)),
                    self._safe_numeric(info_dict.get("total_market_value", 0)),
                    self._safe_numeric(info_dict.get("circulating_market_value", 0)),
                    str(info_dict.get("industry", "")),
                    str(info_dict.get("listing_date", "")),
                    # 公司基本信息
                    str(info_dict.get("org_name_cn", "")),
                    str(info_dict.get("org_short_name_cn", "")),
                    str(info_dict.get("org_name_en", "")),
                    str(info_dict.get("org_short_name_en", "")),
                    str(info_dict.get("main_operation_business", "")),
                    str(info_dict.get("operating_scope", "")),
                    str(info_dict.get("org_cn_introduction", "")),
                    # 管理层信息
                    str(info_dict.get("legal_representative", "")),
                    str(info_dict.get("general_manager", "")),
                    str(info_dict.get("secretary", "")),
                    str(info_dict.get("chairman", "")),
                    int(self._safe_numeric(info_dict.get("executives_nums", 0))),
                    # 财务信息
                    str(info_dict.get("established_date", "")),
                    self._safe_numeric(info_dict.get("reg_asset", 0)),
                    int(self._safe_numeric(info_dict.get("staff_num", 0))),
                    str(info_dict.get("currency", "")),
                    str(info_dict.get("listed_date_timestamp", "")),
                    # 联系信息
                    str(info_dict.get("telephone", "")),
                    str(info_dict.get("postcode", "")),
                    str(info_dict.get("fax", "")),
                    str(info_dict.get("email", "")),
                    str(info_dict.get("org_website", "")),
                    str(info_dict.get("reg_address_cn", "")),
                    str(info_dict.get("reg_address_en", "")),
                    str(info_dict.get("office_address_cn", "")),
                    str(info_dict.get("office_address_en", "")),
                    # 控制权信息
                    str(info_dict.get("provincial_name", "")),
                    str(info_dict.get("actual_controller", "")),
                    str(info_dict.get("classi_name", "")),
                    str(info_dict.get("pre_name_cn", "")),
                    # 发行信息
                    self._safe_numeric(info_dict.get("actual_issue_vol", 0)),
                    self._safe_numeric(info_dict.get("issue_price", 0)),
                    self._safe_numeric(info_dict.get("actual_rc_net_amt", 0)),
                    self._safe_numeric(info_dict.get("pe_after_issuing", 0)),
                    self._safe_numeric(
                        info_dict.get("online_success_rate_of_issue", 0)
                    ),
                    # 行业信息
                    str(info_dict.get("affiliate_industry_code", "")),
                    str(info_dict.get("affiliate_industry_name", "")),
                    now,
                    now,
                ),
            )

            conn.commit()
            conn.close()
            logger.info(f"Saved comprehensive detailed stock info for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to save stock detail info for {symbol}: {e}")
            return False

    def save_news_data(self, df: pd.DataFrame) -> bool:
        """
        保存新闻数据

        Args:
            df: 新闻数据 DataFrame

        Returns:
            是否保存成功
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for news data")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            records = []
            for _, row in df.iterrows():
                date_value = row.get("date", "")
                title = row.get("title", "")
                content = row.get("content", "")
                sentiment = row.get("sentiment", "neutral")

                if not title:
                    continue

                records.append(
                    (
                        str(date_value),
                        str(title),
                        str(content),
                        str(sentiment),
                        "CCTV",
                        now,
                    )
                )

            if records:
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO news_data 
                    (date, title, content, sentiment, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    records,
                )

                conn.commit()
                logger.info(f"Saved {len(records)} news records")
                result = True
            else:
                logger.warning("No valid news records found")
                result = False

            conn.close()
            return result

        except Exception as e:
            logger.error(f"Failed to save news data: {e}")
            return False

    def get_stock_list(self) -> pd.DataFrame:
        """获取所有股票列表

        Returns:
            股票列表DataFrame，包含symbol和name列
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 从stock_info表获取股票列表
            query = "SELECT DISTINCT symbol, name FROM stock_info ORDER BY symbol"
            df = pd.read_sql_query(query, conn)
            
            # 如果stock_info表为空，尝试从stock_prices表获取
            if df.empty:
                query = "SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol"
                df = pd.read_sql_query(query, conn)
                # 添加默认name列
                if not df.empty and 'name' not in df.columns:
                    df['name'] = df['symbol']
            
            conn.close()
            
            logger.info(f"Retrieved {len(df)} stocks from database")
            return df

        except Exception as e:
            logger.error(f"Failed to get stock list: {e}")
            return pd.DataFrame()

    def get_stock_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """获取股票价格数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            价格数据DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM stock_prices WHERE symbol = ?"
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace=True)

            logger.info(f"Retrieved {len(df)} price records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to get stock prices for {symbol}: {e}")
            return pd.DataFrame()

    def get_technical_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """获取技术指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            技术指标数据DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM technical_indicators WHERE symbol = ?"
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace=True)

            logger.info(f"Retrieved {len(df)} technical indicator records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to get technical indicators for {symbol}: {e}")
            return pd.DataFrame()

    def get_trading_signals(
        self,
        symbol: Optional[str] = None,
        strategy_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取交易信号

        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易信号列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM trading_signals WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if strategy_name:
                query += " AND strategy_name = ?"
                params.append(strategy_name)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # 获取列名
            columns = [description[0] for description in cursor.description]

            # 转换为字典列表
            signals = []
            for row in rows:
                signal = dict(zip(columns, row))
                if signal["metadata"]:
                    signal["metadata"] = json.loads(signal["metadata"])
                signals.append(signal)

            conn.close()
            logger.info(f"Retrieved {len(signals)} trading signals")
            return signals

        except Exception as e:
            logger.error(f"Failed to get trading signals: {e}")
            return []

    def get_macro_data(
        self,
        indicator_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """获取宏观经济数据

        Args:
            indicator_type: 指标类型
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            宏观数据 DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM macro_data WHERE 1=1"
            params = []

            if indicator_type:
                query += " AND indicator_type = ?"
                params.append(indicator_type)

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])

            logger.info(f"Retrieved {len(df)} macro data records")
            return df

        except Exception as e:
            logger.error(f"Failed to get macro data: {e}")
            return pd.DataFrame()

    def get_sector_data(
        self,
        sector_name: Optional[str] = None,
        date: Optional[str] = None,
    ) -> pd.DataFrame:
        """获取板块数据

        Args:
            sector_name: 板块名称
            date: 日期

        Returns:
            板块数据 DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM sector_data WHERE 1=1"
            params = []

            if sector_name:
                query += " AND sector_name = ?"
                params.append(sector_name)

            if date:
                query += " AND date = ?"
                params.append(date)

            query += " ORDER BY date DESC"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            logger.info(f"Retrieved {len(df)} sector data records")
            return df

        except Exception as e:
            logger.error(f"Failed to get sector data: {e}")
            return pd.DataFrame()

    def get_stock_news(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        获取个股新闻数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            个股新闻数据 DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM stock_news WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if start_date:
                query += " AND publish_time >= ?"
                params.append(start_date)

            if end_date:
                query += " AND publish_time <= ?"
                params.append(end_date)

            query += " ORDER BY publish_time DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            logger.info(f"Retrieved {len(df)} stock news records")
            return df

        except Exception as e:
            logger.error(f"Failed to get stock news data: {e}")
            return pd.DataFrame()

    def get_daily_market_overview(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取每日A股市场概况数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            市场概况数据 DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM daily_market_overview WHERE 1=1"
            params = []

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            logger.info(f"Retrieved {len(df)} daily market overview records")
            return df

        except Exception as e:
            logger.error(f"Failed to get daily market overview: {e}")
            return pd.DataFrame()

    def get_stock_detail_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取个股详细信息

        Args:
            symbol: 股票代码

        Returns:
            股票详细信息字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM stock_detail_info WHERE symbol = ?", (symbol,)
            )
            row = cursor.fetchone()

            if row:
                columns = [description[0] for description in cursor.description]
                result = dict(zip(columns, row))
            else:
                result = {}

            conn.close()
            return result

        except Exception as e:
            logger.error(f"Failed to get stock detail info for {symbol}: {e}")

    def get_news_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        获取新闻数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            新闻数据 DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM news_data WHERE 1=1"
            params = []

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            logger.info(f"Retrieved {len(df)} news records")
            return df

        except Exception as e:
            logger.error(f"Failed to get news data: {e}")
            return pd.DataFrame()

    def get_backtest_results(
        self, symbol: Optional[str] = None, strategy_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取回测结果

        Args:
            symbol: 股票代码
            strategy_name: 策略名称

        Returns:
            回测结果列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM backtest_results WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if strategy_name:
                query += " AND strategy_name = ?"
                params.append(strategy_name)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # 获取列名
            columns = [description[0] for description in cursor.description]

            # 转换为字典列表
            results = []
            for row in rows:
                result = dict(zip(columns, row))
                if result["equity_curve"]:
                    result["equity_curve"] = json.loads(result["equity_curve"])
                if result["trades"]:
                    result["trades"] = json.loads(result["trades"])
                results.append(result)

            conn.close()
            logger.info(f"Retrieved {len(results)} backtest results")
            return results

        except Exception as e:
            logger.error(f"Failed to get backtest results: {e}")
            return []

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            数据库统计信息字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            stats = {}

            # 获取各表的记录数
            tables = [
                "stock_info",
                "stock_prices",
                "technical_indicators",
                "trading_signals",
                "backtest_results",
            ]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[f"{table}_count"] = count

            # 获取数据库文件大小
            stats["database_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)

            # 获取最后更新时间
            cursor.execute("SELECT MAX(created_at) FROM stock_prices")
            last_update = cursor.fetchone()[0]
            stats["last_update"] = last_update

            # 获取独特股票数量
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM stock_prices")
            unique_symbols = cursor.fetchone()[0]
            stats["unique_symbols"] = unique_symbols

            # 获取日期范围
            cursor.execute("SELECT MIN(date), MAX(date) FROM stock_prices")
            date_range = cursor.fetchone()
            if date_range[0] and date_range[1]:
                stats["date_range"] = {"start": date_range[0], "end": date_range[1]}

            conn.close()
            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 365) -> bool:
        """清理旧数据

        Args:
            days_to_keep: 保留天数

        Returns:
            是否清理成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 计算截止日期
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime(
                "%Y-%m-%d"
            )

            # 清理股票价格数据
            cursor.execute("DELETE FROM stock_prices WHERE date < ?", (cutoff_date,))
            deleted_prices = cursor.rowcount

            # 清理技术指标数据
            cursor.execute(
                "DELETE FROM technical_indicators WHERE date < ?", (cutoff_date,)
            )
            deleted_indicators = cursor.rowcount

            # 清理交易信号
            cutoff_datetime = (
                datetime.now() - timedelta(days=days_to_keep)
            ).isoformat()
            cursor.execute(
                "DELETE FROM trading_signals WHERE timestamp < ?", (cutoff_datetime,)
            )
            deleted_signals = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(
                f"Cleaned up old data: {deleted_prices} prices, {deleted_indicators} indicators, {deleted_signals} signals"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False

    def get_symbols_list(self) -> List[str]:
        """获取数据库中所有股票代码

        Returns:
            股票代码列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol")
            symbols = [row[0] for row in cursor.fetchall()]

            conn.close()
            return symbols

        except Exception as e:
            logger.error(f"Failed to get symbols list: {e}")
            return []


# 便捷函数
def create_database_manager(db_path: str = "data/finloom.db") -> DatabaseManager:
    """创建数据库管理器的便捷函数

    Args:
        db_path: 数据库文件路径

    Returns:
        数据库管理器实例
    """
    return DatabaseManager(db_path)


# 全局数据库管理器实例
_global_db_manager = None


def get_database_manager(db_path: str = "data/finloom.db") -> DatabaseManager:
    """获取全局数据库管理器实例（单例模式）

    Args:
        db_path: 数据库文件路径

    Returns:
        数据库管理器实例
    """
    global _global_db_manager
    if _global_db_manager is None:
        _global_db_manager = DatabaseManager(db_path)
    return _global_db_manager
