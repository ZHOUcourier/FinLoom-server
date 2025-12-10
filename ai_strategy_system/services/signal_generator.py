#!/usr/bin/env python3
"""交易信号生成器 - 基于策略生成每日投资信号"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch

from ai_strategy_system.services.live_trading_manager import (
    LiveTradingManager,
    TradingSignal,
)
from ai_strategy_system.utils.strategy_persistence import StrategyPersistence
from common.logging_system import setup_logger

LOGGER = setup_logger("signal_generator")


class SignalGenerator:
    """交易信号生成器

    功能:
    1. 加载策略和模型
    2. 获取最新市场数据
    3. 计算特征和指标
    4. 模型预测
    5. 生成交易信号
    6. 风险检查和过滤
    """

    def __init__(self):
        """初始化信号生成器"""
        self.persistence = StrategyPersistence()
        self.manager = LiveTradingManager()
        LOGGER.info("📡 信号生成器初始化完成")

    def generate_signals_for_strategy(
        self, strategy_id: str, market_data: Optional[pd.DataFrame] = None
    ) -> List[TradingSignal]:
        """为指定策略生成交易信号

        Args:
            strategy_id: 策略ID
            market_data: 市场数据（如果为None则自动获取）

        Returns:
            交易信号列表
        """
        try:
            LOGGER.info(f"📊 开始为策略生成信号: {strategy_id}")

            # 1. 检查策略状态
            config = self.manager.get_strategy_config(strategy_id)
            if not config:
                LOGGER.error(f"❌ 策略不存在: {strategy_id}")
                return []

            status = config.get("status", "active")
            if status != "active":
                LOGGER.warning(f"⚠️ 策略未激活: {strategy_id} (状态: {status})")
                return []

            # 2. 加载策略
            strategy = self.persistence.load_strategy(strategy_id)
            if not strategy:
                LOGGER.error(f"❌ 加载策略失败: {strategy_id}")
                return []

            # 3. 获取市场数据
            if market_data is None:
                market_data = self._fetch_market_data(config)

            if market_data is None or market_data.empty:
                LOGGER.error("❌ 获取市场数据失败")
                return []

            # 4. 加载模型
            model = self._load_model(strategy)
            if model is None:
                LOGGER.error("❌ 加载模型失败")
                return []

            # 5. 准备特征
            features = self._prepare_features(market_data, strategy)
            if features is None:
                LOGGER.error("❌ 准备特征失败")
                return []

            # 6. 模型预测
            predictions = self._predict(model, features, strategy)
            if predictions is None:
                LOGGER.error("❌ 模型预测失败")
                return []

            # 7. 生成信号
            signals = self._generate_signals(
                predictions=predictions,
                market_data=market_data,
                strategy_config=config,
                account_status=self.manager.get_account_status(strategy_id),
            )

            # 8. 风险过滤
            filtered_signals = self._filter_signals(signals, config)

            # 9. 保存信号
            for signal in filtered_signals:
                self.manager.save_signal(signal)

            LOGGER.info(f"✅ 生成 {len(filtered_signals)} 个交易信号")

            return filtered_signals

        except Exception as e:
            LOGGER.error(f"❌ 生成信号失败: {e}", exc_info=True)
            return []

    def generate_signals_for_all_strategies(self) -> Dict[str, List[TradingSignal]]:
        """为所有活跃策略生成信号

        Returns:
            策略ID -> 信号列表的映射
        """
        all_signals = {}

        # 获取所有活跃策略
        active_strategies = self.manager.get_active_strategies()

        LOGGER.info(f"📊 开始为 {len(active_strategies)} 个策略生成信号")

        # 为每个策略生成信号
        for strategy_config in active_strategies:
            strategy_id = strategy_config["strategy_id"]

            try:
                signals = self.generate_signals_for_strategy(strategy_id)
                all_signals[strategy_id] = signals

            except Exception as e:
                LOGGER.error(f"❌ 策略 {strategy_id} 生成信号失败: {e}")
                all_signals[strategy_id] = []

        return all_signals

    def _fetch_market_data(self, config: Dict) -> Optional[pd.DataFrame]:
        """获取市场数据

        Args:
            config: 策略配置

        Returns:
            市场数据DataFrame
        """
        try:
            from module_01_data_pipeline import AkshareDataCollector

            # 创建数据收集器
            collector = AkshareDataCollector()

            # 从配置中获取股票列表
            strategy_config = config.get("config", {})
            stock_codes = strategy_config.get("stock_universe", [])

            if not stock_codes:
                # 如果没有指定，使用默认股票池
                stock_codes = [
                    "600519.SH",  # 贵州茅台
                    "600036.SH",  # 招商银行
                    "000858.SZ",  # 五粮液
                    "601318.SH",  # 中国平安
                    "000333.SZ",  # 美的集团
                ]

            # 获取最近60天的数据
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - pd.Timedelta(days=60)).strftime("%Y%m%d")

            LOGGER.info(f"📥 获取市场数据: {len(stock_codes)} 只股票")

            all_data = []

            for stock_code in stock_codes:
                try:
                    data = collector.fetch_stock_data(
                        stock_code=stock_code, start_date=start_date, end_date=end_date
                    )

                    if data is not None and not data.empty:
                        data["stock_code"] = stock_code
                        all_data.append(data)

                except Exception as e:
                    LOGGER.warning(f"⚠️ 获取 {stock_code} 数据失败: {e}")
                    continue

            if not all_data:
                return None

            # 合并所有数据
            combined_data = pd.concat(all_data, ignore_index=True)

            LOGGER.info(f"✅ 成功获取 {len(combined_data)} 条数据")

            return combined_data

        except Exception as e:
            LOGGER.error(f"❌ 获取市场数据失败: {e}", exc_info=True)
            return None

    def _load_model(self, strategy: Dict) -> Optional[Any]:
        """加载模型

        Args:
            strategy: 策略字典

        Returns:
            加载的模型
        """
        try:
            model_state = strategy.get("model_state")
            config = strategy.get("config", {})

            if model_state is None:
                LOGGER.warning("⚠️ 策略中没有保存的模型")
                return None

            # 根据模型类型创建模型
            model_type = config.get("model_type", "lstm")

            if model_type == "lstm":
                from module_03_ai_models import LSTMModel, LSTMModelConfig

                model_config = LSTMModelConfig(
                    input_size=config.get("input_size", 10),
                    hidden_size=config.get("hidden_size", 128),
                    num_layers=config.get("num_layers", 2),
                    output_size=config.get("output_size", 1),
                    dropout=config.get("dropout", 0.2),
                )

                model = LSTMModel(model_config)
                model.load_state_dict(model_state)
                model.eval()

            elif model_type == "ensemble":
                from module_03_ai_models import EnsembleConfig, EnsemblePredictor

                ensemble_config = EnsembleConfig(
                    input_size=config.get("input_size", 10)
                )

                model = EnsemblePredictor(ensemble_config)
                model.load_state_dict(model_state)
                model.eval()

            else:
                LOGGER.error(f"❌ 不支持的模型类型: {model_type}")
                return None

            LOGGER.info(f"✅ 模型加载成功: {model_type}")

            return model

        except Exception as e:
            LOGGER.error(f"❌ 加载模型失败: {e}", exc_info=True)
            return None

    def _prepare_features(
        self, market_data: pd.DataFrame, strategy: Dict
    ) -> Optional[torch.Tensor]:
        """准备特征

        Args:
            market_data: 市场数据
            strategy: 策略字典

        Returns:
            特征张量
        """
        try:
            from module_02_feature_engineering import TechnicalIndicators

            # 提取配置
            config = strategy.get("config", {})

            # 按股票分组
            stock_groups = market_data.groupby("stock_code")

            all_features = []

            for stock_code, stock_data in stock_groups:
                try:
                    # 计算技术指标
                    indicators = TechnicalIndicators.calculate_all_indicators(
                        data=stock_data,
                        ma_periods=[5, 10, 20, 60],
                        ema_periods=[12, 26],
                    )

                    if indicators is not None and not indicators.empty:
                        # 选择最新的数据点
                        latest_features = indicators.iloc[-1:].values
                        all_features.append(latest_features)

                except Exception as e:
                    LOGGER.warning(f"⚠️ 计算 {stock_code} 特征失败: {e}")
                    continue

            if not all_features:
                return None

            # 合并特征
            features = np.vstack(all_features)

            # 转换为张量
            features_tensor = torch.FloatTensor(features)

            LOGGER.info(f"✅ 特征准备完成: {features_tensor.shape}")

            return features_tensor

        except Exception as e:
            LOGGER.error(f"❌ 准备特征失败: {e}", exc_info=True)
            return None

    def _predict(
        self, model: Any, features: torch.Tensor, strategy: Dict
    ) -> Optional[np.ndarray]:
        """模型预测

        Args:
            model: 模型
            features: 特征张量
            strategy: 策略字典

        Returns:
            预测结果
        """
        try:
            with torch.no_grad():
                # 预测
                predictions = model(features)

                # 转换为numpy数组
                if isinstance(predictions, torch.Tensor):
                    predictions = predictions.cpu().numpy()

                LOGGER.info(f"✅ 预测完成: {predictions.shape}")

                return predictions

        except Exception as e:
            LOGGER.error(f"❌ 预测失败: {e}", exc_info=True)
            return None

    def _generate_signals(
        self,
        predictions: np.ndarray,
        market_data: pd.DataFrame,
        strategy_config: Dict,
        account_status: Optional[Dict],
    ) -> List[TradingSignal]:
        """生成交易信号

        Args:
            predictions: 模型预测
            market_data: 市场数据
            strategy_config: 策略配置
            account_status: 账户状态

        Returns:
            交易信号列表
        """
        signals = []

        try:
            # 获取股票列表
            stock_codes = market_data["stock_code"].unique()

            # 当前持仓
            current_positions = {}
            if account_status:
                current_positions = account_status.get("positions", {})

            # 为每只股票生成信号
            for i, stock_code in enumerate(stock_codes):
                try:
                    # 获取该股票的最新数据
                    stock_data = market_data[market_data["stock_code"] == stock_code]
                    latest_data = stock_data.iloc[-1]

                    # 当前价格
                    current_price = float(latest_data.get("close", 0))

                    if current_price <= 0:
                        continue

                    # 预测值
                    prediction = predictions[i][0] if len(predictions) > i else 0

                    # 决策逻辑
                    signal_type, confidence, reason = self._make_decision(
                        prediction=prediction,
                        stock_data=stock_data,
                        current_positions=current_positions,
                        stock_code=stock_code,
                    )

                    if signal_type == "hold":
                        continue  # 不生成持有信号

                    # 计算仓位
                    position_size = self._calculate_position_size(
                        signal_type=signal_type,
                        confidence=confidence,
                        strategy_config=strategy_config,
                        account_status=account_status,
                    )

                    # 计算止损止盈价格
                    stop_loss_price = current_price * (
                        1 + strategy_config.get("stop_loss", -0.05)
                    )
                    take_profit_price = current_price * (
                        1 + strategy_config.get("take_profit", 0.15)
                    )

                    # 预期收益
                    expected_return = float(prediction) if abs(prediction) < 1 else None

                    # 风险评分
                    risk_score = self._calculate_risk_score(
                        stock_data=stock_data, prediction=prediction
                    )

                    # 创建信号
                    signal = TradingSignal(
                        signal_id=f"signal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{stock_code}",
                        strategy_id=strategy_config["strategy_id"],
                        timestamp=datetime.now().isoformat(),
                        signal_type=signal_type,
                        stock_code=stock_code,
                        stock_name=self._get_stock_name(stock_code),
                        current_price=current_price,
                        target_price=current_price
                        * (1 + (prediction if abs(prediction) < 0.5 else 0.1)),
                        position_size=position_size,
                        confidence=confidence,
                        reason=reason,
                        stop_loss_price=stop_loss_price,
                        take_profit_price=take_profit_price,
                        expected_return=expected_return,
                        risk_score=risk_score,
                    )

                    signals.append(signal)

                except Exception as e:
                    LOGGER.warning(f"⚠️ 生成 {stock_code} 信号失败: {e}")
                    continue

            LOGGER.info(f"✅ 生成 {len(signals)} 个原始信号")

        except Exception as e:
            LOGGER.error(f"❌ 生成信号失败: {e}", exc_info=True)

        return signals

    def _make_decision(
        self,
        prediction: float,
        stock_data: pd.DataFrame,
        current_positions: Dict,
        stock_code: str,
    ) -> Tuple[str, float, str]:
        """做出交易决策

        Args:
            prediction: 预测值
            stock_data: 股票数据
            current_positions: 当前持仓
            stock_code: 股票代码

        Returns:
            (signal_type, confidence, reason)
        """
        reasons = []

        # 获取最新数据
        latest = stock_data.iloc[-1]

        # 计算简单的技术指标
        close_prices = stock_data["close"].values

        # MA5 和 MA20
        ma5 = np.mean(close_prices[-5:]) if len(close_prices) >= 5 else close_prices[-1]
        ma20 = (
            np.mean(close_prices[-20:]) if len(close_prices) >= 20 else close_prices[-1]
        )

        current_price = close_prices[-1]

        # 判断是否持有
        is_holding = stock_code in current_positions

        # 买入条件
        if prediction > 0.02 and not is_holding:
            if ma5 > ma20:
                reasons.append("LSTM预测上涨")
                reasons.append("MA5上穿MA20")
                confidence = min(abs(prediction) * 10, 0.9)
                return "buy", confidence, ", ".join(reasons)

        # 卖出条件
        if is_holding:
            position = current_positions[stock_code]
            entry_price = position.get("entry_price", current_price)
            pnl_ratio = (current_price - entry_price) / entry_price

            # 止盈
            if pnl_ratio > 0.15:
                reasons.append("达到止盈位")
                return "sell", 0.9, ", ".join(reasons)

            # 止损
            if pnl_ratio < -0.05:
                reasons.append("触发止损")
                return "sell", 0.95, ", ".join(reasons)

            # 预测下跌
            if prediction < -0.02:
                reasons.append("LSTM预测下跌")
                confidence = min(abs(prediction) * 10, 0.9)
                return "sell", confidence, ", ".join(reasons)

        return "hold", 0.0, "hold"

    def _calculate_position_size(
        self,
        signal_type: str,
        confidence: float,
        strategy_config: Dict,
        account_status: Optional[Dict],
    ) -> float:
        """计算仓位大小

        Args:
            signal_type: 信号类型
            confidence: 置信度
            strategy_config: 策略配置
            account_status: 账户状态

        Returns:
            仓位大小（比例）
        """
        if signal_type == "sell":
            return 1.0  # 卖出全部

        # 基础仓位
        base_position = strategy_config.get("max_position_per_stock", 0.2)

        # 根据置信度调整
        position_size = base_position * confidence

        # 限制最小仓位
        min_position = strategy_config.get("min_position_size", 0.05)
        position_size = max(position_size, min_position)

        return position_size

    def _calculate_risk_score(
        self, stock_data: pd.DataFrame, prediction: float
    ) -> float:
        """计算风险评分

        Args:
            stock_data: 股票数据
            prediction: 预测值

        Returns:
            风险评分 (0-1)
        """
        try:
            # 计算波动率
            returns = stock_data["close"].pct_change().dropna()
            volatility = returns.std()

            # 预测的不确定性
            prediction_uncertainty = abs(prediction)

            # 综合风险评分
            risk_score = min(volatility * 10 + prediction_uncertainty, 1.0)

            return risk_score

        except Exception:
            return 0.5  # 默认中等风险

    def _filter_signals(
        self, signals: List[TradingSignal], config: Dict
    ) -> List[TradingSignal]:
        """过滤信号

        Args:
            signals: 原始信号列表
            config: 策略配置

        Returns:
            过滤后的信号列表
        """
        filtered = []

        # 风险检查
        risk_check = self.manager.check_risk_limits(config["strategy_id"])

        if not risk_check["passed"]:
            LOGGER.warning(f"⚠️ 风险检查未通过，不生成新信号")
            LOGGER.warning(f"   违规项: {risk_check['violations']}")
            return []

        # 按置信度排序
        signals.sort(key=lambda x: x.confidence, reverse=True)

        # 限制信号数量
        max_signals = config.get("max_stocks", 10)

        for signal in signals[:max_signals]:
            # 过滤低置信度信号
            if signal.confidence < 0.5:
                continue

            # 过滤高风险信号
            if signal.risk_score > 0.8:
                LOGGER.warning(f"⚠️ 过滤高风险信号: {signal.stock_code}")
                continue

            filtered.append(signal)

        LOGGER.info(f"✅ 过滤后剩余 {len(filtered)} 个信号")

        return filtered

    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        stock_names = {
            "600519.SH": "贵州茅台",
            "600036.SH": "招商银行",
            "000858.SZ": "五粮液",
            "601318.SH": "中国平安",
            "000333.SZ": "美的集团",
            "600900.SH": "长江电力",
            "601888.SH": "中国中免",
            "000568.SZ": "泸州老窖",
        }

        return stock_names.get(stock_code, stock_code)


# CLI工具
if __name__ == "__main__":
    import sys

    generator = SignalGenerator()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python signal_generator.py generate <strategy_id>")
        print("  python signal_generator.py generate_all")
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        if len(sys.argv) < 3:
            print("❌ 缺少参数: strategy_id")
            sys.exit(1)

        strategy_id = sys.argv[2]
        signals = generator.generate_signals_for_strategy(strategy_id)

        print(f"\n📊 生成 {len(signals)} 个交易信号:\n")

        for signal in signals:
            print(
                f"{signal.signal_type.upper()}: {signal.stock_name} ({signal.stock_code})"
            )
            print(f"  当前价格: ¥{signal.current_price:.2f}")
            print(f"  建议仓位: {signal.position_size:.1%}")
            print(f"  置信度: {signal.confidence:.1%}")
            print(f"  理由: {signal.reason}")
            print()

    elif command == "generate_all":
        all_signals = generator.generate_signals_for_all_strategies()

        print(f"\n📊 为 {len(all_signals)} 个策略生成信号:\n")

        for strategy_id, signals in all_signals.items():
            print(f"策略: {strategy_id}")
            print(f"信号数量: {len(signals)}")
            print()

    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)
