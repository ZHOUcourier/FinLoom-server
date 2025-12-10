#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FinLoom 量化投资引擎 - 图形化启动器
提供美观的GUI界面来启动和管理FinLoom服务
"""

import os
import signal
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk


class FinLoomLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("FinLoom 量化投资引擎 - 启动器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 设置窗口图标（如果有的话）
        try:
            if sys.platform == "win32":
                self.root.iconbitmap(default="favicon.ico")
        except:
            pass

        # 进程管理
        self.backend_process = None
        self.is_running = False
        self.build_process = None

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 自动检查环境
        self.root.after(500, self.check_environment)

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use("clam")

        # 配置颜色
        bg_color = "#f5f5f5"
        accent_color = "#2196F3"
        success_color = "#4CAF50"
        warning_color = "#FF9800"
        error_color = "#F44336"

        self.root.configure(bg=bg_color)

        # 按钮样式
        style.configure(
            "Accent.TButton",
            background=accent_color,
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=10,
        )
        style.map("Accent.TButton", background=[("active", "#1976D2")])

        style.configure(
            "Success.TButton",
            background=success_color,
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=10,
        )
        style.map("Success.TButton", background=[("active", "#388E3C")])

        style.configure(
            "Warning.TButton",
            background=warning_color,
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=10,
        )
        style.map("Warning.TButton", background=[("active", "#F57C00")])

        style.configure(
            "Error.TButton",
            background=error_color,
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=10,
        )
        style.map("Error.TButton", background=[("active", "#D32F2F")])

    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))

        title_label = tk.Label(
            title_frame,
            text="🚀 FinLoom 量化投资引擎",
            font=("Microsoft YaHei UI", 24, "bold"),
            bg="#f5f5f5",
            fg="#2196F3",
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_frame,
            text="一键启动 · 简单高效 · 智能量化",
            font=("Microsoft YaHei UI", 10),
            bg="#f5f5f5",
            fg="#666",
        )
        subtitle_label.pack()

        # 状态区域
        status_frame = ttk.LabelFrame(main_frame, text="系统状态", padding="15")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        status_frame.columnconfigure(1, weight=1)

        # 环境状态
        ttk.Label(status_frame, text="Python:", font=("Microsoft YaHei UI", 9)).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10)
        )
        self.python_status = tk.Label(
            status_frame,
            text="检查中...",
            fg="#FF9800",
            font=("Microsoft YaHei UI", 9),
            bg="#f5f5f5",
        )
        self.python_status.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(status_frame, text="Node.js:", font=("Microsoft YaHei UI", 9)).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0)
        )
        self.node_status = tk.Label(
            status_frame,
            text="检查中...",
            fg="#FF9800",
            font=("Microsoft YaHei UI", 9),
            bg="#f5f5f5",
        )
        self.node_status.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

        ttk.Label(status_frame, text="前端构建:", font=("Microsoft YaHei UI", 9)).grid(
            row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0)
        )
        self.build_status = tk.Label(
            status_frame,
            text="检查中...",
            fg="#FF9800",
            font=("Microsoft YaHei UI", 9),
            bg="#f5f5f5",
        )
        self.build_status.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))

        ttk.Label(status_frame, text="服务状态:", font=("Microsoft YaHei UI", 9)).grid(
            row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0)
        )
        self.service_status = tk.Label(
            status_frame,
            text="● 未启动",
            fg="#666",
            font=("Microsoft YaHei UI", 9, "bold"),
            bg="#f5f5f5",
        )
        self.service_status.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))

        # 快捷访问
        access_frame = ttk.LabelFrame(main_frame, text="快捷访问", padding="15")
        access_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        access_button_frame = ttk.Frame(access_frame)
        access_button_frame.pack(fill=tk.X)

        ttk.Button(
            access_button_frame,
            text="🌐 打开主界面",
            command=lambda: self.open_browser("http://localhost:8000"),
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        ttk.Button(
            access_button_frame,
            text="📚 API文档",
            command=lambda: self.open_browser("http://localhost:8000/docs"),
            style="Accent.TButton",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.WORD,
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_text.config(state=tk.DISABLED)

        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.build_button = ttk.Button(
            button_frame,
            text="🔨 构建前端",
            command=self.build_frontend,
            style="Warning.TButton",
        )
        self.build_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        self.start_button = ttk.Button(
            button_frame,
            text="▶ 启动服务",
            command=self.start_service,
            style="Success.TButton",
        )
        self.start_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))

        self.stop_button = ttk.Button(
            button_frame,
            text="⬛ 停止服务",
            command=self.stop_service,
            style="Error.TButton",
            state=tk.DISABLED,
        )
        self.stop_button.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(5, 0))

    def log(self, message, level="INFO"):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        color_map = {
            "INFO": "#4CAF50",
            "WARNING": "#FF9800",
            "ERROR": "#F44336",
            "SUCCESS": "#00E676",
        }

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"[{level}] ", level)
        self.log_text.insert(tk.END, f"{message}\n")

        # 配置标签颜色
        self.log_text.tag_config("timestamp", foreground="#808080")
        self.log_text.tag_config(level, foreground=color_map.get(level, "#d4d4d4"))

        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def check_environment(self):
        """检查运行环境"""
        self.log("开始检查运行环境...", "INFO")

        # 检查Python
        try:
            result = subprocess.run(
                ["python", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32"
                else 0,
            )
            version = result.stdout.strip() or result.stderr.strip()
            self.python_status.config(text=f"✓ {version}", fg="#4CAF50")
            self.log(f"Python环境: {version}", "SUCCESS")
        except Exception as e:
            self.python_status.config(text="✗ 未安装", fg="#F44336")
            self.log(f"Python检查失败: {str(e)}", "ERROR")

        # 检查Node.js
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32"
                else 0,
            )
            version = result.stdout.strip()
            self.node_status.config(text=f"✓ {version}", fg="#4CAF50")
            self.log(f"Node.js环境: {version}", "SUCCESS")
        except Exception as e:
            self.node_status.config(text="✗ 未安装", fg="#F44336")
            self.log(f"Node.js检查失败: {str(e)}", "ERROR")

        # 检查前端构建
        if os.path.exists("web/dist/index.html"):
            self.build_status.config(text="✓ 已构建", fg="#4CAF50")
            self.log("前端构建产物: 已存在", "SUCCESS")
        else:
            self.build_status.config(text="✗ 未构建", fg="#F44336")
            self.log("前端构建产物: 不存在，需要先构建", "WARNING")

        self.log("环境检查完成！", "SUCCESS")

    def build_frontend(self):
        """构建前端"""
        if self.build_process and self.build_process.poll() is None:
            messagebox.showwarning("提示", "前端正在构建中，请稍候...")
            return

        self.log("开始构建前端...", "INFO")
        self.build_button.config(state=tk.DISABLED)
        self.build_status.config(text="⟳ 构建中...", fg="#FF9800")

        def build():
            try:
                os.chdir("web-vue")

                # 检查依赖
                if not os.path.exists("node_modules"):
                    self.log("安装前端依赖中，请耐心等待...", "INFO")
                    result = subprocess.run(
                        ["npm", "install", "--registry=https://registry.npmmirror.com"],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        creationflags=subprocess.CREATE_NO_WINDOW
                        if sys.platform == "win32"
                        else 0,
                    )
                    if result.returncode != 0:
                        raise Exception(f"依赖安装失败: {result.stderr}")
                    self.log("前端依赖安装完成", "SUCCESS")

                # 构建
                self.log("正在构建前端，这可能需要1-2分钟...", "INFO")
                self.build_process = subprocess.Popen(
                    ["npm", "run", "build"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if sys.platform == "win32"
                    else 0,
                )

                stdout, stderr = self.build_process.communicate()

                os.chdir("..")

                if self.build_process.returncode == 0:
                    self.log("前端构建成功！", "SUCCESS")
                    self.build_status.config(text="✓ 已构建", fg="#4CAF50")
                else:
                    raise Exception(f"构建失败: {stderr}")

            except Exception as e:
                self.log(f"构建失败: {str(e)}", "ERROR")
                self.build_status.config(text="✗ 构建失败", fg="#F44336")
                os.chdir("..")
            finally:
                self.build_button.config(state=tk.NORMAL)
                self.build_process = None

        threading.Thread(target=build, daemon=True).start()

    def start_service(self):
        """启动服务"""
        if self.is_running:
            messagebox.showinfo("提示", "服务已经在运行中")
            return

        # 检查前端是否已构建
        if not os.path.exists("web/dist/index.html"):
            response = messagebox.askyesno(
                "前端未构建",
                '检测到前端未构建，是否先构建前端？\n\n点击"是"将自动构建前端（需要1-2分钟）\n点击"否"将取消启动',
            )
            if response:
                self.build_frontend()
                messagebox.showinfo("提示", "请等待前端构建完成后再次点击启动")
            return

        self.log("正在启动FinLoom服务...", "INFO")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.service_status.config(text="● 启动中...", fg="#FF9800")

        def run_backend():
            try:
                # 使用虚拟环境的Python（如果存在）
                python_exe = "python"
                if os.path.exists(".venv/Scripts/python.exe"):
                    python_exe = ".venv/Scripts/python.exe"
                elif os.path.exists(".venv/bin/python"):
                    python_exe = ".venv/bin/python"

                self.backend_process = subprocess.Popen(
                    [python_exe, "main.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if sys.platform == "win32"
                    else 0,
                )

                self.is_running = True
                self.service_status.config(text="● 运行中", fg="#4CAF50")
                self.log("FinLoom服务已启动！", "SUCCESS")
                self.log("访问地址: http://localhost:8000", "INFO")

                # 读取输出
                for line in self.backend_process.stdout:
                    if line.strip():
                        self.log(line.strip(), "INFO")

            except Exception as e:
                self.log(f"服务启动失败: {str(e)}", "ERROR")
                self.service_status.config(text="● 启动失败", fg="#F44336")
                self.is_running = False
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)

        threading.Thread(target=run_backend, daemon=True).start()

    def stop_service(self):
        """停止服务"""
        if not self.is_running or not self.backend_process:
            return

        self.log("正在停止服务...", "WARNING")

        try:
            if sys.platform == "win32":
                # Windows
                self.backend_process.send_signal(signal.CTRL_C_EVENT)
                time.sleep(1)
                if self.backend_process.poll() is None:
                    self.backend_process.terminate()
                    time.sleep(1)
                if self.backend_process.poll() is None:
                    self.backend_process.kill()
            else:
                # Linux/Mac
                self.backend_process.terminate()
                time.sleep(1)
                if self.backend_process.poll() is None:
                    self.backend_process.kill()

            self.is_running = False
            self.service_status.config(text="● 未启动", fg="#666")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.log("服务已停止", "SUCCESS")

        except Exception as e:
            self.log(f"停止服务时出错: {str(e)}", "ERROR")

    def open_browser(self, url):
        """打开浏览器"""
        try:
            webbrowser.open(url)
            self.log(f"已打开浏览器: {url}", "INFO")
        except Exception as e:
            self.log(f"打开浏览器失败: {str(e)}", "ERROR")

    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            response = messagebox.askyesno(
                "确认退出", "服务正在运行中，确定要退出吗？\n\n退出后服务将自动停止。"
            )
            if not response:
                return

            self.stop_service()

        self.root.destroy()


def main():
    """主函数"""
    # 确保在正确的目录下运行
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # 创建主窗口
    root = tk.Tk()
    app = FinLoomLauncher(root)

    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()
