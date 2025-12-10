"""
AI交互模块初始化文件
提供自然语言理解、对话管理、需求解析、策略推荐等功能
"""

# AI服务（主备容错机制）
from .aliyun_ai_service import AliyunAIService

# FIN-R1集成
# 对话历史
from .conversation_history import (
    ConversationHistoryManager,
    ConversationRecord,
    create_history_manager,
)

# 数据库管理
from .database_manager import Module10DatabaseManager, get_database_manager

# 对话管理
from .dialogue_manager import (
    DialogueContext,
    DialogueManager,
    DialogueState,
    create_dialogue_manager,
)
from .hybrid_ai_service import HybridAIService

try:
    from .fin_r1_integration import FINR1Integration, process_investment_request

    _FIN_R1_IMPORT_ERROR = None
except ImportError as exc:  # noqa: F401
    _FIN_R1_IMPORT_ERROR = exc
    FINR1Integration = None  # type: ignore[assignment]

    def process_investment_request(*args, **kwargs):  # type: ignore[override]
        """Fallback when FIN-R1 integration is unavailable."""

        raise RuntimeError(
            "FIN-R1 integration component is not available in the current environment"
        ) from _FIN_R1_IMPORT_ERROR


# 意图分类
from .intent_classifier import (
    IntentClassifier,
    classify_user_intent,
    create_intent_classifier,
)

# NLP处理
from .nlp_processor import (
    NLPProcessor,
    SentimentResult,
    TextEntity,
    create_nlp_processor,
    process_user_input,
)

# 参数映射
from .parameter_mapper import (
    ParameterMapper,
    create_parameter_mapper,
    map_requirement_to_parameters,
)

# 推荐引擎
from .recommendation_engine import (
    InvestmentRecommendation,
    PortfolioRecommendation,
    RecommendationEngine,
    create_recommendation_engine,
    generate_default_recommendations,
)

# 需求解析
from .requirement_parser import (
    InvestmentConstraint,
    InvestmentGoal,
    InvestmentHorizon,
    ParsedRequirement,
    RequirementParser,
    RiskTolerance,
    parse_user_requirement,
)

# 响应生成
from .response_generator import (
    ResponseGenerator,
    ResponseTemplate,
    create_response_generator,
    generate_quick_response,
)

__all__ = [
    # AI服务（主备容错）
    "HybridAIService",
    "AliyunAIService",
    # FIN-R1
    "FINR1Integration",
    "process_investment_request",
    # 需求解析
    "InvestmentConstraint",
    "InvestmentGoal",
    "InvestmentHorizon",
    "ParsedRequirement",
    "RequirementParser",
    "RiskTolerance",
    "parse_user_requirement",
    # NLP
    "NLPProcessor",
    "SentimentResult",
    "TextEntity",
    "create_nlp_processor",
    "process_user_input",
    # 意图分类
    "IntentClassifier",
    "classify_user_intent",
    "create_intent_classifier",
    # 对话管理
    "DialogueContext",
    "DialogueManager",
    "DialogueState",
    "create_dialogue_manager",
    # 参数映射
    "ParameterMapper",
    "create_parameter_mapper",
    "map_requirement_to_parameters",
    # 响应生成
    "ResponseGenerator",
    "ResponseTemplate",
    "create_response_generator",
    "generate_quick_response",
    # 推荐引擎
    "InvestmentRecommendation",
    "PortfolioRecommendation",
    "RecommendationEngine",
    "create_recommendation_engine",
    "generate_default_recommendations",
    # 对话历史
    "ConversationHistoryManager",
    "ConversationRecord",
    "create_history_manager",
    # 数据库
    "Module10DatabaseManager",
    "get_database_manager",
]
