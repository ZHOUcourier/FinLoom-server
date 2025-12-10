"""
贝叶斯优化器 - 用于策略参数优化
使用贝叶斯优化自动寻找最优参数组合
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from common.logging_system import setup_logger

LOGGER = setup_logger("bayesian_optimizer")


@dataclass
class OptimizationResult:
    """优化结果"""

    best_params: Dict[str, float]
    best_score: float
    iterations: int
    param_history: List[Dict[str, float]]
    score_history: List[float]
    convergence_reached: bool


class BayesianOptimizer:
    """贝叶斯优化器

    使用高斯过程回归和采集函数自动寻找最优参数
    比网格搜索更高效，比随机搜索更准确
    """

    def __init__(
        self,
        param_bounds: Dict[str, Tuple[float, float]],
        n_initial_points: int = 5,
        n_iterations: int = 25,
        acquisition: str = "ei",  # ei/ucb/poi
        random_state: Optional[int] = None,
    ):
        """初始化贝叶斯优化器

        Args:
            param_bounds: 参数边界 {'param_name': (min, max)}
            n_initial_points: 初始随机采样点数
            n_iterations: 优化迭代次数
            acquisition: 采集函数类型
            random_state: 随机种子
        """
        self.param_bounds = param_bounds
        self.param_names = list(param_bounds.keys())
        self.bounds_array = np.array([param_bounds[name] for name in self.param_names])

        self.n_initial_points = n_initial_points
        self.n_iterations = n_iterations
        self.acquisition = acquisition
        self.random_state = random_state

        # 高斯过程模型
        kernel = Matern(nu=2.5)
        self.gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=random_state,
        )

        # 历史记录
        self.X_observed: List[np.ndarray] = []
        self.y_observed: List[float] = []

        LOGGER.info(f"📊 贝叶斯优化器初始化: {len(self.param_names)}个参数")

    def optimize(
        self,
        objective_function: Callable[[Dict[str, float]], float],
        maximize: bool = True,
        verbose: bool = True,
    ) -> OptimizationResult:
        """执行贝叶斯优化

        Args:
            objective_function: 目标函数，接受参数字典，返回评分
            maximize: True=最大化，False=最小化
            verbose: 是否打印进度

        Returns:
            优化结果
        """
        try:
            np.random.seed(self.random_state)

            LOGGER.info(f"🚀 开始贝叶斯优化: {self.n_iterations}次迭代")

            # 阶段1: 随机初始化
            if verbose:
                print(f"\n阶段1: 随机初始化 ({self.n_initial_points}个点)")

            for i in range(self.n_initial_points):
                # 随机采样
                x = self._random_sample()
                params = self._array_to_params(x)

                # 评估
                score = objective_function(params)
                if not maximize:
                    score = -score  # 内部统一为最大化

                self.X_observed.append(x)
                self.y_observed.append(score)

                if verbose:
                    print(f"  第{i + 1}次: 参数={params}, 评分={score:.4f}")

            # 阶段2: 贝叶斯优化
            if verbose:
                print(f"\n阶段2: 贝叶斯优化 ({self.n_iterations}次迭代)")

            for i in range(self.n_iterations):
                # 拟合高斯过程
                self.gp.fit(np.array(self.X_observed), np.array(self.y_observed))

                # 选择下一个采样点
                x_next = self._propose_location()
                params_next = self._array_to_params(x_next)

                # 评估
                score_next = objective_function(params_next)
                if not maximize:
                    score_next = -score_next

                # 记录
                self.X_observed.append(x_next)
                self.y_observed.append(score_next)

                # 当前最佳
                best_idx = np.argmax(self.y_observed)
                best_score = self.y_observed[best_idx]
                best_params = self._array_to_params(self.X_observed[best_idx])

                if verbose:
                    print(
                        f"  第{i + 1}次: "
                        f"参数={params_next}, "
                        f"评分={score_next:.4f}, "
                        f"当前最佳={best_score:.4f}"
                    )

            # 整理结果
            best_idx = np.argmax(self.y_observed)
            best_score_final = self.y_observed[best_idx]
            best_params_final = self._array_to_params(self.X_observed[best_idx])

            if not maximize:
                best_score_final = -best_score_final
                y_observed_display = [-y for y in self.y_observed]
            else:
                y_observed_display = self.y_observed.copy()

            result = OptimizationResult(
                best_params=best_params_final,
                best_score=best_score_final,
                iterations=len(self.X_observed),
                param_history=[self._array_to_params(x) for x in self.X_observed],
                score_history=y_observed_display,
                convergence_reached=self._check_convergence(),
            )

            LOGGER.info(f"✅ 优化完成: 最佳评分={best_score_final:.4f}")
            LOGGER.info(f"   最佳参数: {best_params_final}")

            return result

        except Exception as e:
            LOGGER.error(f"❌ 贝叶斯优化失败: {e}", exc_info=True)
            raise

    def _random_sample(self) -> np.ndarray:
        """随机采样一个参数点"""
        x = np.random.uniform(self.bounds_array[:, 0], self.bounds_array[:, 1])
        return x

    def _array_to_params(self, x: np.ndarray) -> Dict[str, float]:
        """将数组转换为参数字典"""
        return {name: float(x[i]) for i, name in enumerate(self.param_names)}

    def _params_to_array(self, params: Dict[str, float]) -> np.ndarray:
        """将参数字典转换为数组"""
        return np.array([params[name] for name in self.param_names])

    def _propose_location(self) -> np.ndarray:
        """提出下一个采样点"""

        # 定义采集函数
        def acquisition_function(x):
            x = x.reshape(1, -1)

            # 预测均值和标准差
            mu, sigma = self.gp.predict(x, return_std=True)
            mu = mu[0]
            sigma = sigma[0]

            # 当前最佳值
            mu_best = np.max(self.y_observed)

            if self.acquisition == "ei":
                # Expected Improvement (期望改进)
                with np.errstate(divide="warn"):
                    imp = mu - mu_best
                    Z = imp / sigma if sigma > 0 else 0
                    ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z) if sigma > 0 else 0
                return -ei  # minimize会最小化，所以取负

            elif self.acquisition == "ucb":
                # Upper Confidence Bound (置信上界)
                kappa = 2.0  # 探索-利用权衡参数
                ucb = mu + kappa * sigma
                return -ucb

            elif self.acquisition == "poi":
                # Probability of Improvement (改进概率)
                xi = 0.01  # 探索参数
                with np.errstate(divide="warn"):
                    imp = mu - mu_best - xi
                    Z = imp / sigma if sigma > 0 else 0
                    poi = norm.cdf(Z) if sigma > 0 else 0
                return -poi

            else:
                raise ValueError(f"未知的采集函数: {self.acquisition}")

        # 多起点优化采集函数
        x_tries = np.random.uniform(
            self.bounds_array[:, 0],
            self.bounds_array[:, 1],
            size=(100, len(self.param_names)),
        )

        ys = [acquisition_function(x) for x in x_tries]
        x_best = x_tries[np.argmin(ys)]

        # 优化
        res = minimize(
            acquisition_function, x0=x_best, bounds=self.bounds_array, method="L-BFGS-B"
        )

        return res.x

    def _check_convergence(self, window: int = 5, threshold: float = 1e-4) -> bool:
        """检查是否收敛

        Args:
            window: 检查最近N次迭代
            threshold: 收敛阈值

        Returns:
            是否收敛
        """
        if len(self.y_observed) < window:
            return False

        recent_scores = self.y_observed[-window:]
        score_range = max(recent_scores) - min(recent_scores)

        return score_range < threshold

    def predict(self, params: Dict[str, float]) -> Tuple[float, float]:
        """预测给定参数的评分（均值和标准差）

        Args:
            params: 参数字典

        Returns:
            (均值, 标准差)
        """
        if not self.X_observed:
            raise ValueError("尚未进行任何观测")

        x = self._params_to_array(params).reshape(1, -1)
        mu, sigma = self.gp.predict(x, return_std=True)

        return float(mu[0]), float(sigma[0])

    def get_importance_scores(self) -> Dict[str, float]:
        """计算参数重要性评分

        通过分析参数对目标函数的影响来评估重要性

        Returns:
            参数重要性字典
        """
        if len(self.X_observed) < 10:
            LOGGER.warning("⚠️ 观测点过少，重要性评分可能不准确")

        importance = {}

        X = np.array(self.X_observed)
        y = np.array(self.y_observed)

        for i, param_name in enumerate(self.param_names):
            # 计算该参数与目标函数的相关性
            correlation = np.corrcoef(X[:, i], y)[0, 1]
            importance[param_name] = abs(correlation)

        # 归一化
        total = sum(importance.values())
        if total > 0:
            importance = {k: v / total for k, v in importance.items()}

        return importance


def optimize_strategy_params(
    backtest_function: Callable[[Dict], float],
    param_ranges: Dict[str, Tuple[float, float]],
    metric: str = "sharpe_ratio",
    n_iterations: int = 25,
) -> OptimizationResult:
    """优化策略参数的便捷函数

    Args:
        backtest_function: 回测函数，接受参数返回回测结果
        param_ranges: 参数范围
        metric: 优化指标
        n_iterations: 迭代次数

    Returns:
        优化结果
    """

    def objective(params: Dict[str, float]) -> float:
        """目标函数"""
        result = backtest_function(params)
        return result.get(metric, 0.0)

    optimizer = BayesianOptimizer(param_bounds=param_ranges, n_iterations=n_iterations)

    return optimizer.optimize(objective, maximize=True)


# 示例用法
if __name__ == "__main__":
    # 示例：优化LSTM策略参数
    def mock_backtest(params: Dict[str, float]) -> float:
        """模拟回测函数"""
        # 假设夏普比率与参数的关系
        sharpe = (
            1.5
            - 0.1 * (params["stop_loss"] + 0.05) ** 2
            + 0.05 * np.log(params["ma_period"] / 10)
            - 0.02 * (params["lstm_hidden"] - 128) ** 2 / 10000
        )
        # 添加噪声
        sharpe += np.random.normal(0, 0.1)
        return sharpe

    # 定义参数范围
    param_bounds = {
        "stop_loss": (-0.10, -0.02),  # 止损 -10% 到 -2%
        "ma_period": (5, 60),  # 移动平均周期
        "lstm_hidden": (64, 256),  # LSTM隐藏层大小
    }

    # 执行优化
    optimizer = BayesianOptimizer(param_bounds, n_iterations=20)
    result = optimizer.optimize(mock_backtest, maximize=True, verbose=True)

    print("\n" + "=" * 60)
    print("优化完成！")
    print(f"最佳参数: {result.best_params}")
    print(f"最佳评分: {result.best_score:.4f}")
    print(f"迭代次数: {result.iterations}")
    print(f"是否收敛: {result.convergence_reached}")

    # 参数重要性
    importance = optimizer.get_importance_scores()
    print("\n参数重要性:")
    for param, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {param}: {score:.3f}")
