"""
模板引擎模块
负责管理和渲染报告模板
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jinja2
import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from common.exceptions import QuantSystemError
from common.logging_system import setup_logger

logger = setup_logger("template_engine")


@dataclass
class TemplateConfig:
    """模板配置数据类"""

    template_id: str
    template_type: str  # 'report', 'email', 'dashboard', 'alert'
    template_file: str
    output_format: str  # 'html', 'pdf', 'markdown', 'text'
    variables: Dict[str, Any] = field(default_factory=dict)
    filters: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    static_assets: List[str] = field(default_factory=list)


@dataclass
class TemplateVariable:
    """模板变量数据类"""

    name: str
    var_type: str  # 'string', 'number', 'date', 'list', 'dict', 'dataframe'
    required: bool = True
    default_value: Any = None
    format_spec: Optional[str] = None
    validation_rule: Optional[str] = None


@dataclass
class RenderResult:
    """渲染结果数据类"""

    success: bool
    output: str
    format: str
    render_time: datetime
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TemplateEngine:
    """模板引擎类"""

    DEFAULT_TEMPLATE_DIR = os.path.join("module_11_visualization", "templates")
    DEFAULT_STATIC_DIR = os.path.join("module_11_visualization", "static")

    BUILTIN_FILTERS = {
        "currency": lambda x: f"${x:,.2f}",
        "percentage": lambda x: f"{x:.2%}",
        "number": lambda x: f"{x:,.0f}",
        "date": lambda x: x.strftime("%Y-%m-%d") if hasattr(x, "strftime") else str(x),
        "datetime": lambda x: x.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(x, "strftime")
        else str(x),
        "round2": lambda x: round(x, 2),
        "round4": lambda x: round(x, 4),
        "abs": abs,
        "capitalize": lambda x: str(x).capitalize(),
    }

    TEMPLATE_SCHEMAS = {
        "daily_report": {
            "required_vars": ["date", "portfolio_value", "daily_pnl", "positions"],
            "optional_vars": ["signals", "alerts", "market_summary"],
            "sections": ["header", "summary", "positions", "performance", "footer"],
        },
        "weekly_report": {
            "required_vars": ["start_date", "end_date", "weekly_return", "trades"],
            "optional_vars": ["top_performers", "risk_metrics"],
            "sections": ["header", "overview", "analysis", "recommendations", "footer"],
        },
        "alert_email": {
            "required_vars": ["alert_type", "message", "timestamp"],
            "optional_vars": ["details", "actions"],
            "sections": ["subject", "body", "footer"],
        },
    }

    def __init__(
        self, template_dir: Optional[str] = None, static_dir: Optional[str] = None
    ):
        """初始化模板引擎

        Args:
            template_dir: 模板目录
            static_dir: 静态文件目录
        """
        self.template_dir = Path(template_dir or self.DEFAULT_TEMPLATE_DIR)
        self.static_dir = Path(static_dir or self.DEFAULT_STATIC_DIR)

        # 创建Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 注册内置过滤器
        for name, filter_func in self.BUILTIN_FILTERS.items():
            self.env.filters[name] = filter_func

        self.templates: Dict[str, Template] = {}
        self.configs: Dict[str, TemplateConfig] = {}
        self.custom_filters: Dict[str, callable] = {}

        # 加载配置
        self._load_template_configs()

    def load_template(
        self, template_name: str, template_type: str = "report"
    ) -> Template:
        """加载模板

        Args:
            template_name: 模板名称
            template_type: 模板类型

        Returns:
            模板对象
        """
        template_key = f"{template_type}:{template_name}"

        if template_key in self.templates:
            return self.templates[template_key]

        try:
            # 构建模板路径
            template_path = f"{template_type}/{template_name}"
            if not template_path.endswith(".html"):
                template_path += ".html"

            # 加载模板
            template = self.env.get_template(template_path)
            self.templates[template_key] = template

            logger.info(f"Loaded template: {template_path}")
            return template

        except jinja2.TemplateNotFound:
            logger.error(f"Template not found: {template_path}")
            raise QuantSystemError(f"Template not found: {template_path}")

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        config: Optional[TemplateConfig] = None,
    ) -> RenderResult:
        """渲染模板

        Args:
            template_name: 模板名称
            context: 上下文数据
            config: 模板配置

        Returns:
            渲染结果
        """
        start_time = datetime.now()
        errors = []
        warnings = []

        try:
            # 获取配置
            if config is None:
                config = self.configs.get(
                    template_name,
                    TemplateConfig(
                        template_id=template_name,
                        template_type="report",
                        template_file=f"{template_name}.html",
                        output_format="html",
                    ),
                )

            # 验证必需变量
            if template_name in self.TEMPLATE_SCHEMAS:
                schema = self.TEMPLATE_SCHEMAS[template_name]
                for var in schema["required_vars"]:
                    if var not in context:
                        errors.append(f"Missing required variable: {var}")

            if errors:
                return RenderResult(
                    success=False,
                    output="",
                    format=config.output_format,
                    render_time=datetime.now(),
                    errors=errors,
                )

            # 加载模板
            template = self.load_template(template_name, config.template_type)

            # 添加默认上下文
            context = self._prepare_context(context, config)

            # 渲染模板
            output = template.render(**context)

            # 后处理
            if config.output_format == "markdown":
                output = self._html_to_markdown(output)
            elif config.output_format == "pdf":
                output = self._html_to_pdf(output)

            return RenderResult(
                success=True,
                output=output,
                format=config.output_format,
                render_time=datetime.now(),
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            errors.append(str(e))
            return RenderResult(
                success=False,
                output="",
                format=config.output_format if config else "html",
                render_time=datetime.now(),
                errors=errors,
            )

    def create_custom_template(
        self,
        template_name: str,
        template_content: str,
        template_type: str = "custom",
        save_to_file: bool = False,
    ) -> bool:
        """创建自定义模板

        Args:
            template_name: 模板名称
            template_content: 模板内容
            template_type: 模板类型
            save_to_file: 是否保存到文件

        Returns:
            是否成功
        """
        try:
            # 创建模板对象
            template = self.env.from_string(template_content)

            # 缓存模板
            template_key = f"{template_type}:{template_name}"
            self.templates[template_key] = template

            # 保存到文件
            if save_to_file:
                template_dir = self.template_dir / template_type
                template_dir.mkdir(parents=True, exist_ok=True)

                template_file = template_dir / f"{template_name}.html"
                template_file.write_text(template_content, encoding="utf-8")

                logger.info(f"Saved custom template to {template_file}")

            return True

        except Exception as e:
            logger.error(f"Failed to create custom template: {e}")
            return False

    def register_filter(self, name: str, filter_func: callable) -> None:
        """注册自定义过滤器

        Args:
            name: 过滤器名称
            filter_func: 过滤器函数
        """
        self.env.filters[name] = filter_func
        self.custom_filters[name] = filter_func
        logger.info(f"Registered custom filter: {name}")

    def compile_template_bundle(
        self, bundle_name: str, templates: List[str], output_dir: str
    ) -> bool:
        """编译模板包

        Args:
            bundle_name: 包名称
            templates: 模板列表
            output_dir: 输出目录

        Returns:
            是否成功
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            bundle = {
                "name": bundle_name,
                "created": datetime.now().isoformat(),
                "templates": {},
            }

            for template_name in templates:
                template = self.load_template(template_name)
                bundle["templates"][template_name] = {
                    "source": template.source,
                    "filename": template.filename,
                }

            # 保存包文件
            bundle_file = output_path / f"{bundle_name}.json"
            with open(bundle_file, "w", encoding="utf-8") as f:
                json.dump(bundle, f, indent=2)

            logger.info(f"Created template bundle: {bundle_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to compile template bundle: {e}")
            return False

    def validate_template(
        self, template_name: str, sample_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """验证模板

        Args:
            template_name: 模板名称
            sample_context: 示例上下文

        Returns:
            验证结果
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_vars": [],
            "unused_vars": [],
        }

        try:
            # 加载模板
            template = self.load_template(template_name)

            # 获取模板变量
            template_vars = template.module.__dict__.get("exported", [])

            # 检查架构
            if template_name in self.TEMPLATE_SCHEMAS:
                schema = self.TEMPLATE_SCHEMAS[template_name]

                # 检查必需变量
                for var in schema["required_vars"]:
                    if sample_context and var not in sample_context:
                        result["missing_vars"].append(var)
                        result["warnings"].append(f"Missing required variable: {var}")

            # 尝试渲染
            if sample_context:
                try:
                    output = template.render(**sample_context)
                    if not output.strip():
                        result["warnings"].append("Template produces empty output")
                except Exception as e:
                    result["errors"].append(f"Render error: {str(e)}")
                    result["valid"] = False

        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
            result["valid"] = False

        return result

    def generate_template_documentation(
        self, template_name: str, output_format: str = "markdown"
    ) -> str:
        """生成模板文档

        Args:
            template_name: 模板名称
            output_format: 输出格式

        Returns:
            文档内容
        """
        doc_lines = []

        if output_format == "markdown":
            doc_lines.append(f"# Template: {template_name}")
            doc_lines.append("")

            # 获取架构
            if template_name in self.TEMPLATE_SCHEMAS:
                schema = self.TEMPLATE_SCHEMAS[template_name]

                doc_lines.append("## Required Variables")
                for var in schema["required_vars"]:
                    doc_lines.append(f"- `{var}`")
                doc_lines.append("")

                doc_lines.append("## Optional Variables")
                for var in schema.get("optional_vars", []):
                    doc_lines.append(f"- `{var}`")
                doc_lines.append("")

                doc_lines.append("## Sections")
                for section in schema.get("sections", []):
                    doc_lines.append(f"- {section}")
                doc_lines.append("")

            # 可用过滤器
            doc_lines.append("## Available Filters")
            for name in sorted(self.env.filters.keys()):
                doc_lines.append(f"- `{name}`")

        elif output_format == "html":
            doc_lines.append(f"<h1>Template: {template_name}</h1>")
            # HTML格式文档
            pass

        return "\n".join(doc_lines)

    def _load_template_configs(self) -> None:
        """加载模板配置"""
        config_file = self.template_dir / "configs.yaml"

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    configs = yaml.safe_load(f)

                for name, config_data in configs.items():
                    self.configs[name] = TemplateConfig(template_id=name, **config_data)

                logger.info(f"Loaded {len(self.configs)} template configs")

            except Exception as e:
                logger.error(f"Failed to load template configs: {e}")

    def _prepare_context(
        self, context: Dict[str, Any], config: TemplateConfig
    ) -> Dict[str, Any]:
        """准备上下文

        Args:
            context: 原始上下文
            config: 模板配置

        Returns:
            处理后的上下文
        """
        # 添加默认变量
        prepared_context = {
            "generated_at": datetime.now(),
            "template_name": config.template_id,
            "static_url": str(self.static_dir),
            **context,
        }

        # 添加配置变量
        prepared_context.update(config.variables)

        # 处理DataFrame
        for key, value in prepared_context.items():
            if hasattr(value, "to_html"):
                # 将DataFrame转换为HTML表格
                prepared_context[f"{key}_html"] = value.to_html(
                    classes="table table-striped", index=False
                )
                prepared_context[f"{key}_json"] = value.to_json(orient="records")

        return prepared_context

    def _html_to_markdown(self, html_content: str) -> str:
        """HTML转Markdown

        Args:
            html_content: HTML内容

        Returns:
            Markdown内容
        """
        import html2text

        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        return h.handle(html_content)

    def _html_to_pdf(self, html_content: str) -> bytes:
        """HTML转PDF（功能已移除，仅返回HTML字节）

        Args:
            html_content: HTML内容

        Returns:
            HTML内容的字节数据
        """
        logger.warning("PDF导出功能已移除，返回HTML内容")
        return html_content.encode("utf-8")


# 模块级别函数
def get_default_engine() -> TemplateEngine:
    """获取默认模板引擎

    Returns:
        模板引擎实例
    """
    return TemplateEngine()


def render_quick_template(template_string: str, context: Dict[str, Any]) -> str:
    """快速渲染模板字符串

    Args:
        template_string: 模板字符串
        context: 上下文数据

    Returns:
        渲染结果
    """
    template = Template(template_string)
    return template.render(**context)


def create_report_from_template(
    template_name: str, data: Dict[str, Any], output_file: str, format: str = "html"
) -> bool:
    """从模板创建报告

    Args:
        template_name: 模板名称
        data: 数据
        output_file: 输出文件
        format: 格式

    Returns:
        是否成功
    """
    try:
        engine = TemplateEngine()

        config = TemplateConfig(
            template_id=template_name,
            template_type="report",
            template_file=f"{template_name}.html",
            output_format=format,
        )

        result = engine.render_template(template_name, data, config)

        if result.success:
            if format == "pdf":
                with open(output_file, "wb") as f:
                    f.write(result.output)
            else:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result.output)

            logger.info(f"Report created: {output_file}")
            return True
        else:
            logger.error(f"Failed to create report: {result.errors}")
            return False

    except Exception as e:
        logger.error(f"Error creating report: {e}")
        return False
