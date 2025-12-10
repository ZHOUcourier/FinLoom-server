"""
优化管理器模块
统一管理和协调各种优化任务
"""

import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from common.logging_system import setup_logger
from module_07_optimization.base_optimizer import OptimizationResult, Parameter
from module_07_optimization.hyperparameter_tuning.bayesian_optimizer import (
    BayesianOptimizer,
)
from module_07_optimization.hyperparameter_tuning.optuna_optimizer import (
    OptunaOptimizer,
)
from module_07_optimization.multi_objective_opt.nsga_optimizer import NSGAOptimizer
from module_07_optimization.strategy_optimization.strategy_optimizer import (
    StrategyOptimizer,
)

logger = setup_logger("optimization_manager")


class OptimizationManager:
    """优化管理器

    提供统一的优化接口和管理功能
    """

    def __init__(
        self, workspace_dir: str = None
    ):
        """初始化优化管理器

        Args:
            workspace_dir: 工作空间目录
        """
        if workspace_dir is None:
            workspace_dir = os.path.join("module_07_optimization", "optimization_workspace")
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # 优化历史
        self.optimization_history: List[Dict[str, Any]] = []
        self.load_history()

    def create_optimization_task(
        self,
        task_name: str,
        optimizer_type: str,
        parameter_space: List[Parameter],
        objective_function: Any,
        **kwargs,
    ) -> str:
        """创建优化任务

        Args:
            task_name: 任务名称
            optimizer_type: 优化器类型
            parameter_space: 参数空间
            objective_function: 目标函数
            **kwargs: 额外参数

        Returns:
            任务ID
        """
        task_id = f"{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建任务目录
        task_dir = self.workspace_dir / task_id
        task_dir.mkdir(exist_ok=True)

        # 保存任务配置
        task_config = {
            "task_id": task_id,
            "task_name": task_name,
            "optimizer_type": optimizer_type,
            "parameter_space": [p.__dict__ for p in parameter_space],
            "kwargs": kwargs,
            "created_at": datetime.now().isoformat(),
        }

        with open(task_dir / "config.json", "w") as f:
            json.dump(task_config, f, indent=2)

        logger.info(f"Created optimization task: {task_id}")
        return task_id

    def run_optimization(
        self,
        task_id: str,
        optimizer_type: str,
        parameter_space: List[Parameter],
        objective_function: Any,
        n_trials: int = 100,
        **kwargs,
    ) -> Union[OptimizationResult, Dict[str, Any]]:
        """运行优化任务

        Args:
            task_id: 任务ID
            optimizer_type: 优化器类型
            parameter_space: 参数空间
            objective_function: 目标函数
            n_trials: 试验次数
            **kwargs: 额外参数

        Returns:
            优化结果
        """
        logger.info(f"Running optimization task: {task_id}")

        # 选择优化器
        if optimizer_type == "bayesian":
            optimizer = BayesianOptimizer(
                parameter_space=parameter_space,
                objective_function=objective_function,
                n_trials=n_trials,
                **kwargs,
            )
            result = optimizer.optimize()

        elif optimizer_type == "optuna":
            optimizer = OptunaOptimizer(
                parameter_space=parameter_space,
                objective_function=objective_function,
                n_trials=n_trials,
                **kwargs,
            )
            result = optimizer.optimize()

        elif optimizer_type == "nsga":
            # 多目标优化需要多个目标函数
            objective_functions = kwargs.pop(
                "objective_functions", [objective_function]
            )
            optimizer = NSGAOptimizer(
                parameter_space=parameter_space,
                objective_functions=objective_functions,
                **kwargs,
            )
            result = optimizer.optimize()

        elif optimizer_type == "random":
            from module_07_optimization.hyperparameter_tuning.random_search import (
                RandomSearchOptimizer,
            )

            optimizer = RandomSearchOptimizer(
                parameter_space=parameter_space,
                objective_function=objective_function,
                n_trials=n_trials,
                **kwargs,
            )
            result = optimizer.optimize()

        else:
            raise ValueError(f"Unknown optimizer type: {optimizer_type}")

        # 保存结果
        self.save_result(task_id, result)

        # 更新历史
        self.optimization_history.append(
            {
                "task_id": task_id,
                "optimizer_type": optimizer_type,
                "completed_at": datetime.now().isoformat(),
                "n_trials": n_trials,
                "best_value": result.best_value
                if hasattr(result, "best_value")
                else None,
            }
        )
        self.save_history()

        logger.info(f"Optimization task completed: {task_id}")
        return result

    def save_result(
        self, task_id: str, result: Union[OptimizationResult, Dict[str, Any]]
    ) -> None:
        """保存优化结果

        Args:
            task_id: 任务ID
            result: 优化结果
        """
        task_dir = self.workspace_dir / task_id
        task_dir.mkdir(exist_ok=True)

        # 保存pickle格式
        with open(task_dir / "result.pkl", "wb") as f:
            pickle.dump(result, f)

        # 保存JSON格式（如果可能）
        try:
            if isinstance(result, OptimizationResult):
                result_dict = {
                    "optimization_id": result.optimization_id,
                    "best_parameters": result.best_parameters,
                    "best_value": result.best_value,
                    "n_trials": result.n_trials,
                    "n_successful_trials": result.n_successful_trials,
                    "total_time_seconds": result.total_time_seconds,
                    "convergence_history": result.convergence_history,
                    "metadata": result.metadata,
                }
            else:
                result_dict = result

            with open(task_dir / "result.json", "w") as f:
                json.dump(result_dict, f, indent=2, default=str)

        except Exception as e:
            logger.warning(f"Could not save JSON format: {e}")

    def load_result(self, task_id: str) -> Union[OptimizationResult, Dict[str, Any]]:
        """加载优化结果

        Args:
            task_id: 任务ID

        Returns:
            优化结果
        """
        task_dir = self.workspace_dir / task_id
        result_file = task_dir / "result.pkl"

        if not result_file.exists():
            raise FileNotFoundError(f"Result not found for task: {task_id}")

        with open(result_file, "rb") as f:
            return pickle.load(f)

    def compare_results(self, task_ids: List[str]) -> pd.DataFrame:
        """比较多个优化结果

        Args:
            task_ids: 任务ID列表

        Returns:
            比较结果DataFrame
        """
        comparison_data = []

        for task_id in task_ids:
            try:
                result = self.load_result(task_id)

                if isinstance(result, OptimizationResult):
                    data = {
                        "task_id": task_id,
                        "best_value": result.best_value,
                        "n_trials": result.n_trials,
                        "n_successful_trials": result.n_successful_trials,
                        "total_time_seconds": result.total_time_seconds,
                        "best_parameters": str(result.best_parameters),
                    }
                else:
                    data = {
                        "task_id": task_id,
                        "type": "multi_objective",
                        "pareto_front_size": len(result.get("pareto_front", [])),
                    }

                comparison_data.append(data)

            except Exception as e:
                logger.error(f"Failed to load result for {task_id}: {e}")

        return pd.DataFrame(comparison_data)

    def get_best_parameters(self, task_id: str) -> Dict[str, Any]:
        """获取最佳参数

        Args:
            task_id: 任务ID

        Returns:
            最佳参数
        """
        result = self.load_result(task_id)

        if isinstance(result, OptimizationResult):
            return result.best_parameters
        elif isinstance(result, dict) and "pareto_front" in result:
            # 多目标优化，返回第一个Pareto解
            if result["pareto_front"]:
                return result["pareto_front"][0]["parameters"]
        elif isinstance(result, dict) and "best_parameters" in result:
            return result["best_parameters"]

        return {}

    def save_history(self) -> None:
        """保存优化历史"""
        history_file = self.workspace_dir / "optimization_history.json"
        with open(history_file, "w") as f:
            json.dump(self.optimization_history, f, indent=2, default=str)

    def load_history(self) -> None:
        """加载优化历史"""
        history_file = self.workspace_dir / "optimization_history.json"
        if history_file.exists():
            with open(history_file, "r") as f:
                self.optimization_history = json.load(f)
        else:
            self.optimization_history = []

    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有优化任务

        Returns:
            任务列表
        """
        tasks = []

        for task_dir in self.workspace_dir.iterdir():
            if task_dir.is_dir() and (task_dir / "config.json").exists():
                with open(task_dir / "config.json", "r") as f:
                    config = json.load(f)

                # 检查是否有结果
                has_result = (task_dir / "result.pkl").exists()
                config["has_result"] = has_result

                tasks.append(config)

        return sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)

    def clean_old_tasks(self, days: int = 30) -> int:
        """清理旧任务

        Args:
            days: 保留天数

        Returns:
            清理的任务数
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0

        for task_dir in self.workspace_dir.iterdir():
            if task_dir.is_dir():
                config_file = task_dir / "config.json"
                if config_file.exists():
                    with open(config_file, "r") as f:
                        config = json.load(f)

                    created_at = datetime.fromisoformat(config.get("created_at", ""))
                    if created_at < cutoff_date:
                        # 删除任务目录
                        import shutil

                        shutil.rmtree(task_dir)
                        cleaned_count += 1
                        logger.info(f"Cleaned old task: {task_dir.name}")

        logger.info(f"Cleaned {cleaned_count} old tasks")
        return cleaned_count


# 全局优化管理器实例
_global_manager: Optional[OptimizationManager] = None


def get_optimization_manager() -> OptimizationManager:
    """获取全局优化管理器实例

    Returns:
        优化管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = OptimizationManager()
    return _global_manager
