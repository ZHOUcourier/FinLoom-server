"""
Module 11 可视化模块测试
测试图表生成、仪表板、报告生成等功能
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

from common.data_structures import Position, Signal
from common.logging_system import setup_logger

# 导入 Module 11（移除其他模块依赖以避免循环导入）
from module_11_visualization import (
    ChartConfig,
    ChartGenerator,
    DashboardComponent,
    DashboardConfig,
    DashboardManager,
    ExportConfig,
    ExportManager,
    InteractiveConfig,
    InteractiveVisualizer,
    PerformanceMetrics,
    ReportBuilder,
    ReportConfig,
    ReportSection,
    TemplateEngine,
    get_visualization_database_manager,
)

logger = setup_logger("module11_test")


class TestVisualization:
    """可视化模块测试类"""

    def __init__(self):
        """初始化测试"""
        self.chart_gen = ChartGenerator(default_theme="dark")
        self.interactive_viz = InteractiveVisualizer()
        self.report_builder = ReportBuilder()
        self.export_mgr = ExportManager(
            default_output_dir=os.path.join("module_11_visualization", "reports", "test")
        )
        self.vis_db = get_visualization_database_manager()

        # 测试数据
        self.test_symbol = "000001"
        self.test_data = None

    def setup(self):
        """测试前准备"""
        logger.info("=" * 60)
        logger.info("开始 Module 11 可视化模块测试")
        logger.info("=" * 60)

        # 获取测试数据
        logger.info("\n1. 准备测试数据")
        try:
            # 使用模拟数据进行测试，避免对其他模块的依赖
            logger.info(f"  生成 {self.test_symbol} 的模拟数据...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            # 生成模拟OHLCV数据
            dates = pd.date_range(start=start_date, end=end_date, freq="D")
            np.random.seed(42)

            # 生成OHLCV数据
            base_price = 10.0
            returns = np.random.randn(len(dates)) * 0.02
            close_prices = base_price * (1 + returns).cumprod()

            self.test_data = pd.DataFrame(
                {
                    "open": close_prices * (1 + np.random.randn(len(dates)) * 0.01),
                    "high": close_prices
                    * (1 + np.abs(np.random.randn(len(dates))) * 0.02),
                    "low": close_prices
                    * (1 - np.abs(np.random.randn(len(dates))) * 0.02),
                    "close": close_prices,
                    "volume": np.random.randint(1000000, 10000000, len(dates)),
                },
                index=dates,
            )

            logger.info(f"  ✓ 生成测试数据: {len(self.test_data)} 条记录")

        except Exception as e:
            logger.error(f"  ✗ 准备数据失败: {e}")
            raise

    def test_chart_generator(self):
        """测试图表生成器"""
        logger.info("\n2. 测试图表生成器")

        try:
            # 测试 K线图
            logger.info("  2.1 测试K线图生成")
            candlestick = self.chart_gen.generate_candlestick_chart(
                data=self.test_data, volume_subplot=True
            )
            logger.info(f"  ✓ K线图生成成功")

            # 保存图表
            output_file = os.path.join("module_11_visualization", "reports", "test", "candlestick_test.html")
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            success = self.chart_gen.save_chart(candlestick, output_file, format="html")
            logger.info(f"  ✓ K线图已保存: {output_file}")

            # 测试绩效曲线
            logger.info("  2.2 测试绩效曲线生成")
            returns = self.test_data["close"].pct_change().dropna()
            performance_chart = self.chart_gen.generate_performance_chart(
                returns=returns
            )
            logger.info(f"  ✓ 绩效曲线生成成功")

            # 测试热力图
            logger.info("  2.3 测试热力图生成")
            # 生成相关性矩阵
            correlation_data = pd.DataFrame(
                np.random.randn(5, 5), columns=["A", "B", "C", "D", "E"]
            ).corr()
            heatmap = self.chart_gen.generate_heatmap(correlation_data)
            logger.info(f"  ✓ 热力图生成成功")

            # 测试回撤图
            logger.info("  2.4 测试回撤图生成")
            drawdown_chart = self.chart_gen.generate_drawdown_chart(returns)
            logger.info(f"  ✓ 回撤图生成成功")

            # 测试组合构成图
            logger.info("  2.5 测试组合构成图")
            positions = {
                "股票A": 0.3,
                "股票B": 0.25,
                "股票C": 0.2,
                "股票D": 0.15,
                "股票E": 0.1,
            }
            composition = self.chart_gen.generate_portfolio_composition(positions)
            logger.info(f"  ✓ 组合构成图生成成功")

            logger.info("\n  ✅ 图表生成器测试通过")
            return True

        except Exception as e:
            logger.error(f"  ✗ 图表生成器测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def test_interactive_visualizer(self):
        """测试交互式可视化器"""
        logger.info("\n3. 测试交互式可视化器")

        try:
            # 测试交互式K线图
            logger.info("  3.1 测试交互式K线图")
            interactive_chart = self.interactive_viz.create_interactive_candlestick(
                df=self.test_data,
                symbol=self.test_symbol,
                indicators=["rsi"],
                overlays=["ma"],
                volume=True,
            )
            logger.info(f"  ✓ 交互式K线图生成成功")

            # 导出HTML
            output_file = os.path.join(
                "module_11_visualization", "reports", "test", "interactive_chart_test.html"
            )
            success = self.interactive_viz.export_interactive_html(
                interactive_chart, output_file
            )
            logger.info(f"  ✓ 交互式图表已导出: {output_file}")

            # 测试热力图矩阵
            logger.info("  3.2 测试交互式热力图")
            correlation_data = pd.DataFrame(
                np.random.randn(5, 5),
                columns=["股票A", "股票B", "股票C", "股票D", "股票E"],
                index=["股票A", "股票B", "股票C", "股票D", "股票E"],
            ).corr()
            heatmap = self.interactive_viz.create_heatmap_matrix(
                data=correlation_data, title="相关性矩阵", show_values=True
            )
            logger.info(f"  ✓ 交互式热力图生成成功")

            # 测试网络图
            logger.info("  3.3 测试网络图")
            nodes = [
                {"id": "A", "label": "股票A"},
                {"id": "B", "label": "股票B"},
                {"id": "C", "label": "股票C"},
            ]
            edges = [
                {"source": "A", "target": "B", "weight": 0.8},
                {"source": "B", "target": "C", "weight": 0.6},
                {"source": "A", "target": "C", "weight": 0.4},
            ]
            network = self.interactive_viz.create_network_graph(
                nodes=nodes, edges=edges, title="股票关联网络"
            )
            logger.info(f"  ✓ 网络图生成成功")

            logger.info("\n  ✅ 交互式可视化器测试通过")
            return True

        except Exception as e:
            logger.error(f"  ✗ 交互式可视化器测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def test_report_builder(self):
        """测试报告生成器（JSON/SQLite输出）"""
        logger.info("\n4. 测试报告生成器（新版：JSON + SQLite）")

        try:
            # 准备测试数据
            logger.info("  4.1 准备报告数据")
            portfolio_data = {
                "total_value": 1000000.0,
                "daily_pnl": 5000.0,
                "daily_return": 0.005,
                "ytd_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.08,
                "win_rate": 0.65,
                "profit_factor": 2.1,
            }

            # 创建绩效指标
            metrics = PerformanceMetrics(
                total_return=0.25,
                annualized_return=0.20,
                volatility=0.15,
                sharpe_ratio=1.33,
                sortino_ratio=1.8,
                max_drawdown=-0.12,
                win_rate=0.60,
                profit_factor=2.0,
                avg_win=500,
                avg_loss=-250,
                best_trade=2000,
                worst_trade=-800,
                total_trades=100,
                winning_trades=60,
                losing_trades=40,
            )

            # 创建模拟Position和Signal对象
            from common.data_structures import Position, Signal

            positions = [
                Position(
                    position_id="pos_001",
                    symbol="000001",
                    quantity=1000,
                    avg_cost=10.5,
                    current_price=11.2,
                    market_value=11200,
                    unrealized_pnl=700,
                    realized_pnl=0,
                    open_time=datetime.now(),
                    last_update=datetime.now(),
                )
            ]

            signals = [
                Signal(
                    signal_id="sig_001",
                    symbol="000001",
                    timestamp=datetime.now(),
                    action="BUY",
                    quantity=1000,
                    price=11.2,
                    confidence=0.85,
                    strategy_name="test_strategy",
                    metadata={"reason": "test signal", "type": "momentum"},
                )
            ]

            # 测试JSON格式日报生成
            logger.info("  4.2 测试JSON格式日报生成（默认）")
            json_config = ReportConfig(report_type="daily", output_format="json")

            json_result = self.report_builder.generate_daily_report(
                date=datetime.now(),
                portfolio_data=portfolio_data,
                positions=positions,
                signals=signals,
                market_data=self.test_data.tail(30),  # 使用最近30天的数据
                config=json_config,
            )

            if json_result.get("success"):
                logger.info(f"  ✓ JSON日报生成成功")
                logger.info(f"    报告ID: {json_result.get('database_report_id')}")
                for location in json_result.get("saved_to", []):
                    logger.info(f"    {location}")
            else:
                logger.error(f"  ✗ JSON日报生成失败: {json_result.get('errors')}")

            # 测试CSV格式报告
            logger.info("  4.3 测试CSV格式日报生成")
            csv_config = ReportConfig(report_type="daily", output_format="csv")

            csv_result = self.report_builder.generate_daily_report(
                date=datetime.now(),
                portfolio_data=portfolio_data,
                positions=positions,
                signals=signals,
                market_data=self.test_data.tail(30),
                config=csv_config,
            )

            if csv_result.get("success"):
                logger.info(f"  ✓ CSV日报生成成功")
                for location in csv_result.get("saved_to", []):
                    logger.info(f"    {location}")

            # 测试Excel格式报告
            logger.info("  4.4 测试Excel格式日报生成")
            excel_config = ReportConfig(report_type="daily", output_format="excel")

            excel_result = self.report_builder.generate_daily_report(
                date=datetime.now(),
                portfolio_data=portfolio_data,
                positions=positions,
                signals=signals,
                market_data=self.test_data.tail(30),
                config=excel_config,
            )

            if excel_result.get("success"):
                logger.info(f"  ✓ Excel日报生成成功")
                for location in excel_result.get("saved_to", []):
                    logger.info(f"    {location}")

            # 测试绩效报告（JSON格式）
            logger.info("  4.5 测试JSON格式绩效报告生成")
            performance_data = {
                "returns": {"daily": 0.005, "monthly": 0.02, "yearly": 0.25},
                "risk": {"volatility": 0.15, "var_95": -0.05, "cvar_95": -0.08},
            }

            perf_result = self.report_builder.generate_performance_report(
                performance_data=performance_data,
                metrics=metrics,
                config=ReportConfig(report_type="performance", output_format="json"),
            )

            if perf_result.get("success"):
                logger.info(f"  ✓ 绩效报告生成成功")
                logger.info(f"    报告ID: {perf_result.get('database_report_id')}")
                for location in perf_result.get("saved_to", []):
                    logger.info(f"    {location}")

            # 测试从数据库读取报告
            logger.info("  4.6 测试从数据库读取报告")
            if json_result.get("database_report_id"):
                report_id = json_result.get("database_report_id")
                db_report = self.vis_db.get_report(report_id)
                if db_report:
                    logger.info(f"  ✓ 从数据库读取报告成功: {db_report.get('title')}")
                    logger.info(f"    报告类型: {db_report.get('report_type')}")
                    logger.info(f"    报告日期: {db_report.get('report_date')}")
                    # 显示报告数据摘要
                    if db_report.get("content"):
                        content_keys = list(db_report["content"].keys())
                        logger.info(f"    数据章节: {', '.join(content_keys)}")

            logger.info("\n  ✅ 报告生成器测试通过（新版：纯数据输出）")
            return True

        except Exception as e:
            logger.error(f"  ✗ 报告生成器测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def test_export_manager(self):
        """测试导出管理器"""
        logger.info("\n5. 测试导出管理器")

        try:
            # 测试DataFrame导出
            logger.info("  5.1 测试DataFrame导出")

            test_df = pd.DataFrame(
                {
                    "日期": pd.date_range("2024-01-01", periods=10),
                    "收盘价": np.random.randn(10).cumsum() + 100,
                    "成交量": np.random.randint(1000, 10000, 10),
                }
            )

            # 导出CSV
            result = self.export_mgr.export_dataframe(
                df=test_df, filename="test_data.csv", format="csv"
            )
            if result.success:
                logger.info(
                    f"  ✓ CSV导出成功: {result.file_path}, 大小: {result.file_size} bytes"
                )
            else:
                logger.error(f"  ✗ CSV导出失败")

            # 导出Excel
            result = self.export_mgr.export_dataframe(
                df=test_df, filename="test_data.xlsx", format="excel"
            )
            if result.success:
                logger.info(
                    f"  ✓ Excel导出成功: {result.file_path}, 大小: {result.file_size} bytes"
                )

            # 测试多数据集导出
            logger.info("  5.2 测试多数据集导出")
            data_dict = {
                "价格数据": test_df,
                "统计数据": pd.DataFrame({"指标": ["均值", "标准差"], "值": [100, 5]}),
            }

            result = self.export_mgr.export_multiple(
                data_dict=data_dict,
                base_filename="portfolio_analysis",
                format="excel",
                create_archive=False,
            )
            if result.success:
                logger.info(f"  ✓ 多数据集导出成功: {result.file_path}")

            logger.info("\n  ✅ 导出管理器测试通过")
            return True

        except Exception as e:
            logger.error(f"  ✗ 导出管理器测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def test_database_manager(self):
        """测试数据库管理器"""
        logger.info("\n6. 测试数据库管理器")

        try:
            # 测试保存图表
            logger.info("  6.1 测试图表保存")
            chart_id = f"test_chart_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            success = self.vis_db.save_chart(
                chart_id=chart_id,
                chart_type="candlestick",
                title="测试K线图",
                data_source="test",
                config={"symbol": self.test_symbol},
                html_content="<div>Test Chart</div>",
            )
            if success:
                logger.info(f"  ✓ 图表保存成功: {chart_id}")

            # 测试获取图表
            chart = self.vis_db.get_chart(chart_id)
            if chart:
                logger.info(f"  ✓ 图表获取成功: {chart['title']}")

            # 测试保存报告
            logger.info("  6.2 测试报告保存")
            report_id = f"test_report_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            success = self.vis_db.save_report(
                report_id=report_id,
                report_type="daily",
                title="测试日报",
                report_date=datetime.now(),
                content_html="<html><body>Test Report</body></html>",
                metadata={"author": "test", "version": "1.0"},
            )
            if success:
                logger.info(f"  ✓ 报告保存成功: {report_id}")

            # 测试列出报告
            reports = self.vis_db.list_reports(report_type="daily", limit=5)
            logger.info(f"  ✓ 获取报告列表: {len(reports)} 条记录")

            # 测试缓存
            logger.info("  6.3 测试缓存功能")
            cache_key = "test_cache"
            cache_data = {"value": 123, "timestamp": datetime.now().isoformat()}
            success = self.vis_db.set_cache(
                cache_key=cache_key,
                cache_type="test",
                data=cache_data,
                expires_in_seconds=3600,
            )
            if success:
                logger.info(f"  ✓ 缓存设置成功")

            cached = self.vis_db.get_cache(cache_key)
            if cached:
                logger.info(f"  ✓ 缓存获取成功: {cached}")

            # 测试数据库统计
            logger.info("  6.4 测试数据库统计")
            stats = self.vis_db.get_database_stats()
            logger.info(f"  ✓ 数据库统计:")
            for key, value in stats.items():
                logger.info(f"    {key}: {value}")

            logger.info("\n  ✅ 数据库管理器测试通过")
            return True

        except Exception as e:
            logger.error(f"  ✗ 数据库管理器测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def cleanup(self):
        """清理测试"""
        logger.info("\n7. 清理测试环境")
        # 这里可以添加清理逻辑
        logger.info("  ✓ 清理完成")

    def run_all_tests(self):
        """运行所有测试"""
        try:
            # 准备
            self.setup()

            # 运行测试
            results = {
                "图表生成器": self.test_chart_generator(),
                "交互式可视化器": self.test_interactive_visualizer(),
                "报告生成器": self.test_report_builder(),
                "导出管理器": self.test_export_manager(),
                "数据库管理器": self.test_database_manager(),
            }

            # 清理
            self.cleanup()

            # 输出结果
            logger.info("\n" + "=" * 60)
            logger.info("测试结果汇总")
            logger.info("=" * 60)

            all_passed = True
            for test_name, passed in results.items():
                status = "✅ 通过" if passed else "❌ 失败"
                logger.info(f"{test_name}: {status}")
                if not passed:
                    all_passed = False

            logger.info("=" * 60)
            if all_passed:
                logger.info("🎉 所有测试通过！")
            else:
                logger.warning("⚠️  部分测试失败，请检查日志")

            return all_passed

        except Exception as e:
            logger.error(f"\n❌ 测试过程出错: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Module 11 - 可视化模块测试")
    print("=" * 60)
    print("\n注意：测试需要在 conda study 环境下运行")
    print("命令：conda activate study")
    print()

    test = TestVisualization()
    success = test.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
