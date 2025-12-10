"""
报告生成器模块
负责生成各类投资报告（默认输出JSON数据格式和SQLite数据库）
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import markdown
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader, Template

from common.data_structures import Position, Signal
from common.exceptions import QuantSystemError
from common.logging_system import setup_logger

from .database_manager import get_visualization_database_manager
from .export_manager import ExportManager

logger = setup_logger("report_builder")


@dataclass
class ReportConfig:
    """报告配置数据类"""

    report_type: str  # 'daily', 'weekly', 'monthly', 'performance', 'risk'
    output_format: str = "json"  # 'json', 'csv', 'excel', 'sqlite' (默认JSON + SQLite)
    output_path: Optional[str] = None  # 输出路径，如果为None则自动生成
    save_to_database: bool = True  # 是否保存到SQLite数据库
    include_charts: bool = False  # 是否包含图表（纯数据模式默认关闭）
    include_tables: bool = True
    include_summary: bool = True
    custom_sections: List[str] = field(default_factory=list)
    template_name: Optional[str] = None  # HTML模板（仅当需要HTML时使用）


@dataclass
class ReportSection:
    """报告章节数据类"""

    section_id: str
    title: str
    content_type: str  # 'text', 'table', 'chart', 'metric'
    content: Any
    order: int
    visible: bool = True


@dataclass
class PerformanceMetrics:
    """绩效指标数据类"""

    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    total_trades: int
    winning_trades: int
    losing_trades: int


class ReportBuilder:
    """报告生成器类 - 默认输出JSON数据和SQLite数据库"""

    OUTPUT_DIR = os.path.join("module_11_visualization", "reports")  # 数据文件输出目录
    DATABASE_PATH = os.path.join("data", "module11_visualization.db")  # SQLite数据库路径

    def __init__(self, output_dir: Optional[str] = None, db_path: Optional[str] = None):
        """初始化报告生成器

        Args:
            output_dir: 输出目录（默认为 module_11_visualization/reports/）
            db_path: 数据库路径（默认为 data/module11_visualization.db）
        """
        self.output_dir = Path(output_dir or self.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.db_manager = get_visualization_database_manager(
            db_path or self.DATABASE_PATH
        )
        self.export_manager = ExportManager(str(self.output_dir))

        self.sections: Dict[str, ReportSection] = {}
        self.metadata: Dict[str, Any] = {}

        logger.info(f"报告生成器已初始化")
        logger.info(f"  - 数据输出目录: {self.output_dir.absolute()}")
        logger.info(f"  - SQLite数据库: {self.db_manager.db_path}")

    def generate_daily_report(
        self,
        date: datetime,
        portfolio_data: Dict[str, Any],
        positions: List[Position],
        signals: List[Signal],
        market_data: pd.DataFrame,
        config: Optional[ReportConfig] = None,
    ) -> Dict[str, Any]:
        """生成日报（默认输出JSON数据并保存到SQLite）

        Args:
            date: 报告日期
            portfolio_data: 组合数据
            positions: 持仓列表
            signals: 信号列表
            market_data: 市场数据
            config: 报告配置

        Returns:
            包含报告数据和保存路径的字典
        """
        if config is None:
            config = ReportConfig(report_type="daily")

        # 清空之前的章节
        self.sections.clear()

        # 设置元数据
        self.metadata = {
            "report_date": date.strftime("%Y-%m-%d"),
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": "Daily Report",
        }

        # 收集报告数据（纯数据，不生成HTML）
        report_data = {
            "metadata": self.metadata,
            "summary": self._collect_summary_data(portfolio_data, date)
            if config.include_summary
            else {},
            "positions": self._collect_positions_data(positions),
            "signals": self._collect_signals_data(signals, date),
            "market_overview": self._collect_market_overview_data(market_data),
            "performance": self._collect_performance_data(portfolio_data),
        }

        # 保存报告数据
        return self._save_report_data(report_data, config)

    def generate_weekly_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        weekly_data: Dict[str, Any],
        config: Optional[ReportConfig] = None,
    ) -> Dict[str, Any]:
        """生成周报（默认输出JSON数据并保存到SQLite）

        Args:
            start_date: 开始日期
            end_date: 结束日期
            weekly_data: 周数据
            config: 报告配置

        Returns:
            包含报告数据和保存路径的字典
        """
        if config is None:
            config = ReportConfig(report_type="weekly")

        self.sections.clear()

        self.metadata = {
            "report_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": "Weekly Summary",
        }

        # 收集周报数据
        report_data = {
            "metadata": self.metadata,
            "weekly_overview": weekly_data.get("overview", {}),
            "weekly_performance": weekly_data.get("performance", {}),
            "trade_statistics": weekly_data.get("trades", []),
        }

        # 保存报告数据
        return self._save_report_data(report_data, config)

    def generate_performance_report(
        self,
        performance_data: Dict[str, Any],
        metrics: PerformanceMetrics,
        config: Optional[ReportConfig] = None,
    ) -> Dict[str, Any]:
        """生成绩效报告（默认输出JSON数据并保存到SQLite）

        Args:
            performance_data: 绩效数据
            metrics: 绩效指标
            config: 报告配置

        Returns:
            包含报告数据和保存路径的字典
        """
        if config is None:
            config = ReportConfig(report_type="performance")

        self.sections.clear()

        self.metadata = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "report_type": "Performance Analysis Report",
        }

        # 收集绩效报告数据
        report_data = {
            "metadata": self.metadata,
            "performance_summary": self._collect_metrics_data(metrics),
            "return_analysis": performance_data.get("returns", {}),
            "risk_analysis": performance_data.get("risk", {}),
            "trade_analysis": {
                "avg_win": metrics.avg_win,
                "avg_loss": metrics.avg_loss,
                "best_trade": metrics.best_trade,
                "worst_trade": metrics.worst_trade,
                "win_loss_ratio": metrics.avg_win / abs(metrics.avg_loss)
                if metrics.avg_loss != 0
                else 0,
            },
        }

        # 保存报告数据
        return self._save_report_data(report_data, config)

    def create_custom_report(
        self, title: str, sections: List[ReportSection], config: ReportConfig
    ) -> str:
        """创建自定义报告

        Args:
            title: 报告标题
            sections: 章节列表
            config: 报告配置

        Returns:
            报告内容
        """
        self.sections.clear()

        self.metadata = {
            "report_title": title,
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "report_type": "Custom Report",
        }

        for section in sections:
            self._add_section(section)

        return self._render_report(config)

    def export_to_pdf(self, html_content: str, output_path: str) -> bool:
        """导出为PDF（功能已移除，改为导出HTML）

        Args:
            html_content: HTML内容
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            # PDF功能已移除，改为保存HTML
            html_path = output_path.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Report exported to HTML: {html_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export HTML: {e}")
            return False

    def export_to_markdown(self, content: Dict[str, Any], output_path: str) -> bool:
        """导出为Markdown

        Args:
            content: 内容字典
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            md_content = self._generate_markdown(content)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info(f"Report exported to Markdown: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export Markdown: {e}")
            return False

    def schedule_report_delivery(
        self,
        report_type: str,
        schedule: str,  # 'daily', 'weekly', 'monthly'
        recipients: List[str],
        delivery_method: str = "email",
    ) -> bool:
        """设置报告定时发送

        Args:
            report_type: 报告类型
            schedule: 发送计划
            recipients: 接收者列表
            delivery_method: 发送方式

        Returns:
            是否成功设置
        """
        # 实际实现需要集成任务调度器
        logger.info(f"Scheduled {report_type} report delivery: {schedule}")
        return True

    # ==================== 数据收集方法 ====================

    def _collect_summary_data(
        self, portfolio_data: Dict[str, Any], date: datetime
    ) -> Dict[str, Any]:
        """收集概要数据

        Args:
            portfolio_data: 组合数据
            date: 日期

        Returns:
            概要数据字典
        """
        return {
            "date": date.strftime("%Y-%m-%d"),
            "total_value": portfolio_data.get("total_value", 0),
            "daily_pnl": portfolio_data.get("daily_pnl", 0),
            "daily_return": portfolio_data.get("daily_return", 0),
            "ytd_return": portfolio_data.get("ytd_return", 0),
        }

    def _collect_positions_data(
        self, positions: List[Position]
    ) -> List[Dict[str, Any]]:
        """收集持仓数据

        Args:
            positions: 持仓列表

        Returns:
            持仓数据列表
        """
        if not positions:
            return []

        positions_data = []
        for pos in positions:
            positions_data.append(
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "return_pct": pos.return_pct,
                }
            )
        return positions_data

    def _collect_signals_data(
        self, signals: List[Signal], date: datetime
    ) -> List[Dict[str, Any]]:
        """收集交易信号数据

        Args:
            signals: 信号列表
            date: 日期

        Returns:
            信号数据列表
        """
        # 筛选当日信号
        today_signals = [s for s in signals if s.timestamp.date() == date.date()]

        if not today_signals:
            return []

        signals_data = []
        for signal in today_signals:
            signals_data.append(
                {
                    "timestamp": signal.timestamp.isoformat(),
                    "symbol": signal.symbol,
                    "action": signal.action,
                    "quantity": signal.quantity,
                    "price": signal.price,
                    "confidence": signal.confidence,
                    "strategy_name": signal.strategy_name,
                }
            )
        return signals_data

    def _collect_market_overview_data(
        self, market_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """收集市场概览数据

        Args:
            market_data: 市场数据

        Returns:
            市场概览数据字典
        """
        if market_data.empty:
            return {}

        return {
            "market_trend": self._determine_market_trend(market_data),
            "volatility": float(market_data["close"].pct_change().std() * np.sqrt(252)),
            "top_gainer": self._find_top_mover(market_data, "gainer"),
            "top_loser": self._find_top_mover(market_data, "loser"),
            "trading_volume": int(market_data["volume"].sum())
            if "volume" in market_data.columns
            else 0,
        }

    def _collect_performance_data(
        self, portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """收集绩效数据

        Args:
            portfolio_data: 组合数据

        Returns:
            绩效数据字典
        """
        return {
            "sharpe_ratio": portfolio_data.get("sharpe_ratio", 0),
            "max_drawdown": portfolio_data.get("max_drawdown", 0),
            "win_rate": portfolio_data.get("win_rate", 0),
            "profit_factor": portfolio_data.get("profit_factor", 0),
        }

    def _collect_metrics_data(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """收集绩效指标数据

        Args:
            metrics: 绩效指标

        Returns:
            绩效指标数据字典
        """
        return {
            "total_return": metrics.total_return,
            "annualized_return": metrics.annualized_return,
            "volatility": metrics.volatility,
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "max_drawdown": metrics.max_drawdown,
            "win_rate": metrics.win_rate,
            "profit_factor": metrics.profit_factor,
            "total_trades": metrics.total_trades,
            "winning_trades": metrics.winning_trades,
            "losing_trades": metrics.losing_trades,
        }

    # ==================== 报告保存方法 ====================

    def _save_report_data(
        self, report_data: Dict[str, Any], config: ReportConfig
    ) -> Dict[str, Any]:
        """保存报告数据到文件和数据库

        Args:
            report_data: 报告数据
            config: 报告配置

        Returns:
            保存结果字典（包含文件路径和数据库状态）
        """
        result = {
            "success": True,
            "report_data": report_data,
            "saved_to": [],
            "errors": [],
        }

        # 生成报告ID和文件名
        report_id = f"{config.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_date_str = report_data.get("metadata", {}).get(
            "report_date", datetime.now().strftime("%Y-%m-%d")
        )

        # 1. 保存到SQLite数据库
        if config.save_to_database:
            try:
                success = self.db_manager.save_report(
                    report_id=report_id,
                    report_type=config.report_type,
                    title=report_data.get("metadata", {}).get("report_type", "Report"),
                    report_date=datetime.strptime(
                        report_date_str.split()[0], "%Y-%m-%d"
                    )
                    if isinstance(report_date_str, str)
                    else datetime.now(),
                    content_html="",  # 不保存HTML
                    content_json=report_data,
                    metadata=report_data.get("metadata", {}),
                )

                if success:
                    result["saved_to"].append(
                        f"SQLite数据库: {self.db_manager.db_path}"
                    )
                    result["database_report_id"] = report_id
                    logger.info(f"✓ 报告已保存到数据库: {report_id}")
                else:
                    result["errors"].append("数据库保存失败")

            except Exception as e:
                logger.error(f"保存到数据库失败: {e}")
                result["errors"].append(f"数据库保存失败: {e}")

        # 2. 保存到文件（JSON/CSV/Excel）
        if config.output_format and config.output_format != "sqlite":
            try:
                # 确定输出路径
                if config.output_path:
                    output_path = Path(config.output_path)
                else:
                    filename = f"{config.report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{config.output_format}"
                    output_path = self.output_dir / filename

                output_path.parent.mkdir(parents=True, exist_ok=True)

                # 根据格式保存
                if config.output_format == "json":
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(
                            report_data, f, indent=2, ensure_ascii=False, default=str
                        )
                    result["saved_to"].append(f"JSON文件: {output_path.absolute()}")
                    result["file_path"] = str(output_path.absolute())
                    logger.info(f"✓ 报告已保存到JSON文件: {output_path.absolute()}")

                elif config.output_format == "csv":
                    # 将报告数据转换为DataFrame并保存为CSV
                    df = self._report_data_to_dataframe(report_data)
                    df.to_csv(output_path, index=False, encoding="utf-8")
                    result["saved_to"].append(f"CSV文件: {output_path.absolute()}")
                    result["file_path"] = str(output_path.absolute())
                    logger.info(f"✓ 报告已保存到CSV文件: {output_path.absolute()}")

                elif config.output_format == "excel":
                    # 将报告数据转换为多个sheet的Excel文件
                    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                        for section_name, section_data in report_data.items():
                            if section_name != "metadata" and section_data:
                                df = (
                                    pd.DataFrame([section_data])
                                    if isinstance(section_data, dict)
                                    else pd.DataFrame(section_data)
                                )
                                df.to_excel(
                                    writer, sheet_name=section_name[:31], index=False
                                )  # Excel sheet name limit
                    result["saved_to"].append(f"Excel文件: {output_path.absolute()}")
                    result["file_path"] = str(output_path.absolute())
                    logger.info(f"✓ 报告已保存到Excel文件: {output_path.absolute()}")

            except Exception as e:
                logger.error(f"保存到文件失败: {e}")
                result["errors"].append(f"文件保存失败: {e}")
                result["success"] = False

        # 输出总结日志
        if result["saved_to"]:
            logger.info(f"=" * 60)
            logger.info(f"报告生成完成！")
            logger.info(f"报告ID: {report_id}")
            logger.info(f"报告类型: {config.report_type}")
            for location in result["saved_to"]:
                logger.info(f"  ✓ {location}")
            logger.info(f"=" * 60)

        if result["errors"]:
            logger.warning(f"保存过程中出现错误: {result['errors']}")

        return result

    def _report_data_to_dataframe(self, report_data: Dict[str, Any]) -> pd.DataFrame:
        """将报告数据转换为DataFrame

        Args:
            report_data: 报告数据

        Returns:
            DataFrame
        """
        # 扁平化报告数据
        flat_data = []
        for section_name, section_data in report_data.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    flat_data.append(
                        {"section": section_name, "field": key, "value": value}
                    )
            elif isinstance(section_data, list):
                for idx, item in enumerate(section_data):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            flat_data.append(
                                {
                                    "section": section_name,
                                    "index": idx,
                                    "field": key,
                                    "value": value,
                                }
                            )

        return pd.DataFrame(flat_data)

    def _add_summary_section(
        self, portfolio_data: Dict[str, Any], date: datetime
    ) -> None:
        """添加概要章节

        Args:
            portfolio_data: 组合数据
            date: 日期
        """
        summary = {
            "Date": date.strftime("%Y-%m-%d"),
            "Total Value": f"${portfolio_data.get('total_value', 0):,.2f}",
            "Daily P&L": f"${portfolio_data.get('daily_pnl', 0):,.2f}",
            "Daily Return": f"{portfolio_data.get('daily_return', 0):.2%}",
            "YTD Return": f"{portfolio_data.get('ytd_return', 0):.2%}",
        }

        self._add_section(
            ReportSection(
                section_id="summary",
                title="Portfolio Summary",
                content_type="metric",
                content=summary,
                order=0,
            )
        )

    def _add_positions_section(self, positions: List[Position]) -> None:
        """添加持仓章节

        Args:
            positions: 持仓列表
        """
        if not positions:
            return

        positions_data = []
        for pos in positions:
            positions_data.append(
                {
                    "Symbol": pos.symbol,
                    "Quantity": pos.quantity,
                    "Avg Cost": f"${pos.avg_cost:.2f}",
                    "Current Price": f"${pos.current_price:.2f}",
                    "Market Value": f"${pos.market_value:,.2f}",
                    "Unrealized P&L": f"${pos.unrealized_pnl:,.2f}",
                    "Return": f"{pos.return_pct:.2%}",
                }
            )

        df = pd.DataFrame(positions_data)

        self._add_section(
            ReportSection(
                section_id="positions",
                title="Current Positions",
                content_type="table",
                content=df.to_html(classes="table table-striped", index=False),
                order=1,
            )
        )

    def _add_signals_section(self, signals: List[Signal], date: datetime) -> None:
        """添加信号章节

        Args:
            signals: 信号列表
            date: 日期
        """
        # 筛选当日信号
        today_signals = [s for s in signals if s.timestamp.date() == date.date()]

        if not today_signals:
            return

        signals_data = []
        for signal in today_signals:
            signals_data.append(
                {
                    "Time": signal.timestamp.strftime("%H:%M:%S"),
                    "Symbol": signal.symbol,
                    "Action": signal.action,
                    "Quantity": signal.quantity,
                    "Price": f"${signal.price:.2f}",
                    "Confidence": f"{signal.confidence:.2%}",
                    "Strategy": signal.strategy_name,
                }
            )

        df = pd.DataFrame(signals_data)

        self._add_section(
            ReportSection(
                section_id="signals",
                title="Today's Trading Signals",
                content_type="table",
                content=df.to_html(classes="table table-striped", index=False),
                order=2,
            )
        )

    def _add_market_overview_section(self, market_data: pd.DataFrame) -> None:
        """添加市场概览章节

        Args:
            market_data: 市场数据
        """
        # 计算市场统计
        overview = {
            "Market Trend": self._determine_market_trend(market_data),
            "Volatility": f"{market_data['close'].pct_change().std() * np.sqrt(252):.2%}",
            "Top Gainer": self._find_top_mover(market_data, "gainer"),
            "Top Loser": self._find_top_mover(market_data, "loser"),
            "Trading Volume": f"{market_data['volume'].sum():,.0f}",
        }

        self._add_section(
            ReportSection(
                section_id="market_overview",
                title="Market Overview",
                content_type="metric",
                content=overview,
                order=3,
            )
        )

    def _add_performance_section(self, portfolio_data: Dict[str, Any]) -> None:
        """添加绩效章节

        Args:
            portfolio_data: 组合数据
        """
        metrics = {
            "Sharpe Ratio": f"{portfolio_data.get('sharpe_ratio', 0):.2f}",
            "Max Drawdown": f"{portfolio_data.get('max_drawdown', 0):.2%}",
            "Win Rate": f"{portfolio_data.get('win_rate', 0):.2%}",
            "Profit Factor": f"{portfolio_data.get('profit_factor', 0):.2f}",
        }

        self._add_section(
            ReportSection(
                section_id="performance",
                title="Performance Metrics",
                content_type="metric",
                content=metrics,
                order=4,
            )
        )

    def _render_report(self, config: ReportConfig) -> str:
        """渲染报告

        Args:
            config: 报告配置

        Returns:
            报告内容
        """
        # 获取模板
        template = self.env.get_template(config.template_name)

        # 准备数据
        sorted_sections = sorted(self.sections.values(), key=lambda x: x.order)

        context = {
            "metadata": self.metadata,
            "sections": sorted_sections,
            "config": config,
        }

        # 渲染HTML
        html_content = template.render(**context)

        # 根据输出格式转换
        if config.output_format == "html":
            return html_content
        elif config.output_format == "markdown":
            return self._html_to_markdown(html_content)
        elif config.output_format == "json":
            return json.dumps(context, default=str, indent=2)
        else:
            return html_content

    def _format_metrics(self, metrics: PerformanceMetrics) -> Dict[str, str]:
        """格式化绩效指标

        Args:
            metrics: 绩效指标

        Returns:
            格式化后的指标字典
        """
        return {
            "Total Return": f"{metrics.total_return:.2%}",
            "Annualized Return": f"{metrics.annualized_return:.2%}",
            "Volatility": f"{metrics.volatility:.2%}",
            "Sharpe Ratio": f"{metrics.sharpe_ratio:.2f}",
            "Sortino Ratio": f"{metrics.sortino_ratio:.2f}",
            "Max Drawdown": f"{metrics.max_drawdown:.2%}",
            "Win Rate": f"{metrics.win_rate:.2%}",
            "Profit Factor": f"{metrics.profit_factor:.2f}",
            "Total Trades": str(metrics.total_trades),
            "Winning Trades": str(metrics.winning_trades),
            "Losing Trades": str(metrics.losing_trades),
        }

    def _format_weekly_overview(self, weekly_data: Dict[str, Any]) -> str:
        """格式化周概览

        Args:
            weekly_data: 周数据

        Returns:
            格式化的文本
        """
        return f"""
        This week's portfolio performance showed a return of {weekly_data.get("weekly_return", 0):.2%} 
        with {weekly_data.get("total_trades", 0)} trades executed. 
        The portfolio value changed from ${weekly_data.get("start_value", 0):,.2f} 
        to ${weekly_data.get("end_value", 0):,.2f}.
        """

    def _format_performance_table(self, performance: Dict) -> str:
        """格式化绩效表格

        Args:
            performance: 绩效数据

        Returns:
            HTML表格
        """
        df = pd.DataFrame([performance])
        return df.to_html(classes="table table-striped", index=False)

    def _format_trade_statistics(self, trades: List[Dict]) -> str:
        """格式化交易统计

        Args:
            trades: 交易列表

        Returns:
            HTML表格
        """
        df = pd.DataFrame(trades)
        return df.to_html(classes="table table-striped", index=False)

    def _format_return_analysis(self, data: Dict) -> str:
        """格式化收益分析

        Args:
            data: 数据

        Returns:
            HTML表格
        """
        return pd.DataFrame([data]).to_html(classes="table table-striped", index=False)

    def _format_risk_analysis(self, data: Dict) -> str:
        """格式化风险分析

        Args:
            data: 数据

        Returns:
            HTML表格
        """
        return pd.DataFrame([data]).to_html(classes="table table-striped", index=False)

    def _format_trade_analysis(self, metrics: PerformanceMetrics) -> str:
        """格式化交易分析

        Args:
            metrics: 绩效指标

        Returns:
            HTML表格
        """
        trade_stats = {
            "Average Win": f"${metrics.avg_win:.2f}",
            "Average Loss": f"${metrics.avg_loss:.2f}",
            "Best Trade": f"${metrics.best_trade:.2f}",
            "Worst Trade": f"${metrics.worst_trade:.2f}",
            "Win/Loss Ratio": f"{metrics.avg_win / abs(metrics.avg_loss) if metrics.avg_loss != 0 else 0:.2f}",
        }
        return pd.DataFrame([trade_stats]).to_html(
            classes="table table-striped", index=False
        )

    def _determine_market_trend(self, market_data: pd.DataFrame) -> str:
        """判断市场趋势

        Args:
            market_data: 市场数据

        Returns:
            趋势描述
        """
        if len(market_data) < 2:
            return "Unknown"

        returns = market_data["close"].pct_change().mean()
        if returns > 0.01:
            return "Bullish"
        elif returns < -0.01:
            return "Bearish"
        else:
            return "Neutral"

    def _find_top_mover(self, market_data: pd.DataFrame, mover_type: str) -> str:
        """查找涨跌幅最大的标的

        Args:
            market_data: 市场数据
            mover_type: 'gainer' or 'loser'

        Returns:
            标的名称和涨跌幅
        """
        if "symbol" not in market_data.columns:
            return "N/A"

        returns = market_data.groupby("symbol")["close"].pct_change().last()

        if mover_type == "gainer":
            top = returns.idxmax()
            return f"{top} ({returns[top]:.2%})"
        else:
            top = returns.idxmin()
            return f"{top} ({returns[top]:.2%})"

    def _html_to_markdown(self, html_content: str) -> str:
        """HTML转Markdown

        Args:
            html_content: HTML内容

        Returns:
            Markdown内容
        """
        # 简化的转换，实际应使用专门的库
        import html2text

        h = html2text.HTML2Text()
        h.ignore_links = False
        return h.handle(html_content)

    def _generate_markdown(self, content: Dict[str, Any]) -> str:
        """生成Markdown内容

        Args:
            content: 内容字典

        Returns:
            Markdown字符串
        """
        md_lines = []

        # 添加标题
        md_lines.append(f"# {content.get('title', 'Report')}")
        md_lines.append(
            f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        )
        md_lines.append("")

        # 添加章节
        for section_id, section_content in content.items():
            if section_id == "title":
                continue

            md_lines.append(f"## {section_id.replace('_', ' ').title()}")

            if isinstance(section_content, dict):
                for key, value in section_content.items():
                    md_lines.append(f"- **{key}**: {value}")
            elif isinstance(section_content, list):
                for item in section_content:
                    md_lines.append(f"- {item}")
            else:
                md_lines.append(str(section_content))

            md_lines.append("")

        return "\n".join(md_lines)


# 模块级别函数
def generate_quick_report(
    data: Dict[str, Any], report_type: str = "daily", output_format: str = "json"
) -> Dict[str, Any]:
    """快速生成报告（默认输出JSON数据并保存到SQLite）

    Args:
        data: 报告数据
        report_type: 报告类型
        output_format: 输出格式（json/csv/excel）

    Returns:
        包含报告数据和保存信息的字典
    """
    builder = ReportBuilder()
    config = ReportConfig(
        report_type=report_type,
        output_format=output_format,
    )

    report_data = {
        "metadata": {
            "report_type": report_type,
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        **data,
    }

    return builder._save_report_data(report_data, config)


def export_report_data(
    report_data: Dict[str, Any], filename: str, format: str = "json"
) -> bool:
    """导出报告数据到文件

    Args:
        report_data: 报告数据字典
        filename: 文件名
        format: 格式（json/csv/excel）

    Returns:
        是否成功
    """
    try:
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        elif format == "csv":
            # 扁平化数据并保存为CSV
            flat_data = []
            for section, content in report_data.items():
                if isinstance(content, dict):
                    for key, value in content.items():
                        flat_data.append(
                            {"section": section, "field": key, "value": value}
                        )
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            flat_data.append({"section": section, **item})
            df = pd.DataFrame(flat_data)
            df.to_csv(output_path, index=False, encoding="utf-8")
        elif format == "excel":
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for section, content in report_data.items():
                    if content:
                        df = (
                            pd.DataFrame([content])
                            if isinstance(content, dict)
                            else pd.DataFrame(content)
                        )
                        df.to_excel(writer, sheet_name=section[:31], index=False)
        else:
            logger.warning(f"不支持的格式: {format}")
            return False

        logger.info(f"报告已导出到: {output_path.absolute()}")
        return True

    except Exception as e:
        logger.error(f"导出报告失败: {e}")
        return False
