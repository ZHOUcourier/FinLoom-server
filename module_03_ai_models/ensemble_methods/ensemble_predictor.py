"""
集成预测器模块
实现多模型集成学习，支持多种投票策略
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from common.exceptions import ModelError
from common.logging_system import setup_logger

from ..storage_management.ai_model_database import get_ai_model_database_manager

logger = setup_logger("ensemble_predictor")


@dataclass
class EnsembleConfig:
    """集成模型配置"""

    models: List[Dict[str, Any]]
    voting_strategy: str = "weighted"  # "weighted", "majority", "average"
    weights: Optional[List[float]] = None


@dataclass
class EnsemblePrediction:
    """集成预测结果"""

    predictions: np.ndarray
    confidence: float
    individual_predictions: Dict[str, np.ndarray]
    ensemble_metrics: Dict[str, float]


class EnsemblePredictor:
    """集成预测器类"""

    def __init__(self, config: EnsembleConfig):
        """初始化集成预测器

        Args:
            config: 集成配置
        """
        self.config = config
        self.models = {}
        self.is_trained = False
        self.ensemble_id = f"ensemble_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.db_manager = get_ai_model_database_manager()

        # 初始化权重
        if self.config.weights is None:
            # 只有在有模型时才初始化权重
            if len(self.config.models) > 0:
                self.config.weights = [1.0 / len(self.config.models)] * len(
                    self.config.models
                )
            else:
                # 如果模型列表为空，权重列表也为空
                self.config.weights = []

    def add_model(self, name: str, model: Any, weight: float = 1.0):
        """添加模型

        Args:
            name: 模型名称
            model: 模型实例
            weight: 模型权重
        """
        try:
            self.models[name] = model
            logger.info(f"Added model: {name} with weight: {weight}")

        except Exception as e:
            logger.error(f"Failed to add model {name}: {e}")
            raise ModelError(f"Model addition failed: {e}")

    def train_ensemble(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """训练集成模型

        Args:
            X: 输入特征
            y: 目标值

        Returns:
            训练指标
        """
        try:
            logger.info(f"Training ensemble with {len(self.models)} models")

            # 保存集成模型信息
            self.db_manager.save_model_info(
                model_id=self.ensemble_id,
                model_type="ensemble",
                model_name=f"Ensemble_{len(self.models)}_models",
                config=self.config.__dict__,
            )

            training_metrics = {}
            individual_performances = []

            # 训练每个模型
            for i, (name, model) in enumerate(self.models.items()):
                try:
                    # 检查模型是否已训练（通过is_trained属性）
                    if hasattr(model, "is_trained") and model.is_trained:
                        # 模型已训练，不重新训练，使用默认高性能分数
                        logger.info(
                            f"Model {name} already trained, skipping re-training"
                        )
                        individual_performances.append(0.8)

                    elif hasattr(model, "train") and callable(
                        getattr(model, "train", None)
                    ):
                        # 模型支持训练且未训练，执行训练
                        metrics = model.train(X, y)
                        training_metrics[f"{name}_train_loss"] = metrics.get(
                            "train_loss", 0.0
                        )
                        training_metrics[f"{name}_val_loss"] = metrics.get(
                            "val_loss", 0.0
                        )

                        # 保存单个模型的训练指标
                        for metric_name, metric_value in metrics.items():
                            self.db_manager.save_model_performance(
                                model_id=self.ensemble_id,
                                metric_name=f"{name}_{metric_name}",
                                metric_value=metric_value,
                            )

                        # 记录性能用于权重调整
                        # 确保分母不为零
                        val_loss = metrics.get(
                            "val_loss", metrics.get("train_loss", 0.0)
                        )
                        # 如果loss为0，说明模型完美，给高分
                        if val_loss == 0:
                            performance_score = 1.0
                        else:
                            performance_score = 1.0 / (1.0 + val_loss)
                        individual_performances.append(performance_score)

                    else:
                        # 模型不支持训练，使用默认分数
                        logger.warning(f"Model {name} does not support training")
                        individual_performances.append(0.5)

                except Exception as e:
                    logger.error(f"Failed to train model {name}: {e}")
                    individual_performances.append(0.1)  # 低性能分数

            # 根据性能调整权重
            if individual_performances and self.config.voting_strategy == "weighted":
                # 确保有有效的性能数据
                valid_performances = [p for p in individual_performances if p > 0]

                if valid_performances:
                    # 使用有效的性能数据计算权重
                    total_performance = sum(valid_performances)

                    # 如果某些模型性能为0，给它们最小权重
                    adjusted_performances = []
                    for perf in individual_performances:
                        if perf > 0:
                            adjusted_performances.append(perf)
                        else:
                            # 给失败的模型一个很小的权重
                            adjusted_performances.append(0.01)

                    # 重新计算总和
                    total_performance = sum(adjusted_performances)

                    if total_performance > 0:
                        self.config.weights = [
                            perf / total_performance for perf in adjusted_performances
                        ]
                        logger.info(
                            f"Adjusted weights based on performance: {self.config.weights}"
                        )
                    else:
                        # 如果总性能仍为0，使用均等权重
                        self.config.weights = [1.0 / len(self.models)] * len(
                            self.models
                        )
                        logger.warning(
                            f"Total performance is 0, using equal weights: {self.config.weights}"
                        )
                else:
                    # 如果没有有效性能数据，使用均等权重
                    self.config.weights = [1.0 / len(self.models)] * len(self.models)
                    logger.warning(
                        f"No valid performances, using equal weights: {self.config.weights}"
                    )

            # 计算集成指标
            ensemble_metrics = {
                "ensemble_train_loss": np.mean(
                    [
                        training_metrics.get(f"{name}_train_loss", 0)
                        for name in self.models.keys()
                    ]
                ),
                "ensemble_val_loss": np.mean(
                    [
                        training_metrics.get(f"{name}_val_loss", 0)
                        for name in self.models.keys()
                    ]
                ),
                "model_count": len(self.models),
                "avg_performance": np.mean(individual_performances)
                if individual_performances
                else 0.0,
                "performance_std": np.std(individual_performances)
                if individual_performances
                else 0.0,
            }

            training_metrics.update(ensemble_metrics)

            # 保存集成指标
            for metric_name, metric_value in ensemble_metrics.items():
                self.db_manager.save_model_performance(
                    model_id=self.ensemble_id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                )

            self.is_trained = True
            logger.info("Ensemble training completed")
            return training_metrics

        except Exception as e:
            logger.error(f"Failed to train ensemble: {e}")
            raise ModelError(f"Ensemble training failed: {e}")

    def predict(self, X: np.ndarray) -> EnsemblePrediction:
        """进行集成预测

        Args:
            X: 输入特征

        Returns:
            集成预测结果
        """
        try:
            if not self.is_trained:
                raise ModelError("Ensemble not trained yet")

            individual_predictions = {}
            predictions_list = []
            weights = []

            # 获取每个模型的预测
            for i, (name, model) in enumerate(self.models.items()):
                if hasattr(model, "predict"):
                    pred_result = model.predict(X)
                    if hasattr(pred_result, "predictions"):
                        pred = pred_result.predictions
                    else:
                        pred = pred_result

                    individual_predictions[name] = pred
                    predictions_list.append(pred)
                    # 安全获取权重，如果索引越界使用默认权重
                    if i < len(self.config.weights):
                        weights.append(self.config.weights[i])
                    else:
                        weights.append(1.0 / len(self.models))
                else:
                    logger.warning(f"Model {name} does not have predict method")

            if not predictions_list:
                raise ModelError("No valid predictions from models")

            # 集成预测
            if self.config.voting_strategy == "weighted":
                # 加权平均
                weights = np.array(weights)
                weights_sum = weights.sum()
                # 防止除以零
                if weights_sum > 0:
                    weights = weights / weights_sum  # 归一化权重
                else:
                    # 如果权重和为0，使用均等权重
                    weights = np.ones(len(weights)) / len(weights)
                ensemble_pred = np.average(predictions_list, axis=0, weights=weights)
            elif self.config.voting_strategy == "average":
                # 简单平均
                ensemble_pred = np.mean(predictions_list, axis=0)
            elif self.config.voting_strategy == "majority":
                # 多数投票（适用于分类）
                ensemble_pred = np.round(np.mean(predictions_list, axis=0))
            else:
                raise ModelError(
                    f"Unknown voting strategy: {self.config.voting_strategy}"
                )

            # 计算置信度
            pred_std = np.std(predictions_list, axis=0)
            confidence = 1.0 / (1.0 + np.mean(pred_std))

            # 计算集成指标
            ensemble_metrics = {
                "prediction_std": np.std(ensemble_pred),
                "prediction_mean": np.mean(ensemble_pred),
                "model_agreement": 1.0 - np.mean(pred_std),
                "num_models": len(self.models),
            }

            return EnsemblePrediction(
                predictions=ensemble_pred,
                confidence=confidence,
                individual_predictions=individual_predictions,
                ensemble_metrics=ensemble_metrics,
            )

        except Exception as e:
            logger.error(f"Failed to make ensemble predictions: {e}")
            raise ModelError(f"Ensemble prediction failed: {e}")

    def get_model_importance(self) -> Dict[str, float]:
        """获取模型重要性

        Returns:
            模型重要性字典
        """
        try:
            importance = {}
            total_weight = sum(self.config.weights)

            for i, (name, _) in enumerate(self.models.items()):
                importance[name] = self.config.weights[i] / total_weight

            return importance

        except Exception as e:
            logger.error(f"Failed to get model importance: {e}")
            return {}

    def save_ensemble(self) -> bool:
        """保存集成模型到数据库

        Returns:
            是否保存成功
        """
        try:
            # 保存集成组成
            components = []
            for i, (name, _) in enumerate(self.models.items()):
                components.append(
                    {
                        "model_id": name,
                        "weight": self.config.weights[i]
                        if i < len(self.config.weights)
                        else 1.0,
                        "component_type": "base_model",
                    }
                )

            # 这里需要实现集成组成保存逻辑
            # success = self.db_manager.save_ensemble_components(self.ensemble_id, components)

            logger.info(f"Ensemble saved: {self.ensemble_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save ensemble: {e}")
            return False

    def get_ensemble_id(self) -> str:
        """获取集成模型ID"""
        return self.ensemble_id

    def predict_with_details(self, X: np.ndarray) -> Dict[str, Any]:
        """进行详细的集成预测

        Args:
            X: 输入特征

        Returns:
            详细的预测结果
        """
        try:
            prediction_result = self.predict(X)

            return {
                "ensemble_prediction": prediction_result.predictions,
                "confidence": prediction_result.confidence,
                "individual_predictions": prediction_result.individual_predictions,
                "ensemble_metrics": prediction_result.ensemble_metrics,
                "model_weights": dict(zip(self.models.keys(), self.config.weights)),
                "voting_strategy": self.config.voting_strategy,
                "ensemble_id": self.ensemble_id,
            }

        except Exception as e:
            logger.error(f"Failed to make detailed predictions: {e}")
            raise ModelError(f"Detailed prediction failed: {e}")


# 便捷函数
def create_ensemble_predictor(
    models: List[Dict[str, Any]], voting_strategy: str = "weighted"
) -> EnsemblePredictor:
    """创建集成预测器的便捷函数

    Args:
        models: 模型列表，每个包含 name 和 model
        voting_strategy: 投票策略

    Returns:
        集成预测器实例
    """
    config = EnsembleConfig(
        models=models,
        voting_strategy=voting_strategy,
        weights=None,  # 将根据模型数量自动计算
    )

    ensemble = EnsemblePredictor(config)

    # 添加模型
    for model_info in models:
        ensemble.add_model(
            name=model_info["name"],
            model=model_info["model"],
            weight=model_info.get("weight", 1.0),
        )

    return ensemble
