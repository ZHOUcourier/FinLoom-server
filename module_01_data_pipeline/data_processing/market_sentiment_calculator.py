#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场情绪计算器 - 改进版
基于学术研究的加权算法
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from common.logging_system import setup_logger

logger = setup_logger("market_sentiment_calculator")


class MarketSentimentCalculator:
    """市场情绪计算器"""
    
    def __init__(self):
        """初始化"""
        self.k_factor = 40  # 调节系数，控制指数范围
        
    def calculate_sentiment(
        self,
        stock_data: pd.DataFrame,
        weight_method: str = "market_cap"
    ) -> Dict:
        """
        计算市场情绪指标（改进版）
        
        Args:
            stock_data: 股票数据DataFrame，需包含:
                - symbol: 股票代码
                - change_pct: 涨跌幅 (%)
                - market_cap: 市值（可选）
                - volume: 成交量（可选）
            weight_method: 权重方法 ('market_cap', 'volume', 'equal')
            
        Returns:
            情绪指标字典
        """
        try:
            if stock_data.empty:
                return self._get_default_sentiment()
            
            # 统计基础数据
            total_stocks = len(stock_data)
            advancing = len(stock_data[stock_data['change_pct'] > 0])
            declining = len(stock_data[stock_data['change_pct'] < 0])
            unchanged = total_stocks - advancing - declining
            
            # 计算加权情绪指数
            sentiment_index = self._calculate_weighted_sentiment(
                stock_data, weight_method
            )
            
            # 计算市场广度指标
            breadth_index = self._calculate_market_breadth(
                advancing, declining, total_stocks
            )
            
            # 计算情绪等级
            sentiment_level, sentiment_desc = self._get_sentiment_level(
                sentiment_index
            )
            
            # 计算涨跌幅分布
            distribution = self._calculate_distribution(stock_data)
            
            result = {
                'fear_greed_index': round(sentiment_index, 2),
                'sentiment_level': sentiment_level,
                'sentiment_description': sentiment_desc,
                'advancing_stocks': int(advancing),
                'declining_stocks': int(declining),
                'unchanged_stocks': int(unchanged),
                'total_stocks': int(total_stocks),
                'breadth_index': round(breadth_index, 2),
                'weight_method': weight_method,
                'distribution': distribution,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(
                f"Market sentiment calculated: {sentiment_level} "
                f"(index={sentiment_index:.2f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate market sentiment: {e}")
            return self._get_default_sentiment()
    
    def _calculate_weighted_sentiment(
        self,
        data: pd.DataFrame,
        method: str
    ) -> float:
        """
        计算加权情绪指数
        
        公式: sentiment = 50 + k × Σ(change × weight) / Σ|change × weight|
        """
        try:
            # 准备权重
            if method == 'market_cap' and 'market_cap' in data.columns:
                weights = data['market_cap'].fillna(1.0)
            elif method == 'volume' and 'volume' in data.columns:
                weights = data['volume'].fillna(1.0)
            else:
                # 等权重
                weights = pd.Series([1.0] * len(data), index=data.index)
            
            # 归一化权重
            weights = weights / weights.sum()
            
            # 计算加权涨跌幅
            weighted_changes = data['change_pct'] * weights
            
            # 计算情绪指数
            weighted_sum = weighted_changes.sum()
            abs_sum = abs(weighted_changes).sum()
            
            if abs_sum == 0:
                return 50.0  # 中性
            
            # 归一化到0-100
            sentiment = 50 + self.k_factor * (weighted_sum / abs_sum)
            
            # 确保在0-100范围内
            sentiment = max(0, min(100, sentiment))
            
            return float(sentiment)
            
        except Exception as e:
            logger.error(f"Failed to calculate weighted sentiment: {e}")
            return 50.0
    
    def _calculate_market_breadth(
        self,
        advancing: int,
        declining: int,
        total: int
    ) -> float:
        """
        计算市场广度指标 (Market Breadth)
        
        公式: breadth = (advancing - declining) / total × 100 + 50
        """
        if total == 0:
            return 50.0
        
        breadth = ((advancing - declining) / total) * 100 + 50
        return float(max(0, min(100, breadth)))
    
    def _get_sentiment_level(self, index: float) -> tuple:
        """
        根据指数值获取情绪等级和描述
        
        Returns:
            (等级, 描述)
        """
        if index >= 80:
            return ('极度贪婪', '市场极度乐观，需警惕回调风险')
        elif index >= 65:
            return ('贪婪', '市场情绪积极，多数股票上涨')
        elif index >= 55:
            return ('中性偏强', '市场情绪稳定，略偏乐观')
        elif index >= 45:
            return ('中性', '市场情绪中性，涨跌均衡')
        elif index >= 35:
            return ('中性偏弱', '市场情绪谨慎，略偏悲观')
        elif index >= 20:
            return ('恐慌', '市场情绪悲观，多数股票下跌')
        else:
            return ('极度恐慌', '市场极度悲观，或有超跌反弹机会')
    
    def _calculate_distribution(self, data: pd.DataFrame) -> Dict:
        """计算涨跌幅分布"""
        try:
            changes = data['change_pct']
            
            return {
                'strong_up': int(len(changes[changes >= 5])),      # 大涨(>=5%)
                'up': int(len(changes[(changes >= 0) & (changes < 5)])),  # 上涨
                'down': int(len(changes[(changes < 0) & (changes > -5)])),  # 下跌
                'strong_down': int(len(changes[changes <= -5])),   # 大跌(<=-5%)
                'limit_up': int(len(changes[changes >= 9.9])),     # 涨停
                'limit_down': int(len(changes[changes <= -9.9])),  # 跌停
            }
        except:
            return {
                'strong_up': 0,
                'up': 0,
                'down': 0,
                'strong_down': 0,
                'limit_up': 0,
                'limit_down': 0
            }
    
    def _get_default_sentiment(self) -> Dict:
        """获取默认情绪数据"""
        return {
            'fear_greed_index': 50.0,
            'sentiment_level': '中性',
            'sentiment_description': '暂无数据',
            'advancing_stocks': 0,
            'declining_stocks': 0,
            'unchanged_stocks': 0,
            'total_stocks': 0,
            'breadth_index': 50.0,
            'weight_method': 'equal',
            'distribution': {
                'strong_up': 0,
                'up': 0,
                'down': 0,
                'strong_down': 0,
                'limit_up': 0,
                'limit_down': 0
            },
            'timestamp': datetime.now().isoformat()
        }


# 便捷函数
def calculate_market_sentiment(
    stock_data: pd.DataFrame,
    weight_method: str = "equal"
) -> Dict:
    """
    计算市场情绪的便捷函数
    
    Args:
        stock_data: 股票数据
        weight_method: 权重方法
        
    Returns:
        情绪指标字典
    """
    calculator = MarketSentimentCalculator()
    return calculator.calculate_sentiment(stock_data, weight_method)

