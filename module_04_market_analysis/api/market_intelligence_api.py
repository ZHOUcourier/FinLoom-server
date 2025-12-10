#!/usr/bin/env python3
"""
市场情报API - 为前端提供板块分析、市场情绪、技术指标和市场资讯
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from common.logging_system import setup_logger

logger = setup_logger("market_intelligence_api")

# 创建API路由器
router = APIRouter(prefix="/api/v1/market", tags=["market_intelligence"])

# 全局实例
data_collector = None
sentiment_analyzer = None


async def initialize_components():
    """延迟初始化组件"""
    global data_collector, sentiment_analyzer

    if data_collector is None:
        try:
            from module_01_data_pipeline import (
                AkshareDataCollector,
                ChineseAlternativeDataCollector,
                get_database_manager,
            )

            data_collector = ChineseAlternativeDataCollector(rate_limit=0.5)
            logger.info("Data collector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize data collector: {e}")

    if sentiment_analyzer is None:
        try:
            from module_04_market_analysis.sentiment_analysis.fin_r1_sentiment import (
                get_sentiment_analyzer,
            )

            sentiment_analyzer = get_sentiment_analyzer()
            logger.info("Sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {e}")


@router.get("/sector-analysis")
async def get_sector_analysis():
    """获取板块分析数据"""
    try:
        logger.info("Fetching sector analysis data...")

        # 使用数据管道协调器
        from module_01_data_pipeline.data_pipeline_coordinator import (
            get_data_pipeline_coordinator,
        )

        coordinator = get_data_pipeline_coordinator()
        result = await coordinator.fetch_sector_analysis_data()

        if not result.get("success", False):
            logger.warning(f"Sector analysis failed: {result.get('message', 'Unknown error')}")
            return {
                "status": "error",
                "data": {
                    "sectors": [],
                    "timestamp": datetime.now().isoformat(),
                    "message": result.get("message", "无法获取板块数据"),
                },
            }

        return {
            "status": "success",
            "data": {
                "sectors": result.get("data", []),
                "timestamp": datetime.now().isoformat(),
                "count": result.get("count", 0),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get sector analysis: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-sentiment")
async def get_market_sentiment():
    """获取市场情绪数据"""
    try:
        logger.info("Fetching market sentiment data...")

        # 使用数据管道协调器
        from module_01_data_pipeline.data_pipeline_coordinator import (
            get_data_pipeline_coordinator,
        )

        coordinator = get_data_pipeline_coordinator()
        result = await coordinator.fetch_market_sentiment_data()

        if not result.get("success", False):
            logger.warning(f"Market sentiment failed: {result.get('message', 'Unknown error')}")
            # 返回错误，让前端显示加载失败
            raise HTTPException(status_code=503, detail=result.get("message", "无法获取市场情绪数据"))

        return {
            "status": "success",
            "data": result.get("data", {
                "fear_greed_index": 50,
                "advancing_stocks": 0,
                "declining_stocks": 0,
            }),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get market sentiment: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical-indicators")
async def get_technical_indicators():
    """获取技术指标数据"""
    try:
        logger.info("Fetching technical indicators...")

        # 使用数据管道协调器
        from module_01_data_pipeline.data_pipeline_coordinator import (
            get_data_pipeline_coordinator,
        )

        coordinator = get_data_pipeline_coordinator()
        result = await coordinator.fetch_technical_indicators_data()

        if not result.get("success", False):
            logger.warning(f"Technical indicators failed: {result.get('message', 'Unknown error')}")
            # 返回错误，让前端显示加载失败
            raise HTTPException(status_code=503, detail=result.get("message", "无法获取技术指标数据"))

        return {
            "status": "success",
            "data": {
                "indicators": result.get("data", []),
                "timestamp": datetime.now().isoformat(),
                "based_on": result.get("based_on", "上证指数"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get technical indicators: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-news")
async def get_market_news(limit: int = 10):
    """获取市场资讯"""
    try:
        logger.info(f"Fetching market news (limit={limit})...")

        # 使用数据管道协调器
        from module_01_data_pipeline.data_pipeline_coordinator import (
            get_data_pipeline_coordinator,
        )

        coordinator = get_data_pipeline_coordinator()
        result = await coordinator.fetch_market_news_data(limit=limit)

        if not result.get("success", False):
            logger.warning(f"Market news failed: {result.get('message', 'Unknown error')}")
            # 返回错误，让前端显示加载失败
            raise HTTPException(status_code=503, detail=result.get("message", "无法获取市场资讯"))

        return {
            "status": "success",
            "data": {
                "news": result.get("data", []),
                "timestamp": datetime.now().isoformat(),
                "count": result.get("count", 0),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get market news: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# 技术指标计算函数已移至 module_01_data_pipeline/data_pipeline_coordinator.py


