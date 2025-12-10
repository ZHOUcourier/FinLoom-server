#!/usr/bin/env python3
"""
Module 04 市场分析 API
主要提供增强的情感分析和市场数据分析功能
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Enhanced sentiment analysis imports
try:
    from ..sentiment_analysis.enhanced_news_sentiment import (
        EnhancedNewsSentimentAnalyzer,
    )
    from ..sentiment_analysis.fin_r1_sentiment import get_sentiment_analyzer
except ImportError:
    EnhancedNewsSentimentAnalyzer = None
    get_sentiment_analyzer = None

# Module integrations
try:
    from module_01_data_pipeline import (
        AkshareDataCollector,
        ChineseAlternativeDataCollector,
    )
except ImportError:
    AkshareDataCollector = None
    ChineseAlternativeDataCollector = None

from common.logging_system import setup_logger

from ..storage_management.market_analysis_database import get_market_analysis_db

logger = setup_logger("market_analysis_api")

# 创建API路由器
router = APIRouter(prefix="/api/v1/market", tags=["market_analysis"])

# 全局实例
data_collector: Optional[AkshareDataCollector] = None
enhanced_sentiment_analyzer: Optional[EnhancedNewsSentimentAnalyzer] = None


class SentimentAnalysisRequest(BaseModel):
    """情感分析请求模型"""

    symbols: List[str] = Field(..., description="股票代码列表")
    market_data: Optional[Dict[str, Any]] = Field(None, description="市场数据")
    include_news: bool = Field(True, description="是否包含新闻分析")
    include_social: bool = Field(True, description="是否包含社交媒体分析")
    days_back: int = Field(7, description="回看天数")


class SentimentAnalysisResponse(BaseModel):
    """情感分析响应模型"""

    request_id: str
    symbols: List[str]
    individual_results: Dict[str, Any]
    market_sentiment: Dict[str, Any]
    execution_time: float
    timestamp: str
    status: str


class MarketDataRequest(BaseModel):
    """市场数据请求模型"""

    symbols: List[str] = Field(..., description="股票代码列表")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    data_types: List[str] = Field(["basic", "history"], description="数据类型")


class MarketDataResponse(BaseModel):
    """市场数据响应模型"""

    request_id: str
    symbols: List[str]
    stock_data: Dict[str, Any]
    news_data: Optional[List[Dict[str, Any]]]
    sector_data: Optional[List[Dict[str, Any]]]
    execution_time: float
    timestamp: str
    status: str


async def initialize_components():
    """初始化组件"""
    global data_collector, enhanced_sentiment_analyzer

    if data_collector is None and AkshareDataCollector:
        data_collector = AkshareDataCollector(rate_limit=1.0)
        logger.info("Data collector initialized")

    if enhanced_sentiment_analyzer is None and EnhancedNewsSentimentAnalyzer:
        enhanced_sentiment_analyzer = EnhancedNewsSentimentAnalyzer()
        logger.info("Enhanced sentiment analyzer initialized")


# ❌ 移除自动启动初始化，改为延迟加载避免启动卡顿
# @router.on_event("startup")
# async def startup_event():
#     """启动事件"""
#     await initialize_components()


@router.post("/sentiment/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """进行情感分析"""
    try:
        await initialize_components()

        logger.info(f"Starting sentiment analysis for symbols: {request.symbols}")
        start_time = datetime.now()

        # 使用增强的情感分析器
        if enhanced_sentiment_analyzer:
            result = await enhanced_sentiment_analyzer.analyze_comprehensive_sentiment(
                symbols=request.symbols
            )
        else:
            # 回退到基础情感分析器
            basic_analyzer = get_sentiment_analyzer()
            if basic_analyzer:
                result = await basic_analyzer.analyze_stock_sentiment(
                    symbols=request.symbols, days=request.days_back
                )
            else:
                raise HTTPException(
                    status_code=503, detail="No sentiment analyzer available"
                )

        execution_time = (datetime.now() - start_time).total_seconds()

        response = SentimentAnalysisResponse(
            request_id=f"sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            symbols=request.symbols,
            individual_results=result.get("individual_results", {}),
            market_sentiment=result.get(
                "market_sentiment", result.get("overall_sentiment", {})
            ),
            execution_time=execution_time,
            timestamp=datetime.now().isoformat(),
            status="completed",
        )

        logger.info(
            f"Sentiment analysis completed for {request.symbols} in {execution_time:.2f}s"
        )
        return response

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/collect", response_model=MarketDataResponse)
async def collect_market_data(request: MarketDataRequest):
    """收集市场数据"""
    try:
        await initialize_components()

        logger.info(f"Collecting market data for symbols: {request.symbols}")
        start_time = datetime.now()

        stock_data = {}
        news_data = None
        sector_data = None

        if data_collector:
            # 收集股票基础数据
            for symbol in request.symbols:
                try:
                    stock_info = data_collector.get_stock_basic_info(symbol)
                    stock_data[symbol] = {"basic_info": stock_info}

                    # 如果需要历史数据
                    if "history" in request.data_types:
                        end_date = request.end_date or datetime.now().strftime("%Y%m%d")
                        start_date = request.start_date or (
                            datetime.now() - timedelta(days=30)
                        ).strftime("%Y%m%d")

                        history = data_collector.fetch_stock_history(
                            symbol, start_date, end_date
                        )
                        stock_data[symbol]["history"] = (
                            history.to_dict()
                            if hasattr(history, "to_dict")
                            else history
                        )

                except Exception as e:
                    logger.warning(f"Failed to collect data for {symbol}: {e}")
                    stock_data[symbol] = {"error": str(e)}

            # 收集新闻数据
            if ChineseAlternativeDataCollector:
                alt_collector = ChineseAlternativeDataCollector(rate_limit=1.0)
                try:
                    news_data = alt_collector.fetch_news_data(limit=10)
                    sector_data = alt_collector.fetch_sector_performance()
                except Exception as e:
                    logger.warning(f"Failed to collect alternative data: {e}")

        execution_time = (datetime.now() - start_time).total_seconds()

        response = MarketDataResponse(
            request_id=f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            symbols=request.symbols,
            stock_data=stock_data,
            news_data=news_data,
            sector_data=sector_data,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat(),
            status="completed",
        )

        logger.info(
            f"Market data collection completed for {request.symbols} in {execution_time:.2f}s"
        )
        return response

    except Exception as e:
        logger.error(f"Market data collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        await initialize_components()

        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "data_collector": data_collector is not None,
                "enhanced_sentiment_analyzer": enhanced_sentiment_analyzer is not None,
                "basic_sentiment_analyzer": get_sentiment_analyzer() is not None
                if get_sentiment_analyzer
                else False,
            },
        }

        # 检查数据库连接
        try:
            db = get_market_analysis_db()
            db_stats = db.get_database_stats()
            status["database"] = {"connected": True, "stats": db_stats}
        except Exception as e:
            status["database"] = {"connected": False, "error": str(e)}

        return status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


@router.get("/status")
async def get_api_status():
    """获取API状态"""
    try:
        await initialize_components()

        status = {
            "api_version": "v1",
            "service_name": "Module 04 Market Analysis",
            "timestamp": datetime.now().isoformat(),
            "available_endpoints": [
                "/sentiment/analyze",
                "/data/collect",
                "/health",
                "/status",
            ],
            "components_status": {
                "data_collector": "available" if data_collector else "unavailable",
                "enhanced_sentiment_analyzer": "available"
                if enhanced_sentiment_analyzer
                else "unavailable",
                "basic_sentiment_analyzer": "available"
                if get_sentiment_analyzer
                else "unavailable",
            },
        }

        return status

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "api_version": "v1",
            "service_name": "Module 04 Market Analysis",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "status": "error",
        }
