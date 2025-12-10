"""
数据管道模块初始化文件

主要功能：
1. 数据采集 - 专注于中国A股市场数据获取（股票、宏观、财务数据）
2. 数据处理 - 数据清洗、验证和质量管理
3. 数据存储 - 统一的数据库管理和缓存
4. 实时数据 - 中国A股实时行情和情绪数据
"""

# 数据采集模块
from .data_acquisition.akshare_collector import (
    AkshareDataCollector,
    create_akshare_collector,
    fetch_stock_data_batch,
)

# 尝试导入可选模块
try:
    from .data_acquisition.alternative_data_collector import (
        ChineseAlternativeDataCollector,
    )
except ImportError:
    ChineseAlternativeDataCollector = None

try:
    from .data_acquisition.fundamental_collector import (
        ChineseFundamentalCollector,
    )
    from .data_acquisition.fundamental_collector import (
        FundamentalCollector as FundamentalDataCollector,
    )
except ImportError:
    ChineseFundamentalCollector = None
    FundamentalDataCollector = None

# 数据处理模块
from .data_processing.data_cleaner import (
    DataCleaner,
    create_data_cleaner,
    quick_clean_data,
)
from .data_processing.data_validator import (
    DataQualityMetrics,
    DataValidator,
    ValidationResult,
    ensure_data_quality,
    validate_dataframe,
)

# 尝试导入可选模块
try:
    from .data_processing.data_transformer import DataTransformer
except ImportError:
    DataTransformer = None

# 存储管理模块
from .storage_management.database_manager import (
    DatabaseManager,
    create_database_manager,
    get_database_manager,
)

# 尝试导入可选模块
try:
    from .storage_management.cache_manager import CacheManager
except ImportError:
    CacheManager = None

try:
    from .storage_management.file_storage import FileStorageManager
except ImportError:
    FileStorageManager = None

# 流处理模块已在简化版本中移除，专注于中国A股数据

__all__ = [
    # 数据采集
    "AkshareDataCollector",
    "create_akshare_collector",
    "fetch_stock_data_batch",
    # 数据处理
    "DataCleaner",
    "create_data_cleaner",
    "quick_clean_data",
    "DataValidator",
    "ValidationResult",
    "DataQualityMetrics",
    "validate_dataframe",
    "ensure_data_quality",
    # 存储管理
    "DatabaseManager",
    "get_database_manager",
    "create_database_manager",
]

# 数据管道协调器
try:
    from .data_pipeline_coordinator import (
        DataPipelineCoordinator,
        get_data_pipeline_coordinator,
        fetch_all_market_intelligence_data,
    )
except ImportError:
    DataPipelineCoordinator = None
    get_data_pipeline_coordinator = None
    fetch_all_market_intelligence_data = None

# 添加可选模块到导出列表
if ChineseAlternativeDataCollector is not None:
    __all__.append("ChineseAlternativeDataCollector")
if ChineseFundamentalCollector is not None:
    __all__.append("ChineseFundamentalCollector")
if FundamentalDataCollector is not None:
    __all__.append("FundamentalDataCollector")
if DataTransformer is not None:
    __all__.append("DataTransformer")
if CacheManager is not None:
    __all__.append("CacheManager")
if FileStorageManager is not None:
    __all__.append("FileStorageManager")
if DataPipelineCoordinator is not None:
    __all__.extend(["DataPipelineCoordinator", "get_data_pipeline_coordinator", "fetch_all_market_intelligence_data"])

# 版本信息
__version__ = "1.0.0"
__author__ = "FinLoom Team"
__description__ = "Chinese A-share financial data pipeline module for comprehensive market data collection"
