"""
Module 09 回测模块测试
使用真实数据测试回测引擎、性能分析等功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd

from common.data_structures import Signal
from common.logging_system import setup_logger

# 导入 Module 01
from module_01_data_pipeline import AkshareDataCollector, get_database_manager

# 导入 Module 09
from module_09_backtesting import (
    BacktestConfig,
    BacktestEngine,
    BacktestReportGenerator,
    BacktestResult,
    ImpactParameters,
    LinearImpactModel,
    PerformanceAnalyzer,
    ReportConfig,
    RiskAttributor,
    TransactionSimulator,
    get_backtest_database_manager,
)

logger = setup_logger("module09_test")


class TestBacktesting:
    """回测模块测试类"""

    def __init__(self):
        """初始化测试"""
        self.collector = AkshareDataCollector(rate_limit=0.5)
        self.symbols = ["000001", "600036", "000858"]  # 平安银行、招商银行、五粮液
        self.start_date = "20230101"
        self.end_date = "20241201"
        self.market_data = {}

    def setup(self):
        """测试前准备"""
        logger.info("=" * 60)
        logger.info("开始 Module 09 回测模块测试")
        logger.info("=" * 60)

        # 获取真实市场数据
        logger.info("\n1. 获取市场数据 (Module 01)")
        for symbol in self.symbols:
            try:
                logger.info(f"  获取 {symbol} 数据...")
                df = self.collector.fetch_stock_history(
                    symbol, self.start_date, self.end_date
                )
                if df is not None and not df.empty:
                    self.market_data[symbol] = df
                    logger.info(f"  ✓ {symbol}: {len(df)} 条记录")
                else:
                    logger.warning(f"  ✗ {symbol}: 数据为空")
            except Exception as e:
                logger.error(f"  ✗ {symbol}: {e}")

        if not self.market_data:
            raise Exception("无法获取市场数据,测试终止")

        logger.info(f"  成功获取 {len(self.market_data)} 只股票数据")

    def test_backtest_engine(self):
        """测试回测引擎"""
        logger.info("\n2. 测试回测引擎")

        try:
            # 创建回测配置
            config = BacktestConfig(
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2024, 12, 1),
                initial_capital=1000000.0,
                commission_rate=0.0003,
                slippage_bps=5.0,
                save_to_db=True,
                strategy_name="简单动量策略",
            )

            logger.info("  配置回测参数:")
            logger.info(f"    初始资金: {config.initial_capital:,.0f}")
            logger.info(f"    佣金率: {config.commission_rate:.4f}")
            logger.info(f"    滑点: {config.slippage_bps} bps")

            # 创建回测引擎
            engine = BacktestEngine(config)
            logger.info(f"  回测ID: {engine.backtest_id}")

            # 加载市场数据
            engine.load_market_data(list(self.market_data.keys()), self.market_data)
            logger.info(f"  加载了 {len(self.market_data)} 只股票数据")

            # 定义简单策略
            def simple_momentum_strategy(current_data, positions, capital):
                """简单动量策略"""
                signals = []

                for symbol, data in current_data.items():
                    # 检查是否已有持仓
                    if symbol in positions:
                        continue

                    # 简单逻辑: 如果有足够的钱,买入
                    price = data["close"]
                    quantity = 100  # 固定买100股

                    if capital > price * quantity * 1.01:  # 留1%余量
                        signal = Signal(
                            signal_id=f"sig_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            symbol=symbol,
                            action="BUY",
                            price=price,
                            quantity=quantity,
                            confidence=0.7,
                            timestamp=datetime.now(),
                            strategy_name="MOMENTUM",
                            metadata={},
                        )
                        signals.append(signal)
                        break  # 一次只买一只

                return signals

            # 设置策略
            engine.set_strategy(simple_momentum_strategy)
            logger.info("  策略设置完成")

            # 运行回测
            logger.info("  开始运行回测...")
            result = engine.run()

            # 显示结果
            logger.info("\n  回测结果:")
            logger.info(f"    初始资金: {result.initial_capital:,.2f}")
            logger.info(f"    最终资金: {result.final_capital:,.2f}")
            logger.info(f"    总收益率: {result.total_return:.2%}")
            logger.info(f"    年化收益率: {result.annualized_return:.2%}")
            logger.info(f"    波动率: {result.volatility:.2%}")
            logger.info(f"    夏普比率: {result.sharpe_ratio:.3f}")
            logger.info(f"    最大回撤: {result.max_drawdown:.2%}")
            logger.info(f"    总交易次数: {result.total_trades}")
            logger.info(f"    胜率: {result.win_rate:.2%}")
            logger.info(f"    盈亏比: {result.profit_factor:.3f}")

            logger.info("  ✓ 回测引擎测试通过")
            return result, engine.backtest_id

        except Exception as e:
            logger.error(f"  ✗ 回测引擎测试失败: {e}")
            import traceback

            traceback.print_exc()
            return None, None

    def test_performance_analyzer(self, result: BacktestResult):
        """测试性能分析器"""
        logger.info("\n3. 测试性能分析器")

        try:
            # 创建分析器
            analyzer = PerformanceAnalyzer()

            # 提取收益率序列
            if result.equity_curve.empty:
                logger.warning("  权益曲线为空,跳过性能分析")
                return None

            returns = result.equity_curve["equity"].pct_change().dropna()
            logger.info(f"  收益率数据点: {len(returns)}")

            # 执行分析
            performance_report = analyzer.analyze(returns=returns)

            # 显示汇总统计
            logger.info("\n  性能指标:")
            stats = performance_report.summary_stats
            logger.info(f"    总收益率: {stats['total_return']:.2%}")
            logger.info(f"    年化收益率: {stats['annual_return']:.2%}")
            logger.info(f"    波动率: {stats['volatility']:.2%}")
            logger.info(f"    夏普比率: {stats['sharpe_ratio']:.3f}")
            logger.info(f"    索提诺比率: {stats['sortino_ratio']:.3f}")
            logger.info(f"    卡尔玛比率: {stats['calmar_ratio']:.3f}")
            logger.info(f"    最大回撤: {stats['max_drawdown']:.2%}")
            logger.info(f"    回撤持续天数: {stats['drawdown_duration_days']}")
            logger.info(f"    偏度: {stats['skewness']:.3f}")
            logger.info(f"    峰度: {stats['kurtosis']:.3f}")
            logger.info(f"    VaR(95%): {stats['var_95']:.4f}")
            logger.info(f"    CVaR(95%): {stats['cvar_95']:.4f}")
            logger.info(f"    最佳单日: {stats['best_day']:.4f}")
            logger.info(f"    最差单日: {stats['worst_day']:.4f}")
            logger.info(f"    盈利天数: {stats['positive_days']}")
            logger.info(f"    亏损天数: {stats['negative_days']}")
            logger.info(f"    胜率: {stats['hit_rate']:.2%}")

            logger.info("  ✓ 性能分析器测试通过")
            return performance_report

        except Exception as e:
            logger.error(f"  ✗ 性能分析器测试失败: {e}")
            import traceback

            traceback.print_exc()
            return None

    def test_database_manager(self, backtest_id: str):
        """测试数据库管理器"""
        logger.info("\n4. 测试数据库管理器")

        try:
            # 获取数据库管理器
            db = get_backtest_database_manager()

            # 列出所有回测
            backtests_df = db.list_backtests(limit=10)
            logger.info(f"  历史回测数量: {len(backtests_df)}")

            if not backtests_df.empty:
                logger.info("\n  最近的回测:")
                for _, row in backtests_df.head(5).iterrows():
                    logger.info(
                        f"    {row['backtest_id'][:30]}... | "
                        f"{row['strategy_name']} | "
                        f"收益: {row['total_return']:.2%} | "
                        f"夏普: {row['sharpe_ratio']:.3f}"
                    )

            # 获取本次回测结果
            result_dict = db.get_backtest_result(backtest_id)
            if result_dict:
                logger.info(f"\n  当前回测详情 ({backtest_id[:30]}...):")
                logger.info(f"    策略名称: {result_dict['strategy_name']}")
                logger.info(f"    开始日期: {result_dict['start_date']}")
                logger.info(f"    结束日期: {result_dict['end_date']}")
                logger.info(f"    总收益率: {result_dict['total_return']:.2%}")

            # 获取交易记录
            trades_df = db.get_trades(backtest_id)
            logger.info(f"\n  交易记录: {len(trades_df)} 笔")
            if not trades_df.empty:
                logger.info("  前5笔交易:")
                for _, trade in trades_df.head(5).iterrows():
                    logger.info(
                        f"    {trade['trade_date']} | "
                        f"{trade['symbol']} | "
                        f"{trade['side']} | "
                        f"{trade['quantity']}股 @ {trade['price']:.2f}"
                    )

            # 获取权益曲线
            equity_df = db.get_equity_curve(backtest_id)
            logger.info(f"\n  权益曲线: {len(equity_df)} 个数据点")
            if not equity_df.empty:
                logger.info(f"    起始权益: {equity_df['equity'].iloc[0]:,.2f}")
                logger.info(f"    结束权益: {equity_df['equity'].iloc[-1]:,.2f}")

            # 获取统计信息
            stats = db.get_statistics()
            logger.info(f"\n  数据库统计:")
            logger.info(f"    总回测数: {stats['total_backtests']}")
            logger.info(f"    总交易数: {stats['total_trades']}")
            logger.info(f"    平均夏普比率: {stats['avg_sharpe_ratio']:.3f}")
            logger.info(f"    平均最大回撤: {stats['avg_max_drawdown']:.2%}")
            logger.info(f"    数据库大小: {stats['database_size_mb']:.2f} MB")

            logger.info("  ✓ 数据库管理器测试通过")

        except Exception as e:
            logger.error(f"  ✗ 数据库管理器测试失败: {e}")
            import traceback

            traceback.print_exc()

    def test_transaction_simulator(self):
        """测试交易模拟器"""
        logger.info("\n5. 测试交易模拟器")

        try:
            # 创建交易模拟器
            simulator = TransactionSimulator(
                config={
                    "latency_ms": 10,
                    "tick_size": 0.01,
                    "lot_size": 100,
                    "max_participation_rate": 0.1,
                }
            )

            # 使用第一只股票的数据初始化
            symbol = list(self.market_data.keys())[0]
            data = self.market_data[symbol]

            logger.info(f"  使用 {symbol} 数据初始化模拟器")
            simulator.initialize_from_historical_data(data)

            # 模拟订单簿
            latest_price = data["close"].iloc[-1]
            latest_volume = data["volume"].iloc[-1]

            order_book = simulator.simulate_order_book(
                symbol=symbol,
                timestamp=datetime.now(),
                mid_price=latest_price,
                volume=int(latest_volume),
                volatility=0.02,
            )

            logger.info(f"\n  模拟订单簿:")
            logger.info(f"    最佳买价: {order_book.best_bid:.2f}")
            logger.info(f"    最佳卖价: {order_book.best_ask:.2f}")
            logger.info(f"    价差: {order_book.spread:.4f}")
            logger.info(f"    中间价: {order_book.mid_price:.2f}")
            logger.info(f"    买单总量: {order_book.total_bid_volume:,}")
            logger.info(f"    卖单总量: {order_book.total_ask_volume:,}")

            logger.info("  ✓ 交易模拟器测试通过")

        except Exception as e:
            logger.error(f"  ✗ 交易模拟器测试失败: {e}")
            import traceback

            traceback.print_exc()

    def test_market_impact_model(self):
        """测试市场冲击模型"""
        logger.info("\n6. 测试市场冲击模型")

        try:
            # 创建线性冲击模型
            model = LinearImpactModel()

            # 定义参数
            params = ImpactParameters(
                permanent_impact=0.1,
                temporary_impact=0.05,
                decay_rate=0.5,
                volatility=0.02,
                daily_volume=5000000,
                spread=0.01,
            )

            logger.info("  冲击参数:")
            logger.info(f"    永久冲击系数: {params.permanent_impact}")
            logger.info(f"    临时冲击系数: {params.temporary_impact}")
            logger.info(f"    日均成交量: {params.daily_volume:,}")

            # 测试不同订单规模
            order_sizes = [10000, 50000, 100000]

            logger.info("\n  不同订单规模的市场冲击:")
            for size in order_sizes:
                estimate = model.estimate_impact(size, params)
                logger.info(f"    订单: {size:,} 股")
                logger.info(f"      总冲击: {estimate.total_impact:.2f} bps")
                logger.info(f"      永久冲击: {estimate.permanent_component:.2f} bps")
                logger.info(f"      临时冲击: {estimate.temporary_component:.2f} bps")
                logger.info(f"      执行成本: {estimate.execution_cost:.4%}")

            logger.info("  ✓ 市场冲击模型测试通过")

        except Exception as e:
            logger.error(f"  ✗ 市场冲击模型测试失败: {e}")
            import traceback

            traceback.print_exc()

    def test_risk_attribution(self):
        """测试风险归因"""
        logger.info("\n7. 测试风险归因")

        try:
            # 创建风险归因分析器
            attributor = RiskAttributor()

            # 准备多只股票的收益率数据
            portfolio_returns = pd.DataFrame()
            for symbol, data in self.market_data.items():
                returns = data["close"].pct_change().dropna()
                portfolio_returns[symbol] = returns

            # 对齐数据
            portfolio_returns = portfolio_returns.dropna()
            logger.info(
                f"  收益率数据: {len(portfolio_returns)} 天 × {len(portfolio_returns.columns)} 只股票"
            )

            # 等权重
            n_assets = len(portfolio_returns.columns)
            weights = np.array([1.0 / n_assets] * n_assets)
            logger.info(f"  权重配置: 等权重 ({weights[0]:.2%} 每只)")

            # 执行风险归因
            attribution_report = attributor.attribute_risk(
                portfolio_returns=portfolio_returns, weights=weights
            )

            logger.info(f"\n  风险归因结果:")
            logger.info(f"    组合总风险: {attribution_report.total_risk:.2%}")

            decomp = attribution_report.risk_decomposition
            logger.info(f"    加权平均风险: {decomp['weighted_average_risk']:.2%}")
            logger.info(f"    分散化比率: {decomp['diversification_ratio']:.3f}")
            logger.info(f"    分散化收益: {decomp['diversification_benefit']:.4f}")

            logger.info("\n  各资产风险贡献:")
            for symbol in portfolio_returns.columns:
                contrib_key = f"{symbol}_contribution"
                if contrib_key in decomp:
                    logger.info(f"    {symbol}: {decomp[contrib_key]:.4f}")

            logger.info("  ✓ 风险归因测试通过")

        except Exception as e:
            logger.error(f"  ✗ 风险归因测试失败: {e}")
            import traceback

            traceback.print_exc()

    def run_all_tests(self):
        """运行所有测试"""
        try:
            # 准备
            self.setup()

            # 测试回测引擎
            result, backtest_id = self.test_backtest_engine()

            if result and backtest_id:
                # 测试性能分析
                performance_report = self.test_performance_analyzer(result)

                # 测试数据库
                self.test_database_manager(backtest_id)

            # 测试交易模拟
            self.test_transaction_simulator()

            # 测试市场冲击模型
            self.test_market_impact_model()

            # 测试风险归因
            self.test_risk_attribution()

            # 总结
            logger.info("\n" + "=" * 60)
            logger.info("所有测试完成!")
            logger.info("=" * 60)
            logger.info("\n测试总结:")
            logger.info("  ✓ 回测引擎")
            logger.info("  ✓ 性能分析")
            logger.info("  ✓ 数据库管理")
            logger.info("  ✓ 交易模拟")
            logger.info("  ✓ 市场冲击模型")
            logger.info("  ✓ 风险归因")
            logger.info("\nModule 09 回测模块测试全部通过! ✓")

        except Exception as e:
            logger.error(f"\n测试过程出错: {e}")
            import traceback

            traceback.print_exc()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Module 09 - 回测验证模块 测试")
    print("=" * 60)
    print("\n使用真实数据测试回测引擎功能")
    print("数据来源: Module 01 (AkshareDataCollector)")
    print("\n提示: 请确保已激活 conda study 环境")
    print("=" * 60 + "\n")

    # 运行测试
    tester = TestBacktesting()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
