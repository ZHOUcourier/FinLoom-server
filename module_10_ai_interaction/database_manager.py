"""
数据库管理器模块
负责Module 10的数据存储和查询
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from common.logging_system import setup_logger

logger = setup_logger("module10_database")


class Module10DatabaseManager:
    """Module 10 数据库管理器"""

    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            import os
            db_path = os.path.join("data", "module10_ai_interaction.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 用户需求表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                raw_input TEXT NOT NULL,
                parsed_data TEXT,
                system_parameters TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_req_user_id ON user_requirements(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_req_session_id ON user_requirements(session_id)"
        )

        # 策略推荐表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                requirement_id INTEGER,
                recommendation_type TEXT,
                recommendation_data TEXT NOT NULL,
                confidence_score REAL,
                accepted BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (requirement_id) REFERENCES user_requirements(id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rec_user_id ON strategy_recommendations(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rec_session_id ON strategy_recommendations(session_id)"
        )

        # 对话会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialogue_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                turn_count INTEGER DEFAULT 0,
                final_state TEXT,
                session_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sess_user_id ON dialogue_sessions(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sess_session_id ON dialogue_sessions(session_id)"
        )

        # 意图分类日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                turn_id INTEGER,
                user_input TEXT NOT NULL,
                detected_intent TEXT NOT NULL,
                confidence REAL,
                entities TEXT,
                timestamp DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_intent_session_id ON intent_logs(session_id)"
        )

        # FIN-R1模型调用日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fin_r1_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_input TEXT NOT NULL,
                model_output TEXT,
                processing_time REAL,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                timestamp DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_finr1_session_id ON fin_r1_logs(session_id)"
        )

        # 参数映射记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parameter_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id INTEGER,
                target_module TEXT,
                input_parameters TEXT NOT NULL,
                output_parameters TEXT NOT NULL,
                validation_result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (requirement_id) REFERENCES user_requirements(id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_param_requirement_id ON parameter_mappings(requirement_id)"
        )

        # 用户反馈表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT,
                recommendation_id INTEGER,
                feedback_type TEXT,
                rating INTEGER,
                comment TEXT,
                timestamp DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES strategy_recommendations(id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON user_feedback(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON user_feedback(session_id)"
        )

        # 收藏对话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorite_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                title TEXT,
                summary TEXT,
                tags TEXT,
                rating INTEGER DEFAULT 0,
                favorited_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_fav_user_session ON favorite_conversations(user_id, session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_fav_user_id ON favorite_conversations(user_id)"
        )

        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.db_path}")

    # ========== 用户需求相关 ==========

    def save_user_requirement(
        self,
        user_id: str,
        session_id: str,
        raw_input: str,
        parsed_data: Dict[str, Any],
        system_parameters: Dict[str, Any],
    ) -> int:
        """保存用户需求

        Args:
            user_id: 用户ID
            session_id: 会话ID
            raw_input: 原始输入
            parsed_data: 解析后的数据
            system_parameters: 系统参数

        Returns:
            需求ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO user_requirements (
                    user_id, session_id, timestamp, raw_input, parsed_data, system_parameters
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    session_id,
                    datetime.now().isoformat(),
                    raw_input,
                    json.dumps(parsed_data, ensure_ascii=False),
                    json.dumps(system_parameters, ensure_ascii=False),
                ),
            )

            requirement_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Saved user requirement {requirement_id} for user {user_id}")
            return requirement_id

        except Exception as e:
            logger.error(f"Failed to save user requirement: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()

    def get_user_requirements(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取用户需求记录

        Args:
            user_id: 用户ID（可选）
            session_id: 会话ID（可选）
            limit: 限制数量

        Returns:
            需求记录列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM user_requirements WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "user_id": row[1],
                    "session_id": row[2],
                    "timestamp": row[3],
                    "raw_input": row[4],
                    "parsed_data": json.loads(row[5]) if row[5] else {},
                    "system_parameters": json.loads(row[6]) if row[6] else {},
                    "created_at": row[7],
                }
            )

        return results

    # ========== 策略推荐相关 ==========

    def save_strategy_recommendation(
        self,
        user_id: str,
        session_id: str,
        requirement_id: Optional[int],
        recommendation_type: str,
        recommendation_data: Dict[str, Any],
        confidence_score: float,
    ) -> int:
        """保存策略推荐

        Args:
            user_id: 用户ID
            session_id: 会话ID
            requirement_id: 需求ID
            recommendation_type: 推荐类型
            recommendation_data: 推荐数据
            confidence_score: 置信度分数

        Returns:
            推荐ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO strategy_recommendations (
                    user_id, session_id, requirement_id, recommendation_type,
                    recommendation_data, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    session_id,
                    requirement_id,
                    recommendation_type,
                    json.dumps(recommendation_data, ensure_ascii=False),
                    confidence_score,
                ),
            )

            recommendation_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Saved strategy recommendation {recommendation_id}")
            return recommendation_id

        except Exception as e:
            logger.error(f"Failed to save strategy recommendation: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()

    def get_strategy_recommendations(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        accepted_only: bool = False,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取策略推荐记录

        Args:
            user_id: 用户ID（可选）
            session_id: 会话ID（可选）
            accepted_only: 只返回已接受的推荐
            limit: 限制数量

        Returns:
            推荐记录列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM strategy_recommendations WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if accepted_only:
            query += " AND accepted = 1"

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "user_id": row[1],
                    "session_id": row[2],
                    "requirement_id": row[3],
                    "recommendation_type": row[4],
                    "recommendation_data": json.loads(row[5]) if row[5] else {},
                    "confidence_score": row[6],
                    "accepted": bool(row[7]),
                    "created_at": row[8],
                }
            )

        return results

    def update_recommendation_acceptance(
        self, recommendation_id: int, accepted: bool
    ) -> bool:
        """更新推荐接受状态

        Args:
            recommendation_id: 推荐ID
            accepted: 是否接受

        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE strategy_recommendations
                SET accepted = ?
                WHERE id = ?
            """,
                (int(accepted), recommendation_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to update recommendation acceptance: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ========== 对话会话相关 ==========

    def save_dialogue_session(
        self,
        session_id: str,
        user_id: str,
        start_time: datetime,
        session_data: Dict[str, Any],
    ) -> bool:
        """保存对话会话

        Args:
            session_id: 会话ID
            user_id: 用户ID
            start_time: 开始时间
            session_data: 会话数据

        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO dialogue_sessions (
                    session_id, user_id, start_time, session_data
                ) VALUES (?, ?, ?, ?)
            """,
                (
                    session_id,
                    user_id,
                    start_time.isoformat(),
                    json.dumps(session_data, ensure_ascii=False),
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to save dialogue session: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_dialogue_session(
        self,
        session_id: str,
        turn_count: Optional[int] = None,
        end_time: Optional[datetime] = None,
        final_state: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """更新对话会话

        Args:
            session_id: 会话ID
            turn_count: 回合数
            end_time: 结束时间
            final_state: 最终状态
            session_data: 会话数据

        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            updates = []
            params = []

            if turn_count is not None:
                updates.append("turn_count = ?")
                params.append(turn_count)

            if end_time is not None:
                updates.append("end_time = ?")
                params.append(end_time.isoformat())

            if final_state is not None:
                updates.append("final_state = ?")
                params.append(final_state)

            if session_data is not None:
                updates.append("session_data = ?")
                params.append(json.dumps(session_data, ensure_ascii=False))

            if not updates:
                return True

            query = f"UPDATE dialogue_sessions SET {', '.join(updates)} WHERE session_id = ?"
            params.append(session_id)

            cursor.execute(query, params)
            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to update dialogue session: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ========== 意图日志相关 ==========

    def save_intent_log(
        self,
        session_id: str,
        turn_id: int,
        user_input: str,
        detected_intent: str,
        confidence: float,
        entities: Dict[str, Any],
    ) -> bool:
        """保存意图分类日志

        Args:
            session_id: 会话ID
            turn_id: 回合ID
            user_input: 用户输入
            detected_intent: 检测到的意图
            confidence: 置信度
            entities: 实体

        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO intent_logs (
                    session_id, turn_id, user_input, detected_intent,
                    confidence, entities, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    turn_id,
                    user_input,
                    detected_intent,
                    confidence,
                    json.dumps(entities, ensure_ascii=False),
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to save intent log: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ========== FIN-R1日志相关 ==========

    def save_fin_r1_log(
        self,
        user_input: str,
        model_output: Optional[Dict[str, Any]],
        processing_time: float,
        success: bool,
        session_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """保存FIN-R1模型调用日志

        Args:
            user_input: 用户输入
            model_output: 模型输出
            processing_time: 处理时间
            success: 是否成功
            session_id: 会话ID（可选）
            error_message: 错误信息（可选）

        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO fin_r1_logs (
                    session_id, user_input, model_output, processing_time,
                    success, error_message, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    user_input,
                    json.dumps(model_output, ensure_ascii=False)
                    if model_output
                    else None,
                    processing_time,
                    int(success),
                    error_message,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to save FIN-R1 log: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ========== 参数映射相关 ==========

    def save_parameter_mapping(
        self,
        requirement_id: int,
        target_module: str,
        input_parameters: Dict[str, Any],
        output_parameters: Dict[str, Any],
        validation_result: Dict[str, Any],
    ) -> bool:
        """保存参数映射记录

        Args:
            requirement_id: 需求ID
            target_module: 目标模块
            input_parameters: 输入参数
            output_parameters: 输出参数
            validation_result: 验证结果

        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO parameter_mappings (
                    requirement_id, target_module, input_parameters,
                    output_parameters, validation_result
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    requirement_id,
                    target_module,
                    json.dumps(input_parameters, ensure_ascii=False),
                    json.dumps(output_parameters, ensure_ascii=False),
                    json.dumps(validation_result, ensure_ascii=False),
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to save parameter mapping: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ========== 用户反馈相关 ==========

    def save_user_feedback(
        self,
        user_id: str,
        feedback_type: str,
        rating: int,
        comment: Optional[str] = None,
        session_id: Optional[str] = None,
        recommendation_id: Optional[int] = None,
    ) -> bool:
        """保存用户反馈

        Args:
            user_id: 用户ID
            feedback_type: 反馈类型
            rating: 评分
            comment: 评论
            session_id: 会话ID（可选）
            recommendation_id: 推荐ID（可选）

        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO user_feedback (
                    user_id, session_id, recommendation_id, feedback_type,
                    rating, comment, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    session_id,
                    recommendation_id,
                    feedback_type,
                    rating,
                    comment,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to save user feedback: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ========== 统计查询 ==========

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # 总需求数
        cursor.execute("SELECT COUNT(*) FROM user_requirements")
        stats["total_requirements"] = cursor.fetchone()[0]

        # 总推荐数
        cursor.execute("SELECT COUNT(*) FROM strategy_recommendations")
        stats["total_recommendations"] = cursor.fetchone()[0]

        # 接受的推荐数
        cursor.execute(
            "SELECT COUNT(*) FROM strategy_recommendations WHERE accepted = 1"
        )
        stats["accepted_recommendations"] = cursor.fetchone()[0]

        # 总会话数
        cursor.execute("SELECT COUNT(*) FROM dialogue_sessions")
        stats["total_sessions"] = cursor.fetchone()[0]

        # 平均会话回合数
        cursor.execute(
            "SELECT AVG(turn_count) FROM dialogue_sessions WHERE turn_count > 0"
        )
        result = cursor.fetchone()[0]
        stats["avg_turns_per_session"] = round(result, 2) if result else 0

        # FIN-R1成功率
        cursor.execute("SELECT COUNT(*) FROM fin_r1_logs")
        total_fin_r1_calls = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM fin_r1_logs WHERE success = 1")
        successful_fin_r1_calls = cursor.fetchone()[0]
        stats["fin_r1_success_rate"] = (
            successful_fin_r1_calls / total_fin_r1_calls
            if total_fin_r1_calls > 0
            else 0
        )

        conn.close()

        return stats

    # ========== 收藏对话相关 ==========

    def add_favorite_conversation(
        self,
        user_id: str,
        session_id: str,
        title: str = None,
        summary: str = None,
        tags: List[str] = None,
        rating: int = 0,
    ) -> int:
        """添加收藏对话

        Args:
            user_id: 用户ID
            session_id: 会话ID
            title: 收藏标题
            summary: 对话摘要
            tags: 标签列表
            rating: 评分(0-5)

        Returns:
            收藏记录ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tags_json = json.dumps(tags) if tags else None
        favorited_at = datetime.now().isoformat()

        try:
            cursor.execute(
                """
                INSERT INTO favorite_conversations 
                (user_id, session_id, title, summary, tags, rating, favorited_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (user_id, session_id, title, summary, tags_json, rating, favorited_at),
            )
            favorite_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Added favorite conversation: {session_id} for user {user_id}")
            return favorite_id

        except sqlite3.IntegrityError:
            logger.warning(f"Conversation {session_id} already favorited by user {user_id}")
            # 如果已存在,更新信息
            cursor.execute(
                """
                UPDATE favorite_conversations 
                SET title = ?, summary = ?, tags = ?, rating = ?, favorited_at = ?
                WHERE user_id = ? AND session_id = ?
            """,
                (title, summary, tags_json, rating, favorited_at, user_id, session_id),
            )
            conn.commit()
            cursor.execute(
                "SELECT id FROM favorite_conversations WHERE user_id = ? AND session_id = ?",
                (user_id, session_id),
            )
            favorite_id = cursor.fetchone()[0]
            return favorite_id

        finally:
            conn.close()

    def remove_favorite_conversation(self, user_id: str, session_id: str) -> bool:
        """移除收藏对话

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            是否成功移除
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM favorite_conversations 
            WHERE user_id = ? AND session_id = ?
        """,
            (user_id, session_id),
        )

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Removed favorite conversation: {session_id} for user {user_id}")

        return deleted

    def get_favorite_conversations(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取用户收藏的对话列表

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            收藏对话列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, session_id, title, summary, tags, rating, favorited_at, created_at
            FROM favorite_conversations
            WHERE user_id = ?
            ORDER BY favorited_at DESC
            LIMIT ?
        """,
            (user_id, limit),
        )

        favorites = []
        for row in cursor.fetchall():
            favorites.append(
                {
                    "id": row[0],
                    "session_id": row[1],
                    "title": row[2],
                    "summary": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                    "rating": row[5],
                    "favorited_at": row[6],
                    "created_at": row[7],
                }
            )

        conn.close()

        return favorites

    def is_conversation_favorited(self, user_id: str, session_id: str) -> bool:
        """检查对话是否已收藏

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            是否已收藏
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) FROM favorite_conversations 
            WHERE user_id = ? AND session_id = ?
        """,
            (user_id, session_id),
        )

        is_favorited = cursor.fetchone()[0] > 0
        conn.close()

        return is_favorited

    def update_favorite_conversation(
        self,
        user_id: str,
        session_id: str,
        title: str = None,
        summary: str = None,
        tags: List[str] = None,
        rating: int = None,
    ) -> bool:
        """更新收藏对话信息

        Args:
            user_id: 用户ID
            session_id: 会话ID
            title: 新标题
            summary: 新摘要
            tags: 新标签列表
            rating: 新评分

        Returns:
            是否更新成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 构建更新语句
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)

        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)

        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))

        if rating is not None:
            updates.append("rating = ?")
            params.append(rating)

        if not updates:
            conn.close()
            return False

        params.extend([user_id, session_id])

        cursor.execute(
            f"""
            UPDATE favorite_conversations 
            SET {', '.join(updates)}
            WHERE user_id = ? AND session_id = ?
        """,
            params,
        )

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if updated:
            logger.info(f"Updated favorite conversation: {session_id} for user {user_id}")

        return updated


# 模块级别函数
_global_db_manager = None


def get_database_manager(
    db_path: str = "data/module10_ai_interaction.db",
) -> Module10DatabaseManager:
    """获取全局数据库管理器实例

    Args:
        db_path: 数据库路径

    Returns:
        数据库管理器实例
    """
    global _global_db_manager
    if _global_db_manager is None:
        _global_db_manager = Module10DatabaseManager(db_path)
    return _global_db_manager
