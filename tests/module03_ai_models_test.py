#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 03 AI模型测试脚本

测试AI模型模块的各个组件，包括LSTM、Transformer、集成学习、在线学习和强化学习
与Module 01和Module 02集成测试
"""

import os
import sys
from datetime import datetime, timedelta

# 设置 Windows 控制台 UTF-8 编码支持
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

import numpy as np
import pandas as pd

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module_01_data_pipeline import AkshareDataCollector, get_database_manager
from module_02_feature_engineering import (
    TechnicalIndicators,
    calculate_technical_indicators,
    get_feature_database_manager,
)
from module_03_ai_models import (
    EnsembleConfig,
    EnsemblePredictor,
    LSTMModel,
    LSTMModelConfig,
    OnlineLearner,
    OnlineLearningConfig,
    PPOAgent,
    PPOConfig,
    RLAgent,
    RLConfig,
    TradingEnvironment,
    get_ai_model_database_manager,
)
from module_03_ai_models.utils import (
    create_lstm_predictor,
    evaluate_model_performance,
    prepare_features_for_training,
    train_ensemble_model,
)


def test_data_integration():
    """测试与Module 01和02的数据集成"""
    print("🔗 测试数据集成...")

    # 测试股票代码
    symbols = ["000001", "600036", "000858"]

    try:
        # 从Module 01获取数据
        collector = AkshareDataCollector(rate_limit=0.5)
        data_db = get_database_manager()

        for symbol in symbols[:1]:  # 只测试一只股票
            # 获取更多历史数据
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=180)).strftime(
                "%Y%m%d"
            )  # 增加到180天

            stock_data = collector.fetch_stock_history(symbol, start_date, end_date)
            if not stock_data.empty:
                print(f"✓ {symbol}: 获取了 {len(stock_data)} 条数据")

                # 计算技术指标
                calculator = TechnicalIndicators()
                indicators = calculator.calculate_all_indicators(stock_data)
                print(f"✓ {symbol}: 计算了 {indicators.shape[1]} 个技术指标")

                return indicators
            else:
                print(f"⚠️ {symbol}: 数据为空")

        return pd.DataFrame()

    except Exception as e:
        print(f"❌ 数据集成测试失败: {e}")
        return pd.DataFrame()


def test_lstm_model(features_data):
    """测试LSTM模型"""
    print("\n🧠 测试LSTM模型...")

    try:
        if features_data.empty:
            print("⚠️ 没有特征数据，跳过LSTM测试")
            return None

        # 创建LSTM配置
        config = LSTMModelConfig(
            sequence_length=5,  # 进一步减少序列长度以适应小数据集
            hidden_size=16,
            num_layers=1,
            dropout=0.1,
            learning_rate=0.001,
            batch_size=8,
            epochs=3,  # 减少训练轮数
        )

        # 创建LSTM模型
        lstm_model = LSTMModel(config)
        lstm_model.set_model_id("test_lstm_001")

        # 准备数据 - 只使用数值列
        numeric_columns = features_data.select_dtypes(include=[np.number]).columns
        features_data = features_data[numeric_columns]
        features_data["returns"] = features_data["close"].pct_change().fillna(0)
        clean_data = features_data.dropna()

        if len(clean_data) < config.sequence_length + 2:
            print(
                f"⚠️ 数据量不足，需要至少{config.sequence_length + 2}条记录，当前有{len(clean_data)}条"
            )
            return None

        # 准备训练数据
        X, y = lstm_model.prepare_data(clean_data, "returns")
        print(f"✓ 准备了训练数据: X{X.shape}, y{y.shape}")

        # 训练模型
        metrics = lstm_model.train(X, y)
        print(f"✓ LSTM训练完成: {metrics}")

        # 进行预测
        test_features = clean_data.drop(columns=["returns"]).values[
            -5:
        ]  # 使用最后5个样本
        predictions = lstm_model.predict(test_features)
        print(f"✓ LSTM预测完成: {len(predictions.predictions)} 个预测值")

        # 保存模型
        success = lstm_model.save_model("test_lstm_001")
        print(f"✓ LSTM模型保存: {'成功' if success else '失败'}")

        return lstm_model

    except Exception as e:
        print(f"❌ LSTM模型测试失败: {e}")
        return None


def test_ensemble_model(features_data):
    """测试集成模型"""
    print("\n🎯 测试集成模型...")

    try:
        if features_data.empty:
            print("⚠️ 没有特征数据，跳过集成模型测试")
            return None

        # 创建多个简单模型用于集成
        models = []

        # 简单线性模型1
        class SimpleLinearModel:
            def __init__(self, name):
                self.name = name
                self.weights = None

            def train(self, X, y):
                # 简单的线性回归
                self.weights = np.random.normal(0, 0.1, X.shape[1])
                return {"train_loss": 0.1, "val_loss": 0.12}

            def predict(self, X):
                if self.weights is None:
                    return np.random.normal(0, 0.01, len(X))
                return np.dot(X, self.weights)

        # 创建多个模型
        for i in range(3):
            model = SimpleLinearModel(f"linear_model_{i}")
            models.append({"name": f"model_{i}", "model": model, "weight": 1.0})

        # 创建集成模型
        config = EnsembleConfig(models=models, voting_strategy="weighted")

        ensemble = EnsemblePredictor(config)

        # 添加模型到集成
        for model_info in models:
            ensemble.add_model(
                name=model_info["name"],
                model=model_info["model"],
                weight=model_info["weight"],
            )

        # 准备数据
        features_data["returns"] = features_data["close"].pct_change().fillna(0)
        clean_data = features_data.dropna()

        if len(clean_data) < 10:
            print("⚠️ 数据量不足，跳过集成模型训练")
            return None

        # 只选择数值型列，避免timestamp类型错误
        numeric_columns = clean_data.select_dtypes(include=[np.number]).columns
        numeric_data = clean_data[numeric_columns].drop(columns=["returns"])

        X = numeric_data.values
        y = clean_data["returns"].values

        # 训练集成模型
        training_metrics = ensemble.train_ensemble(X, y)
        print(f"✓ 集成模型训练完成: {training_metrics}")

        # 进行预测
        predictions = ensemble.predict(X[-5:])  # 预测最后5个样本
        print(f"✓ 集成预测完成: 置信度={predictions.confidence:.3f}")

        return ensemble

    except Exception as e:
        print(f"❌ 集成模型测试失败: {e}")
        return None


def test_online_learning():
    """测试在线学习"""
    print("\n📊 测试在线学习...")

    try:
        # 创建在线学习配置
        config = OnlineLearningConfig(
            learning_rate=0.01, buffer_size=100, update_frequency=10, decay_rate=0.95
        )

        # 创建在线学习器
        online_learner = OnlineLearner(config)

        # 模拟数据流
        n_samples = 50
        feature_dim = 5

        print(f"✓ 开始模拟 {n_samples} 个样本的在线学习...")

        for i in range(n_samples):
            # 生成模拟特征和目标
            features = np.random.normal(0, 1, feature_dim)
            target = np.sum(
                features * np.array([0.5, -0.3, 0.2, 0.1, -0.1])
            ) + np.random.normal(0, 0.1)

            # 添加样本
            online_learner.add_sample(features, target)

            # 每10个样本进行一次预测
            if i % 10 == 9:
                result = online_learner.predict(features)
                print(
                    f"  样本 {i + 1}: 预测={result.prediction:.4f}, 置信度={result.confidence:.3f}"
                )

        # 获取最终状态
        final_state = online_learner.get_model_state()
        print(
            f"✓ 在线学习完成: 缓冲区大小={final_state['buffer_size']}, 更新次数={final_state['update_count']}"
        )

        return online_learner

    except Exception as e:
        print(f"❌ 在线学习测试失败: {e}")
        return None


def test_rl_agent():
    """测试强化学习智能体"""
    print("\n🤖 测试强化学习智能体...")

    try:
        # 创建RL配置
        config = RLConfig(learning_rate=0.01, discount_factor=0.95, epsilon=0.1)

        # 创建RL智能体
        rl_agent = RLAgent(config)

        # 模拟简单的交易环境
        for episode in range(5):
            print(f"  回合 {episode + 1}:")

            # 模拟状态
            state_features = np.random.normal(0, 1, 5)
            from module_03_ai_models.reinforcement_learning.rl_agent import RLState

            state = RLState(
                features=state_features,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                market_data={"price": 100.0 + np.random.normal(0, 2)},
            )

            # 选择动作
            action = rl_agent.choose_action(state)
            print(f"    动作: {action.action.name}, Q值: {action.q_value:.4f}")

            # 模拟奖励
            market_return = np.random.normal(0, 0.02)
            reward = rl_agent.calculate_reward(action, market_return)

            # 下一状态
            next_state_features = state_features + np.random.normal(0, 0.1, 5)
            next_state = RLState(
                features=next_state_features,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                market_data={"price": 100.0 + np.random.normal(0, 2)},
            )

            # 学习经验
            from module_03_ai_models.reinforcement_learning.rl_agent import RLExperience

            experience = RLExperience(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=False,
            )

            rl_agent.store_experience(experience)
            rl_agent.learn(experience)

            print(f"    奖励: {reward:.4f}")

        # 获取智能体统计
        stats = rl_agent.get_agent_stats()
        print(
            f"✓ RL智能体测试完成: Q表大小={stats['q_table_size']}, ε={stats['epsilon']:.3f}"
        )

        return rl_agent

    except Exception as e:
        print(f"❌ RL智能体测试失败: {e}")
        return None


def test_database_operations():
    """测试数据库操作"""
    print("\n💾 测试数据库操作...")

    try:
        # 获取数据库管理器
        db_manager = get_ai_model_database_manager()

        # 测试保存模型信息
        model_id = "test_model_001"
        success = db_manager.save_model_info(
            model_id=model_id,
            model_type="test",
            model_name="测试模型",
            config={"test": True},
        )
        print(f"✓ 保存模型信息: {'成功' if success else '失败'}")

        # 测试保存性能指标
        success = db_manager.save_model_performance(
            model_id=model_id, metric_name="test_accuracy", metric_value=0.85
        )
        print(f"✓ 保存性能指标: {'成功' if success else '失败'}")

        # 测试保存预测结果
        success = db_manager.save_model_prediction(
            model_id=model_id,
            symbol="000001",
            prediction_date="2024-12-01",
            prediction_value=0.05,
            confidence=0.8,
        )
        print(f"✓ 保存预测结果: {'成功' if success else '失败'}")

        # 测试查询数据
        predictions = db_manager.get_model_predictions(model_id)
        print(f"✓ 查询预测结果: {len(predictions)} 条记录")

        performance = db_manager.get_model_performance(model_id)
        print(f"✓ 查询性能指标: {len(performance)} 条记录")

        # 获取数据库统计
        stats = db_manager.get_database_stats()
        print(f"✓ 数据库统计: {stats}")

        return True

    except Exception as e:
        print(f"❌ 数据库操作测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始 Module 03 AI模型综合测试")
    print("=" * 60)

    # 测试结果收集
    results = {}

    # 1. 测试数据集成
    features_data = test_data_integration()
    results["data_integration"] = not features_data.empty

    # 2. 测试LSTM模型
    lstm_model = test_lstm_model(features_data)
    results["lstm_model"] = lstm_model is not None

    # 3. 测试集成模型
    ensemble_model = test_ensemble_model(features_data)
    results["ensemble_model"] = ensemble_model is not None

    # 4. 测试在线学习
    online_learner = test_online_learning()
    results["online_learning"] = online_learner is not None

    # 5. 测试强化学习
    rl_agent = test_rl_agent()
    results["rl_agent"] = rl_agent is not None

    # 6. 测试数据库操作
    db_success = test_database_operations()
    results["database_operations"] = db_success

    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 Module 03 测试总结:")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(results.values())

    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总计: {passed_tests}/{total_tests} 个测试通过")
    success_rate = (passed_tests / total_tests) * 100
    print(f"成功率: {success_rate:.1f}%")

    if success_rate >= 80:
        print("\n🎉 Module 03 AI模型模块测试基本通过！")
    else:
        print("\n⚠️ Module 03 存在一些问题需要修复")

    print("\n✨ Module 03 集成了深度学习、集成学习、在线学习和强化学习")
    print("✨ 支持与Module 01和Module 02的完整数据流集成")
    print("✨ 提供完整的模型生命周期管理和数据库存储")


if __name__ == "__main__":
    main()
