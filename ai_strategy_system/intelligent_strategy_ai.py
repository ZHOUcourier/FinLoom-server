#!/usr/bin/env python3
"""High-level CLI orchestrator for the FinLoom intelligent strategy workflow."""

from __future__ import annotations

import asyncio
import inspect
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional


def _ensure_repo_path() -> None:
    """Ensure the repository root is on sys.path for module resolution."""

    module_path = Path(__file__).resolve()
    candidates = {module_path.parent, module_path.parent.parent}
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


_ensure_repo_path()

from ai_strategy_system.core.strategy_workflow import (  # noqa: E402
    StrategyWorkflow,
    StrategyWorkflowResult,
)
from common.logging_system import setup_logger  # noqa: E402

LOGGER = setup_logger("intelligent_strategy_ai")

ProgressCallback = Callable[[int, str, str], Optional[Awaitable[None]]]


class IntelligentStrategyAI:
    """Command-style wrapper that executes the full intelligent workflow."""

    def __init__(
        self,
        user_requirement: Optional[str] = None,
        initial_capital: float = 1_000_000.0,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        self.user_requirement = user_requirement or "中等风险，追求稳健收益"
        self.initial_capital = initial_capital
        self.workflow = StrategyWorkflow()
        self._progress_callback = progress_callback

        self.requirement_context = None
        self.market_context = None
        self.universe = None
        self.feature_bundle = None
        self.model_choice = None
        self.trained_model = None
        self.strategy_params = None
        self.portfolio_plan = None
        self.execution_plan = None
        self.backtest_summary = None
        self.workflow_result: Optional[StrategyWorkflowResult] = None

        self.recommended_stocks: List[str] = []
        self.selected_model_type: Optional[str] = None
        self.selected_model_config: Dict[str, Any] = {}
        self.selected_model_reason: Optional[str] = None
        self.backtest_id: Optional[str] = None

        LOGGER.info("=" * 60)
        LOGGER.info("🤖 智能策略AI系统初始化")
        LOGGER.info("=" * 60)
        LOGGER.info(f"用户需求: {self.user_requirement}")
        LOGGER.info(f"初始资金: ¥{self.initial_capital:,.0f}")

    async def _notify_progress(
        self, step_index: int, step_name: str, status: str
    ) -> None:
        if not self._progress_callback:
            return
        try:
            result = self._progress_callback(step_index, step_name, status)
            if inspect.isawaitable(result):
                await result  # type: ignore[arg-type]
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("Progress callback failed for step %s: %s", step_name, exc)

    async def step1_understand_requirement(self) -> bool:
        LOGGER.info("\n" + "=" * 60)
        LOGGER.info("步骤1: AI理解用户需求 (Module 10 - NLP)")
        LOGGER.info("=" * 60)
        try:
            self.requirement_context = await self.workflow.requirement_service.process(
                self.user_requirement
            )
            parsed = self.requirement_context.parsed_requirement
            system_params = self.requirement_context.system_params

            investment_amount = getattr(parsed, "investment_amount", None)
            if investment_amount:
                LOGGER.info(f"✓ 投资金额: ¥{investment_amount:,.0f}")
            risk_tolerance = getattr(parsed, "risk_tolerance", None)
            if risk_tolerance:
                LOGGER.info(f"✓ 风险偏好: {risk_tolerance}")
            horizon = getattr(parsed, "investment_horizon", None)
            if horizon:
                LOGGER.info(f"✓ 投资期限: {horizon}")
            goals = getattr(parsed, "goals", None)
            if goals:
                LOGGER.info(f"✓ 投资目标: {', '.join(goal.value for goal in goals)}")

            if system_params:
                LOGGER.info(f"✓ 系统参数映射完成: {', '.join(system_params.keys())}")

            if self.requirement_context.portfolio_recommendations:
                best = self.requirement_context.portfolio_recommendations[0]
                LOGGER.info(
                    f"推荐组合: {best.name} (适配度 {best.suitability_score:.2f})"
                )

            explanation = self.requirement_context.explanation
            if explanation:
                LOGGER.info(f"AI解释:\n{explanation}")
            return True
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(f"✗ 需求解析失败: {exc}")
            return False

    async def step2_analyze_market(self) -> bool:
        LOGGER.info("\n" + "=" * 60)
        LOGGER.info("步骤2: AI分析市场状态 (Module 04 - 多维分析)")
        LOGGER.info("=" * 60)
        try:
            self.market_context = await self.workflow.market_service.analyse()
            regime_state = self.market_context.regime.get("state")
            regime_conf = self.market_context.regime.get("confidence")
            sentiment_score = self.market_context.sentiment.get("score")
            sentiment_conf = self.market_context.sentiment.get("confidence")

            LOGGER.info(f"✓ 市场状态: {regime_state} (置信度 {regime_conf or 0.0:.2f})")
            LOGGER.info(
                f"✓ 市场情感: {sentiment_score or 0.0:.2f} (置信度 {sentiment_conf or 0.0:.2f})"
            )
            LOGGER.info(f"数据来源: {self.market_context.data_sources}")
            return True
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(f"✗ 市场分析失败: {exc}")
            return False

    async def step3_ai_select_stocks(self) -> bool:
        LOGGER.info("\n" + "=" * 60)
        LOGGER.info("步骤3: AI智能选股 (Module 10 - 推荐引擎)")
        LOGGER.info("=" * 60)
        try:
            if not self.requirement_context or not self.market_context:
                raise RuntimeError("前置步骤未完成")

            self.universe = await self.workflow.universe_service.build_universe(
                self.requirement_context,
                self.market_context,
            )
            self.recommended_stocks = list(self.universe.symbols)
            LOGGER.info(
                f"✓ 入选股票池 ({len(self.recommended_stocks)}只): {', '.join(self.recommended_stocks)}"
            )
            LOGGER.info(f"选股依据: {self.universe.rationale}")
            return True
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(f"✗ AI选股失败: {exc}")
            return False

    async def step4_ai_select_model(self) -> bool:
        LOGGER.info("\n" + "=" * 60)
        LOGGER.info("步骤4: AI自动选择最优模型 (Module 03)")
        LOGGER.info("=" * 60)
        try:
            if not self.market_context:
                raise RuntimeError("市场上下文不可用")
            self.model_choice = self.workflow.model_service.select_model(
                self.market_context
            )
            self.selected_model_type = self.model_choice.model_type
            self.selected_model_config = self.model_choice.config
            self.selected_model_reason = self.model_choice.reason
            LOGGER.info(f"✓ 选择模型: {self.selected_model_type.upper()}")
            LOGGER.info(f"  原因: {self.selected_model_reason}")
            LOGGER.info(f"  配置: {self.selected_model_config}")
            return True
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(f"✗ 模型选择失败: {exc}")
            return False

    async def step5_train_selected_model(self) -> bool:
        LOGGER.info("\n" + "=" * 60)
        LOGGER.info("步骤5: 准备特征并训练模型")
        LOGGER.info("=" * 60)
        try:
            if not self.universe or not self.model_choice:
                raise RuntimeError("缺少模型或股票池信息")

            LOGGER.info("  >>> 开始特征准备...")
            self.feature_bundle = await self.workflow.feature_service.prepare(
                self.universe
            )
            LOGGER.info(
                f"✓ 特征数据量: {len(self.feature_bundle.combined_features)} 条"
            )

            LOGGER.info("  >>> 开始模型训练...")
            self.trained_model = await self.workflow.model_service.train_model(
                self.model_choice,
                self.feature_bundle,
            )
            LOGGER.info("✓ 模型训练完成")
            LOGGER.info(f"  训练摘要: {self.trained_model.training_metadata}")
            return True
        except ZeroDivisionError as zde:
            LOGGER.error(f"✗ 模型训练失败（除零错误）: {zde}", exc_info=True)
            return False
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(f"✗ 模型训练失败: {exc}", exc_info=True)
            return False

    async def step6_generate_strategy(self) -> bool:
        LOGGER.info("\n" + "=" * 60)
        LOGGER.info("步骤6: 生成交易策略与执行计划")
        LOGGER.info("=" * 60)
        try:
            if (
                not self.market_context
                or not self.feature_bundle
                or not self.trained_model
            ):
                raise RuntimeError("策略生成缺乏必要上下文")

            self.strategy_params = self.workflow.strategy_service.build_parameters(
                self.market_context
            )
            LOGGER.info(
                "✓ 策略参数: buy_threshold=%.3f, confidence_threshold=%.2f, max_position=%.2f",
                self.strategy_params.buy_threshold,
                self.strategy_params.confidence_threshold,
                self.strategy_params.max_position,
            )

            self.portfolio_plan = self.workflow.portfolio_service.construct_portfolio(
                self.feature_bundle,
                self.strategy_params,
                self.initial_capital,
            )
            LOGGER.info(f"✓ 组合权重: {self.portfolio_plan.weights}")
            LOGGER.info(f"  风险指标: {self.portfolio_plan.risk_metrics}")

            self.execution_plan = self.workflow.execution_service.build_plan(
                self.portfolio_plan,
                self.feature_bundle,
                self.strategy_params,
                self.initial_capital,
            )
            LOGGER.info(
                "✓ 执行计划(%d单): %s",
                len(self.execution_plan.orders),
                self.execution_plan.algorithm,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("✗ 策略生成失败: {}", exc)
            return False

    async def step7_run_backtest(self) -> bool:
        """步骤7: 运行智能回测 (Module 09)

        注意：这个方法现在主要用于向后兼容，新的流程应该使用 run_backtest() 方法
        """
        LOGGER.info("\n" + "=" * 60)
        LOGGER.info("步骤7: 运行智能回测 (Module 09)")
        LOGGER.info("=" * 60)
        return await self.run_backtest()

    async def run_backtest(self, progress_callback=None) -> bool:
        """独立执行回测（在策略生成完成后）

        Args:
            progress_callback: 进度回调函数 async def callback(current: int, total: int, message: str)

        Returns:
            bool: 回测是否成功
        """
        if not self.feature_bundle or not self.trained_model:
            LOGGER.error("缺少必要的数据或模型，无法执行回测")
            return False

        try:
            # 尝试从需求上下文中获取回测日期
            start_date = None
            end_date = None
            if self.requirement_context and hasattr(
                self.requirement_context, "system_params"
            ):
                sys_params = self.requirement_context.system_params
                start_date = sys_params.get("backtest_start_date") or sys_params.get(
                    "start_date"
                )
                end_date = sys_params.get("backtest_end_date") or sys_params.get(
                    "end_date"
                )
                if start_date and end_date:
                    LOGGER.info(
                        f"📅 使用需求中的回测日期: {start_date.date() if hasattr(start_date, 'date') else start_date} 至 {end_date.date() if hasattr(end_date, 'date') else end_date}"
                    )

            self.backtest_summary = await self.workflow.backtest_service.run_backtest(
                feature_bundle=self.feature_bundle,
                execution_plan=self.execution_plan,
                trained_model=self.trained_model,
                strategy_params=self.strategy_params,
                initial_capital=self.initial_capital,
                start_date=start_date,
                end_date=end_date,
                progress_callback=progress_callback,
            )
            result = self.backtest_summary.result
            self.backtest_id = self.backtest_summary.backtest_id
            LOGGER.info("✓ 回测完成")
            LOGGER.info(f"  总收益率: {result.total_return * 100:.2f}%")
            LOGGER.info(f"  年化收益率: {result.annualized_return * 100:.2f}%")
            LOGGER.info(f"  夏普比率: {result.sharpe_ratio:.3f}")
            LOGGER.info(f"  最大回撤: {result.max_drawdown * 100:.2f}%")
            LOGGER.info(f"  交易次数: {result.total_trades}")
            LOGGER.info(f"  胜率: {result.win_rate * 100:.2f}%")
            LOGGER.info(f"报告文件: {self.backtest_summary.report_files}")
            return True
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("✗ 回测失败: {}", exc, exc_info=True)
            return False

    async def run_intelligent_workflow(self, skip_backtest: bool = True) -> bool:
        """运行智能策略工作流

        Args:
            skip_backtest: 是否跳过回测步骤（默认True，前端需要单独点击回测按钮）

        Returns:
            是否成功
        """
        LOGGER.info("\n🤖 " + "=" * 56 + " 🤖")
        LOGGER.info("🤖  完全智能化AI策略系统  🤖")
        LOGGER.info("🤖 " + "=" * 56 + " 🤖")

        steps = [
            ("AI理解用户需求", self.step1_understand_requirement),
            ("AI分析市场状态", self.step2_analyze_market),
            ("AI智能选股", self.step3_ai_select_stocks),
            ("AI选择最优模型", self.step4_ai_select_model),
            ("训练AI模型", self.step5_train_selected_model),
            ("生成交易策略", self.step6_generate_strategy),
        ]

        # 只有在不跳过回测时才添加回测步骤
        if not skip_backtest:
            steps.append(("运行智能回测", self.step7_run_backtest))

        for idx, (name, func) in enumerate(steps, 1):
            try:
                await self._notify_progress(idx, name, "running")
                success = await func()
                if not success:
                    LOGGER.error("\n❌ 步骤{}失败: {}", idx, name)
                    await self._notify_progress(idx, name, "failed")
                    return False
                await self._notify_progress(idx, name, "completed")
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("\n❌ 步骤{}异常: {} - {}", idx, name, exc)
                await self._notify_progress(idx, name, "failed")
                return False

        self.workflow_result = StrategyWorkflowResult(
            requirement=self.requirement_context,
            market=self.market_context,
            universe=self.universe,
            features=self.feature_bundle,
            model=self.trained_model,
            strategy_params=self.strategy_params,
            portfolio=self.portfolio_plan,
            execution=self.execution_plan,
            backtest=self.backtest_summary,
        )

        LOGGER.info("\n" + "=" * 60)
        if skip_backtest:
            LOGGER.info("✅ 智能AI策略生成成功! (未执行回测)")
            LOGGER.info("=" * 60)
            LOGGER.info('💡 提示: 请在前端点击"回测"按钮执行回测')
        else:
            LOGGER.info("✅ 智能AI策略完整流程执行成功!")
            LOGGER.info("=" * 60)

        if self.backtest_id:
            LOGGER.info(f"回测ID: {self.backtest_id}")
        if self.selected_model_type:
            LOGGER.info(f"选用模型: {self.selected_model_type.upper()}")
        LOGGER.info(f"股票数量: {len(self.recommended_stocks)}")

        if self.backtest_summary and hasattr(self.backtest_summary, "result"):
            LOGGER.info(
                f"最终收益率: {self.backtest_summary.result.total_return * 100:.2f}%"
            )
            # 新增：显示策略保存信息
            if (
                hasattr(self.backtest_summary, "strategy_id")
                and self.backtest_summary.strategy_id
            ):
                LOGGER.info(f"📁 策略已保存，ID: {self.backtest_summary.strategy_id}")
                LOGGER.info(
                    f"📁 策略路径: ai_strategy_system/generated_strategies/{self.backtest_summary.strategy_id}/"
                )
                LOGGER.info(
                    "💡 查看策略: python ai_strategy_system/strategy_persistence.py load %s",
                    self.backtest_summary.strategy_id,
                )

        return True


async def main() -> None:
    print("\n" + "=" * 70)
    print("🤖  FinLoom 智能AI策略系统  🤖")
    print("=" * 70)

    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        print("\n📝 用户需求: %s" % user_input)
    else:
        user_input = "我想要一个中等风险的策略，追求稳健收益，投资期限1-2年"
        print("\n📝 默认需求: %s" % user_input)
        print('💡 可自定义: python intelligent_strategy_ai.py "您的需求"\n')

    print("\n系统将自动完成:")
    print("  1. 理解投资需求")
    print("  2. 分析市场状态")
    print("  3. 智能推荐股票")
    print("  4. 选择最优AI模型")
    print("  5. 训练模型生成策略")
    print("  6. 运行回测生成报告")
    print("\n⏱️  预计耗时: 5-10分钟")
    print("=" * 70 + "\n")

    try:
        ai_system = IntelligentStrategyAI(
            user_requirement=user_input, initial_capital=1_000_000.0
        )
        success = await ai_system.run_intelligent_workflow()

        if success and ai_system.backtest_summary:
            print("\n" + "=" * 70)
            print("✅ 所有任务完成!")
            print("=" * 70)
            print("\n📊 结果:")
            if ai_system.backtest_id:
                print("  回测ID: %s" % ai_system.backtest_id)
            if ai_system.selected_model_type:
                print("  选用模型: %s" % ai_system.selected_model_type.upper())
            print("  股票数量: %d" % len(ai_system.recommended_stocks))
            result = ai_system.backtest_summary.result
            print("  收益率: %.2f%%" % (result.total_return * 100))
            print("  夏普比率: %.3f" % result.sharpe_ratio)
            print("  最大回撤: %.2f%%" % (result.max_drawdown * 100))
            print("\n📁 报告目录: reports/")
            print("=" * 70)
        else:
            print("\n❌ 执行失败，查看日志")
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as exc:  # noqa: BLE001
        print("\n\n❌ 错误: %s" % exc)
        raise


if __name__ == "__main__":
    asyncio.run(main())
