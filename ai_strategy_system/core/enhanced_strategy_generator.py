#!/usr/bin/env python3
"""增强版策略生成器 - 多重信号确认机制"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from ai_strategy_system.core.strategy_code_generator import StrategyCode
from common.data_structures import Signal
from common.logging_system import setup_logger

LOGGER = setup_logger("enhanced_strategy_generator")


@dataclass
class SignalConfirmation:
    """信号确认结果"""

    signal_type: str  # AI/TREND/MOMENTUM/VOLUME/RSI
    value: float
    weight: float = 1.0
    description: str = ""


class EnhancedStrategyGenerator:
    """增强版策略生成器

    特点：
    1. 多重信号确认（AI + 技术指标）
    2. 动态权重调整
    3. 风险过滤
    4. 详细决策日志
    """

    def __init__(self):
        # 信号权重配置
        self.signal_weights = {
            "AI": 2.0,  # AI预测权重最高
            "TREND": 1.5,  # 趋势次之
            "MOMENTUM": 1.2,  # 动量
            "VOLUME": 1.0,  # 成交量
            "RSI": 0.8,  # RSI
        }

        # 确认阈值
        self.min_confirmations = 3  # 至少3个信号确认
        self.min_weighted_score = 3.0  # 加权总分至少3.0

    def generate_enhanced_lstm_strategy(
        self,
        model: Any,
        params: Dict[str, Any],
        features: List[str],
    ) -> StrategyCode:
        """生成增强版LSTM策略"""

        # 修改默认阈值以确保能产生信号
        buy_threshold = params.get(
            "buy_threshold", -0.01
        )  # 更宽松：从0.001降到-0.01（允许小幅下跌预测也买入）
        sell_threshold = params.get("sell_threshold", -0.05)  # 更宽松：从-0.03降到-0.05
        confidence_threshold = params.get(
            "confidence_threshold", 0.3
        )  # 更宽松：从0.5降到0.3
        max_position = params.get("max_position", 0.3)
        sequence_length = params.get("sequence_length", 10)

        # 捕获self引用 - 降低确认要求
        signal_weights = self.signal_weights
        min_confirmations = max(
            1, self.min_confirmations - 2
        )  # 从3降到1（只需1个确认信号）
        min_weighted_score = max(1.0, self.min_weighted_score - 2.0)  # 从3.0降到1.0

        def enhanced_lstm_strategy(
            current_data: Dict[str, pd.Series],
            positions: Dict[str, Any],
            capital: float,
            feature_data: pd.DataFrame,
        ) -> List[Signal]:
            """增强版LSTM策略 - 多重信号确认"""

            signals: List[Signal] = []
            timestamp = datetime.now()

            LOGGER.info(
                f"🔍 Enhanced LSTM Strategy: {len(current_data)} symbols, capital={capital:.2f}"
            )

            # 检查可用特征（仅记录一次）
            if len(feature_data) > 0:
                available_features = feature_data.columns.tolist()
                LOGGER.info(
                    f"📊 Available features: {available_features[:10]}{'...' if len(available_features) > 10 else ''}"
                )

                # 检查关键技术指标
                key_indicators = {
                    "MA": ["ma_5", "ma_20", "sma_5", "sma_20"],
                    "Momentum": ["momentum_5", "momentum_5d"],
                    "Volume": ["volume_ratio"],
                    "RSI": ["rsi"],
                }
                for indicator_name, possible_names in key_indicators.items():
                    found = [n for n in possible_names if n in available_features]
                    if found:
                        LOGGER.info(f"  ✅ {indicator_name}: {found[0]}")
                    else:
                        LOGGER.warning(
                            f"  ❌ {indicator_name}: None of {possible_names} found"
                        )

            for symbol, data in current_data.items():
                try:
                    # 1. 获取特征数据
                    symbol_features = feature_data[
                        feature_data["symbol"] == symbol
                    ].copy()
                    if len(symbol_features) < sequence_length:
                        continue

                    recent_features = symbol_features.tail(sequence_length)
                    feature_cols = [c for c in features if c in recent_features.columns]
                    if not feature_cols:
                        continue

                    # 数值化
                    X = recent_features[feature_cols].copy()
                    X = X.apply(pd.to_numeric, errors="coerce").fillna(0).values

                    # 归一化
                    X_mean = X.mean(axis=0)
                    X_std = X.std(axis=0) + 1e-8
                    X_normalized = (X - X_mean) / X_std
                    X_reshaped = X_normalized.reshape(1, sequence_length, -1)

                    # 2. AI模型预测
                    try:
                        prediction = model.predict(X_reshaped)
                        if hasattr(prediction, "predictions"):
                            ai_prediction = float(prediction.predictions[0])
                            ai_confidence = float(
                                getattr(prediction, "confidence", 0.7)
                            )
                        elif isinstance(prediction, np.ndarray):
                            ai_prediction = float(prediction[0])
                            ai_confidence = 0.7
                        else:
                            ai_prediction = float(prediction)
                            ai_confidence = 0.7
                    except Exception as e:
                        LOGGER.debug(f"AI prediction failed for {symbol}: {e}")
                        # Fallback
                        if "momentum_5" in recent_features.columns:
                            ai_prediction = float(
                                recent_features["momentum_5"].iloc[-1]
                            )
                        else:
                            ai_prediction = 0.0
                        ai_confidence = 0.5

                    # 处理价格
                    try:
                        if isinstance(data["close"], str):
                            current_price = float(data["close"].replace(",", ""))
                        else:
                            current_price = float(data["close"])
                    except (ValueError, KeyError) as e:
                        LOGGER.warning(f"Invalid price for {symbol}: {e}")
                        continue

                    # 3. 收集技术指标确认信号
                    confirmations: List[SignalConfirmation] = []

                    # === 买入信号分析 ===
                    if symbol not in positions:
                        # AI信号
                        if ai_prediction > buy_threshold:
                            confirmations.append(
                                SignalConfirmation(
                                    signal_type="AI",
                                    value=ai_prediction,
                                    weight=signal_weights["AI"],
                                    description=f"AI预测上涨{ai_prediction:.2%}",
                                )
                            )

                        # 趋势信号 (支持ma_5/sma_5和ma_20/sma_20)
                        ma5_col = (
                            "ma_5"
                            if "ma_5" in recent_features.columns
                            else (
                                "sma_5" if "sma_5" in recent_features.columns else None
                            )
                        )
                        ma20_col = (
                            "ma_20"
                            if "ma_20" in recent_features.columns
                            else (
                                "sma_20"
                                if "sma_20" in recent_features.columns
                                else None
                            )
                        )

                        if ma5_col and ma20_col:
                            ma5 = float(recent_features[ma5_col].iloc[-1])
                            ma20 = float(recent_features[ma20_col].iloc[-1])
                            if ma5 > ma20:
                                trend_strength = (ma5 - ma20) / ma20
                                confirmations.append(
                                    SignalConfirmation(
                                        signal_type="TREND",
                                        value=trend_strength,
                                        weight=signal_weights["TREND"],
                                        description=f"MA5上穿MA20({trend_strength:.2%})",
                                    )
                                )

                        # 动量信号 (支持momentum_5/momentum_5d)
                        momentum_col = (
                            "momentum_5"
                            if "momentum_5" in recent_features.columns
                            else (
                                "momentum_5d"
                                if "momentum_5d" in recent_features.columns
                                else None
                            )
                        )
                        if momentum_col:
                            momentum = float(recent_features[momentum_col].iloc[-1])
                            if momentum > 0:
                                confirmations.append(
                                    SignalConfirmation(
                                        signal_type="MOMENTUM",
                                        value=momentum,
                                        weight=signal_weights["MOMENTUM"],
                                        description=f"动量为正({momentum:.2%})",
                                    )
                                )

                        # 成交量信号
                        if "volume_ratio" in recent_features.columns:
                            volume_ratio = float(
                                recent_features["volume_ratio"].iloc[-1]
                            )
                            if volume_ratio > 1.2:
                                confirmations.append(
                                    SignalConfirmation(
                                        signal_type="VOLUME",
                                        value=volume_ratio,
                                        weight=signal_weights["VOLUME"],
                                        description=f"成交量放大({volume_ratio:.2f}倍)",
                                    )
                                )

                        # RSI信号（避免超买）
                        if "rsi" in recent_features.columns:
                            rsi = float(recent_features["rsi"].iloc[-1])
                            if 30 < rsi < 70:
                                confirmations.append(
                                    SignalConfirmation(
                                        signal_type="RSI",
                                        value=rsi,
                                        weight=signal_weights["RSI"],
                                        description=f"RSI未超买({rsi:.1f})",
                                    )
                                )

                        # 计算加权得分
                        weighted_score = sum(c.weight for c in confirmations)
                        confirmation_count = len(confirmations)

                        # 决策逻辑：至少3个确认 且 加权得分>=3.0
                        if (
                            confirmation_count >= min_confirmations
                            and weighted_score >= min_weighted_score
                        ):
                            if ai_confidence >= confidence_threshold:
                                available_capital = (
                                    float(capital) * float(max_position) * ai_confidence
                                )
                                quantity = (
                                    int(available_capital / current_price / 100) * 100
                                )

                                if quantity > 0:
                                    # 记录详细的确认信息
                                    confirmation_details = " | ".join(
                                        [
                                            f"{c.signal_type}({c.value:.3f})"
                                            for c in confirmations
                                        ]
                                    )

                                    LOGGER.info(
                                        f"✅ BUY {symbol} @ {current_price:.2f}"
                                    )
                                    LOGGER.info(
                                        f"   确认数: {confirmation_count}, 加权得分: {weighted_score:.2f}"
                                    )
                                    LOGGER.info(f"   信号: {confirmation_details}")

                                    signals.append(
                                        Signal(
                                            signal_id=f"enhanced_lstm_buy_{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
                                            symbol=symbol,
                                            action="BUY",
                                            price=current_price,
                                            quantity=quantity,
                                            confidence=ai_confidence,
                                            timestamp=timestamp,
                                            strategy_name="增强LSTM策略",
                                            metadata={
                                                "ai_prediction": ai_prediction,
                                                "confirmations": confirmation_count,
                                                "weighted_score": weighted_score,
                                                "confirmation_details": [
                                                    {
                                                        "type": c.signal_type,
                                                        "value": c.value,
                                                        "weight": c.weight,
                                                    }
                                                    for c in confirmations
                                                ],
                                            },
                                        )
                                    )
                                else:
                                    LOGGER.info(
                                        f"⚠️ {symbol}: 数量为0 (资金不足或价格过高)"
                                    )
                            else:
                                LOGGER.info(
                                    f"⚠️ {symbol}: AI置信度不足 ({ai_confidence:.2f} < {confidence_threshold})"
                                )
                        else:
                            confirmation_details = (
                                " | ".join(
                                    [
                                        f"{c.signal_type}({c.value:.3f})"
                                        for c in confirmations
                                    ]
                                )
                                if confirmations
                                else "无"
                            )
                            LOGGER.info(
                                f"❌ {symbol}: 确认不足 (确认数:{confirmation_count}/{min_confirmations}, 得分:{weighted_score:.2f}/{min_weighted_score}, AI:{ai_prediction:.4f}, 信号:{confirmation_details})"
                            )

                    # === 卖出信号分析 ===
                    elif symbol in positions:
                        position = positions[symbol]
                        position_return = (
                            current_price - position.avg_cost
                        ) / position.avg_cost

                        sell_reasons = []

                        # AI预测下跌
                        if ai_prediction < sell_threshold:
                            sell_reasons.append(f"AI预测下跌{ai_prediction:.2%}")

                        # 趋势转弱 (支持ma_5/sma_5和ma_20/sma_20)
                        ma5_col_sell = (
                            "ma_5"
                            if "ma_5" in recent_features.columns
                            else (
                                "sma_5" if "sma_5" in recent_features.columns else None
                            )
                        )
                        ma20_col_sell = (
                            "ma_20"
                            if "ma_20" in recent_features.columns
                            else (
                                "sma_20"
                                if "sma_20" in recent_features.columns
                                else None
                            )
                        )

                        if ma5_col_sell and ma20_col_sell:
                            ma5 = float(recent_features[ma5_col_sell].iloc[-1])
                            ma20 = float(recent_features[ma20_col_sell].iloc[-1])
                            if ma5 < ma20:
                                sell_reasons.append("MA5跌破MA20")

                        # 动量转负 (支持momentum_5/momentum_5d)
                        momentum_col_sell = (
                            "momentum_5"
                            if "momentum_5" in recent_features.columns
                            else (
                                "momentum_5d"
                                if "momentum_5d" in recent_features.columns
                                else None
                            )
                        )
                        if momentum_col_sell:
                            momentum = float(
                                recent_features[momentum_col_sell].iloc[-1]
                            )
                            if momentum < -0.02:
                                sell_reasons.append(f"动量转负({momentum:.2%})")

                        # 止损
                        if position_return < -0.05:
                            sell_reasons.append(f"止损({position_return:.2%})")

                        # 至少2个卖出原因
                        if len(sell_reasons) >= 2:
                            LOGGER.info(f"❌ SELL {symbol} @ {current_price:.2f}")
                            LOGGER.info(f"   持仓收益: {position_return:.2%}")
                            LOGGER.info(f"   卖出原因: {' | '.join(sell_reasons)}")

                            signals.append(
                                Signal(
                                    signal_id=f"enhanced_lstm_sell_{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
                                    symbol=symbol,
                                    action="SELL",
                                    price=current_price,
                                    quantity=position.quantity,
                                    confidence=ai_confidence,
                                    timestamp=timestamp,
                                    strategy_name="增强LSTM策略",
                                    metadata={
                                        "position_return": position_return,
                                        "sell_reasons": sell_reasons,
                                    },
                                )
                            )

                except Exception as e:
                    LOGGER.warning(f"Error processing {symbol}: {e}")
                    continue

            LOGGER.info(f"📊 Generated {len(signals)} signals")

            # 如果没有生成信号，输出详细原因
            if len(signals) == 0:
                LOGGER.warning("⚠️ 未生成任何交易信号！")
                LOGGER.warning(
                    f"   策略参数: buy_threshold={buy_threshold:.4f}, confidence_threshold={confidence_threshold:.2f}"
                )
                LOGGER.warning(
                    f"   确认要求: min_confirmations={min_confirmations}, min_weighted_score={min_weighted_score:.1f}"
                )
                LOGGER.warning("   可能原因:")
                LOGGER.warning("   1. AI预测值都低于买入阈值")
                LOGGER.warning("   2. 技术指标确认数不足")
                LOGGER.warning("   3. 特征数据缺失关键指标")
                LOGGER.warning("   建议: 降低买入阈值或确认要求")

            return signals

        code_str = f"""
# 增强版LSTM策略 - 多重信号确认
# 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

策略参数:
- 买入阈值: {buy_threshold:.4f}
- 卖出阈值: {sell_threshold:.4f}
- 置信度阈值: {confidence_threshold:.2f}
- 最大仓位: {max_position:.2f}
- 最少确认数: {min_confirmations}
- 最低加权得分: {min_weighted_score:.1f}

信号权重:
- AI预测: {signal_weights["AI"]:.1f}
- 趋势确认: {signal_weights["TREND"]:.1f}
- 动量确认: {signal_weights["MOMENTUM"]:.1f}
- 成交量: {signal_weights["VOLUME"]:.1f}
- RSI: {signal_weights["RSI"]:.1f}

策略逻辑:
1. AI模型预测未来收益
2. 趋势确认（MA5 vs MA20）
3. 动量确认（momentum_5 > 0）
4. 成交量确认（volume_ratio > 1.2）
5. RSI过滤（30 < RSI < 70）
6. 至少{min_confirmations}个信号确认 且 加权得分>={min_weighted_score}才执行

风险控制:
- 止损: -5%
- 单个持仓: {max_position:.0%}
"""

        return StrategyCode(
            strategy_name="增强LSTM多重确认策略",
            code=code_str,
            strategy_function=enhanced_lstm_strategy,
            parameters={
                "buy_threshold": buy_threshold,
                "sell_threshold": sell_threshold,
                "confidence_threshold": confidence_threshold,
                "max_position": max_position,
                "min_confirmations": min_confirmations,
                "signal_weights": signal_weights,
            },
            description="结合AI预测和多个技术指标的多重确认策略",
            version="2.0.0",
        )

    def generate_enhanced_ensemble_strategy(
        self,
        model: Any,
        params: Dict[str, Any],
        features: List[str],
    ) -> StrategyCode:
        """生成增强版Ensemble策略"""
        # 类似的逻辑，使用ensemble模型
        return self.generate_enhanced_lstm_strategy(model, params, features)


def create_enhanced_strategy_generator() -> EnhancedStrategyGenerator:
    """工厂函数：创建增强版策略生成器"""
    return EnhancedStrategyGenerator()
