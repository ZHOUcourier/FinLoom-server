"""
模型推理诊断工具
帮助排查模型推理卡住或速度慢的问题
"""

import os
import time

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def check_system_resources():
    """检查系统资源"""
    console.print("\n[bold cyan]📊 系统资源检查[/bold cyan]\n")

    table = Table(show_header=True)
    table.add_column("资源", style="cyan")
    table.add_column("状态", style="white")
    table.add_column("说明", style="yellow")

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    table.add_row(
        "CPU",
        f"{cpu_percent}% ({cpu_count} cores)",
        "✅ OK" if cpu_percent < 90 else "⚠️ High",
    )

    # 内存
    mem = psutil.virtual_memory()
    table.add_row(
        "内存",
        f"{mem.percent}% ({mem.available / 1024**3:.1f}GB free)",
        "✅ OK" if mem.percent < 90 else "⚠️ High",
    )

    # 磁盘
    disk = psutil.disk_usage("/")
    table.add_row(
        "磁盘",
        f"{disk.percent}% ({disk.free / 1024**3:.1f}GB free)",
        "✅ OK" if disk.percent < 90 else "⚠️ High",
    )

    console.print(table)


def check_pytorch():
    """检查PyTorch配置"""
    console.print("\n[bold cyan]🔥 PyTorch配置检查[/bold cyan]\n")

    try:
        import torch

        table = Table(show_header=True)
        table.add_column("项目", style="cyan")
        table.add_column("值", style="white")

        table.add_row("PyTorch版本", torch.__version__)
        table.add_row(
            "CUDA可用", "✅ Yes" if torch.cuda.is_available() else "❌ No (使用CPU)"
        )

        if torch.cuda.is_available():
            table.add_row("CUDA版本", torch.version.cuda)
            table.add_row("GPU数量", str(torch.cuda.device_count()))
            table.add_row("当前GPU", torch.cuda.get_device_name(0))
        else:
            table.add_row("设备", "CPU (较慢)")
            table.add_row("⚠️ 提示", "使用CPU推理会很慢，建议使用GPU")

        table.add_row("线程数", str(torch.get_num_threads()))

        console.print(table)

    except ImportError:
        console.print("[red]❌ PyTorch未安装[/red]")


def test_model_loading():
    """测试模型加载"""
    console.print("\n[bold cyan]📦 测试模型加载[/bold cyan]\n")

    model_path = ".Fin-R1"

    if not os.path.exists(model_path):
        console.print(f"[red]❌ 模型路径不存在: {model_path}[/red]")
        console.print("[yellow]💡 请确保 FIN-R1 模型已下载到当前目录[/yellow]")
        return False

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        console.print(f"✓ 模型路径存在: {model_path}")

        # 测试分词器
        console.print("⏳ 加载分词器...")
        start = time.time()
        tokenizer = AutoTokenizer.from_pretrained(
            model_path, trust_remote_code=True, use_fast=False
        )
        console.print(f"✅ 分词器加载成功 ({time.time() - start:.2f}s)")

        # 测试模型（使用最小配置）
        console.print("⏳ 加载模型（可能需要几分钟）...")
        start = time.time()
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,  # 减少内存占用
        )
        model.eval()
        console.print(f"✅ 模型加载成功 ({time.time() - start:.2f}s)")

        # 计算模型大小
        param_count = sum(p.numel() for p in model.parameters())
        console.print(f"📊 模型参数量: {param_count / 1e9:.2f}B")

        return True

    except Exception as e:
        console.print(f"[red]❌ 模型加载失败: {e}[/red]")
        return False


def test_simple_generation():
    """测试简单生成"""
    console.print("\n[bold cyan]🚀 测试模型推理[/bold cyan]\n")

    try:
        from threading import Thread

        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TextIteratorStreamer,
        )

        model_path = ".Fin-R1"

        console.print("⏳ 初始化模型...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path, trust_remote_code=True, use_fast=False
        )

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        model.eval()

        # 简单测试
        console.print("⏳ 测试生成（非流式）...")
        test_input = "你好"
        inputs = tokenizer(test_input, return_tensors="pt")

        start = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=5,  # 只生成5个token测试
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        elapsed = time.time() - start

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        console.print(f"✅ 非流式生成成功 ({elapsed:.2f}s)")
        console.print(f"   输入: {test_input}")
        console.print(f"   输出: {result}")
        console.print(f"   速率: {5 / elapsed:.2f} tokens/s")

        # 测试流式生成
        console.print("\n⏳ 测试生成（流式）...")
        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
            timeout=10.0,  # 10秒超时
        )

        generation_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=10,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        start = time.time()
        thread.start()

        generated_text = ""
        token_count = 0
        try:
            for text in streamer:
                generated_text += text
                token_count += 1
                console.print(f"  Token #{token_count}: {text}", end="")
        except TimeoutError:
            console.print("\n[red]❌ 流式生成超时！[/red]")
            return False

        thread.join(timeout=20)
        elapsed = time.time() - start

        console.print(f"\n✅ 流式生成成功 ({elapsed:.2f}s)")
        console.print(f"   生成了 {token_count} tokens")
        console.print(f"   速率: {token_count / elapsed:.2f} tokens/s")

        if token_count == 0:
            console.print("[yellow]⚠️ 警告：没有生成任何token！[/yellow]")
            return False

        return True

    except Exception as e:
        console.print(f"[red]❌ 推理测试失败: {e}[/red]")
        import traceback

        console.print(traceback.format_exc())
        return False


def main():
    """主函数"""
    console.print(
        Panel.fit(
            "[bold cyan]🔍 FIN-R1 模型推理诊断工具[/bold cyan]\n"
            "帮助排查模型推理卡住或速度慢的问题",
            border_style="cyan",
        )
    )

    # 1. 检查系统资源
    check_system_resources()

    # 2. 检查PyTorch
    check_pytorch()

    # 3. 测试模型加载
    model_loaded = test_model_loading()

    if not model_loaded:
        console.print("\n[red]❌ 模型加载失败，无法继续测试[/red]")
        return

    # 4. 测试推理
    inference_ok = test_simple_generation()

    # 总结
    console.print("\n" + "=" * 60)
    if inference_ok:
        console.print("[bold green]✅ 诊断完成：模型工作正常！[/bold green]")
        console.print("\n💡 如果实际使用时还是很慢：")
        console.print("   1. 检查是否在CPU上运行（CPU推理很慢）")
        console.print("   2. 减少 max_new_tokens 参数")
        console.print("   3. 考虑使用更小的模型")
    else:
        console.print("[bold red]❌ 诊断失败：发现问题！[/bold red]")
        console.print("\n🔧 可能的解决方案：")
        console.print("   1. 确保模型文件完整下载")
        console.print(
            "   2. 检查 transformers 版本：pip install --upgrade transformers"
        )
        console.print("   3. 检查是否有足够的内存")
        console.print("   4. 尝试重新下载模型")
    console.print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
