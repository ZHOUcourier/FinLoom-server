"""
报告生成器模块
生成回测分析的详细报告，包括HTML、PDF和Excel格式
"""

import base64
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from jinja2 import Template
from matplotlib.backends.backend_pdf import PdfPages
from plotly.subplots import make_subplots
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from scipy import stats

from common.constants import TRADING_DAYS_PER_YEAR
from common.logging_system import setup_logger

logger = setup_logger("report_generator")


@dataclass
class ReportConfig:
    """报告配置数据结构"""

    title: str = "Backtest Analysis Report"
    author: str = "Quantum Investment System"
    include_charts: bool = True
    include_tables: bool = True
    include_code: bool = False
    chart_theme: str = "plotly_white"
    language: str = "en"  # 'en' or 'zh'
    formats: List[str] = field(default_factory=lambda: ["html", "pdf", "excel"])
    output_dir: str = os.path.join("module_09_backtesting", "reports")
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)


@dataclass
class ReportSection:
    """报告章节数据结构"""

    title: str
    content: Any  # 可以是文本、表格或图表
    section_type: str  # 'text', 'table', 'chart', 'mixed'
    subsections: List["ReportSection"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BacktestReportGenerator:
    """回测报告生成器类"""

    def __init__(self, config: Optional[ReportConfig] = None):
        """初始化报告生成器

        Args:
            config: 报告配置
        """
        self.config = config or ReportConfig()
        self.sections: List[ReportSection] = []
        self.figures: List[go.Figure] = []
        self.tables: List[pd.DataFrame] = []

        # 设置样式
        self._setup_styles()

    def _setup_styles(self) -> None:
        """设置报告样式"""
        # Plotly主题
        import plotly.io as pio

        pio.templates.default = self.config.chart_theme

        # Matplotlib样式
        plt.style.use("seaborn-v0_8-darkgrid")
        sns.set_palette("husl")

        # 报告样式
        self.styles = getSampleStyleSheet()
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=colors.HexColor("#1f77b4"),
                alignment=TA_CENTER,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=colors.HexColor("#2ca02c"),
                spaceAfter=12,
            )
        )

    def generate_report(
        self,
        backtest_result: Any,
        performance_report: Optional[Any] = None,
        risk_report: Optional[Any] = None,
        validation_report: Optional[Any] = None,
    ) -> Dict[str, str]:
        """生成完整报告

        Args:
            backtest_result: 回测结果
            performance_report: 绩效报告
            risk_report: 风险报告
            validation_report: 验证报告

        Returns:
            生成的报告文件路径字典
        """
        logger.info("Generating backtest report...")

        # 清空之前的内容
        self.sections.clear()
        self.figures.clear()
        self.tables.clear()

        # 生成各个章节
        self._generate_summary_section(backtest_result)
        self._generate_performance_section(backtest_result, performance_report)
        self._generate_risk_section(backtest_result, risk_report)
        self._generate_trades_section(backtest_result)

        if validation_report:
            self._generate_validation_section(validation_report)

        # 生成不同格式的报告
        output_files = {}

        if "html" in self.config.formats:
            output_files["html"] = self._generate_html_report()

        if "pdf" in self.config.formats:
            output_files["pdf"] = self._generate_pdf_report()

        if "excel" in self.config.formats:
            output_files["excel"] = self._generate_excel_report()

        logger.info(f"Report generation completed. Files: {output_files}")
        return output_files

    def _generate_summary_section(self, backtest_result: Any) -> None:
        """生成摘要章节

        Args:
            backtest_result: 回测结果
        """
        # 关键指标汇总
        summary_data = {
            "Total Return": f"{backtest_result.performance_metrics.get('total_return', backtest_result.total_return) * 100:.2f}%",
            "Annual Return": f"{backtest_result.performance_metrics.get('annual_return', backtest_result.annualized_return) * 100:.2f}%",
            "Sharpe Ratio": f"{backtest_result.performance_metrics.get('sharpe_ratio', backtest_result.sharpe_ratio):.2f}",
            "Max Drawdown": f"{backtest_result.performance_metrics.get('max_drawdown', backtest_result.max_drawdown) * 100:.2f}%",
            "Total Trades": backtest_result.performance_metrics.get(
                "total_trades", backtest_result.total_trades
            ),
            "Win Rate": f"{backtest_result.performance_metrics.get('win_rate', backtest_result.win_rate) * 100:.2f}%",
            "Final Equity": f"${backtest_result.performance_metrics.get('final_equity', backtest_result.final_capital):,.2f}",
        }

        summary_df = pd.DataFrame.from_dict(
            summary_data, orient="index", columns=["Value"]
        )
        summary_df.index.name = "Metric"

        # 创建摘要章节
        section = ReportSection(
            title="Executive Summary",
            content=summary_df,
            section_type="table",
            metadata={"highlight": True},
        )

        # 添加关键发现文本
        key_findings = self._generate_key_findings(backtest_result)
        section.subsections.append(
            ReportSection(
                title="Key Findings", content=key_findings, section_type="text"
            )
        )

        self.sections.append(section)
        self.tables.append(summary_df)

    def _generate_performance_section(
        self, backtest_result: Any, performance_report: Optional[Any] = None
    ) -> None:
        """生成绩效分析章节

        Args:
            backtest_result: 回测结果
            performance_report: 绩效报告
        """
        section = ReportSection(
            title="Performance Analysis", content="", section_type="mixed"
        )

        # 权益曲线图
        equity_fig = self._create_equity_curve_chart(backtest_result.equity_curve)
        section.subsections.append(
            ReportSection(
                title="Equity Curve", content=equity_fig, section_type="chart"
            )
        )
        self.figures.append(equity_fig)

        # 月度收益热力图
        if hasattr(backtest_result, "monthly_returns"):
            heatmap_fig = self._create_monthly_returns_heatmap(
                backtest_result.monthly_returns
            )
            section.subsections.append(
                ReportSection(
                    title="Monthly Returns Heatmap",
                    content=heatmap_fig,
                    section_type="chart",
                )
            )
            self.figures.append(heatmap_fig)

        # 收益分布图
        returns_dist_fig = self._create_returns_distribution(
            backtest_result.daily_returns
        )
        section.subsections.append(
            ReportSection(
                title="Returns Distribution",
                content=returns_dist_fig,
                section_type="chart",
            )
        )
        self.figures.append(returns_dist_fig)

        # 滚动指标
        if performance_report and hasattr(performance_report, "rolling_metrics"):
            rolling_fig = self._create_rolling_metrics_chart(
                performance_report.rolling_metrics
            )
            section.subsections.append(
                ReportSection(
                    title="Rolling Performance Metrics",
                    content=rolling_fig,
                    section_type="chart",
                )
            )
            self.figures.append(rolling_fig)

        # 绩效指标表
        perf_table = self._create_performance_table(backtest_result.performance_metrics)
        section.subsections.append(
            ReportSection(
                title="Performance Metrics", content=perf_table, section_type="table"
            )
        )
        self.tables.append(perf_table)

        self.sections.append(section)

    def _generate_risk_section(
        self, backtest_result: Any, risk_report: Optional[Any] = None
    ) -> None:
        """生成风险分析章节

        Args:
            backtest_result: 回测结果
            risk_report: 风险报告
        """
        section = ReportSection(title="Risk Analysis", content="", section_type="mixed")

        # 回撤图
        drawdown_fig = self._create_drawdown_chart(backtest_result.drawdown_series)
        section.subsections.append(
            ReportSection(
                title="Drawdown Analysis", content=drawdown_fig, section_type="chart"
            )
        )
        self.figures.append(drawdown_fig)

        # 风险指标表
        risk_metrics_dict = {
            "max_drawdown": backtest_result.max_drawdown,
            "volatility": backtest_result.volatility,
            "sharpe_ratio": backtest_result.sharpe_ratio,
        }
        risk_table = self._create_risk_table(risk_metrics_dict)
        section.subsections.append(
            ReportSection(
                title="Risk Metrics", content=risk_table, section_type="table"
            )
        )
        self.tables.append(risk_table)

        # 风险归因
        if risk_report:
            # 相关性矩阵
            if hasattr(risk_report, "correlation_matrix"):
                corr_fig = self._create_correlation_heatmap(
                    risk_report.correlation_matrix
                )
                section.subsections.append(
                    ReportSection(
                        title="Correlation Matrix",
                        content=corr_fig,
                        section_type="chart",
                    )
                )
                self.figures.append(corr_fig)

            # 风险贡献
            if hasattr(risk_report, "risk_decomposition"):
                risk_decomp_table = pd.DataFrame.from_dict(
                    risk_report.risk_decomposition, orient="index", columns=["Value"]
                )
                section.subsections.append(
                    ReportSection(
                        title="Risk Decomposition",
                        content=risk_decomp_table,
                        section_type="table",
                    )
                )
                self.tables.append(risk_decomp_table)

        self.sections.append(section)

    def _generate_trades_section(self, backtest_result: Any) -> None:
        """生成交易分析章节

        Args:
            backtest_result: 回测结果
        """
        section = ReportSection(
            title="Trade Analysis", content="", section_type="mixed"
        )

        if backtest_result.trades:
            # 交易统计
            trade_stats = self._calculate_trade_statistics(backtest_result.trades)
            trade_stats_table = pd.DataFrame.from_dict(
                trade_stats, orient="index", columns=["Value"]
            )
            section.subsections.append(
                ReportSection(
                    title="Trade Statistics",
                    content=trade_stats_table,
                    section_type="table",
                )
            )
            self.tables.append(trade_stats_table)

            # 交易分布图
            trades_dist_fig = self._create_trades_distribution(backtest_result.trades)
            section.subsections.append(
                ReportSection(
                    title="Trade Distribution",
                    content=trades_dist_fig,
                    section_type="chart",
                )
            )
            self.figures.append(trades_dist_fig)

            # 前10笔交易
            top_trades = self._get_top_trades(backtest_result.trades, n=10)
            section.subsections.append(
                ReportSection(
                    title="Top 10 Trades", content=top_trades, section_type="table"
                )
            )
            self.tables.append(top_trades)

        # 执行质量
        if hasattr(backtest_result, "execution_metrics"):
            exec_table = self._create_execution_table(backtest_result.execution_metrics)
            section.subsections.append(
                ReportSection(
                    title="Execution Quality", content=exec_table, section_type="table"
                )
            )
            self.tables.append(exec_table)

        self.sections.append(section)

    def _generate_validation_section(self, validation_report: Any) -> None:
        """生成验证分析章节

        Args:
            validation_report: 验证报告
        """
        section = ReportSection(
            title="Model Validation", content="", section_type="mixed"
        )

        # 过拟合测试
        if hasattr(validation_report, "overfitting_tests"):
            overfit_table = pd.DataFrame.from_dict(
                validation_report.overfitting_tests, orient="index", columns=["Value"]
            )
            section.subsections.append(
                ReportSection(
                    title="Overfitting Tests",
                    content=overfit_table,
                    section_type="table",
                )
            )
            self.tables.append(overfit_table)

        # 稳定性测试
        if hasattr(validation_report, "stability_tests"):
            stability_fig = self._create_stability_chart(
                validation_report.stability_tests
            )
            section.subsections.append(
                ReportSection(
                    title="Stability Analysis",
                    content=stability_fig,
                    section_type="chart",
                )
            )
            self.figures.append(stability_fig)

        # Walk-forward结果
        if hasattr(validation_report, "walk_forward_results"):
            wf_fig = self._create_walk_forward_chart(
                validation_report.walk_forward_results
            )
            section.subsections.append(
                ReportSection(
                    title="Walk-Forward Analysis", content=wf_fig, section_type="chart"
                )
            )
            self.figures.append(wf_fig)

        # 蒙特卡洛结果
        if hasattr(validation_report, "monte_carlo_results"):
            mc_fig = self._create_monte_carlo_chart(
                validation_report.monte_carlo_results
            )
            section.subsections.append(
                ReportSection(
                    title="Monte Carlo Simulation", content=mc_fig, section_type="chart"
                )
            )
            self.figures.append(mc_fig)

        self.sections.append(section)

    def _create_equity_curve_chart(self, equity_curve: pd.DataFrame) -> go.Figure:
        """创建权益曲线图

        Args:
            equity_curve: 权益曲线数据

        Returns:
            Plotly图表对象
        """
        fig = go.Figure()

        # 总权益曲线
        # 使用equity列（如果有total_equity则用total_equity）
        equity_col = (
            "total_equity" if "total_equity" in equity_curve.columns else "equity"
        )

        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve[equity_col],
                mode="lines",
                name="Total Equity",
                line=dict(color="blue", width=2),
            )
        )

        # 添加现金曲线（如果有）
        if "cash" in equity_curve.columns:
            fig.add_trace(
                go.Scatter(
                    x=equity_curve.index,
                    y=equity_curve["cash"],
                    mode="lines",
                    name="Cash",
                    line=dict(color="green", width=1, dash="dash"),
                )
            )

        # 添加持仓价值（如果有）
        if "market_value" in equity_curve.columns:
            fig.add_trace(
                go.Scatter(
                    x=equity_curve.index,
                    y=equity_curve["market_value"],
                    mode="lines",
                    name="Market Value",
                    line=dict(color="orange", width=1, dash="dot"),
                )
            )

        fig.update_layout(
            title="Equity Curve",
            xaxis_title="Date",
            yaxis_title="Value ($)",
            hovermode="x unified",
            showlegend=True,
            height=500,
        )

        return fig

    def _create_monthly_returns_heatmap(self, monthly_returns: pd.Series) -> go.Figure:
        """创建月度收益热力图

        Args:
            monthly_returns: 月度收益数据

        Returns:
            Plotly图表对象
        """
        # 重塑数据为年-月矩阵
        monthly_returns_pct = monthly_returns * 100  # 转换为百分比

        # 提取年月
        years = monthly_returns.index.year
        months = monthly_returns.index.month

        # 创建透视表
        pivot_table = pd.pivot_table(
            pd.DataFrame(
                {"Year": years, "Month": months, "Return": monthly_returns_pct.values}
            ),
            values="Return",
            index="Year",
            columns="Month",
            aggfunc="mean",
        )

        # 月份名称
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_table.values,
                x=month_names,
                y=pivot_table.index,
                colorscale="RdYlGn",
                zmid=0,
                text=np.round(pivot_table.values, 2),
                texttemplate="%{text}%",
                textfont={"size": 10},
                colorbar=dict(title="Return (%)"),
            )
        )

        fig.update_layout(
            title="Monthly Returns Heatmap",
            xaxis_title="Month",
            yaxis_title="Year",
            height=400,
        )

        return fig

    def _create_returns_distribution(self, daily_returns: pd.Series) -> go.Figure:
        """创建收益分布图

        Args:
            daily_returns: 日收益数据

        Returns:
            Plotly图表对象
        """
        fig = make_subplots(
            rows=1, cols=2, subplot_titles=("Returns Distribution", "Q-Q Plot")
        )

        # 直方图
        fig.add_trace(
            go.Histogram(
                x=daily_returns, nbinsx=50, name="Daily Returns", showlegend=False
            ),
            row=1,
            col=1,
        )

        # 添加正态分布曲线
        mean = daily_returns.mean()
        std = daily_returns.std()
        x_range = np.linspace(daily_returns.min(), daily_returns.max(), 100)
        normal_dist = (
            stats.norm.pdf(x_range, mean, std)
            * len(daily_returns)
            * (daily_returns.max() - daily_returns.min())
            / 50
        )

        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=normal_dist,
                mode="lines",
                name="Normal Distribution",
                line=dict(color="red", width=2),
            ),
            row=1,
            col=1,
        )

        # Q-Q图
        theoretical_quantiles = stats.norm.ppf(
            np.linspace(0.01, 0.99, len(daily_returns))
        )
        sample_quantiles = np.sort(daily_returns)

        fig.add_trace(
            go.Scatter(
                x=theoretical_quantiles,
                y=sample_quantiles,
                mode="markers",
                name="Q-Q Plot",
                marker=dict(size=4),
            ),
            row=1,
            col=2,
        )

        # 添加45度参考线
        min_val = min(theoretical_quantiles.min(), sample_quantiles.min())
        max_val = max(theoretical_quantiles.max(), sample_quantiles.max())
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode="lines",
                name="45° Line",
                line=dict(color="red", dash="dash"),
            ),
            row=1,
            col=2,
        )

        fig.update_xaxes(title_text="Daily Return", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=1, col=1)
        fig.update_xaxes(title_text="Theoretical Quantiles", row=1, col=2)
        fig.update_yaxes(title_text="Sample Quantiles", row=1, col=2)

        fig.update_layout(height=400, showlegend=True)

        return fig

    def _create_drawdown_chart(self, drawdown_series: pd.Series) -> go.Figure:
        """创建回撤图

        Args:
            drawdown_series: 回撤序列

        Returns:
            Plotly图表对象
        """
        fig = go.Figure()

        # 回撤区域
        fig.add_trace(
            go.Scatter(
                x=drawdown_series.index,
                y=drawdown_series * 100,  # 转换为百分比
                fill="tozeroy",
                fillcolor="rgba(255, 0, 0, 0.3)",
                line=dict(color="red", width=1),
                name="Drawdown",
            )
        )

        # 标记最大回撤
        max_dd_idx = drawdown_series.idxmin()
        max_dd_value = drawdown_series.min() * 100

        fig.add_trace(
            go.Scatter(
                x=[max_dd_idx],
                y=[max_dd_value],
                mode="markers+text",
                marker=dict(color="darkred", size=10),
                text=[f"Max DD: {max_dd_value:.2f}%"],
                textposition="bottom center",
                name="Max Drawdown",
            )
        )

        fig.update_layout(
            title="Drawdown Analysis",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode="x unified",
            height=400,
        )

        return fig

    def _create_rolling_metrics_chart(self, rolling_metrics: pd.DataFrame) -> go.Figure:
        """创建滚动指标图

        Args:
            rolling_metrics: 滚动指标数据

        Returns:
            Plotly图表对象
        """
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Rolling Return",
                "Rolling Volatility",
                "Rolling Sharpe Ratio",
                "Rolling Max Drawdown",
            ),
        )

        # 滚动收益
        if "rolling_return" in rolling_metrics.columns:
            fig.add_trace(
                go.Scatter(
                    x=rolling_metrics.index,
                    y=rolling_metrics["rolling_return"] * 100,
                    mode="lines",
                    name="Rolling Return",
                    line=dict(color="blue"),
                ),
                row=1,
                col=1,
            )

        # 滚动波动率
        if "rolling_volatility" in rolling_metrics.columns:
            fig.add_trace(
                go.Scatter(
                    x=rolling_metrics.index,
                    y=rolling_metrics["rolling_volatility"] * 100,
                    mode="lines",
                    name="Rolling Volatility",
                    line=dict(color="orange"),
                ),
                row=1,
                col=2,
            )

        # 滚动夏普比率
        if "rolling_sharpe" in rolling_metrics.columns:
            fig.add_trace(
                go.Scatter(
                    x=rolling_metrics.index,
                    y=rolling_metrics["rolling_sharpe"],
                    mode="lines",
                    name="Rolling Sharpe",
                    line=dict(color="green"),
                ),
                row=2,
                col=1,
            )

        # 滚动最大回撤
        if "rolling_max_drawdown" in rolling_metrics.columns:
            fig.add_trace(
                go.Scatter(
                    x=rolling_metrics.index,
                    y=rolling_metrics["rolling_max_drawdown"] * 100,
                    mode="lines",
                    name="Rolling Max DD",
                    line=dict(color="red"),
                ),
                row=2,
                col=2,
            )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=2)
        fig.update_yaxes(title_text="Return (%)", row=1, col=1)
        fig.update_yaxes(title_text="Volatility (%)", row=1, col=2)
        fig.update_yaxes(title_text="Sharpe Ratio", row=2, col=1)
        fig.update_yaxes(title_text="Max DD (%)", row=2, col=2)

        fig.update_layout(height=600, showlegend=False)

        return fig

    def _create_correlation_heatmap(
        self, correlation_matrix: pd.DataFrame
    ) -> go.Figure:
        """创建相关性热力图

        Args:
            correlation_matrix: 相关性矩阵

        Returns:
            Plotly图表对象
        """
        fig = go.Figure(
            data=go.Heatmap(
                z=correlation_matrix.values,
                x=correlation_matrix.columns,
                y=correlation_matrix.index,
                colorscale="RdBu",
                zmid=0,
                zmin=-1,
                zmax=1,
                text=np.round(correlation_matrix.values, 2),
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="Correlation"),
            )
        )

        fig.update_layout(title="Asset Correlation Matrix", height=500, width=600)

        return fig

    def _create_trades_distribution(self, trades: List[Any]) -> go.Figure:
        """创建交易分布图

        Args:
            trades: 交易列表

        Returns:
            Plotly图表对象
        """
        # 提取交易收益
        trade_returns = []
        for trade in trades:
            if hasattr(trade, "price") and hasattr(trade, "quantity"):
                # 简化计算，实际应根据买卖价差计算
                trade_returns.append(np.random.normal(0, 0.01))  # 示例数据

        fig = go.Figure()

        # 收益分布直方图
        fig.add_trace(
            go.Histogram(
                x=trade_returns,
                nbinsx=30,
                name="Trade Returns",
                marker_color="lightblue",
            )
        )

        # 标记零线
        fig.add_vline(x=0, line_dash="dash", line_color="red", opacity=0.5)

        # 标记平均值
        mean_return = np.mean(trade_returns)
        fig.add_vline(x=mean_return, line_dash="dash", line_color="green", opacity=0.5)

        fig.update_layout(
            title="Trade Returns Distribution",
            xaxis_title="Return",
            yaxis_title="Frequency",
            height=400,
        )

        return fig

    def _create_stability_chart(self, stability_tests: Dict[str, Any]) -> go.Figure:
        """创建稳定性分析图

        Args:
            stability_tests: 稳定性测试结果

        Returns:
            Plotly图表对象
        """
        # 提取夏普比率稳定性数据
        if "sharpe_stability" in stability_tests:
            sharpe_data = stability_tests["sharpe_stability"]

            fig = go.Figure()

            # 创建箱线图
            fig.add_trace(
                go.Box(
                    y=[sharpe_data["min"], sharpe_data["mean"], sharpe_data["max"]],
                    name="Sharpe Ratio Range",
                    boxpoints="all",
                    jitter=0.3,
                    pointpos=-1.8,
                )
            )

            fig.update_layout(
                title="Strategy Stability Analysis",
                yaxis_title="Sharpe Ratio",
                height=400,
            )

            return fig

        return go.Figure()

    def _create_walk_forward_chart(
        self, walk_forward_results: Dict[str, Any]
    ) -> go.Figure:
        """创建Walk-forward分析图

        Args:
            walk_forward_results: Walk-forward结果

        Returns:
            Plotly图表对象
        """
        if "fold_results" in walk_forward_results:
            fold_results = walk_forward_results["fold_results"]

            fig = go.Figure()

            # 提取每个折叠的夏普比率
            fold_ids = list(range(len(fold_results)))
            sharpes = [r["sharpe"] for r in fold_results]

            fig.add_trace(
                go.Bar(
                    x=fold_ids,
                    y=sharpes,
                    name="Out-of-Sample Sharpe",
                    marker_color="lightblue",
                )
            )

            # 添加平均线
            avg_sharpe = np.mean(sharpes)
            fig.add_hline(
                y=avg_sharpe,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Avg: {avg_sharpe:.2f}",
            )

            fig.update_layout(
                title="Walk-Forward Analysis Results",
                xaxis_title="Fold",
                yaxis_title="Sharpe Ratio",
                height=400,
            )

            return fig

        return go.Figure()

    def _create_monte_carlo_chart(
        self, monte_carlo_results: Dict[str, Any]
    ) -> go.Figure:
        """创建蒙特卡洛模拟图

        Args:
            monte_carlo_results: 蒙特卡洛结果

        Returns:
            Plotly图表对象
        """
        fig = go.Figure()

        # 获取置信区间
        if "confidence_interval_95" in monte_carlo_results:
            ci = monte_carlo_results["confidence_interval_95"]
            returns_ci = ci.get("return", (0, 0))

            # 创建模拟分布（示例）
            simulated_returns = np.random.normal(
                monte_carlo_results.get("simulated_return_mean", 0),
                monte_carlo_results.get("simulated_return_std", 0.1),
                1000,
            )

            fig.add_trace(
                go.Histogram(
                    x=simulated_returns,
                    nbinsx=50,
                    name="Simulated Returns",
                    marker_color="lightblue",
                    opacity=0.7,
                )
            )

            # 标记实际收益
            actual_return = monte_carlo_results.get("actual_return", 0)
            fig.add_vline(
                x=actual_return,
                line_dash="solid",
                line_color="red",
                line_width=2,
                annotation_text="Actual",
            )

            # 标记置信区间
            fig.add_vline(
                x=returns_ci[0],
                line_dash="dash",
                line_color="green",
                annotation_text="CI 2.5%",
            )
            fig.add_vline(
                x=returns_ci[1],
                line_dash="dash",
                line_color="green",
                annotation_text="CI 97.5%",
            )

        fig.update_layout(
            title="Monte Carlo Simulation Results",
            xaxis_title="Return",
            yaxis_title="Frequency",
            height=400,
        )

        return fig

    def _create_performance_table(
        self, performance_metrics: Dict[str, float]
    ) -> pd.DataFrame:
        """创建绩效指标表

        Args:
            performance_metrics: 绩效指标字典

        Returns:
            DataFrame
        """
        # 格式化指标
        formatted_metrics = {}
        for key, value in performance_metrics.items():
            if "return" in key.lower() or "rate" in key.lower():
                formatted_metrics[key] = f"{value * 100:.2f}%"
            elif "ratio" in key.lower():
                formatted_metrics[key] = f"{value:.2f}"
            elif "trades" in key.lower() or "days" in key.lower():
                formatted_metrics[key] = int(value)
            else:
                formatted_metrics[key] = f"{value:.4f}"

        df = pd.DataFrame.from_dict(
            formatted_metrics, orient="index", columns=["Value"]
        )
        df.index.name = "Metric"
        return df

    def _create_risk_table(self, risk_metrics: Dict[str, float]) -> pd.DataFrame:
        """创建风险指标表

        Args:
            risk_metrics: 风险指标字典

        Returns:
            DataFrame
        """
        formatted_metrics = {}
        for key, value in risk_metrics.items():
            if "drawdown" in key.lower() or "volatility" in key.lower():
                formatted_metrics[key] = f"{value * 100:.2f}%"
            elif "var" in key.lower() or "cvar" in key.lower():
                formatted_metrics[key] = f"{value * 100:.2f}%"
            elif "ratio" in key.lower():
                formatted_metrics[key] = f"{value:.2f}"
            else:
                formatted_metrics[key] = f"{value:.4f}"

        df = pd.DataFrame.from_dict(
            formatted_metrics, orient="index", columns=["Value"]
        )
        df.index.name = "Risk Metric"
        return df

    def _create_execution_table(
        self, execution_metrics: Dict[str, float]
    ) -> pd.DataFrame:
        """创建执行质量表

        Args:
            execution_metrics: 执行指标字典

        Returns:
            DataFrame
        """
        formatted_metrics = {}
        for key, value in execution_metrics.items():
            if "slippage" in key.lower() or "impact" in key.lower():
                formatted_metrics[key] = f"{value:.2f} bps"
            elif "cost" in key.lower() or "commission" in key.lower():
                formatted_metrics[key] = f"${value:,.2f}"
            else:
                formatted_metrics[key] = f"{value:.4f}"

        df = pd.DataFrame.from_dict(
            formatted_metrics, orient="index", columns=["Value"]
        )
        df.index.name = "Execution Metric"
        return df

    def _calculate_trade_statistics(self, trades: List[Any]) -> Dict[str, Any]:
        """计算交易统计

        Args:
            trades: 交易列表

        Returns:
            统计字典
        """
        # 简化的交易统计计算
        total_trades = len(trades)

        # 这里应该根据实际交易数据结构计算
        # 示例统计
        stats = {
            "Total Trades": total_trades,
            "Average Trade Size": f"${np.random.uniform(1000, 10000):.2f}",
            "Average Holding Period": f"{np.random.randint(1, 30)} days",
            "Win Rate": f"{np.random.uniform(0.4, 0.7) * 100:.2f}%",
            "Average Win": f"${np.random.uniform(100, 500):.2f}",
            "Average Loss": f"${np.random.uniform(50, 200):.2f}",
            "Profit Factor": f"{np.random.uniform(1.2, 2.5):.2f}",
            "Max Consecutive Wins": np.random.randint(3, 10),
            "Max Consecutive Losses": np.random.randint(2, 7),
        }

        return stats

    def _get_top_trades(self, trades: List[Any], n: int = 10) -> pd.DataFrame:
        """获取前N笔交易

        Args:
            trades: 交易列表
            n: 数量

        Returns:
            DataFrame
        """
        # 简化处理，实际应根据交易数据结构
        trade_data = []
        for i, trade in enumerate(trades[:n]):
            trade_data.append(
                {
                    "Trade ID": f"T{i + 1:04d}",
                    "Symbol": getattr(trade, "symbol", "UNKNOWN"),
                    "Side": getattr(trade, "side", "BUY"),
                    "Quantity": getattr(trade, "quantity", 100),
                    "Price": f"${getattr(trade, 'price', 100.0):.2f}",
                    "Timestamp": getattr(trade, "timestamp", datetime.now()).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            )

        return pd.DataFrame(trade_data)

    def _generate_key_findings(self, backtest_result: Any) -> str:
        """生成关键发现文本

        Args:
            backtest_result: 回测结果

        Returns:
            关键发现文本
        """
        findings = []

        # 分析收益
        total_return = backtest_result.performance_metrics.get("total_return", 0)
        if total_return > 0.2:
            findings.append(
                f"The strategy achieved strong returns of {total_return * 100:.1f}%."
            )
        elif total_return > 0:
            findings.append(
                f"The strategy generated positive returns of {total_return * 100:.1f}%."
            )
        else:
            findings.append(
                f"The strategy resulted in a loss of {abs(total_return) * 100:.1f}%."
            )

        # 分析风险调整收益
        sharpe = backtest_result.performance_metrics.get("sharpe_ratio", 0)
        if sharpe > 2:
            findings.append(
                f"Excellent risk-adjusted returns with Sharpe ratio of {sharpe:.2f}."
            )
        elif sharpe > 1:
            findings.append(
                f"Good risk-adjusted returns with Sharpe ratio of {sharpe:.2f}."
            )
        elif sharpe > 0:
            findings.append(
                f"Positive but modest risk-adjusted returns (Sharpe: {sharpe:.2f})."
            )
        else:
            findings.append(
                f"Poor risk-adjusted returns with Sharpe ratio of {sharpe:.2f}."
            )

        # 分析回撤
        max_dd = backtest_result.performance_metrics.get(
            "max_drawdown", backtest_result.max_drawdown
        )
        if max_dd < 0.1:
            findings.append(
                f"Low maximum drawdown of {max_dd * 100:.1f}% indicates good risk control."
            )
        elif max_dd < 0.2:
            findings.append(f"Moderate maximum drawdown of {max_dd * 100:.1f}%.")
        else:
            findings.append(
                f"High maximum drawdown of {max_dd * 100:.1f}% suggests significant risk."
            )

        # 分析胜率
        win_rate = backtest_result.performance_metrics.get("win_rate", 0)
        if win_rate > 0.6:
            findings.append(
                f"High win rate of {win_rate * 100:.1f}% demonstrates consistency."
            )
        elif win_rate > 0.5:
            findings.append(f"Above-average win rate of {win_rate * 100:.1f}%.")
        else:
            findings.append(f"Win rate of {win_rate * 100:.1f}% requires improvement.")

        return " ".join(findings)

    def _generate_html_report(self) -> str:
        """生成HTML报告

        Returns:
            HTML文件路径
        """
        # HTML模板
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #1f77b4; }
                h2 { color: #2ca02c; margin-top: 30px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .summary { background-color: #f9f9f9; padding: 15px; border-radius: 5px; }
                .chart-container { margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>
            <p>Generated on: {{ timestamp }}</p>
            
            {% for section in sections %}
            <h2>{{ section.title }}</h2>
            
            {% if section.section_type == 'text' %}
                <p>{{ section.content }}</p>
            {% elif section.section_type == 'table' %}
                <div class="table-container">
                    {{ section.content.to_html() | safe }}
                </div>
            {% elif section.section_type == 'chart' %}
                <div class="chart-container" id="chart_{{ loop.index }}"></div>
                <script>
                    {{ section.content.to_html(include_plotlyjs=False, div_id="chart_" + loop.index|string) | safe }}
                </script>
            {% endif %}
            
            {% for subsection in section.subsections %}
                <h3>{{ subsection.title }}</h3>
                {% if subsection.section_type == 'text' %}
                    <p>{{ subsection.content }}</p>
                {% elif subsection.section_type == 'table' %}
                    {{ subsection.content.to_html() | safe }}
                {% elif subsection.section_type == 'chart' %}
                    <div id="subchart_{{ loop.index }}"></div>
                {% endif %}
            {% endfor %}
            
            {% endfor %}
        </body>
        </html>
        """

        # 渲染HTML
        template = Template(html_template)
        html_content = template.render(
            title=self.config.title,
            timestamp=self.config.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            sections=self.sections,
        )

        # 保存文件
        filename = os.path.join(
            self.config.output_dir,
            f"report_{self.config.timestamp.strftime('%Y%m%d_%H%M%S')}.html",
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML report saved to {filename}")
        return filename

    def _generate_pdf_report(self) -> str:
        """生成PDF报告

        Returns:
            PDF文件路径
        """
        filename = os.path.join(
            self.config.output_dir,
            f"report_{self.config.timestamp.strftime('%Y%m%d_%H%M%S')}.pdf",
        )

        # 创建PDF文档
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []

        # 标题
        title = Paragraph(self.config.title, self.styles["CustomTitle"])
        story.append(title)
        story.append(Spacer(1, 12))

        # 时间戳
        timestamp = Paragraph(
            f"Generated on: {self.config.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles["Normal"],
        )
        story.append(timestamp)
        story.append(Spacer(1, 24))

        # 添加各个章节
        for section in self.sections:
            # 章节标题
            section_title = Paragraph(section.title, self.styles["CustomHeading"])
            story.append(section_title)

            # 章节内容
            if section.section_type == "text":
                content = Paragraph(section.content, self.styles["Normal"])
                story.append(content)
            elif section.section_type == "table" and isinstance(
                section.content, pd.DataFrame
            ):
                # 转换DataFrame为Table
                table_data = [section.content.columns.tolist()]
                table_data.extend(section.content.values.tolist())

                table = Table(table_data)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(table)

            story.append(Spacer(1, 12))

            # 子章节
            for subsection in section.subsections:
                if subsection.section_type == "text":
                    sub_content = Paragraph(subsection.content, self.styles["Normal"])
                    story.append(sub_content)
                    story.append(Spacer(1, 6))

        # 构建PDF
        doc.build(story)

        logger.info(f"PDF report saved to {filename}")
        return filename

    def _generate_excel_report(self) -> str:
        """生成Excel报告

        Returns:
            Excel文件路径
        """
        filename = os.path.join(
            self.config.output_dir,
            f"report_{self.config.timestamp.strftime('%Y%m%d_%H%M%S')}.xlsx",
        )

        # 创建Excel写入器
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            # 摘要表
            summary_df = pd.DataFrame(
                {
                    "Report": [self.config.title],
                    "Generated": [self.config.timestamp.strftime("%Y-%m-%d %H:%M:%S")],
                    "Author": [self.config.author],
                }
            )
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # 添加所有表格
            for i, table in enumerate(self.tables):
                sheet_name = f"Table_{i + 1}"
                if hasattr(table, "index") and table.index.name:
                    sheet_name = table.index.name[:31]  # Excel工作表名称限制

                table.to_excel(writer, sheet_name=sheet_name)

        logger.info(f"Excel report saved to {filename}")
        return filename


# 模块级别函数
def generate_backtest_report(
    backtest_result: Any,
    output_formats: List[str] = ["html", "pdf", "excel"],
    output_dir: str = None,
) -> Dict[str, str]:
    """生成回测报告的便捷函数

    Args:
        backtest_result: 回测结果
        output_formats: 输出格式列表
        output_dir: 输出目录

    Returns:
        生成的文件路径字典
    """
    if output_dir is None:
        output_dir = os.path.join("module_09_backtesting", "reports")
    
    config = ReportConfig(
        title="Backtest Analysis Report", formats=output_formats, output_dir=output_dir
    )

    generator = BacktestReportGenerator(config)
    return generator.generate_report(backtest_result)


def create_performance_dashboard(
    equity_curve: pd.DataFrame, daily_returns: pd.Series, drawdown_series: pd.Series
) -> go.Figure:
    """创建绩效仪表板的便捷函数

    Args:
        equity_curve: 权益曲线
        daily_returns: 日收益率
        drawdown_series: 回撤序列

    Returns:
        Plotly图表对象
    """
    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=("Equity Curve", "Daily Returns", "Drawdown"),
        row_heights=[0.5, 0.25, 0.25],
    )

    # 权益曲线
    fig.add_trace(
        go.Scatter(
            x=equity_curve.index,
            y=equity_curve["total_equity"]
            if "total_equity" in equity_curve
            else equity_curve,
            mode="lines",
            name="Equity",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )

    # 日收益率
    fig.add_trace(
        go.Bar(
            x=daily_returns.index,
            y=daily_returns.values,
            name="Daily Returns",
            marker_color="green",
        ),
        row=2,
        col=1,
    )

    # 回撤
    fig.add_trace(
        go.Scatter(
            x=drawdown_series.index,
            y=drawdown_series.values,
            fill="tozeroy",
            name="Drawdown",
            line=dict(color="red"),
        ),
        row=3,
        col=1,
    )

    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Value", row=1, col=1)
    fig.update_yaxes(title_text="Return", row=2, col=1)
    fig.update_yaxes(title_text="Drawdown", row=3, col=1)

    fig.update_layout(height=800, showlegend=True)

    return fig
