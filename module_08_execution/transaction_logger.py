"""
交易日志记录器模块
负责记录所有交易活动的详细日志
"""

import csv
import json
import os
import queue
import threading
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from common.exceptions import ExecutionError
from common.logging_system import setup_logger
from module_08_execution.order_manager import Order

logger = setup_logger("transaction_logger")


@dataclass
class TransactionLog:
    """交易日志记录"""

    log_id: str
    timestamp: datetime
    log_type: str  # 'ORDER', 'FILL', 'CANCEL', 'REJECT', 'ERROR'
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: Optional[float]
    status: str
    broker: str
    account_id: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def to_csv_row(self) -> List[str]:
        """转换为CSV行"""
        return [
            self.log_id,
            self.timestamp.isoformat(),
            self.log_type,
            self.order_id,
            self.symbol,
            self.side,
            str(self.quantity),
            str(self.price) if self.price else "",
            self.status,
            self.broker,
            self.account_id,
            json.dumps(self.metadata),
        ]


class TransactionLogger:
    """交易日志记录器类"""

    CSV_HEADERS = [
        "log_id",
        "timestamp",
        "log_type",
        "order_id",
        "symbol",
        "side",
        "quantity",
        "price",
        "status",
        "broker",
        "account_id",
        "metadata",
    ]

    def __init__(self, config: Dict[str, Any]):
        """初始化交易日志记录器

        Args:
            config: 配置字典
        """
        self.config = config

        # 日志目录
        import os
        default_log_dir = os.path.join("logs", "transactions")
        self.log_dir = Path(config.get("log_dir", default_log_dir))
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 日志格式
        self.log_format = config.get("log_format", "both")  # 'json', 'csv', 'both'

        # 文件句柄
        self.current_date: Optional[date] = None
        self.json_file = None
        self.csv_file = None
        self.csv_writer = None

        # 日志队列
        self.log_queue: queue.Queue = queue.Queue()

        # 写入线程
        self.writer_thread: Optional[threading.Thread] = None
        self.is_running = False

        # 统计信息
        self.log_count = 0
        self.error_count = 0

        # 启动写入线程
        self._start_writer()

    def log_order_submission(
        self,
        order: Order,
        broker: str,
        account_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录订单提交

        Args:
            order: 订单对象
            broker: 券商名称
            account_id: 账户ID
            metadata: 元数据
        """
        log = TransactionLog(
            log_id=f"LOG_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(),
            log_type="ORDER",
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            status=str(order.status.value),
            broker=broker,
            account_id=account_id,
            metadata=metadata or {},
        )

        self._enqueue_log(log)

    def log_order_fill(
        self,
        order_id: str,
        symbol: str,
        side: str,
        filled_quantity: int,
        fill_price: float,
        broker: str,
        account_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录订单成交

        Args:
            order_id: 订单ID
            symbol: 标的代码
            side: 买卖方向
            filled_quantity: 成交数量
            fill_price: 成交价格
            broker: 券商名称
            account_id: 账户ID
            metadata: 元数据
        """
        log = TransactionLog(
            log_id=f"LOG_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(),
            log_type="FILL",
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=filled_quantity,
            price=fill_price,
            status="FILLED",
            broker=broker,
            account_id=account_id,
            metadata=metadata or {},
        )

        self._enqueue_log(log)

    def log_order_cancellation(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        reason: str,
        broker: str,
        account_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录订单取消

        Args:
            order_id: 订单ID
            symbol: 标的代码
            side: 买卖方向
            quantity: 数量
            reason: 取消原因
            broker: 券商名称
            account_id: 账户ID
            metadata: 元数据
        """
        metadata = metadata or {}
        metadata["cancellation_reason"] = reason

        log = TransactionLog(
            log_id=f"LOG_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(),
            log_type="CANCEL",
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=None,
            status="CANCELLED",
            broker=broker,
            account_id=account_id,
            metadata=metadata,
        )

        self._enqueue_log(log)

    def log_order_rejection(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        reason: str,
        broker: str,
        account_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录订单拒绝

        Args:
            order_id: 订单ID
            symbol: 标的代码
            side: 买卖方向
            quantity: 数量
            reason: 拒绝原因
            broker: 券商名称
            account_id: 账户ID
            metadata: 元数据
        """
        metadata = metadata or {}
        metadata["rejection_reason"] = reason

        log = TransactionLog(
            log_id=f"LOG_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(),
            log_type="REJECT",
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=None,
            status="REJECTED",
            broker=broker,
            account_id=account_id,
            metadata=metadata,
        )

        self._enqueue_log(log)

    def log_error(
        self,
        order_id: str,
        error_type: str,
        error_message: str,
        broker: str,
        account_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录错误

        Args:
            order_id: 订单ID
            error_type: 错误类型
            error_message: 错误消息
            broker: 券商名称
            account_id: 账户ID
            metadata: 元数据
        """
        metadata = metadata or {}
        metadata["error_type"] = error_type
        metadata["error_message"] = error_message

        log = TransactionLog(
            log_id=f"LOG_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(),
            log_type="ERROR",
            order_id=order_id,
            symbol="",
            side="",
            quantity=0,
            price=None,
            status="ERROR",
            broker=broker,
            account_id=account_id,
            metadata=metadata,
        )

        self._enqueue_log(log)
        self.error_count += 1

    def query_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_id: Optional[str] = None,
        symbol: Optional[str] = None,
        log_type: Optional[str] = None,
    ) -> List[TransactionLog]:
        """查询日志

        Args:
            start_date: 开始日期
            end_date: 结束日期
            order_id: 订单ID
            symbol: 标的代码
            log_type: 日志类型

        Returns:
            符合条件的日志列表
        """
        logs = []

        # 确定要查询的日期范围
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        current = start_date.date()
        end = end_date.date()

        while current <= end:
            # 读取该日期的日志文件
            day_logs = self._read_logs_for_date(current)

            # 过滤日志
            for log in day_logs:
                if order_id and log.order_id != order_id:
                    continue
                if symbol and log.symbol != symbol:
                    continue
                if log_type and log.log_type != log_type:
                    continue
                if log.timestamp < start_date or log.timestamp > end_date:
                    continue

                logs.append(log)

            # 下一天
            current = current.replace(day=current.day + 1)

        return logs

    def get_daily_summary(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """获取每日汇总

        Args:
            target_date: 目标日期（默认今天）

        Returns:
            汇总信息字典
        """
        if target_date is None:
            target_date = date.today()

        logs = self._read_logs_for_date(target_date)

        summary = {
            "date": target_date.isoformat(),
            "total_logs": len(logs),
            "order_submissions": 0,
            "fills": 0,
            "cancellations": 0,
            "rejections": 0,
            "errors": 0,
            "unique_symbols": set(),
            "total_volume": 0,
            "by_broker": {},
            "by_symbol": {},
        }

        for log in logs:
            # 按类型统计
            if log.log_type == "ORDER":
                summary["order_submissions"] += 1
            elif log.log_type == "FILL":
                summary["fills"] += 1
                summary["total_volume"] += log.quantity
            elif log.log_type == "CANCEL":
                summary["cancellations"] += 1
            elif log.log_type == "REJECT":
                summary["rejections"] += 1
            elif log.log_type == "ERROR":
                summary["errors"] += 1

            # 收集唯一标的
            if log.symbol:
                summary["unique_symbols"].add(log.symbol)

            # 按券商统计
            if log.broker not in summary["by_broker"]:
                summary["by_broker"][log.broker] = {
                    "orders": 0,
                    "fills": 0,
                    "volume": 0,
                }
            summary["by_broker"][log.broker]["orders"] += 1
            if log.log_type == "FILL":
                summary["by_broker"][log.broker]["fills"] += 1
                summary["by_broker"][log.broker]["volume"] += log.quantity

            # 按标的统计
            if log.symbol and log.symbol not in summary["by_symbol"]:
                summary["by_symbol"][log.symbol] = {
                    "orders": 0,
                    "fills": 0,
                    "volume": 0,
                }
            if log.symbol:
                summary["by_symbol"][log.symbol]["orders"] += 1
                if log.log_type == "FILL":
                    summary["by_symbol"][log.symbol]["fills"] += 1
                    summary["by_symbol"][log.symbol]["volume"] += log.quantity

        summary["unique_symbols"] = len(summary["unique_symbols"])

        return summary

    def export_logs(
        self,
        output_file: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "csv",
    ) -> bool:
        """导出日志

        Args:
            output_file: 输出文件路径
            start_date: 开始日期
            end_date: 结束日期
            format: 导出格式 ('csv' 或 'json')

        Returns:
            是否成功导出
        """
        try:
            logs = self.query_logs(start_date, end_date)

            if format == "csv":
                with open(output_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(self.CSV_HEADERS)
                    for log in logs:
                        writer.writerow(log.to_csv_row())

            elif format == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    log_dicts = [log.to_dict() for log in logs]
                    json.dump(log_dicts, f, indent=2, default=str)

            else:
                logger.error(f"Unsupported export format: {format}")
                return False

            logger.info(f"Exported {len(logs)} logs to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return False

    def close(self) -> None:
        """关闭日志记录器"""
        self.is_running = False

        # 等待队列清空
        while not self.log_queue.empty():
            import time

            time.sleep(0.1)

        # 等待写入线程结束
        if self.writer_thread:
            self.writer_thread.join(timeout=5)

        # 关闭文件
        self._close_files()

        logger.info(
            f"Transaction logger closed. Total logs: {self.log_count}, Errors: {self.error_count}"
        )

    def _start_writer(self) -> None:
        """启动写入线程"""
        self.is_running = True
        self.writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.writer_thread.start()

    def _writer_loop(self) -> None:
        """写入循环"""
        while self.is_running or not self.log_queue.empty():
            try:
                # 获取日志（超时1秒）
                log = self.log_queue.get(timeout=1)

                # 写入文件
                self._write_log(log)

                self.log_count += 1

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error writing log: {e}")

    def _enqueue_log(self, log: TransactionLog) -> None:
        """将日志加入队列

        Args:
            log: 日志对象
        """
        try:
            self.log_queue.put(log, block=False)
        except queue.Full:
            logger.error("Log queue is full, dropping log")

    def _write_log(self, log: TransactionLog) -> None:
        """写入日志

        Args:
            log: 日志对象
        """
        # 检查日期变化
        log_date = log.timestamp.date()
        if log_date != self.current_date:
            self._rotate_files(log_date)

        # 写入JSON
        if self.log_format in ["json", "both"] and self.json_file:
            json_data = json.dumps(log.to_dict(), default=str)
            self.json_file.write(json_data + "\n")
            self.json_file.flush()

        # 写入CSV
        if self.log_format in ["csv", "both"] and self.csv_writer:
            self.csv_writer.writerow(log.to_csv_row())
            self.csv_file.flush()

    def _rotate_files(self, new_date: date) -> None:
        """轮换日志文件

        Args:
            new_date: 新日期
        """
        # 关闭旧文件
        self._close_files()

        # 创建新文件
        self.current_date = new_date
        date_str = new_date.strftime("%Y%m%d")

        # JSON文件
        if self.log_format in ["json", "both"]:
            json_path = self.log_dir / f"transactions_{date_str}.json"
            self.json_file = open(json_path, "a", encoding="utf-8")

        # CSV文件
        if self.log_format in ["csv", "both"]:
            csv_path = self.log_dir / f"transactions_{date_str}.csv"

            # 检查文件是否存在
            file_exists = csv_path.exists()

            self.csv_file = open(csv_path, "a", newline="", encoding="utf-8")
            self.csv_writer = csv.writer(self.csv_file)

            # 如果是新文件，写入表头
            if not file_exists:
                self.csv_writer.writerow(self.CSV_HEADERS)

    def _close_files(self) -> None:
        """关闭文件"""
        if self.json_file:
            self.json_file.close()
            self.json_file = None

        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None

    def _read_logs_for_date(self, target_date: date) -> List[TransactionLog]:
        """读取指定日期的日志

        Args:
            target_date: 目标日期

        Returns:
            日志列表
        """
        logs = []
        date_str = target_date.strftime("%Y%m%d")

        # 优先读取JSON文件
        json_path = self.log_dir / f"transactions_{date_str}.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                        logs.append(TransactionLog(**data))
                    except Exception as e:
                        logger.error(f"Error parsing log line: {e}")

        # 如果没有JSON，尝试CSV
        elif (self.log_dir / f"transactions_{date_str}.csv").exists():
            csv_path = self.log_dir / f"transactions_{date_str}.csv"
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        row["timestamp"] = datetime.fromisoformat(row["timestamp"])
                        row["quantity"] = int(row["quantity"])
                        row["price"] = float(row["price"]) if row["price"] else None
                        row["metadata"] = json.loads(row["metadata"])
                        logs.append(TransactionLog(**row))
                    except Exception as e:
                        logger.error(f"Error parsing CSV row: {e}")

        return logs


# 全局日志记录器
_global_logger: Optional[TransactionLogger] = None


def get_transaction_logger() -> TransactionLogger:
    """获取全局交易日志记录器

    Returns:
        交易日志记录器实例
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = TransactionLogger({"log_format": "both"})
    return _global_logger


def close_transaction_logger() -> None:
    """关闭全局交易日志记录器"""
    global _global_logger
    if _global_logger:
        _global_logger.close()
        _global_logger = None
