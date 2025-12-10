"""
报告生成器模块
生成各类投资报告
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader, Template

from common.exceptions import ModelError
from common.logging_system import setup_logger

logger = setup_logger("report_generator")


class ReportType(Enum):
    """报告类型枚举"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"
    REAL_TIME = "real_time"


class ReportFormat(Enum):
    """报告格式枚举"""

    HTML = "html"
    EXCEL = "excel"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class ReportConfig:
    """报告配置"""

    report_type: ReportType
    format: ReportFormat
    include_charts: bool = True
    include_metrics: bool = True
    include_positions: bool = True
    include_transactions: bool = True
    include_attribution: bool = True
    include_risk_analysis: bool = True
    include_market_analysis: bool = False
    include_recommendations: bool = False
    template_name: Optional[str] = None
    custom_sections: List[str] = field(default_factory=list)


@dataclass
class ReportData:
    """报告数据"""

    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    portfolio_summary: Dict[str, Any]
    performance_metrics: Dict[str, float]
    positions: List[Dict[str, Any]]
    transactions: List[Dict[str, Any]]
    risk_metrics: Dict[str, float]
    attribution_analysis: Dict[str, float]
    market_analysis: Optional[Dict[str, Any]] = None
    charts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReportGenerator:
    """报告生成器类"""

    def __init__(
        self,
        template_dir: str = "templates",
        output_dir: str = None,
    ):
        """初始化报告生成器

        Args:
            template_dir: 模板目录
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = os.path.join("module_06_monitoring_alerting", "reports")
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, config: ReportConfig, data: Dict[str, Any]) -> str:
        """生成报告

        Args:
            config: 报告配置
            data: 报告数据

        Returns:
            报告文件路径
        """
        logger.info(
            f"Generating {config.report_type.value} report in {config.format.value} format"
        )

        # 准备报告数据
        report_data = self._prepare_report_data(config, data)

        # 生成图表
        if config.include_charts:
            report_data.charts = self._generate_charts(report_data)

        # 根据格式生成报告
        if config.format == ReportFormat.HTML:
            file_path = self._generate_html_report(config, report_data)
        elif config.format == ReportFormat.EXCEL:
            file_path = self._generate_excel_report(config, report_data)
        elif config.format == ReportFormat.JSON:
            file_path = self._generate_json_report(config, report_data)
        elif config.format == ReportFormat.MARKDOWN:
            file_path = self._generate_markdown_report(config, report_data)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        logger.info(f"Report generated: {file_path}")
        return file_path

    def _prepare_report_data(
        self, config: ReportConfig, raw_data: Dict[str, Any]
    ) -> ReportData:
        """准备报告数据

        Args:
            config: 报告配置
            raw_data: 原始数据

        Returns:
            报告数据对象
        """
        # 确定报告周期
        period_end = datetime.now()

        if config.report_type == ReportType.DAILY:
            period_start = period_end - timedelta(days=1)
        elif config.report_type == ReportType.WEEKLY:
            period_start = period_end - timedelta(weeks=1)
        elif config.report_type == ReportType.MONTHLY:
            period_start = period_end - timedelta(days=30)
        elif config.report_type == ReportType.QUARTERLY:
            period_start = period_end - timedelta(days=90)
        elif config.report_type == ReportType.ANNUAL:
            period_start = period_end - timedelta(days=365)
        else:
            period_start = raw_data.get("period_start", period_end - timedelta(days=30))

        # 提取各部分数据
        report_data = ReportData(
            report_id=f"{config.report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            portfolio_summary=self._extract_portfolio_summary(raw_data),
            performance_metrics=self._calculate_performance_metrics(
                raw_data, period_start, period_end
            ),
            positions=self._extract_positions(raw_data)
            if config.include_positions
            else [],
            transactions=self._extract_transactions(raw_data, period_start, period_end)
            if config.include_transactions
            else [],
            risk_metrics=self._calculate_risk_metrics(raw_data)
            if config.include_risk_analysis
            else {},
            attribution_analysis=self._perform_attribution_analysis(raw_data)
            if config.include_attribution
            else {},
            market_analysis=self._perform_market_analysis(raw_data)
            if config.include_market_analysis
            else None,
        )

        return report_data

    def _extract_portfolio_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取投资组合摘要

        Args:
            data: 原始数据

        Returns:
            投资组合摘要
        """
        return {
            "total_value": data.get("portfolio_value", 0),
            "cash_balance": data.get("cash_balance", 0),
            "positions_value": data.get("positions_value", 0),
            "number_of_positions": len(data.get("positions", [])),
            "leverage": data.get("leverage", 1.0),
            "margin_used": data.get("margin_used", 0),
            "buying_power": data.get("buying_power", 0),
        }

    def _calculate_performance_metrics(
        self, data: Dict[str, Any], period_start: datetime, period_end: datetime
    ) -> Dict[str, float]:
        """计算绩效指标

        Args:
            data: 原始数据
            period_start: 周期开始
            period_end: 周期结束

        Returns:
            绩效指标字典
        """
        metrics = {}

        # 收益率
        start_value = data.get("start_value", 100000)
        end_value = data.get("portfolio_value", 100000)

        metrics["total_return"] = (
            (end_value - start_value) / start_value if start_value > 0 else 0
        )
        metrics["daily_return"] = data.get("daily_return", 0)

        # 年化指标
        days = (period_end - period_start).days
        if days > 0 and abs(metrics["total_return"]) < 10:  # 防止溢出
            try:
                metrics["annualized_return"] = (1 + metrics["total_return"]) ** (
                    365 / days
                ) - 1
            except (OverflowError, ValueError):
                # 如果计算溢出，使用简化公式
                metrics["annualized_return"] = metrics["total_return"] * (365 / days)
        elif days > 0:
            # 收益率过大时使用线性近似
            metrics["annualized_return"] = metrics["total_return"] * (365 / days)
        else:
            metrics["annualized_return"] = 0

        # 风险调整收益
        metrics["sharpe_ratio"] = data.get("sharpe_ratio", 0)
        metrics["sortino_ratio"] = data.get("sortino_ratio", 0)
        metrics["calmar_ratio"] = data.get("calmar_ratio", 0)

        # 风险指标
        metrics["volatility"] = data.get("volatility", 0)
        metrics["max_drawdown"] = data.get("max_drawdown", 0)
        metrics["var_95"] = data.get("var_95", 0)

        # 其他指标
        metrics["win_rate"] = data.get("win_rate", 0)
        metrics["profit_factor"] = data.get("profit_factor", 0)
        metrics["average_win"] = data.get("average_win", 0)
        metrics["average_loss"] = data.get("average_loss", 0)

        return metrics

    def _extract_positions(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取持仓信息

        Args:
            data: 原始数据

        Returns:
            持仓列表
        """
        positions = []

        for position in data.get("positions", []):
            positions.append(
                {
                    "symbol": position.get("symbol"),
                    "quantity": position.get("quantity"),
                    "avg_cost": position.get("avg_cost"),
                    "current_price": position.get("current_price"),
                    "market_value": position.get("market_value"),
                    "unrealized_pnl": position.get("unrealized_pnl"),
                    "unrealized_pnl_pct": position.get("return_pct"),
                    "weight": position.get("weight"),
                    "days_held": position.get("holding_period_days"),
                }
            )

        return positions

    def _extract_transactions(
        self, data: Dict[str, Any], period_start: datetime, period_end: datetime
    ) -> List[Dict[str, Any]]:
        """提取交易记录

        Args:
            data: 原始数据
            period_start: 周期开始
            period_end: 周期结束

        Returns:
            交易列表
        """
        transactions = []

        for transaction in data.get("transactions", []):
            trans_time = transaction.get("timestamp")
            if isinstance(trans_time, str):
                trans_time = datetime.fromisoformat(trans_time)

            if period_start <= trans_time <= period_end:
                transactions.append(
                    {
                        "timestamp": trans_time,
                        "symbol": transaction.get("symbol"),
                        "action": transaction.get("action"),
                        "quantity": transaction.get("quantity"),
                        "price": transaction.get("price"),
                        "commission": transaction.get("commission", 0),
                        "pnl": transaction.get("pnl", 0),
                    }
                )

        return transactions

    def _calculate_risk_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """计算风险指标

        Args:
            data: 原始数据

        Returns:
            风险指标字典
        """
        return {
            "portfolio_beta": data.get("portfolio_beta", 1.0),
            "portfolio_alpha": data.get("portfolio_alpha", 0),
            "tracking_error": data.get("tracking_error", 0),
            "information_ratio": data.get("information_ratio", 0),
            "downside_deviation": data.get("downside_deviation", 0),
            "upside_capture": data.get("upside_capture", 0),
            "downside_capture": data.get("downside_capture", 0),
            "correlation_to_market": data.get("correlation_to_market", 0),
        }

    def _perform_attribution_analysis(self, data: Dict[str, Any]) -> Dict[str, float]:
        """执行归因分析

        Args:
            data: 原始数据

        Returns:
            归因分析结果
        """
        return {
            "allocation_effect": data.get("allocation_effect", 0),
            "selection_effect": data.get("selection_effect", 0),
            "interaction_effect": data.get("interaction_effect", 0),
            "total_effect": data.get("total_attribution", 0),
            "factor_attribution": data.get("factor_attribution", {}),
        }

    def _perform_market_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行市场分析

        Args:
            data: 原始数据

        Returns:
            市场分析结果
        """
        return {
            "market_regime": data.get("market_regime", "unknown"),
            "market_volatility": data.get("market_volatility", 0),
            "market_trend": data.get("market_trend", "neutral"),
            "sector_performance": data.get("sector_performance", {}),
            "correlation_analysis": data.get("correlation_analysis", {}),
            "market_breadth": data.get("market_breadth", 0.5),
        }

    def _generate_charts(self, report_data: ReportData) -> Dict[str, Any]:
        """生成图表

        Args:
            report_data: 报告数据

        Returns:
            图表字典
        """
        charts = {}

        # 生成累计收益曲线
        charts["cumulative_returns"] = self._create_cumulative_returns_chart(
            report_data
        )

        # 生成持仓分布饼图
        if report_data.positions:
            charts["position_allocation"] = self._create_position_allocation_chart(
                report_data
            )

        # 生成风险指标雷达图
        if report_data.risk_metrics:
            charts["risk_radar"] = self._create_risk_radar_chart(report_data)

        # 生成月度收益热力图
        charts["monthly_returns"] = self._create_monthly_returns_heatmap(report_data)

        return charts

    def _create_cumulative_returns_chart(self, report_data: ReportData) -> str:
        """创建累计收益曲线

        Args:
            report_data: 报告数据

        Returns:
            图表HTML或路径
        """
        # 使用Plotly创建交互式图表
        fig = go.Figure()

        # 模拟数据（实际应从report_data提取）
        dates = pd.date_range(
            report_data.period_start, report_data.period_end, freq="D"
        )
        returns = np.random.randn(len(dates)) * 0.01
        cumulative = (1 + returns).cumprod()

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cumulative,
                mode="lines",
                name="Portfolio",
                line=dict(color="blue", width=2),
            )
        )

        fig.update_layout(
            title="Cumulative Returns",
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
            hovermode="x unified",
        )

        return fig.to_html(div_id="cumulative_returns_chart", include_plotlyjs=False)

    def _create_position_allocation_chart(self, report_data: ReportData) -> str:
        """创建持仓分配饼图

        Args:
            report_data: 报告数据

        Returns:
            图表HTML或路径
        """
        positions = report_data.positions

        # 提取数据
        symbols = [p["symbol"] for p in positions[:10]]  # 取前10个
        values = [p["market_value"] for p in positions[:10]]

        fig = go.Figure(data=[go.Pie(labels=symbols, values=values, hole=0.3)])

        fig.update_layout(
            title="Position Allocation",
            annotations=[
                dict(text="Portfolio", x=0.5, y=0.5, font_size=20, showarrow=False)
            ],
        )

        return fig.to_html(div_id="position_allocation_chart", include_plotlyjs=False)

    def _create_risk_radar_chart(self, report_data: ReportData) -> str:
        """创建风险雷达图

        Args:
            report_data: 报告数据

        Returns:
            图表HTML或路径
        """
        categories = list(report_data.risk_metrics.keys())[:6]
        values = list(report_data.risk_metrics.values())[:6]

        fig = go.Figure(
            data=go.Scatterpolar(
                r=values, theta=categories, fill="toself", name="Risk Profile"
            )
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=False,
            title="Risk Profile",
        )

        return fig.to_html(div_id="risk_radar_chart", include_plotlyjs=False)

    def _create_monthly_returns_heatmap(self, report_data: ReportData) -> str:
        """创建月度收益热力图

        Args:
            report_data: 报告数据

        Returns:
            图表HTML或路径
        """
        # 模拟月度收益数据
        months = [
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
        years = ["2023", "2024"]

        z = np.random.randn(len(years), len(months)) * 0.05

        fig = go.Figure(
            data=go.Heatmap(z=z, x=months, y=years, colorscale="RdYlGn", zmid=0)
        )

        fig.update_layout(
            title="Monthly Returns Heatmap", xaxis_title="Month", yaxis_title="Year"
        )

        return fig.to_html(div_id="monthly_returns_heatmap", include_plotlyjs=False)

    def _generate_html_report(
        self, config: ReportConfig, report_data: ReportData
    ) -> str:
        """生成HTML报告

        Args:
            config: 报告配置
            report_data: 报告数据

        Returns:
            文件路径
        """
        html_content = self._generate_html_content(config, report_data)

        file_name = f"{report_data.report_id}.html"
        file_path = os.path.join(self.output_dir, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path

    def _generate_html_content(
        self, config: ReportConfig, report_data: ReportData
    ) -> str:
        """生成HTML内容

        Args:
            config: 报告配置
            report_data: 报告数据

        Returns:
            HTML内容
        """
        # 选择模板
        template_name = (
            config.template_name or f"{config.report_type.value}_report.html"
        )

        # 如果模板不存在，使用默认模板
        try:
            template = self.env.get_template(template_name)
        except:
            template = self._get_default_template()

        # 渲染模板
        html_content = template.render(
            report=report_data,
            config=config,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return html_content

    def _generate_excel_report(
        self, config: ReportConfig, report_data: ReportData
    ) -> str:
        """生成Excel报告

        Args:
            config: 报告配置
            report_data: 报告数据

        Returns:
            文件路径
        """
        file_name = f"{report_data.report_id}.xlsx"
        file_path = os.path.join(self.output_dir, file_name)

        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            # 写入摘要
            summary_df = pd.DataFrame([report_data.portfolio_summary])
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # 写入绩效指标
            metrics_df = pd.DataFrame([report_data.performance_metrics])
            metrics_df.to_excel(writer, sheet_name="Performance", index=False)

            # 写入持仓
            if report_data.positions:
                positions_df = pd.DataFrame(report_data.positions)
                positions_df.to_excel(writer, sheet_name="Positions", index=False)

            # 写入交易记录
            if report_data.transactions:
                transactions_df = pd.DataFrame(report_data.transactions)
                transactions_df.to_excel(writer, sheet_name="Transactions", index=False)

            # 写入风险指标
            if report_data.risk_metrics:
                risk_df = pd.DataFrame([report_data.risk_metrics])
                risk_df.to_excel(writer, sheet_name="Risk", index=False)

        return file_path

    def _generate_json_report(
        self, config: ReportConfig, report_data: ReportData
    ) -> str:
        """生成JSON报告

        Args:
            config: 报告配置
            report_data: 报告数据

        Returns:
            文件路径
        """
        file_name = f"{report_data.report_id}.json"
        file_path = os.path.join(self.output_dir, file_name)

        # 转换为可序列化的字典
        report_dict = {
            "report_id": report_data.report_id,
            "generated_at": report_data.generated_at.isoformat(),
            "period_start": report_data.period_start.isoformat(),
            "period_end": report_data.period_end.isoformat(),
            "portfolio_summary": report_data.portfolio_summary,
            "performance_metrics": report_data.performance_metrics,
            "positions": report_data.positions,
            "transactions": [
                {**t, "timestamp": t["timestamp"].isoformat()}
                for t in report_data.transactions
            ],
            "risk_metrics": report_data.risk_metrics,
            "attribution_analysis": report_data.attribution_analysis,
            "market_analysis": report_data.market_analysis,
            "metadata": report_data.metadata,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        return file_path

    def _generate_markdown_report(
        self, config: ReportConfig, report_data: ReportData
    ) -> str:
        """生成Markdown报告

        Args:
            config: 报告配置
            report_data: 报告数据

        Returns:
            文件路径
        """
        file_name = f"{report_data.report_id}.md"
        file_path = os.path.join(self.output_dir, file_name)

        # 生成Markdown内容
        md_content = self._generate_markdown_content(report_data)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return file_path

    def _generate_markdown_content(self, report_data: ReportData) -> str:
        """生成Markdown内容

        Args:
            report_data: 报告数据

        Returns:
            Markdown内容
        """
        md = []

        # 标题
        md.append(f"# Portfolio Report - {report_data.report_id}")
        md.append(
            f"\n**Generated at:** {report_data.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        md.append(
            f"\n**Period:** {report_data.period_start.strftime('%Y-%m-%d')} to {report_data.period_end.strftime('%Y-%m-%d')}"
        )

        # 投资组合摘要
        md.append("\n## Portfolio Summary")
        for key, value in report_data.portfolio_summary.items():
            md.append(f"- **{key.replace('_', ' ').title()}:** {value:,.2f}")

        # 绩效指标
        md.append("\n## Performance Metrics")
        for key, value in report_data.performance_metrics.items():
            md.append(f"- **{key.replace('_', ' ').title()}:** {value:.4f}")

        # 持仓
        if report_data.positions:
            md.append("\n## Positions")
            md.append(
                "\n| Symbol | Quantity | Market Value | Unrealized P&L | Weight |"
            )
            md.append("|--------|----------|--------------|----------------|--------|")

            for pos in report_data.positions[:10]:
                md.append(
                    f"| {pos['symbol']} | {pos['quantity']} | "
                    f"${pos['market_value']:,.2f} | ${pos['unrealized_pnl']:,.2f} | "
                    f"{pos['weight']:.2%} |"
                )

        # 风险指标
        if report_data.risk_metrics:
            md.append("\n## Risk Metrics")
            for key, value in report_data.risk_metrics.items():
                md.append(f"- **{key.replace('_', ' ').title()}:** {value:.4f}")

        return "\n".join(md)

    def _get_default_template(self) -> Template:
        """获取默认模板

        Returns:
            默认模板对象
        """
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Portfolio Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Portfolio Report - {{ report.report_id }}</h1>
            <p><strong>Generated at:</strong> {{ generated_at }}</p>
            <p><strong>Period:</strong> {{ report.period_start }} to {{ report.period_end }}</p>
            
            <h2>Portfolio Summary</h2>
            <table>
                {% for key, value in report.portfolio_summary.items() %}
                <tr>
                    <td>{{ key }}</td>
                    <td>{{ value }}</td>
                </tr>
                {% endfor %}
            </table>
            
            <h2>Performance Metrics</h2>
            <table>
                {% for key, value in report.performance_metrics.items() %}
                <tr>
                    <td>{{ key }}</td>
                    <td>{{ value }}</td>
                </tr>
                {% endfor %}
            </table>
            
            {% if config.include_charts %}
            <h2>Charts</h2>
            {% for chart_name, chart_html in report.charts.items() %}
            <div>{{ chart_html|safe }}</div>
            {% endfor %}
            {% endif %}
        </body>
        </html>
        """

        return Template(template_str)
