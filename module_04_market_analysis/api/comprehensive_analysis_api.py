"""
综合市场分析API接口
提供异常检测、相关性分析、市场状态检测、情感分析等功能的REST API
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from common.logging_system import setup_logger
from module_01_data_pipeline.data_acquisition.akshare_collector import (
    AkshareDataCollector,
)

logger = setup_logger("comprehensive_analysis_api")

from ..storage_management import get_market_analysis_db

try:
    from ..anomaly_detection.price_anomaly_detector import (
        AnomalyDetection,
        PriceAnomalyDetector,
    )
except ImportError as e:
    logger.warning(f"Failed to import PriceAnomalyDetector: {e}")
    PriceAnomalyDetector = None
    AnomalyDetection = None

try:
    from ..anomaly_detection.volume_anomaly_detector import VolumeAnomalyDetector
except ImportError as e:
    logger.warning(f"Failed to import VolumeAnomalyDetector: {e}")
    VolumeAnomalyDetector = None

try:
    from ..anomaly_detection.multi_dimensional_anomaly import (
        MultiDimensionalAnomalyDetector,
    )
except ImportError as e:
    logger.warning(f"Failed to import MultiDimensionalAnomalyDetector: {e}")
    MultiDimensionalAnomalyDetector = None

try:
    from ..correlation_analysis.correlation_analyzer import CorrelationAnalyzer
except ImportError as e:
    logger.warning(f"Failed to import CorrelationAnalyzer: {e}")
    CorrelationAnalyzer = None

try:
    from ..regime_detection.market_regime_detector import MarketRegimeDetector
except ImportError as e:
    logger.warning(f"Failed to import MarketRegimeDetector: {e}")
    MarketRegimeDetector = None

try:
    from ..regime_detection.hmm_regime_model import RegimeDetectionConfig
except ImportError as e:
    logger.warning(f"Failed to import RegimeDetectionConfig: {e}")
    RegimeDetectionConfig = None

try:
    from ..sentiment_analysis.fin_r1_sentiment import FINR1SentimentAnalyzer
except ImportError as e:
    logger.warning(f"Failed to import FINR1SentimentAnalyzer: {e}")
    FINR1SentimentAnalyzer = None

try:
    from ..sentiment_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer
except ImportError as e:
    logger.warning(f"Failed to import NewsSentimentAnalyzer: {e}")
    NewsSentimentAnalyzer = None

try:
    from ..sentiment_analysis.sentiment_aggregator import (
        SentimentAggregator,
        SentimentSource,
    )
except ImportError as e:
    logger.warning(f"Failed to import SentimentAggregator/SentimentSource: {e}")
    SentimentAggregator = None
    SentimentSource = None
from ..storage_management import get_market_analysis_db

logger = setup_logger("comprehensive_analysis_api")

# 创建API路由器
router = APIRouter(prefix="/api/v1/analysis", tags=["comprehensive_analysis"])

# 全局分析器实例
price_anomaly_detector: Optional[PriceAnomalyDetector] = None
volume_anomaly_detector: Optional[VolumeAnomalyDetector] = None
multi_dim_anomaly_detector: Optional[MultiDimensionalAnomalyDetector] = None
correlation_analyzer: Optional[CorrelationAnalyzer] = None
regime_detector: Optional[MarketRegimeDetector] = None
sentiment_analyzer: Optional[FINR1SentimentAnalyzer] = None
news_sentiment_analyzer: Optional[NewsSentimentAnalyzer] = None
sentiment_aggregator: Optional[SentimentAggregator] = None
data_collector: Optional[AkshareDataCollector] = None


class AnomalyDetectionRequest(BaseModel):
    """异常检测请求模型"""

    symbol: str = Field(..., description="股票代码")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    detection_method: str = Field(
        "all", description="检测方法: price, volume, multi_dim, all"
    )
    threshold: Optional[float] = Field(None, description="异常阈值")


class CorrelationAnalysisRequest(BaseModel):
    """相关性分析请求模型"""

    symbols: List[str] = Field(..., description="股票代码列表")
    method: str = Field("pearson", description="相关性方法: pearson, spearman, kendall")
    window_size: int = Field(60, description="窗口大小")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


class RegimeDetectionRequest(BaseModel):
    """市场状态检测请求模型"""

    symbols: List[str] = Field(..., description="股票代码列表")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    regime_count: int = Field(4, description="状态数量")
    detection_methods: List[str] = Field(
        ["hmm", "clustering", "rule_based"], description="检测方法"
    )


class SentimentAnalysisRequest(BaseModel):
    """情感分析请求模型"""

    texts: List[str] = Field(..., description="待分析文本列表")
    text_type: str = Field("news", description="文本类型: news, social_media, reports")
    symbols: Optional[List[str]] = Field(None, description="相关股票代码")
    batch_size: int = Field(32, description="批处理大小")
    use_local_model: bool = Field(True, description="是否使用本地FIN-R1模型")


class BatchSentimentRequest(BaseModel):
    """批量情感分析请求"""

    sources: List[Dict[str, Any]] = Field(..., description="情感数据源列表")
    weights: Optional[Dict[str, float]] = Field(None, description="自定义权重")


async def initialize_analyzers():
    """初始化分析器"""
    global price_anomaly_detector, volume_anomaly_detector, multi_dim_anomaly_detector
    global correlation_analyzer, regime_detector, sentiment_analyzer
    global news_sentiment_analyzer, sentiment_aggregator, data_collector

    if price_anomaly_detector is None:
        logger.info("Initializing analysis engines...")

        # 初始化数据收集器
        try:
            data_collector = AkshareDataCollector()
            logger.info("Data collector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize data collector: {e}")
            data_collector = None

        # 初始化异常检测器
        try:
            if PriceAnomalyDetector:
                price_anomaly_detector = PriceAnomalyDetector(data_collector)
                logger.info("Price anomaly detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize price anomaly detector: {e}")

        try:
            if VolumeAnomalyDetector:
                volume_anomaly_detector = VolumeAnomalyDetector(data_collector)
                logger.info("Volume anomaly detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize volume anomaly detector: {e}")

        try:
            if MultiDimensionalAnomalyDetector:
                multi_dim_anomaly_detector = MultiDimensionalAnomalyDetector()
                logger.info("Multi-dimensional anomaly detector initialized")
        except Exception as e:
            logger.error(
                f"Failed to initialize multi-dimensional anomaly detector: {e}"
            )

        # 初始化相关性分析器
        try:
            if CorrelationAnalyzer:
                correlation_analyzer = CorrelationAnalyzer()
                logger.info("Correlation analyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize correlation analyzer: {e}")

        # 初始化市场状态检测器
        try:
            if MarketRegimeDetector:
                regime_detector = MarketRegimeDetector()
                logger.info("Market regime detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize market regime detector: {e}")

        # 初始化情感分析器
        try:
            if FINR1SentimentAnalyzer:
                sentiment_analyzer = FINR1SentimentAnalyzer()
                logger.info("FIN-R1 sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize FIN-R1 sentiment analyzer: {e}")

        try:
            if NewsSentimentAnalyzer:
                news_sentiment_analyzer = NewsSentimentAnalyzer()
                logger.info("News sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize news sentiment analyzer: {e}")

        try:
            if SentimentAggregator:
                sentiment_aggregator = SentimentAggregator()
                logger.info("Sentiment aggregator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize sentiment aggregator: {e}")

        logger.info("Analysis engine initialization completed")


# ❌ 移除自动启动初始化，改为延迟加载避免启动卡顿
# @router.on_event("startup")
# async def startup_event():
#     """启动事件"""
#     await initialize_analyzers()


@router.post("/anomaly/detect")
async def detect_anomalies(request: AnomalyDetectionRequest):
    """异常检测"""
    try:
        if price_anomaly_detector is None:
            await initialize_analyzers()

        # 获取股票数据
        end_date = request.end_date or datetime.now().strftime("%Y%m%d")
        start_date = request.start_date or (
            datetime.now() - timedelta(days=90)
        ).strftime("%Y%m%d")

        # 获取数据
        stock_data = await data_collector.get_stock_daily(
            request.symbol, start_date, end_date
        )

        results = {}

        # 价格异常检测
        if request.detection_method in ["price", "all"]:
            price_anomalies = price_anomaly_detector.detect_price_anomalies(
                stock_data, symbol=request.symbol, threshold=request.threshold
            )
            results["price_anomalies"] = {
                "anomalies": [
                    {
                        "date": anomaly.timestamp.strftime("%Y-%m-%d"),
                        "price": anomaly.value,
                        "anomaly_score": anomaly.anomaly_score,
                        "anomaly_type": anomaly.anomaly_type,
                        "description": anomaly.description,
                    }
                    for anomaly in price_anomalies
                ],
                "count": len(price_anomalies),
            }

        # 成交量异常检测
        if request.detection_method in ["volume", "all"]:
            volume_anomalies = volume_anomaly_detector.detect_volume_anomalies(
                stock_data, symbol=request.symbol, threshold=request.threshold
            )
            results["volume_anomalies"] = {
                "anomalies": [
                    {
                        "date": anomaly.timestamp.strftime("%Y-%m-%d"),
                        "volume": anomaly.value,
                        "anomaly_score": anomaly.anomaly_score,
                        "anomaly_type": anomaly.anomaly_type,
                        "description": anomaly.description,
                    }
                    for anomaly in volume_anomalies
                ],
                "count": len(volume_anomalies),
            }

        # 多维异常检测
        if request.detection_method in ["multi_dim", "all"]:
            multi_dim_anomalies = multi_dim_anomaly_detector.detect_anomalies(
                stock_data, symbol=request.symbol
            )
            results["multi_dimensional_anomalies"] = {
                "anomalies": [
                    {
                        "date": anomaly.timestamp.strftime("%Y-%m-%d"),
                        "anomaly_score": anomaly.anomaly_score,
                        "anomaly_type": anomaly.anomaly_type,
                        "description": anomaly.description,
                        "features": anomaly.features,
                    }
                    for anomaly in multi_dim_anomalies
                ],
                "count": len(multi_dim_anomalies),
            }

        # 保存到数据库
        db = get_market_analysis_db()
        for method, anomaly_data in results.items():
            for anomaly in anomaly_data["anomalies"]:
                db.save_anomaly_detection(
                    symbol=request.symbol,
                    anomaly_type=anomaly["anomaly_type"],
                    anomaly_score=anomaly["anomaly_score"],
                    description=anomaly["description"],
                    detection_method=method,
                    timestamp=datetime.strptime(anomaly["date"], "%Y-%m-%d"),
                )

        return {
            "symbol": request.symbol,
            "detection_period": {"start_date": start_date, "end_date": end_date},
            "detection_method": request.detection_method,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/correlation/analyze")
async def analyze_correlation(request: CorrelationAnalysisRequest):
    """相关性分析"""
    try:
        if correlation_analyzer is None:
            await initialize_analyzers()

        # 获取股票数据
        end_date = request.end_date or datetime.now().strftime("%Y%m%d")
        start_date = request.start_date or (
            datetime.now() - timedelta(days=180)
        ).strftime("%Y%m%d")

        # 获取多只股票数据
        stock_data = {}
        for symbol in request.symbols:
            data = await data_collector.get_stock_daily(symbol, start_date, end_date)
            stock_data[symbol] = data

        # 执行相关性分析
        correlation_result = correlation_analyzer.analyze_correlations(
            stock_data,
            symbols=request.symbols,
            method=request.method,
            window_size=request.window_size,
        )

        # 保存到数据库
        db = get_market_analysis_db()
        db.save_correlation_analysis(
            analysis_id=f"corr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(tuple(request.symbols)) % 10000}",
            symbols=request.symbols,
            correlation_matrix=correlation_result.correlation_matrix.to_dict(),
            correlation_type=request.method,
            time_window=request.window_size,
            analysis_date=datetime.now(),
            insights=correlation_result.insights,
        )

        return {
            "symbols": request.symbols,
            "correlation_method": request.method,
            "analysis_period": {"start_date": start_date, "end_date": end_date},
            "correlation_matrix": correlation_result.correlation_matrix.to_dict(),
            "highly_correlated_pairs": correlation_result.highly_correlated_pairs,
            "insights": correlation_result.insights,
            "network_analysis": correlation_result.network_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regime/detect")
async def detect_market_regime(request: RegimeDetectionRequest):
    """市场状态检测"""
    try:
        if regime_detector is None:
            await initialize_analyzers()

        # 获取市场数据
        end_date = request.end_date or datetime.now().strftime("%Y%m%d")
        start_date = request.start_date or (
            datetime.now() - timedelta(days=252)
        ).strftime("%Y%m%d")

        # 获取数据（使用第一个symbol作为主要市场数据）
        main_symbol = request.symbols[0]
        market_data = await data_collector.get_stock_daily(
            main_symbol, start_date, end_date
        )

        # 配置检测器
        config = RegimeDetectionConfig(
            n_regimes=request.regime_count,
            use_hmm="hmm" in request.detection_methods,
            use_clustering="clustering" in request.detection_methods,
        )
        regime_detector.config = config

        # 执行状态检测
        regime_state = regime_detector.detect_market_regime(
            market_data, request.symbols
        )

        # 计算市场压力指标
        stress_indicators = regime_detector.assess_market_stress(market_data)

        # 预测状态转换
        transition_predictions = regime_detector.predict_regime_transitions(
            regime_state.characteristics, horizon=5
        )

        # 保存到数据库
        db = get_market_analysis_db()
        db.save_regime_detection(
            detection_id=f"regime_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(tuple(request.symbols)) % 10000}",
            market_regime=regime_state.regime.value,
            confidence=regime_state.confidence,
            regime_features=regime_state.characteristics,
            detection_method=",".join(request.detection_methods),
            symbols=request.symbols,
            analysis_date=datetime.now(),
        )

        return {
            "symbols": request.symbols,
            "analysis_period": {"start_date": start_date, "end_date": end_date},
            "current_regime": {
                "regime": regime_state.regime.value,
                "probability": regime_state.probability,
                "confidence": regime_state.confidence,
                "duration_days": regime_state.duration_days,
                "characteristics": regime_state.characteristics,
            },
            "stress_indicators": stress_indicators,
            "transition_predictions": [
                {
                    "from_regime": t.from_regime.value,
                    "to_regime": t.to_regime.value,
                    "probability": t.probability,
                    "transition_date": t.transition_date.isoformat(),
                    "trigger_factors": t.trigger_factors,
                }
                for t in transition_predictions
            ],
            "detection_methods": request.detection_methods,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Market regime detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment/analyze")
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """情感分析"""
    try:
        if sentiment_analyzer is None:
            await initialize_analyzers()

        # 选择分析器
        analyzer = (
            sentiment_analyzer if request.use_local_model else news_sentiment_analyzer
        )

        # 执行情感分析
        if request.use_local_model:
            # 使用FIN-R1本地模型
            batch_result = analyzer.analyze_batch(
                request.texts, batch_size=request.batch_size
            )

            results = {
                "overall_sentiment": batch_result.overall_sentiment,
                "average_confidence": batch_result.average_confidence,
                "sentiment_distribution": batch_result.sentiment_distribution,
                "processing_time": batch_result.processing_time,
                "individual_results": [
                    {
                        "text": result.text[:100],  # 截取前100字符
                        "sentiment": result.sentiment,
                        "confidence": result.confidence,
                        "probability_scores": result.probability_scores,
                        "timestamp": result.timestamp.isoformat(),
                    }
                    for result in batch_result.results
                ],
            }
        else:
            # 使用新闻情感分析器
            from ..sentiment_analysis.news_sentiment_analyzer import NewsArticle

            articles = []
            for i, text in enumerate(request.texts):
                article = NewsArticle(
                    article_id=f"text_{i}",
                    title="",
                    content=text,
                    source=request.text_type,
                    timestamp=datetime.now(),
                    url="",
                    symbols=request.symbols or [],
                    metadata={"index": i},
                )
                articles.append(article)

            analysis_results = analyzer.analyze_news_sentiment(
                articles, request.symbols
            )

            results = {
                "symbols": list(analysis_results.keys()),
                "sentiment_by_symbol": {},
            }

            for symbol, sentiment_results in analysis_results.items():
                results["sentiment_by_symbol"][symbol] = [
                    {
                        "article_id": result.article_id,
                        "overall_sentiment": result.overall_sentiment,
                        "sentiment_label": result.sentiment_label,
                        "confidence": result.confidence,
                        "keywords": result.keywords,
                        "timestamp": result.timestamp.isoformat(),
                    }
                    for result in sentiment_results
                ]

        # 保存到数据库
        db = get_market_analysis_db()
        for i, text in enumerate(request.texts):
            if request.use_local_model:
                result = batch_result.results[i]
                db.save_sentiment_analysis(
                    analysis_id=f"sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    symbol=request.symbols[0] if request.symbols else None,
                    text_source=request.text_type,
                    sentiment_score=1.0
                    if result.sentiment == "positive"
                    else (-1.0 if result.sentiment == "negative" else 0.0),
                    sentiment_label=result.sentiment,
                    confidence=result.confidence,
                    keywords=[],  # FIN-R1模型暂不提供关键词
                    analysis_method="FIN-R1",
                    source_data={"text": text[:200]},
                    timestamp=datetime.now(),
                )

        return {
            "text_type": request.text_type,
            "text_count": len(request.texts),
            "use_local_model": request.use_local_model,
            "analyzer_model": "FIN-R1" if request.use_local_model else "FinBERT",
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment/aggregate")
async def aggregate_sentiment(request: BatchSentimentRequest):
    """聚合情感分析"""
    try:
        if sentiment_aggregator is None:
            await initialize_analyzers()

        # 构建情感数据源
        sentiment_sources = []
        for source_data in request.sources:
            source = SentimentSource(
                source_name=source_data.get("source_name", "unknown"),
                sentiment_score=source_data.get("sentiment_score", 0.0),
                confidence=source_data.get("confidence", 0.5),
                weight=source_data.get("weight", 1.0),
                timestamp=datetime.fromisoformat(
                    source_data.get("timestamp", datetime.now().isoformat())
                ),
                metadata=source_data.get("metadata", {}),
            )
            sentiment_sources.append(source)

        # 执行聚合
        aggregated_result = sentiment_aggregator.aggregate_sentiments(
            sentiment_sources, custom_weights=request.weights
        )

        return {
            "overall_sentiment": aggregated_result.overall_sentiment,
            "confidence": aggregated_result.confidence,
            "sentiment_trend": aggregated_result.sentiment_trend,
            "volatility": aggregated_result.volatility,
            "source_contributions": aggregated_result.source_contributions,
            "key_insights": aggregated_result.key_insights,
            "risk_factors": aggregated_result.risk_factors,
            "source_count": len(sentiment_sources),
            "timestamp": aggregated_result.timestamp.isoformat(),
        }

    except Exception as e:
        logger.error(f"Sentiment aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        await initialize_analyzers()

        health_status = {
            "status": "healthy",
            "analyzers": {
                "price_anomaly_detector": price_anomaly_detector is not None,
                "volume_anomaly_detector": volume_anomaly_detector is not None,
                "multi_dim_anomaly_detector": multi_dim_anomaly_detector is not None,
                "correlation_analyzer": correlation_analyzer is not None,
                "regime_detector": regime_detector is not None,
                "sentiment_analyzer": sentiment_analyzer is not None,
                "news_sentiment_analyzer": news_sentiment_analyzer is not None,
                "sentiment_aggregator": sentiment_aggregator is not None,
                "data_collector": data_collector is not None,
            },
            "fin_r1_model": {
                "loaded": sentiment_analyzer is not None
                and sentiment_analyzer.model is not None,
                "device": sentiment_analyzer.device if sentiment_analyzer else None,
                "model_path": sentiment_analyzer.model_path
                if sentiment_analyzer
                else None,
            },
            "timestamp": datetime.now().isoformat(),
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/database/stats")
async def get_database_stats():
    """获取数据库统计信息"""
    try:
        db = get_market_analysis_db()
        stats = db.get_database_stats()
        return {"database_stats": stats, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
