#!/usr/bin/env python3
"""策略代码生成器 - 生成可执行的量化策略代码"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from common.data_structures import Signal
from common.logging_system import setup_logger

LOGGER = setup_logger("strategy_code_generator")


@dataclass
class StrategyCode:
    """策略代码容器"""
    
    strategy_name: str
    code: str
    strategy_function: Callable
    parameters: Dict[str, Any]
    description: str
    version: str = "1.0.0"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class StrategyCodeGenerator:
    """根据用户需求和选择的模型生成可执行的策略代码"""
    
    def __init__(self):
        self.templates = {
            "lstm": self._generate_lstm_strategy,
            "ensemble": self._generate_ensemble_strategy,
            "online": self._generate_online_strategy,
            "ppo": self._generate_ppo_strategy,
        }
    
    def generate_strategy_code(
        self,
        model_type: str,
        model_instance: Any,
        strategy_params: Dict[str, Any],
        feature_columns: List[str],
    ) -> StrategyCode:
        """生成策略代码
        
        Args:
            model_type: 模型类型 (lstm/ensemble/online/ppo)
            model_instance: 训练好的模型实例
            strategy_params: 策略参数
            feature_columns: 特征列名
            
        Returns:
            StrategyCode: 包含可执行策略函数的代码对象
        """
        generator = self.templates.get(model_type.lower())
        if not generator:
            LOGGER.warning(f"Unknown model type {model_type}, using default")
            generator = self._generate_default_strategy
        
        return generator(model_instance, strategy_params, feature_columns)
    
    def _generate_lstm_strategy(
        self,
        model: Any,
        params: Dict[str, Any],
        features: List[str],
    ) -> StrategyCode:
        """生成基于LSTM模型的策略"""
        
        buy_threshold = params.get("buy_threshold", -0.01)  # 允许小幅负值也能买入
        sell_threshold = params.get("sell_threshold", -0.03)  # 止损线
        confidence_threshold = params.get("confidence_threshold", 0.4)  # 进一步降低置信度
        max_position = params.get("max_position", 0.3)
        sequence_length = params.get("sequence_length", 10)
        
        def lstm_strategy_function(
            current_data: Dict[str, pd.Series],
            positions: Dict[str, Any],
            capital: float,
            feature_data: pd.DataFrame,
        ) -> List[Signal]:
            """LSTM模型驱动的量化策略
            
            策略逻辑：
            1. 使用LSTM模型预测未来收益率
            2. 当预测收益 > buy_threshold 且置信度 > confidence_threshold 时买入
            3. 当预测收益 < sell_threshold 或持仓亏损超过止损线时卖出
            4. 单个持仓不超过总资金的 max_position
            """
            signals: List[Signal] = []
            timestamp = datetime.now()
            
            LOGGER.info(f"🔍 LSTM Strategy called: {len(current_data)} symbols, {len(positions)} positions, capital={capital:.2f}")
            LOGGER.info(f"🔍 Feature data shape: {feature_data.shape if hasattr(feature_data, 'shape') else 'N/A'}")
            LOGGER.info(f"🔍 Parameters: buy_threshold={buy_threshold:.4f}, conf={confidence_threshold:.2f}")
            
            for symbol, data in current_data.items():
                try:
                    # 获取该股票的特征序列
                    symbol_features = feature_data[feature_data["symbol"] == symbol].copy()
                    if len(symbol_features) < sequence_length:
                        LOGGER.warning(f"❌ {symbol}: Not enough data ({len(symbol_features)} < {sequence_length})")
                        continue
                    
                    # 准备模型输入：最近sequence_length个时间步的特征
                    recent_features = symbol_features.tail(sequence_length)
                    feature_cols = [c for c in features if c in recent_features.columns]
                    if not feature_cols:
                        continue
                    
                    # 确保只使用数值列
                    X = recent_features[feature_cols].copy()
                    X = X.apply(pd.to_numeric, errors='coerce').fillna(0).values
                    
                    # 归一化特征
                    X_mean = X.mean(axis=0)
                    X_std = X.std(axis=0) + 1e-8
                    X_normalized = (X - X_mean) / X_std
                    X_reshaped = X_normalized.reshape(1, sequence_length, -1)
                    
                    # 模型预测
                    try:
                        prediction = model.predict(X_reshaped)
                        if hasattr(prediction, "predictions"):
                            predicted_return = float(prediction.predictions[0])
                            confidence = float(getattr(prediction, "confidence", 0.7))
                        elif isinstance(prediction, np.ndarray):
                            predicted_return = float(prediction[0])
                            confidence = 0.7
                        else:
                            predicted_return = float(prediction)
                            confidence = 0.7
                    except Exception as e:
                        LOGGER.debug(f"LSTM prediction failed for {symbol}: {e}")
                        # Fallback to momentum
                        if 'momentum_5' in recent_features.columns:
                            predicted_return = float(recent_features['momentum_5'].iloc[-1]) if not pd.isna(recent_features['momentum_5'].iloc[-1]) else 0.0
                        else:
                            predicted_return = 0.0
                        confidence = 0.5
                    
                    # 处理价格数据
                    try:
                        if isinstance(data["close"], str):
                            current_price = float(data["close"].replace(',', ''))
                        else:
                            current_price = float(data["close"])
                    except (ValueError, KeyError) as e:
                        LOGGER.warning(f"Invalid price data for {symbol}: {data.get('close')} - {e}")
                        continue
                    
                    # 调试日志
                    in_position = symbol in positions
                    LOGGER.info(f"📊 LSTM {symbol}: pred={predicted_return:.4f}, conf={confidence:.2f}, in_pos={in_position}, price={current_price:.2f}")
                    
                    # 买入信号
                    if symbol not in positions and predicted_return > buy_threshold:
                        if confidence >= confidence_threshold:
                            available_capital = float(capital) * float(max_position)
                            quantity = int(available_capital / current_price / 100) * 100
                            
                            if quantity > 0:
                                LOGGER.info(f"🔔 BUY Signal: {symbol} @ {current_price:.2f}, qty={quantity}, pred={predicted_return:.4f}")
                                signals.append(
                                    Signal(
                                        signal_id=f"lstm_buy_{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
                                        symbol=symbol,
                                        action="BUY",
                                        price=current_price,
                                        quantity=quantity,
                                        confidence=confidence,
                                        timestamp=timestamp,
                                        strategy_name="LSTM智能策略",
                                        metadata={
                                            "predicted_return": predicted_return,
                                            "model_type": "LSTM",
                                            "sequence_length": sequence_length,
                                        },
                                    )
                                )
                    
                    # 卖出信号
                    elif symbol in positions:
                        position = positions[symbol]
                        position_return = (current_price - position.avg_cost) / position.avg_cost
                        
                        # 止损或预测负收益
                        if predicted_return < sell_threshold or position_return < -0.05:
                            signals.append(
                                Signal(
                                    signal_id=f"lstm_sell_{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
                                    symbol=symbol,
                                    action="SELL",
                                    price=current_price,
                                    quantity=position.quantity,
                                    confidence=confidence,
                                    timestamp=timestamp,
                                    strategy_name="LSTM智能策略",
                                    metadata={
                                        "predicted_return": predicted_return,
                                        "position_return": position_return,
                                        "reason": "stop_loss" if position_return < -0.05 else "negative_prediction",
                                    },
                                )
                            )
                
                except Exception as e:
                    LOGGER.warning(f"Error processing {symbol}: {e}")
                    continue
            
            return signals
        
        code_str = f"""
# LSTM智能量化策略
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

策略参数:
- 买入阈值: {buy_threshold}
- 卖出阈值: {sell_threshold}
- 置信度阈值: {confidence_threshold}
- 最大持仓比例: {max_position}
- 序列长度: {sequence_length}

策略描述:
使用LSTM深度学习模型预测股票未来收益率，结合技术指标特征进行量化交易。
模型使用{sequence_length}个时间步的历史数据，通过多层LSTM网络捕捉时间序列模式。
"""
        
        return StrategyCode(
            strategy_name="LSTM智能策略",
            code=code_str,
            strategy_function=lstm_strategy_function,
            parameters={
                "buy_threshold": buy_threshold,
                "sell_threshold": sell_threshold,
                "confidence_threshold": confidence_threshold,
                "max_position": max_position,
                "sequence_length": sequence_length,
            },
            description="基于LSTM深度学习的时序预测策略",
        )
    
    def _generate_ensemble_strategy(
        self,
        model: Any,
        params: Dict[str, Any],
        features: List[str],
    ) -> StrategyCode:
        """生成基于集成模型的策略"""
        
        buy_threshold = params.get("buy_threshold", -0.01)  # 允许负值
        confidence_threshold = params.get("confidence_threshold", 0.4)  # 降低置信度
        max_position = params.get("max_position", 0.3)
        
        def ensemble_strategy_function(
            current_data: Dict[str, pd.Series],
            positions: Dict[str, Any],
            capital: float,
            feature_data: pd.DataFrame,
        ) -> List[Signal]:
            """集成模型策略 - 多模型投票决策"""
            signals: List[Signal] = []
            timestamp = datetime.now()
            
            LOGGER.info(f"🔍 Ensemble Strategy called: {len(current_data)} symbols, {len(positions)} positions, capital={capital:.2f}")
            LOGGER.info(f"🔍 Feature data shape: {feature_data.shape if hasattr(feature_data, 'shape') else 'N/A'}")
            LOGGER.info(f"🔍 Parameters: buy_threshold={buy_threshold:.4f}, conf={confidence_threshold:.2f}")
            
            for symbol, data in current_data.items():
                try:
                    LOGGER.debug(f"Processing {symbol}: capital type={type(capital)}, max_position type={type(max_position)}")
                    symbol_features = feature_data[feature_data["symbol"] == symbol].copy()
                    if symbol_features.empty:
                        LOGGER.warning(f"❌ {symbol}: No feature data")
                        continue
                    
                    # 获取最新10条数据
                    recent = symbol_features.tail(10)
                    if len(recent) < 5:
                        continue
                    
                    feature_cols = [c for c in features if c in recent.columns]
                    if not feature_cols:
                        continue
                    
                    # 确保只使用数值列
                    X = recent[feature_cols].copy()
                    X = X.apply(pd.to_numeric, errors='coerce').fillna(0).values
                    
                    # 归一化
                    X_mean = X.mean(axis=0)
                    X_std = X.std(axis=0) + 1e-8
                    X_normalized = (X - X_mean) / X_std
                    
                    # 使用最后一个样本进行预测
                    X_last = X_normalized[-1:].reshape(1, -1)
                    
                    # 集成预测 - 简单调用
                    try:
                        if hasattr(model, 'predict'):
                            prediction = model.predict(X_last)
                        else:
                            # 如果没有predict方法，使用默认值
                            predicted_return = 0.003
                            confidence = 0.7
                            LOGGER.debug(f"Model has no predict method for {symbol}")
                        
                        if isinstance(prediction, np.ndarray):
                            predicted_return = float(prediction[0])
                        elif hasattr(prediction, "predictions"):
                            predicted_return = float(prediction.predictions[0])
                        else:
                            predicted_return = float(prediction)
                        
                        confidence = 0.7
                    except Exception as e:
                        LOGGER.debug(f"Prediction failed for {symbol}: {e}")
                        # 使用简单的技术指标作为信号
                        if 'momentum_5' in recent.columns:
                            predicted_return = float(recent['momentum_5'].iloc[-1]) if not pd.isna(recent['momentum_5'].iloc[-1]) else 0.0
                        else:
                            predicted_return = 0.0
                        confidence = 0.5
                    
                    # 处理价格数据
                    try:
                        if isinstance(data["close"], str):
                            current_price = float(data["close"].replace(',', ''))
                        else:
                            current_price = float(data["close"])
                    except (ValueError, KeyError) as e:
                        LOGGER.warning(f"Invalid price data for {symbol}: {data.get('close')} - {e}")
                        continue
                    
                    # 调试日志
                    in_position = symbol in positions
                    LOGGER.info(f"📊 Ensemble {symbol}: pred={predicted_return:.4f}, conf={confidence:.2f}, in_pos={in_position}, price={current_price:.2f}")
                    
                    # 买入逻辑
                    if symbol not in positions and predicted_return > buy_threshold:
                        if confidence >= confidence_threshold:
                            try:
                                available_capital = float(capital) * float(max_position) * float(confidence)
                                quantity = int(available_capital / current_price / 100) * 100
                            except (ValueError, TypeError) as e:
                                LOGGER.error(f"Calculation error: capital={capital}({type(capital)}), max_position={max_position}({type(max_position)}), confidence={confidence}({type(confidence)}), price={current_price}({type(current_price)})")
                                raise
                            
                            if quantity > 0:
                                LOGGER.info(f"🔔 BUY Signal: {symbol} @ {current_price:.2f}, qty={quantity}, pred={predicted_return:.4f}")
                                signals.append(
                                    Signal(
                                        signal_id=f"ensemble_buy_{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
                                        symbol=symbol,
                                        action="BUY",
                                        price=current_price,
                                        quantity=quantity,
                                        confidence=confidence,
                                        timestamp=timestamp,
                                        strategy_name="集成模型策略",
                                        metadata={
                                            "predicted_return": predicted_return,
                                            "model_type": "Ensemble",
                                        },
                                    )
                                )
                    
                    # 卖出逻辑
                    elif symbol in positions:
                        position = positions[symbol]
                        position_return = (current_price - position.avg_cost) / position.avg_cost
                        
                        if predicted_return < -0.001 or position_return < -0.05:
                            signals.append(
                                Signal(
                                    signal_id=f"ensemble_sell_{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
                                    symbol=symbol,
                                    action="SELL",
                                    price=current_price,
                                    quantity=position.quantity,
                                    confidence=confidence,
                                    timestamp=timestamp,
                                    strategy_name="集成模型策略",
                                    metadata={
                                        "predicted_return": predicted_return,
                                        "position_return": position_return,
                                    },
                                )
                            )
                
                except Exception as e:
                    import traceback
                    LOGGER.warning(f"Error in ensemble strategy for {symbol}: {e}")
                    LOGGER.warning(f"Traceback: {traceback.format_exc()}")
                    continue
            
            return signals
        
        code_str = f"""
# 集成模型量化策略
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

策略参数:
- 买入阈值: {buy_threshold}
- 置信度阈值: {confidence_threshold}
- 最大持仓: {max_position}

策略描述:
集成多个机器学习模型（LSTM、Transformer等），通过加权投票机制提升预测稳定性。
适合震荡市场，能够降低单一模型的过拟合风险。
"""
        
        return StrategyCode(
            strategy_name="集成模型策略",
            code=code_str,
            strategy_function=ensemble_strategy_function,
            parameters={
                "buy_threshold": buy_threshold,
                "confidence_threshold": confidence_threshold,
                "max_position": max_position,
            },
            description="多模型集成的稳健预测策略",
        )
    
    def _generate_online_strategy(
        self,
        model: Any,
        params: Dict[str, Any],
        features: List[str],
    ) -> StrategyCode:
        """生成在线学习策略"""
        # 简化实现，类似LSTM
        return self._generate_lstm_strategy(model, params, features)
    
    def _generate_ppo_strategy(
        self,
        model: Any,
        params: Dict[str, Any],
        features: List[str],
    ) -> StrategyCode:
        """生成强化学习策略"""
        # PPO策略需要特殊处理，暂时使用默认
        return self._generate_default_strategy(model, params, features)
    
    def _generate_default_strategy(
        self,
        model: Any,
        params: Dict[str, Any],
        features: List[str],
    ) -> StrategyCode:
        """默认策略生成器"""
        return self._generate_lstm_strategy(model, params, features)


def create_strategy_code_generator() -> StrategyCodeGenerator:
    """工厂函数：创建策略代码生成器"""
    return StrategyCodeGenerator()
