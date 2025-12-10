"""
对话历史管理器模块
负责管理和存储对话历史
"""

import json
import pickle
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from common.exceptions import QuantSystemError
from common.logging_system import setup_logger

logger = setup_logger("conversation_history")


@dataclass
class ConversationRecord:
    """对话记录数据结构"""

    session_id: str
    user_id: str
    turn_id: str
    timestamp: datetime
    user_input: str
    system_response: str
    intent: str
    entities: Dict[str, Any]
    confidence: float
    context_state: str
    metadata: Dict[str, Any]


class ConversationHistoryManager:
    """对话历史管理器类"""

    def __init__(
        self,
        storage_path: str = "./conversation_history",
        storage_type: str = "sqlite",  # 'sqlite', 'json', 'memory'
    ):
        """初始化对话历史管理器

        Args:
            storage_path: 存储路径
            storage_type: 存储类型
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.storage_type = storage_type

        if storage_type == "sqlite":
            self.db_path = self.storage_path / "conversations.db"
            self._init_database()
        elif storage_type == "memory":
            self.memory_storage: Dict[str, List[ConversationRecord]] = {}

        self.cache: Dict[str, List[ConversationRecord]] = {}
        self.cache_size = 100

    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                turn_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                user_input TEXT NOT NULL,
                system_response TEXT NOT NULL,
                intent TEXT,
                entities TEXT,
                confidence REAL,
                context_state TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_id ON conversations(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_id ON conversations(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)"
        )

        conn.commit()
        conn.close()

    def save_conversation_turn(self, record: ConversationRecord) -> bool:
        """保存对话回合

        Args:
            record: 对话记录

        Returns:
            是否成功保存
        """
        try:
            if self.storage_type == "sqlite":
                return self._save_to_sqlite(record)
            elif self.storage_type == "json":
                return self._save_to_json(record)
            elif self.storage_type == "memory":
                return self._save_to_memory(record)
            else:
                raise ValueError(f"Unknown storage type: {self.storage_type}")

        except Exception as e:
            logger.error(f"Failed to save conversation turn: {e}")
            return False

    def get_session_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[ConversationRecord]:
        """获取会话历史

        Args:
            session_id: 会话ID
            limit: 限制返回数量

        Returns:
            对话记录列表
        """
        # 先检查缓存
        if session_id in self.cache:
            records = self.cache[session_id]
            if limit:
                return records[-limit:]
            return records

        # 从存储加载
        if self.storage_type == "sqlite":
            records = self._load_from_sqlite(session_id, limit)
        elif self.storage_type == "json":
            records = self._load_from_json(session_id, limit)
        elif self.storage_type == "memory":
            records = self._load_from_memory(session_id, limit)
        else:
            records = []

        # 更新缓存
        if len(records) <= self.cache_size:
            self.cache[session_id] = records

        return records

    def get_user_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[ConversationRecord]:
        """获取用户历史

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量

        Returns:
            对话记录列表
        """
        if self.storage_type == "sqlite":
            return self._load_user_history_sqlite(user_id, start_date, end_date, limit)
        elif self.storage_type == "memory":
            return self._load_user_history_memory(user_id, start_date, end_date, limit)
        else:
            logger.warning(f"User history not supported for {self.storage_type}")
            return []

    def search_conversations(
        self, query: str, user_id: Optional[str] = None, limit: int = 10
    ) -> List[ConversationRecord]:
        """搜索对话

        Args:
            query: 搜索关键词
            user_id: 用户ID（可选）
            limit: 限制数量

        Returns:
            匹配的对话记录
        """
        if self.storage_type == "sqlite":
            return self._search_sqlite(query, user_id, limit)
        elif self.storage_type == "memory":
            return self._search_memory(query, user_id, limit)
        else:
            logger.warning(f"Search not supported for {self.storage_type}")
            return []

    def get_statistics(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取统计信息

        Args:
            user_id: 用户ID（可选）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            统计信息字典
        """
        stats = {
            "total_conversations": 0,
            "total_turns": 0,
            "average_turns_per_session": 0,
            "most_common_intents": {},
            "average_confidence": 0,
            "user_count": 0,
        }

        if self.storage_type == "sqlite":
            stats = self._get_statistics_sqlite(user_id, start_date, end_date)
        elif self.storage_type == "memory":
            stats = self._get_statistics_memory(user_id, start_date, end_date)

        return stats

    def export_history(
        self,
        output_path: str,
        format: str = "json",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """导出历史记录

        Args:
            output_path: 输出路径
            format: 导出格式 ('json', 'csv')
            user_id: 用户ID（可选）
            session_id: 会话ID（可选）

        Returns:
            是否成功导出
        """
        try:
            # 获取要导出的记录
            if session_id:
                records = self.get_session_history(session_id)
            elif user_id:
                records = self.get_user_history(user_id)
            else:
                records = self._get_all_records()

            if format == "json":
                self._export_to_json(records, output_path)
            elif format == "csv":
                self._export_to_csv(records, output_path)
            else:
                raise ValueError(f"Unknown export format: {format}")

            logger.info(f"Exported {len(records)} records to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            return False

    def clean_old_records(self, days_to_keep: int = 30) -> int:
        """清理旧记录

        Args:
            days_to_keep: 保留天数

        Returns:
            删除的记录数
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        if self.storage_type == "sqlite":
            return self._clean_old_records_sqlite(cutoff_date)
        elif self.storage_type == "memory":
            return self._clean_old_records_memory(cutoff_date)
        else:
            return 0

    def _save_to_sqlite(self, record: ConversationRecord) -> bool:
        """保存到SQLite数据库

        Args:
            record: 对话记录

        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO conversations (
                    session_id, user_id, turn_id, timestamp,
                    user_input, system_response, intent,
                    entities, confidence, context_state, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.session_id,
                    record.user_id,
                    record.turn_id,
                    record.timestamp.isoformat(),
                    record.user_input,
                    record.system_response,
                    record.intent,
                    json.dumps(record.entities),
                    record.confidence,
                    record.context_state,
                    json.dumps(record.metadata),
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"SQLite save error: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def _save_to_json(self, record: ConversationRecord) -> bool:
        """保存到JSON文件

        Args:
            record: 对话记录

        Returns:
            是否成功
        """
        file_path = self.storage_path / f"{record.session_id}.json"

        try:
            # 读取现有记录
            if file_path.exists():
                with open(file_path, "r") as f:
                    data = json.load(f)
            else:
                data = []

            # 添加新记录
            record_dict = asdict(record)
            record_dict["timestamp"] = record.timestamp.isoformat()
            data.append(record_dict)

            # 写回文件
            with open(file_path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"JSON save error: {e}")
            return False

    def _save_to_memory(self, record: ConversationRecord) -> bool:
        """保存到内存

        Args:
            record: 对话记录

        Returns:
            是否成功
        """
        if record.session_id not in self.memory_storage:
            self.memory_storage[record.session_id] = []

        self.memory_storage[record.session_id].append(record)
        return True

    def _load_from_sqlite(
        self, session_id: str, limit: Optional[int]
    ) -> List[ConversationRecord]:
        """从SQLite加载

        Args:
            session_id: 会话ID
            limit: 限制数量

        Returns:
            对话记录列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT * FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (session_id,))
        rows = cursor.fetchall()
        conn.close()

        records = []
        for row in rows:
            records.append(self._row_to_record(row))

        return records

    def _load_from_json(
        self, session_id: str, limit: Optional[int]
    ) -> List[ConversationRecord]:
        """从JSON加载

        Args:
            session_id: 会话ID
            limit: 限制数量

        Returns:
            对话记录列表
        """
        file_path = self.storage_path / f"{session_id}.json"

        if not file_path.exists():
            return []

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            records = []
            for item in data:
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                records.append(ConversationRecord(**item))

            if limit:
                return records[-limit:]
            return records

        except Exception as e:
            logger.error(f"JSON load error: {e}")
            return []

    def _load_from_memory(
        self, session_id: str, limit: Optional[int]
    ) -> List[ConversationRecord]:
        """从内存加载

        Args:
            session_id: 会话ID
            limit: 限制数量

        Returns:
            对话记录列表
        """
        records = self.memory_storage.get(session_id, [])

        if limit:
            return records[-limit:]
        return records

    def _load_user_history_sqlite(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[ConversationRecord]:
        """从SQLite加载用户历史

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量

        Returns:
            对话记录列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM conversations WHERE user_id = ?"
        params = [user_id]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        records = []
        for row in rows:
            records.append(self._row_to_record(row))

        return records

    def _load_user_history_memory(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[ConversationRecord]:
        """从内存加载用户历史

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量

        Returns:
            对话记录列表
        """
        all_records = []
        for session_records in self.memory_storage.values():
            for record in session_records:
                if record.user_id == user_id:
                    if start_date and record.timestamp < start_date:
                        continue
                    if end_date and record.timestamp > end_date:
                        continue
                    all_records.append(record)

        # 按时间戳排序
        all_records.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            return all_records[:limit]
        return all_records

    def _search_sqlite(
        self, query: str, user_id: Optional[str] = None, limit: int = 10
    ) -> List[ConversationRecord]:
        """从SQLite搜索对话

        Args:
            query: 搜索关键词
            user_id: 用户ID（可选）
            limit: 限制数量

        Returns:
            匹配的对话记录
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        sql_query = """
            SELECT * FROM conversations
            WHERE (user_input LIKE ? OR system_response LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%"]

        if user_id:
            sql_query += " AND user_id = ?"
            params.append(user_id)

        sql_query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql_query, params)
        rows = cursor.fetchall()
        conn.close()

        records = []
        for row in rows:
            records.append(self._row_to_record(row))

        return records

    def _search_memory(
        self, query: str, user_id: Optional[str] = None, limit: int = 10
    ) -> List[ConversationRecord]:
        """从内存搜索对话

        Args:
            query: 搜索关键词
            user_id: 用户ID（可选）
            limit: 限制数量

        Returns:
            匹配的对话记录
        """
        matched_records = []

        for session_records in self.memory_storage.values():
            for record in session_records:
                if user_id and record.user_id != user_id:
                    continue

                if query.lower() in record.user_input.lower() or query.lower() in record.system_response.lower():
                    matched_records.append(record)

        # 按时间戳排序
        matched_records.sort(key=lambda x: x.timestamp, reverse=True)

        return matched_records[:limit]

    def _row_to_record(self, row: tuple) -> ConversationRecord:
        """将数据库行转换为记录对象

        Args:
            row: 数据库行

        Returns:
            对话记录对象
        """
        return ConversationRecord(
            session_id=row[1],
            user_id=row[2],
            turn_id=row[3],
            timestamp=datetime.fromisoformat(row[4]),
            user_input=row[5],
            system_response=row[6],
            intent=row[7],
            entities=json.loads(row[8]) if row[8] else {},
            confidence=row[9],
            context_state=row[10],
            metadata=json.loads(row[11]) if row[11] else {},
        )

    def _get_statistics_sqlite(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """从SQLite获取统计信息

        Args:
            user_id: 用户ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 构建查询条件
            conditions = []
            params = []

            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date.isoformat())
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date.isoformat())

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # 总会话数
            cursor.execute(
                f"SELECT COUNT(DISTINCT session_id) FROM conversations {where_clause}",
                params,
            )
            total_conversations = cursor.fetchone()[0]

            # 总回合数
            cursor.execute(f"SELECT COUNT(*) FROM conversations {where_clause}", params)
            total_turns = cursor.fetchone()[0]

            # 平均回合数
            average_turns = (
                total_turns / total_conversations if total_conversations > 0 else 0
            )

            # 最常见意图
            cursor.execute(
                f"SELECT intent, COUNT(*) as count FROM conversations {where_clause} GROUP BY intent ORDER BY count DESC LIMIT 5",
                params,
            )
            most_common_intents = {row[0]: row[1] for row in cursor.fetchall()}

            # 平均置信度
            cursor.execute(
                f"SELECT AVG(confidence) FROM conversations {where_clause}", params
            )
            average_confidence = cursor.fetchone()[0] or 0

            # 用户数
            cursor.execute(
                f"SELECT COUNT(DISTINCT user_id) FROM conversations {where_clause}",
                params,
            )
            user_count = cursor.fetchone()[0]

            return {
                "total_conversations": total_conversations,
                "total_turns": total_turns,
                "average_turns_per_session": average_turns,
                "most_common_intents": most_common_intents,
                "average_confidence": average_confidence,
                "user_count": user_count,
            }

        except Exception as e:
            logger.error(f"Error getting statistics from SQLite: {e}")
            return {
                "total_conversations": 0,
                "total_turns": 0,
                "average_turns_per_session": 0,
                "most_common_intents": {},
                "average_confidence": 0,
                "user_count": 0,
            }
        finally:
            conn.close()

    def _get_statistics_memory(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """从内存获取统计信息

        Args:
            user_id: 用户ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            统计信息字典
        """
        # 过滤记录
        records = [r for session in self.memory_storage.values() for r in session]

        if user_id:
            records = [r for r in records if r.user_id == user_id]
        if start_date:
            records = [r for r in records if r.timestamp >= start_date]
        if end_date:
            records = [r for r in records if r.timestamp <= end_date]

        # 统计
        sessions = set(r.session_id for r in records)
        total_conversations = len(sessions)
        total_turns = len(records)
        average_turns = (
            total_turns / total_conversations if total_conversations > 0 else 0
        )

        # 最常见意图
        intent_counts = {}
        for record in records:
            intent_counts[record.intent] = intent_counts.get(record.intent, 0) + 1
        most_common_intents = dict(
            sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        )

        # 平均置信度
        confidences = [r.confidence for r in records if r.confidence is not None]
        average_confidence = sum(confidences) / len(confidences) if confidences else 0

        # 用户数
        users = set(r.user_id for r in records)
        user_count = len(users)

        return {
            "total_conversations": total_conversations,
            "total_turns": total_turns,
            "average_turns_per_session": average_turns,
            "most_common_intents": most_common_intents,
            "average_confidence": average_confidence,
            "user_count": user_count,
        }

    def _export_to_json(self, records: List[ConversationRecord], output_path: str):
        """导出为JSON格式

        Args:
            records: 记录列表
            output_path: 输出路径
        """
        data = []
        for record in records:
            record_dict = asdict(record)
            record_dict["timestamp"] = record.timestamp.isoformat()
            data.append(record_dict)

        with open(output_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _export_to_csv(self, records: List[ConversationRecord], output_path: str):
        """导出为CSV格式

        Args:
            records: 记录列表
            output_path: 输出路径
        """
        import csv

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # 写入表头
            writer.writerow(
                [
                    "session_id",
                    "user_id",
                    "turn_id",
                    "timestamp",
                    "user_input",
                    "system_response",
                    "intent",
                    "confidence",
                    "context_state",
                ]
            )

            # 写入数据
            for record in records:
                writer.writerow(
                    [
                        record.session_id,
                        record.user_id,
                        record.turn_id,
                        record.timestamp.isoformat(),
                        record.user_input,
                        record.system_response,
                        record.intent,
                        record.confidence,
                        record.context_state,
                    ]
                )


# 模块级别函数
def create_history_manager(storage_type: str = "sqlite") -> ConversationHistoryManager:
    """创建历史管理器实例

    Args:
        storage_type: 存储类型

    Returns:
        历史管理器实例
    """
    return ConversationHistoryManager(storage_type=storage_type)
