"""
模型推理可视化模块
提供类似 Ollama 的专业模型推理进度显示，包括速率、进度条和预估时间
"""

import queue
import time
from datetime import timedelta
from threading import Thread
from typing import Any, Dict, Optional

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    from transformers import TextIteratorStreamer

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

from common.logging_system import setup_logger

logger = setup_logger("model_inference_visualizer")


class ModelInferenceVisualizer:
    """模型推理可视化器 - 类似 Ollama 的专业进度显示"""

    def __init__(self):
        """初始化可视化器"""
        self.console = Console() if HAS_RICH else None
        self.start_time = None
        self.token_count = 0
        self.last_token_time = None

    def create_progress_display(self) -> Optional[Progress]:
        """创建进度条显示

        Returns:
            Rich Progress 对象
        """
        if not HAS_RICH:
            return None

        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="cyan", finished_style="green"),
            TaskProgressColumn(),
            "•",
            TextColumn("[cyan]{task.fields[speed]}"),
            "•",
            TimeRemainingColumn(),
            console=self.console,
        )

    def create_stats_table(
        self,
        tokens_generated: int,
        tokens_per_sec: float,
        elapsed_time: float,
        eta: Optional[float] = None,
    ) -> Table:
        """创建统计信息表格

        Args:
            tokens_generated: 已生成的 token 数
            tokens_per_sec: 生成速率 (tokens/s)
            elapsed_time: 已用时间
            eta: 预估剩余时间

        Returns:
            Rich Table 对象
        """
        if not HAS_RICH:
            return None

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("🎯 Tokens", f"{tokens_generated}")
        table.add_row("⚡ Speed", f"{tokens_per_sec:.2f} tokens/s")
        table.add_row("⏱️  Elapsed", f"{elapsed_time:.2f}s")

        if eta is not None:
            table.add_row("⏳ ETA", f"{eta:.1f}s")

        return table

    def display_loading_model(self, model_name: str = "FIN-R1"):
        """显示模型加载界面

        Args:
            model_name: 模型名称
        """
        if not HAS_RICH:
            logger.info(f"Loading {model_name} model...")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(f"[cyan]Loading {model_name} model...", total=None)
            # 这个函数立即返回，实际加载在调用处进行

    def create_inference_streamer(
        self, tokenizer, max_new_tokens: int = 100, skip_prompt: bool = True
    ):
        """创建流式推理器

        Args:
            tokenizer: 分词器
            max_new_tokens: 最大生成 token 数
            skip_prompt: 是否跳过输入提示词

        Returns:
            TextIteratorStreamer 对象和生成线程
        """
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not available, cannot create streamer")
            return None, None

        streamer = TextIteratorStreamer(
            tokenizer, skip_prompt=skip_prompt, skip_special_tokens=True
        )

        return streamer

    def visualize_generation(
        self, streamer, max_new_tokens: int, model_name: str = "FIN-R1", timeout: int = 30
    ) -> str:
        """可视化模型生成过程

        Args:
            streamer: TextIteratorStreamer 对象
            max_new_tokens: 最大生成 token 数
            model_name: 模型名称
            timeout: 超时时间（秒），如果超时且没有生成任何token则抛出异常

        Returns:
            生成的完整文本
            
        Raises:
            TimeoutError: 如果超时且没有生成任何token
        """
        if not HAS_RICH or streamer is None:
            # Fallback: 简单的文本输出
            generated_text = ""
            logger.info("⚡ Streaming generation (simple mode)...")
            start = time.time()
            try:
                for text in streamer:
                    generated_text += text
                    print(text, end="", flush=True)
                    # 检查超时
                    if time.time() - start > timeout and len(generated_text) == 0:
                        logger.error(f"⏱️ Timeout: {timeout}s elapsed with 0 tokens")
                        raise TimeoutError(f"Generation timeout after {timeout}s with no tokens")
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                if isinstance(e, TimeoutError):
                    raise
            print()
            return generated_text

        generated_text = ""
        self.start_time = time.time()
        self.token_count = 0
        last_update_time = self.start_time
        timeout_checked = False

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="cyan", finished_style="green"),
            MofNCompleteColumn(),
            "•",
            TextColumn("[cyan]{task.fields[speed]}"),
            "•",
            TimeRemainingColumn(),
            console=self.console,
            transient=False,  # 保持进度条显示
        ) as progress:
            task = progress.add_task(
                f"[cyan]🤖 {model_name} Generating",
                total=max_new_tokens,
                speed="0.00 tok/s",
            )

            try:
                # 🔑 关键：使用 try-except 捕获超时错误
                for text in streamer:
                    generated_text += text
                    self.token_count += 1

                    # 更新进度（限制更新频率，避免过于频繁）
                    current_time = time.time()
                    if current_time - last_update_time >= 0.1:  # 每100ms更新一次
                        elapsed = current_time - self.start_time
                        tokens_per_sec = (
                            self.token_count / elapsed if elapsed > 0 else 0
                        )

                        progress.update(
                            task,
                            completed=self.token_count,
                            speed=f"{tokens_per_sec:.2f} tok/s",
                        )
                        last_update_time = current_time
                        
                        # 🔑 检查超时：如果超过指定时间且没有生成任何token
                        if elapsed > timeout and self.token_count == 0 and not timeout_checked:
                            timeout_checked = True
                            logger.error(f"⏱️ Timeout: {timeout}s elapsed with 0 tokens")
                            self.console.print(
                                f"[red]❌ Generation timeout: {timeout}s elapsed with no tokens[/red]"
                            )
                            raise TimeoutError(f"Generation timeout after {timeout}s with no tokens")

                # 最后更新到实际完成的数量
                elapsed = time.time() - self.start_time
                tokens_per_sec = self.token_count / elapsed if elapsed > 0 else 0
                progress.update(
                    task,
                    completed=self.token_count,
                    speed=f"{tokens_per_sec:.2f} tok/s",
                )

            except StopIteration:
                logger.info("✅ Generation completed normally")
            except TimeoutError:
                # 🔑 检查是否是0 token超时
                elapsed = time.time() - self.start_time
                if self.token_count == 0 and elapsed > timeout:
                    logger.error(f"❌ FIN-R1 timeout with 0 tokens after {elapsed:.1f}s - will switch to Aliyun")
                    self.console.print("[red]❌ Model timeout with 0 tokens - switching to backup[/red]")
                    raise  # 重新抛出异常，让上层切换到阿里云
                else:
                    logger.warning("⚠️ Generation timeout - streamer timed out")
                    self.console.print("[yellow]⚠️ Generation timeout[/yellow]")
            except Exception as e:
                logger.error(f"❌ Generation error: {e}")
                self.console.print(f"[red]❌ Error: {e}[/red]")
                # 如果是超时相关的异常，重新抛出
                if "timeout" in str(e).lower() or isinstance(e, TimeoutError):
                    raise

        # 🔑 最终检查：如果整个过程完成但没有生成任何token
        elapsed = time.time() - self.start_time
        if self.token_count == 0 and elapsed > timeout:
            logger.error(f"❌ FIN-R1 generated 0 tokens after {elapsed:.1f}s")
            self.console.print(
                "[red]❌ Model generated no tokens - switching to backup service[/red]"
            )
            raise TimeoutError(f"Model generated 0 tokens after {elapsed:.1f}s")

        # 显示最终统计
        tokens_per_sec = self.token_count / elapsed if elapsed > 0 else 0

        self.console.print()

        if self.token_count > 0:
            self.console.print(
                Panel(
                    self.create_stats_table(self.token_count, tokens_per_sec, elapsed),
                    title="[bold green]✅ Generation Complete",
                    border_style="green",
                )
            )
        else:
            self.console.print(
                "[yellow]⚠️ No tokens generated - check if model is working properly[/yellow]"
            )

        return generated_text

    def simple_progress_bar(self, description: str, total: int, callback=None):
        """简单的进度条（用于非流式生成）

        Args:
            description: 任务描述
            total: 总步骤数
            callback: 执行的回调函数
        """
        if not HAS_RICH:
            logger.info(f"{description}...")
            if callback:
                return callback()
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(description, total=total)

            if callback:
                result = callback(progress, task)
                progress.update(task, completed=total)
                return result


class InferenceProgressCallback:
    """推理进度回调类 - 用于非流式生成的进度监控"""

    def __init__(
        self, max_new_tokens: int, visualizer: Optional[ModelInferenceVisualizer] = None
    ):
        """初始化回调

        Args:
            max_new_tokens: 最大生成 token 数
            visualizer: 可视化器实例
        """
        self.max_new_tokens = max_new_tokens
        self.visualizer = visualizer or ModelInferenceVisualizer()
        self.start_time = None
        self.current_tokens = 0

    def __call__(self, *args, **kwargs):
        """回调函数"""
        if self.start_time is None:
            self.start_time = time.time()

        self.current_tokens += 1
        elapsed = time.time() - self.start_time
        tokens_per_sec = self.current_tokens / elapsed if elapsed > 0 else 0

        # 更新进度显示
        if self.visualizer and self.visualizer.console:
            progress_pct = (self.current_tokens / self.max_new_tokens) * 100
            self.visualizer.console.print(
                f"⚡ Progress: {progress_pct:.1f}% | "
                f"Speed: {tokens_per_sec:.2f} tok/s | "
                f"Tokens: {self.current_tokens}/{self.max_new_tokens}",
                end="\r",
            )


def display_model_info(model_name: str, model_size: str = "Unknown"):
    """显示模型信息面板

    Args:
        model_name: 模型名称
        model_size: 模型大小
    """
    if not HAS_RICH:
        logger.info(f"Model: {model_name} ({model_size})")
        return

    console = Console()

    table = Table(show_header=False, box=None)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("🤖 Model", model_name)
    table.add_row("📦 Size", model_size)
    table.add_row("⚙️  Status", "[green]Ready[/green]")

    console.print(
        Panel(table, title="[bold cyan]Model Information", border_style="cyan")
    )


# 便捷函数
def create_visualizer() -> ModelInferenceVisualizer:
    """创建可视化器实例

    Returns:
        ModelInferenceVisualizer 实例
    """
    return ModelInferenceVisualizer()


if __name__ == "__main__":
    # 测试代码
    import asyncio

    visualizer = ModelInferenceVisualizer()

    # 测试1: 显示模型信息
    display_model_info("FIN-R1", "7B")

    # 测试2: 模拟生成过程
    print("\n" + "=" * 50)
    print("测试流式生成可视化")
    print("=" * 50 + "\n")

    class MockStreamer:
        """模拟流式生成器"""

        def __iter__(self):
            import random

            words = ["分析", "市场", "趋势", "数据", "建议", "策略", "风险", "收益"]
            for i in range(20):
                time.sleep(random.uniform(0.05, 0.2))  # 模拟生成延迟
                yield random.choice(words)

    mock_streamer = MockStreamer()
    result = visualizer.visualize_generation(
        mock_streamer, max_new_tokens=20, model_name="FIN-R1"
    )

    print(f"\n生成结果: {result}")
