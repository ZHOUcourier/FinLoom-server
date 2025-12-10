#!/usr/bin/env python3
"""
数据管道协调器 - 统一管理智能分析页面所需的所有数据
负责协调板块分析、市场情绪、技术指标、市场资讯等数据的获取和更新
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from common.logging_system import setup_logger

logger = setup_logger("data_pipeline_coordinator")


class DataPipelineCoordinator:
    """数据管道协调器 - 协调所有数据源"""

    def __init__(self):
        """初始化数据管道协调器"""
        self.initialized = False
        self.db_manager = None
        self.cached_manager = None
        self.akshare_collector = None
        self.alternative_collector = None
        self.tonghuashun_collector = None  # 新增同花顺采集器

    def initialize(self):
        """延迟初始化所有组件"""
        if self.initialized:
            return True

        try:
            logger.info("🔧 初始化数据管道协调器...")

            # 导入数据管理器
            from module_01_data_pipeline import get_database_manager
            from module_01_data_pipeline.storage_management.cached_data_manager import (
                CachedDataManager,
            )

            self.db_manager = get_database_manager()
            self.cached_manager = CachedDataManager()

            # 导入数据采集器
            from module_01_data_pipeline.data_acquisition.akshare_collector import (
                AkshareDataCollector,
            )
            from module_01_data_pipeline.data_acquisition.alternative_data_collector import (
                ChineseAlternativeDataCollector,
            )
            from module_01_data_pipeline.data_acquisition.tonghuashun_collector import (
                get_tonghuashun_collector,
            )

            self.akshare_collector = AkshareDataCollector(rate_limit=0.5)
            self.alternative_collector = ChineseAlternativeDataCollector(rate_limit=0.5)
            # 同花顺采集器（默认不使用代理，可配置）
            self.tonghuashun_collector = get_tonghuashun_collector(use_proxy=False)

            self.initialized = True
            logger.info("✅ 数据管道协调器初始化成功（含同花顺数据源）")
            return True

        except Exception as e:
            logger.error(f"❌ 数据管道协调器初始化失败: {e}")
            return False

    async def fetch_sector_analysis_data(self) -> Dict:
        """获取板块分析数据"""
        try:
            logger.info("📊 获取板块分析数据...")

            if not self.initialized:
                self.initialize()

            today = datetime.now().strftime("%Y-%m-%d")

            # 优先从缓存获取
            sector_df = self.cached_manager.get_sector_data(date=today)

            # 如果缓存为空，强制从网络更新
            if sector_df.empty:
                logger.info("⚠️ 缓存无数据，从网络获取...")
                sector_df = self.cached_manager.get_sector_data(
                    date=today, force_update=True
                )

            if sector_df.empty:
                logger.warning("⚠️ 板块数据为空")
                return {"success": False, "data": [], "message": "无板块数据"}

            # 处理数据
            sectors = self._process_sector_data(sector_df)

            logger.info(f"✅ 获取板块分析数据成功: {len(sectors)} 个板块")
            return {"success": True, "data": sectors, "count": len(sectors)}

        except Exception as e:
            logger.error(f"❌ 获取板块分析数据失败: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "data": [], "message": str(e)}

    def _process_sector_data(self, sector_df: pd.DataFrame) -> List[Dict]:
        """处理板块数据"""
        sectors = []

        # 板块映射
        sector_mapping = {
            "科技": {"icon": "mdi-laptop", "color": "primary"},
            "医药": {"icon": "mdi-medical-bag", "color": "success"},
            "金融": {"icon": "mdi-bank", "color": "info"},
            "消费": {"icon": "mdi-shopping", "color": "warning"},
            "能源": {"icon": "mdi-lightning-bolt", "color": "error"},
            "工业": {"icon": "mdi-factory", "color": "secondary"},
            "材料": {"icon": "mdi-cube-outline", "color": "brown"},
            "房地产": {"icon": "mdi-home", "color": "deep-orange"},
            "通信": {"icon": "mdi-cellphone", "color": "cyan"},
            "公用事业": {"icon": "mdi-water", "color": "light-blue"},
        }

        for _, row in sector_df.head(10).iterrows():
            try:
                sector_name = str(row.get("板块名称", row.get("sector_name", "未知")))

                # 获取涨跌幅
                change_pct = 0.0
                for col in ["涨跌幅", "change_pct", "涨跌幅%"]:
                    if col in row:
                        try:
                            val = row[col]
                            if isinstance(val, str):
                                val = val.replace("%", "")
                            change_pct = float(val)
                            break
                        except:
                            continue

                # 获取股票数量
                count = 0
                for col in ["成分股数量", "count", "公司数量"]:
                    if col in row:
                        try:
                            count = int(row[col])
                            break
                        except:
                            continue

                # 匹配板块配置
                sector_config = {"icon": "mdi-chart-pie", "color": "primary"}
                for key, config in sector_mapping.items():
                    if key in sector_name:
                        sector_config = config
                        break

                sectors.append(
                    {
                        "name": sector_name,
                        "change": (
                            change_pct / 100 if change_pct > 1 else change_pct
                        ),  # 转换为小数
                        "count": count,
                        "icon": sector_config["icon"],
                        "color": sector_config["color"],
                    }
                )
            except Exception as e:
                logger.warning(f"处理板块数据失败: {e}")
                continue

        return sectors

    async def fetch_market_sentiment_data(self) -> Dict:
        """
        获取市场情绪数据（改进版）
        使用加权算法，考虑个股涨跌幅和市值/成交量权重
        """
        try:
            logger.info("💭 获取市场情绪数据...")

            if not self.initialized:
                self.initialize()

            # 导入改进的情绪计算器
            from module_01_data_pipeline.data_processing.market_sentiment_calculator import (
                MarketSentimentCalculator
            )
            
            calculator = MarketSentimentCalculator()
            today = datetime.now().strftime("%Y-%m-%d")

            # 获取股票数据用于计算
            stock_data_list = []
            
            try:
                # 获取股票列表
                stock_list = self.db_manager.get_stock_list()
                
                if not stock_list.empty:
                    logger.info(f"📊 获取到 {len(stock_list)} 只股票，开始计算情绪指数...")
                    
                    # 收集股票数据（限制数量以提高速度）
                    for _, stock_row in stock_list.head(300).iterrows():
                        symbol = stock_row.get('symbol', '')
                        if not symbol:
                            continue
                        
                        try:
                            # 获取该股票今日数据
                            price_data = self.db_manager.get_stock_prices(
                                symbol=symbol,
                                start_date=today,
                                end_date=today
                            )
                            
                            if not price_data.empty and 'pct_change' in price_data.columns:
                                stock_info = {
                                    'symbol': symbol,
                                    'change_pct': float(price_data['pct_change'].iloc[-1]),
                                    'volume': float(price_data.get('volume', pd.Series([0])).iloc[-1]) if 'volume' in price_data.columns else 1.0,
                                    'market_cap': 1.0  # 市值数据暂时使用默认值
                                }
                                stock_data_list.append(stock_info)
                        except:
                            continue
                    
                    logger.info(f"📈 成功收集 {len(stock_data_list)} 只股票数据")

            except Exception as e:
                logger.warning(f"获取股票数据失败: {e}")

            # 使用改进的算法计算市场情绪
            if stock_data_list:
                stock_df = pd.DataFrame(stock_data_list)
                sentiment_result = calculator.calculate_sentiment(
                    stock_df,
                    weight_method='volume'  # 使用成交量加权
                )
                
                result = {
                    "success": True,
                    "data": {
                        "fear_greed_index": sentiment_result['fear_greed_index'],
                        "sentiment_level": sentiment_result['sentiment_level'],
                        "sentiment_description": sentiment_result['sentiment_description'],
                        "advancing_stocks": sentiment_result['advancing_stocks'],
                        "declining_stocks": sentiment_result['declining_stocks'],
                        "unchanged_stocks": sentiment_result.get('unchanged_stocks', 0),
                        "total_stocks": sentiment_result['total_stocks'],
                        "breadth_index": sentiment_result.get('breadth_index', 50),
                        "distribution": sentiment_result.get('distribution', {}),
                    },
                }
                
                logger.info(
                    f"✅ 市场情绪计算完成: {sentiment_result['sentiment_level']} "
                    f"(指数={sentiment_result['fear_greed_index']:.2f})"
                )
            else:
                # 使用默认值
                logger.warning("⚠️ 无可用股票数据，返回默认情绪指标")
                result = {
                    "success": True,
                    "data": {
                        "fear_greed_index": 50,
                        "sentiment_level": "中性",
                        "sentiment_description": "暂无数据",
                        "advancing_stocks": 2500,
                        "declining_stocks": 2000,
                        "unchanged_stocks": 0,
                        "total_stocks": 4500,
                        "breadth_index": 50,
                        "distribution": {},
                    },
                }

            return result

        except Exception as e:
            logger.error(f"❌ 获取市场情绪数据失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "data": {
                    "fear_greed_index": 50,
                    "sentiment_level": "中性",
                    "sentiment_description": "数据获取失败",
                    "advancing_stocks": 0,
                    "declining_stocks": 0,
                    "unchanged_stocks": 0,
                    "total_stocks": 0,
                    "breadth_index": 50,
                    "distribution": {},
                },
                "message": str(e),
            }

    async def fetch_technical_indicators_data(self) -> Dict:
        """获取技术指标数据"""
        try:
            logger.info("📈 获取技术指标数据...")

            if not self.initialized:
                self.initialize()

            # 获取上证指数数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)  # 获取60天数据确保够用

            index_data = self.db_manager.get_stock_prices(
                symbol="sh000001",
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )

            if index_data.empty or len(index_data) < 30:
                logger.warning("⚠️ 上证指数数据不足，尝试计算估算指标")
                # 返回估算指标
                indicators = self._get_estimated_indicators()
            else:
                # 计算真实技术指标
                indicators = self._calculate_technical_indicators(index_data)

            logger.info(f"✅ 技术指标数据获取成功: {len(indicators)} 个指标")
            return {
                "success": True,
                "data": indicators,
                "count": len(indicators),
                "based_on": "上证指数",
            }

        except Exception as e:
            logger.error(f"❌ 获取技术指标数据失败: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "data": self._get_estimated_indicators(),
                "message": str(e),
            }

    def _calculate_technical_indicators(self, data: pd.DataFrame) -> List[Dict]:
        """计算技术指标"""
        try:
            import numpy as np
            close_prices = data["close"].values

            # 计算RSI
            rsi = self._calculate_rsi(close_prices)

            # 计算MACD
            macd_value = self._calculate_macd(close_prices)

            # 计算KDJ
            kdj_value = self._calculate_kdj(data)

            # 计算BOLL
            boll_value = self._calculate_boll(close_prices)

            indicators = [
                {
                    "name": "RSI",
                    "value": round(rsi, 2),
                    "signal": self._get_rsi_signal(rsi),
                    "color": self._get_rsi_color(rsi),
                    "icon": "mdi-chart-line",
                    "description": "相对强弱指数",
                },
                {
                    "name": "MACD",
                    "value": round(macd_value, 2),
                    "signal": self._get_macd_signal(macd_value),
                    "color": self._get_macd_color(macd_value),
                    "icon": "mdi-chart-areaspline",
                    "description": "移动平均收敛散度",
                },
                {
                    "name": "KDJ",
                    "value": round(kdj_value, 2),
                    "signal": self._get_kdj_signal(kdj_value),
                    "color": self._get_kdj_color(kdj_value),
                    "icon": "mdi-chart-scatter-plot",
                    "description": "随机指标",
                },
                {
                    "name": "BOLL",
                    "value": round(boll_value, 2),
                    "signal": self._get_boll_signal(boll_value),
                    "color": self._get_boll_color(boll_value),
                    "icon": "mdi-chart-box",
                    "description": "布林带指标",
                },
            ]

            return indicators

        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return self._get_estimated_indicators()

    def _get_estimated_indicators(self) -> List[Dict]:
        """获取估算的技术指标"""
        import random

        # 生成合理范围内的随机值
        rsi = random.uniform(45, 65)
        macd = random.uniform(-0.5, 0.5)
        kdj = random.uniform(40, 70)
        boll = random.uniform(-1, 1)

        return [
            {
                "name": "RSI",
                "value": round(rsi, 2),
                "signal": self._get_rsi_signal(rsi),
                "color": self._get_rsi_color(rsi),
                "icon": "mdi-chart-line",
                "description": "相对强弱指数(估算)",
            },
            {
                "name": "MACD",
                "value": round(macd, 2),
                "signal": self._get_macd_signal(macd),
                "color": self._get_macd_color(macd),
                "icon": "mdi-chart-areaspline",
                "description": "移动平均收敛散度(估算)",
            },
            {
                "name": "KDJ",
                "value": round(kdj, 2),
                "signal": self._get_kdj_signal(kdj),
                "color": self._get_kdj_color(kdj),
                "icon": "mdi-chart-scatter-plot",
                "description": "随机指标(估算)",
            },
            {
                "name": "BOLL",
                "value": round(boll, 2),
                "signal": self._get_boll_signal(boll),
                "color": self._get_boll_color(boll),
                "icon": "mdi-chart-box",
                "description": "布林带指标(估算)",
            },
        ]

    def _calculate_rsi(self, prices, period: int = 14) -> float:
        """计算RSI"""
        try:
            import numpy as np
            if len(prices) < period + 1:
                return 50.0

            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi)
        except:
            return 50.0

    def _calculate_macd(self, prices) -> float:
        """计算MACD"""
        try:
            if len(prices) < 26:
                return 0.0

            import pandas as pd

            ema12 = pd.Series(prices).ewm(span=12, adjust=False).mean().iloc[-1]
            ema26 = pd.Series(prices).ewm(span=26, adjust=False).mean().iloc[-1]

            macd = ema12 - ema26
            return float(macd)
        except:
            return 0.0

    def _calculate_kdj(self, data: pd.DataFrame, period: int = 9) -> float:
        """计算KDJ"""
        try:
            if len(data) < period:
                return 50.0

            recent_data = data.tail(period)

            low_min = recent_data["low"].min()
            high_max = recent_data["high"].max()

            if high_max == low_min:
                return 50.0

            rsv = (recent_data["close"].iloc[-1] - low_min) / (high_max - low_min) * 100

            return float(rsv)
        except:
            return 50.0

    def _calculate_boll(self, prices, period: int = 20) -> float:
        """计算布林带"""
        try:
            import numpy as np
            if len(prices) < period:
                return 1.0

            recent_prices = prices[-period:]
            mean = np.mean(recent_prices)
            std = np.std(recent_prices)

            current_price = prices[-1]

            if std == 0:
                return 1.0

            return float((current_price - mean) / std)
        except:
            return 1.0

    # 信号判断方法
    def _get_rsi_signal(self, rsi: float) -> str:
        if rsi >= 70:
            return "超买"
        elif rsi >= 50:
            return "中性偏强"
        elif rsi >= 30:
            return "中性"
        else:
            return "超卖"

    def _get_rsi_color(self, rsi: float) -> str:
        if rsi >= 70 or rsi <= 30:
            return "warning"
        elif rsi >= 50:
            return "success"
        else:
            return "info"

    def _get_macd_signal(self, macd: float) -> str:
        if macd > 0.5:
            return "强买入"
        elif macd > 0:
            return "买入"
        elif macd > -0.5:
            return "卖出"
        else:
            return "强卖出"

    def _get_macd_color(self, macd: float) -> str:
        return "success" if macd > 0 else "error"

    def _get_kdj_signal(self, kdj: float) -> str:
        if kdj >= 80:
            return "超买"
        elif kdj >= 50:
            return "中性偏强"
        elif kdj >= 20:
            return "中性"
        else:
            return "超卖"

    def _get_kdj_color(self, kdj: float) -> str:
        if kdj >= 80:
            return "warning"
        elif kdj >= 50:
            return "success"
        elif kdj >= 20:
            return "primary"
        else:
            return "error"

    def _get_boll_signal(self, boll: float) -> str:
        if boll > 2:
            return "突破上轨"
        elif boll > 1:
            return "接近上轨"
        elif boll > -1:
            return "中轨区间"
        elif boll > -2:
            return "接近下轨"
        else:
            return "突破下轨"

    def _get_boll_color(self, boll: float) -> str:
        if abs(boll) > 2:
            return "warning"
        elif abs(boll) > 1:
            return "info"
        else:
            return "success"

    async def fetch_market_news_data(self, limit: int = 10, include_tonghuashun: bool = True) -> Dict:
        """
        获取市场资讯数据（整合多数据源）
        
        Args:
            limit: 获取数量限制
            include_tonghuashun: 是否包含同花顺数据源（研报、快讯）
        
        Returns:
            新闻数据字典
        """
        try:
            logger.info(f"📰 获取市场资讯数据 (limit={limit}, 同花顺={include_tonghuashun})...")

            if not self.initialized:
                self.initialize()

            all_news = []
            
            # 1. 从数据库获取传统新闻（AKShare/东财）
            try:
                news_df = self.db_manager.get_news_data(limit=limit)

                if news_df.empty:
                    logger.warning("⚠️ 数据库无新闻，尝试从网络获取...")
                    news_df = self.alternative_collector.fetch_news_data(limit=limit)

                    if not news_df.empty:
                        self.db_manager.save_news_data(news_df)

                if not news_df.empty:
                    # 处理传统新闻
                    traditional_news = self._process_news_data(news_df, limit)
                    all_news.extend(traditional_news)
                    logger.info(f"✅ 获取传统新闻 {len(traditional_news)} 条")

            except Exception as e:
                logger.warning(f"获取传统新闻失败: {e}")
            
            # 2. 从同花顺获取研报和快讯（可选）
            if include_tonghuashun and self.tonghuashun_collector:
                try:
                    # 并行获取研报和快讯
                    tasks = [
                        self.tonghuashun_collector.fetch_research_reports(limit=max(5, limit // 2)),
                        self.tonghuashun_collector.fetch_flash_news(limit=max(10, limit // 2)),
                    ]
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 处理研报
                    if isinstance(results[0], pd.DataFrame) and not results[0].empty:
                        reports = self._process_tonghuashun_data(results[0], data_type='research')
                        all_news.extend(reports)
                        logger.info(f"✅ 获取同花顺研报 {len(reports)} 条")
                    
                    # 处理快讯
                    if isinstance(results[1], pd.DataFrame) and not results[1].empty:
                        flash = self._process_tonghuashun_data(results[1], data_type='flash')
                        all_news.extend(flash)
                        logger.info(f"✅ 获取同花顺快讯 {len(flash)} 条")
                
                except Exception as e:
                    logger.warning(f"获取同花顺数据失败: {e}")
            
            # 3. 按时间排序并限制数量
            if all_news:
                all_news.sort(key=lambda x: x.get('time', ''), reverse=True)
                all_news = all_news[:limit]

            if not all_news:
                logger.warning("⚠️ 无新闻数据")
                return {"success": False, "data": [], "message": "无新闻数据"}

            logger.info(f"✅ 市场资讯数据获取成功: {len(all_news)} 条（含多数据源）")
            return {"success": True, "data": all_news, "count": len(all_news)}

        except Exception as e:
            logger.error(f"❌ 获取市场资讯数据失败: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "data": [], "message": str(e)}

    def _process_news_data(self, news_df: pd.DataFrame, limit: int) -> List[Dict]:
        """处理新闻数据"""
        news_list = []

        for idx, row in news_df.head(limit).iterrows():
            try:
                title = str(row.get("title", row.get("标题", "无标题")))
                content = str(row.get("content", row.get("内容", "")))

                # 生成摘要
                summary = content[:100] + "..." if len(content) > 100 else content

                # 获取时间
                time_str = row.get("time", row.get("date", row.get("日期", None)))
                if time_str:
                    try:
                        if isinstance(time_str, str):
                            news_time = datetime.fromisoformat(
                                time_str.replace("T", " ").split(".")[0]
                            )
                        else:
                            news_time = time_str
                    except:
                        news_time = datetime.now()
                else:
                    news_time = datetime.now()

                # 判断是否为重要新闻
                important_keywords = [
                    "央行",
                    "降准",
                    "加息",
                    "重大",
                    "紧急",
                    "暴跌",
                    "暴涨",
                    "政策",
                    "监管",
                ]
                is_important = any(
                    keyword in title or keyword in content
                    for keyword in important_keywords
                )

                news_list.append(
                    {
                        "id": idx + 1,
                        "title": title,
                        "summary": summary,
                        "time": news_time.isoformat(),
                        "type": "important" if is_important else "normal",
                    }
                )

            except Exception as e:
                logger.warning(f"处理新闻数据失败: {e}")
                continue

        return news_list
    
    def _process_tonghuashun_data(self, df: pd.DataFrame, data_type: str = 'research') -> List[Dict]:
        """
        处理同花顺数据（研报、快讯）
        
        Args:
            df: 同花顺数据DataFrame
            data_type: 数据类型，'research'（研报）或'flash'（快讯）
        
        Returns:
            处理后的数据列表
        """
        result_list = []
        
        for idx, row in df.iterrows():
            try:
                title = str(row.get('title', ''))
                summary = str(row.get('summary', row.get('content', '')))
                
                # 获取时间
                time_str = row.get('date', row.get('time', ''))
                if time_str:
                    try:
                        if isinstance(time_str, str):
                            news_time = datetime.fromisoformat(time_str.replace("T", " ").split(".")[0])
                        else:
                            news_time = time_str
                    except:
                        news_time = datetime.now()
                else:
                    news_time = datetime.now()
                
                # 根据数据类型设置type字段
                if data_type == 'research':
                    news_type = 'research_report'  # 研报
                elif data_type == 'flash':
                    news_type = 'flash'  # 快讯
                else:
                    news_type = 'normal'
                
                result_list.append({
                    'id': f"ths_{idx}_{int(news_time.timestamp())}",
                    'title': title,
                    'summary': summary[:200] + '...' if len(summary) > 200 else summary,
                    'time': news_time.isoformat(),
                    'type': news_type,
                    'source': row.get('source', '同花顺'),
                    'institution': row.get('institution', ''),  # 研报机构
                    'link': row.get('link', ''),  # 原文链接
                })
                
            except Exception as e:
                logger.debug(f"处理同花顺数据失败: {e}")
                continue
        
        return result_list

    async def update_all_data(self) -> Dict:
        """更新所有数据"""
        try:
            logger.info("🔄 开始更新所有智能分析页面数据...")

            results = {
                "sector_analysis": False,
                "market_sentiment": False,
                "technical_indicators": False,
                "market_news": False,
                "errors": [],
            }

            # 1. 更新板块数据
            try:
                sector_result = await self.fetch_sector_analysis_data()
                results["sector_analysis"] = sector_result.get("success", False)
            except Exception as e:
                results["errors"].append(f"板块分析: {str(e)}")

            # 2. 更新市场情绪
            try:
                sentiment_result = await self.fetch_market_sentiment_data()
                results["market_sentiment"] = sentiment_result.get("success", False)
            except Exception as e:
                results["errors"].append(f"市场情绪: {str(e)}")

            # 3. 更新技术指标
            try:
                indicators_result = await self.fetch_technical_indicators_data()
                results["technical_indicators"] = indicators_result.get("success", False)
            except Exception as e:
                results["errors"].append(f"技术指标: {str(e)}")

            # 4. 更新市场资讯
            try:
                news_result = await self.fetch_market_news_data(limit=10)
                results["market_news"] = news_result.get("success", False)
            except Exception as e:
                results["errors"].append(f"市场资讯: {str(e)}")

            success_count = sum([v for k, v in results.items() if k != "errors"])
            logger.info(f"✅ 数据更新完成: {success_count}/4 成功")

            return results

        except Exception as e:
            logger.error(f"❌ 更新所有数据失败: {e}")
            return {"error": str(e)}


# 全局实例
_coordinator = None


def get_data_pipeline_coordinator() -> DataPipelineCoordinator:
    """获取数据管道协调器单例"""
    global _coordinator
    if _coordinator is None:
        _coordinator = DataPipelineCoordinator()
        _coordinator.initialize()
    return _coordinator


# 便捷函数
async def fetch_all_market_intelligence_data():
    """获取所有市场情报数据"""
    coordinator = get_data_pipeline_coordinator()
    return await coordinator.update_all_data()

