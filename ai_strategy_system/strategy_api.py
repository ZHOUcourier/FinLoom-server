#!/usr/bin/env python3
"""FastAPI router exposing the intelligent strategy workflow as background jobs."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from ai_strategy_system.intelligent_strategy_ai import IntelligentStrategyAI
from common.logging_system import setup_logger

LOGGER = setup_logger("strategy_api")

STEP_ORDER = [
    "AI理解用户需求",
    "AI分析市场状态",
    "AI智能选股",
    "AI选择最优模型",
    "训练AI模型",
    "生成交易策略",
]

STEP_MESSAGES = {
    "AI理解用户需求": "正在解析投资需求...",
    "AI分析市场状态": "正在分析市场环境...",
    "AI智能选股": "正在筛选候选股票...",
    "AI选择最优模型": "正在匹配最优模型...",
    "训练AI模型": "正在训练AI模型...",
    "生成交易策略": "正在生成策略与组合...",
}


class StrategyRequest(BaseModel):
    """Payload originating from the strategy builder UI."""

    target_return: float = Field(
        ..., alias="targetReturn", description="年度收益目标，百分比"
    )
    investment_period: str = Field(
        ..., alias="investmentPeriod", description="投资期限代码"
    )
    initial_capital: float = Field(
        ..., alias="initialCapital", description="初始资金（单位: 万元）"
    )
    risk_preference: str = Field(
        ..., alias="riskPreference", description="风险偏好代码"
    )
    max_drawdown: float = Field(
        ..., alias="maxDrawdown", description="最大回撤容忍度，百分比"
    )
    preferred_tags: list[str] = Field(
        default_factory=list, alias="preferredTags", description="偏好行业标签"
    )
    strategy_type: str = Field(..., alias="strategyType", description="策略类型代码")
    trading_frequency: str = Field(
        ..., alias="tradingFrequency", description="交易频率代码"
    )
    additional_requirements: Optional[str] = Field(
        None, alias="additionalRequirements", description="额外需求"
    )

    class Config:
        allow_population_by_field_name = True


class StrategyJobStatus(BaseModel):
    """Response model summarising job execution state."""

    job_id: str = Field(..., alias="jobId")
    status: str
    progress: float
    step_index: Optional[int] = Field(None, alias="stepIndex")
    step_name: Optional[str] = Field(None, alias="stepName")
    message: Optional[str]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class StrategyJob:
    """In-memory representation of a workflow execution job."""

    def __init__(self, job_id: str, user_id: Optional[str]) -> None:
        self.job_id = job_id
        self.user_id = user_id
        self.status: str = "pending"
        self.progress: float = 0.0
        self.step_index: Optional[int] = None
        self.step_name: Optional[str] = None
        self.message: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = self.created_at
        self.task: Optional[asyncio.Task[None]] = None
        self.ai_instance: Optional[Any] = None  # 保存AI实例供回测使用

    def to_status(self) -> StrategyJobStatus:
        return StrategyJobStatus(
            jobId=self.job_id,
            status=self.status,
            progress=round(self.progress, 4),
            stepIndex=self.step_index,
            stepName=self.step_name,
            message=self.message,
            result=self.result,
            error=self.error,
            createdAt=self.created_at,
            updatedAt=self.updated_at,
        )


class StrategyJobManager:
    """Coordinates background execution of strategy workflow jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[str, StrategyJob] = {}
        self._lock = asyncio.Lock()

    async def create_job(
        self, request: StrategyRequest, user_id: Optional[str]
    ) -> StrategyJob:
        job_id = uuid.uuid4().hex
        job = StrategyJob(job_id, user_id)
        async with self._lock:
            self._jobs[job_id] = job
        job.task = asyncio.create_task(self._run_job(job, request))
        return job

    async def _run_job(self, job: StrategyJob, request: StrategyRequest) -> None:
        job.status = "running"
        job.updated_at = datetime.utcnow()

        async def progress_callback(
            step_index: int, step_name: str, status_flag: str
        ) -> None:
            await self.update_progress(job.job_id, step_index, step_name, status_flag)

        try:
            requirement_text = build_requirement_text(request)
            initial_capital = request.initial_capital * 10_000  # 转换为元

            ai = IntelligentStrategyAI(
                user_requirement=requirement_text,
                initial_capital=initial_capital,
                progress_callback=progress_callback,
            )
            # 默认跳过回测，由用户手动点击回测按钮触发
            success = await ai.run_intelligent_workflow(skip_backtest=True)

            # 保存AI实例的引用，供后续回测使用
            job.ai_instance = ai

            if success and ai.workflow_result:
                job.status = "completed"
                job.progress = 1.0
                job.step_index = len(STEP_ORDER)
                job.step_name = STEP_ORDER[-1]
                job.message = "策略生成与回测完成"
                job.result = serialize_workflow_result(ai.workflow_result)
            else:
                job.status = "failed"
                job.message = "策略流程执行失败"
                job.error = "Workflow returned unsuccessful result"
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
            job.message = "执行过程中发生错误"
        finally:
            job.updated_at = datetime.utcnow()

    async def update_progress(
        self, job_id: str, step_index: int, step_name: str, status_flag: str
    ) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status in {"completed", "failed"}:
                return
            job.step_index = step_index
            job.step_name = step_name
            job.status = "running"
            job.progress = compute_progress(step_index, status_flag)
            job.message = derive_message(step_name, status_flag)
            job.updated_at = datetime.utcnow()

    async def get_job(self, job_id: str) -> StrategyJob:
        async with self._lock:
            job = self._jobs.get(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在或已过期"
            )
        return job


job_manager = StrategyJobManager()
router = APIRouter(prefix="/api/v1/strategy/workflow", tags=["strategy-workflow"])
backtest_router = APIRouter(prefix="/api/v1/strategy", tags=["strategy-backtest"])


@router.post("/start", response_model=StrategyJobStatus)
async def start_strategy_workflow(
    request: StrategyRequest,
    authorization: Optional[str] = Header(None),
) -> StrategyJobStatus:
    user_id = await validate_strategy_permission(authorization)
    job = await job_manager.create_job(request, user_id)
    return job.to_status()


@router.get("/{job_id}/status", response_model=StrategyJobStatus)
async def get_strategy_status(job_id: str) -> StrategyJobStatus:
    job = await job_manager.get_job(job_id)
    return job.to_status()


@router.get("/{job_id}/result", response_model=Dict[str, Any])
async def get_strategy_result(job_id: str) -> Dict[str, Any]:
    job = await job_manager.get_job(job_id)
    if job.status != "completed" or not job.result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="任务尚未完成")
    return job.result


async def validate_strategy_permission(authorization: Optional[str]) -> Optional[str]:
    from common.permissions import UserPermissions, get_user_permissions  # noqa: WPS433
    from common.user_database import user_db  # noqa: WPS433

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="未授权：请先登录"
        )

    token = authorization.replace("Bearer ", "")
    valid, message, user_info = user_db.verify_token(token)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message or "令牌无效或已过期",
        )

    user_perms = get_user_permissions(user_info)
    if not user_perms.has_permission(UserPermissions.PERMISSION_STRATEGY_GENERATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="您没有策略生成权限"
        )

    return user_info.get("user_id") if isinstance(user_info, dict) else None


def compute_progress(step_index: int, status_flag: str) -> float:
    total_steps = len(STEP_ORDER)
    base = max(step_index - 1, 0) / total_steps
    if status_flag == "running":
        return min(base + 0.05, 0.99)
    if status_flag == "completed":
        return min(step_index / total_steps, 1.0)
    if status_flag == "failed":
        return base
    return base


def derive_message(step_name: str, status_flag: str) -> str:
    if status_flag == "running":
        return STEP_MESSAGES.get(step_name, f"正在执行 {step_name}...")
    if status_flag == "completed":
        return f"{step_name} 完成"
    if status_flag == "failed":
        return f"{step_name} 失败"
    return step_name


def build_requirement_text(request: StrategyRequest) -> str:
    period_map = {
        "short": "1-3个月",
        "medium": "3-12个月",
        "long": "1年以上",
    }
    risk_map = {
        "conservative": "保守型",
        "moderate": "稳健型",
        "aggressive": "进取型",
    }
    frequency_map = {
        "daily": "每日调仓",
        "weekly": "每周调仓",
        "monthly": "每月调仓",
        "quarterly": "每季度调仓",
    }
    strategy_map = {
        "value": "价值投资",
        "growth": "成长投资",
        "momentum": "动量交易",
        "mean_reversion": "均值回归",
        "quant": "量化多因子",
    }

    capital_amount = request.initial_capital * 10_000
    preferred_tags = request.preferred_tags or ["不限"]
    extra = (
        f" 其他需求：{request.additional_requirements}"
        if request.additional_requirements
        else ""
    )

    return (
        f"我有约{capital_amount:,.0f}元资金，期望年化收益{request.target_return:.2f}%"
        f"，投资期限{period_map.get(request.investment_period, request.investment_period)}"
        f"，风险偏好{risk_map.get(request.risk_preference, request.risk_preference)}"
        f"，最大可接受回撤{request.max_drawdown:.2f}%"
        f"，偏好行业包括{'、'.join(preferred_tags)}"
        f"，倾向的策略类型是{strategy_map.get(request.strategy_type, request.strategy_type)}"
        f"，交易频率希望{frequency_map.get(request.trading_frequency, request.trading_frequency)}。"
        f"请基于这些要求设计一个可实施的量化策略，包含模型选择、因子、仓位管理和风险控制。"
        + extra
    )


def serialize_workflow_result(result: StrategyWorkflowResult) -> Dict[str, Any]:
    """Convert StrategyWorkflowResult into a JSON-friendly structure."""

    # 提取回测指标
    backtest_metrics = {}
    if (
        result.backtest
        and hasattr(result.backtest, "result")
        and result.backtest.result
    ):
        bt_result = result.backtest.result
        backtest_metrics = {
            "totalReturn": getattr(bt_result, "total_return", 0.0),
            "annualizedReturn": getattr(bt_result, "annualized_return", 0.0),
            "sharpeRatio": getattr(bt_result, "sharpe_ratio", 0.0),
            "maxDrawdown": getattr(bt_result, "max_drawdown", 0.0),
            "totalTrades": getattr(bt_result, "total_trades", 0),
            "winRate": getattr(bt_result, "win_rate", 0.0),
            "profitFactor": getattr(bt_result, "profit_factor", 0.0),
            "calmarRatio": getattr(bt_result, "calmar_ratio", 0.0),
            "sortinoRatio": getattr(bt_result, "sortino_ratio", 0.0),
        }
        LOGGER.info(f"📊 回测指标已提取: {backtest_metrics}")

    # 提取策略代码
    strategy_code_info = None
    if (
        result.backtest
        and hasattr(result.backtest, "strategy_code")
        and result.backtest.strategy_code
    ):
        strategy_code_info = {
            "name": getattr(
                result.backtest.strategy_code, "strategy_name", "未命名策略"
            ),
            "code": getattr(result.backtest.strategy_code, "code", ""),
            "parameters": getattr(result.backtest.strategy_code, "parameters", {}),
            "description": getattr(result.backtest.strategy_code, "description", ""),
            "version": getattr(result.backtest.strategy_code, "version", "1.0.0"),
            "createdAt": getattr(
                result.backtest.strategy_code, "created_at", datetime.utcnow()
            ).isoformat(),
        }

    # 提取推荐股票列表
    recommended_stocks = []
    if hasattr(result, "universe") and result.universe:
        recommended_stocks = getattr(result.universe, "symbols", [])

    return {
        "title": f"智能AI策略 - {result.model.choice.model_type.upper()}",
        "description": result.requirement.explanation,
        "recommendedStocks": recommended_stocks,
        "strategyCode": strategy_code_info,
        "requirement": {
            "rawText": result.requirement.raw_text,
            "systemParams": result.requirement.system_params,
        },
        "market": {
            "asOf": result.market.as_of.isoformat(),
            "regime": result.market.regime,
            "sentiment": result.market.sentiment,
            "macro": result.market.macro_summary,
        },
        "universe": {
            "symbols": result.universe.symbols,
            "rationale": result.universe.rationale,
        },
        "model": {
            "type": result.model.choice.model_type,
            "reason": result.model.choice.reason,
            "config": result.model.choice.config,
            "training": result.model.training_metadata,
        },
        "strategyParams": {
            "buyThreshold": result.strategy_params.buy_threshold,
            "confidenceThreshold": result.strategy_params.confidence_threshold,
            "maxPosition": result.strategy_params.max_position,
            "style": result.strategy_params.style,
        },
        "portfolio": {
            "weights": result.portfolio.weights,
            "cashBuffer": result.portfolio.cash_buffer,
            "riskMetrics": result.portfolio.risk_metrics,
        },
        "execution": {
            "orders": result.execution.orders,
            "algorithm": result.execution.algorithm,
            "notes": result.execution.notes,
        },
        "backtest": backtest_metrics,
    }


# Late import for type checking to avoid circular reference at runtime
from ai_strategy_system.core.strategy_workflow import StrategyWorkflowResult  # noqa: E402  # isort: skip


# ==================== 实盘交易管理 API ====================

live_trading_router = APIRouter(prefix="/api/v1/strategy/live", tags=["live-trading"])


class ActivateStrategyRequest(BaseModel):
    """激活策略请求"""

    strategy_id: str = Field(..., alias="strategyId")
    initial_capital: float = Field(..., alias="initialCapital")
    max_position_per_stock: float = Field(0.2, alias="maxPositionPerStock")
    max_total_position: float = Field(0.8, alias="maxTotalPosition")
    max_daily_loss: float = Field(0.05, alias="maxDailyLoss")
    max_drawdown: float = Field(0.15, alias="maxDrawdown")
    stop_loss: float = Field(0.1, alias="stopLoss")
    take_profit: float = Field(0.2, alias="takeProfit")
    risk_level: str = Field("medium", alias="riskLevel")
    notification_channels: List[str] = Field(
        default_factory=lambda: ["email"], alias="notificationChannels"
    )

    class Config:
        allow_population_by_field_name = True


class StrategyStatusResponse(BaseModel):
    """策略状态响应"""

    strategy_id: str = Field(..., alias="strategyId")
    status: str
    activated_at: Optional[datetime] = Field(None, alias="activatedAt")
    last_run_at: Optional[datetime] = Field(None, alias="lastRunAt")
    current_capital: float = Field(..., alias="currentCapital")
    total_pnl: float = Field(..., alias="totalPnl")
    total_pnl_pct: float = Field(..., alias="totalPnlPct")
    active_positions: int = Field(..., alias="activePositions")
    total_trades: int = Field(..., alias="totalTrades")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat() if dt else None}


@live_trading_router.post("/activate", response_model=Dict[str, Any])
async def activate_strategy(
    request: ActivateStrategyRequest,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """激活策略到实盘运行"""
    await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.services.live_trading_manager import (
            LiveTradingConfig,
            LiveTradingManager,
        )

        manager = LiveTradingManager()

        # 创建实盘配置
        config = LiveTradingConfig(
            strategy_id=request.strategy_id,
            strategy_name=f"策略_{request.strategy_id[:8]}",
            initial_capital=request.initial_capital,
            max_position_per_stock=request.max_position_per_stock,
            max_total_position=request.max_total_position,
            max_daily_loss=request.max_daily_loss,
            max_drawdown=request.max_drawdown,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            risk_level=request.risk_level,
            notification_channels=request.notification_channels,
            trading_hours={"start": "09:30", "end": "15:00"},
        )

        # 激活策略
        success = manager.activate_strategy(request.strategy_id, config)

        if success:
            return {
                "success": True,
                "message": "策略已成功激活",
                "strategyId": request.strategy_id,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略激活失败",
            )
    except Exception as e:
        LOGGER.error(f"激活策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"激活策略时发生错误: {str(e)}",
        )


@live_trading_router.post("/{strategy_id}/pause")
async def pause_strategy(
    strategy_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """暂停策略"""
    await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.services.live_trading_manager import LiveTradingManager

        manager = LiveTradingManager()
        success = manager.pause_strategy(strategy_id)

        if success:
            return {"success": True, "message": "策略已暂停"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在或无法暂停",
            )
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"暂停策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"暂停策略时发生错误: {str(e)}",
        )


@live_trading_router.post("/{strategy_id}/resume")
async def resume_strategy(
    strategy_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """恢复策略"""
    await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.services.live_trading_manager import LiveTradingManager

        manager = LiveTradingManager()
        success = manager.resume_strategy(strategy_id)

        if success:
            return {"success": True, "message": "策略已恢复"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在或无法恢复",
            )
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"恢复策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复策略时发生错误: {str(e)}",
        )


@live_trading_router.post("/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """停止策略"""
    await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.services.live_trading_manager import LiveTradingManager

        manager = LiveTradingManager()
        success = manager.stop_strategy(strategy_id)

        if success:
            return {"success": True, "message": "策略已停止"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在或无法停止",
            )
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"停止策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止策略时发生错误: {str(e)}",
        )


@live_trading_router.get("/{strategy_id}/status", response_model=StrategyStatusResponse)
async def get_live_strategy_status(
    strategy_id: str,
    authorization: Optional[str] = Header(None),
) -> StrategyStatusResponse:
    """获取策略实盘状态"""
    await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.services.live_trading_manager import LiveTradingManager

        manager = LiveTradingManager()
        status_data = manager.get_strategy_status(strategy_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在",
            )

        return StrategyStatusResponse(
            strategyId=strategy_id,
            status=status_data.get("status", "unknown"),
            activatedAt=status_data.get("activated_at"),
            lastRunAt=status_data.get("last_run_at"),
            currentCapital=status_data.get("current_capital", 0.0),
            totalPnl=status_data.get("total_pnl", 0.0),
            totalPnlPct=status_data.get("total_pnl_pct", 0.0),
            activePositions=status_data.get("active_positions", 0),
            totalTrades=status_data.get("total_trades", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"获取策略状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略状态时发生错误: {str(e)}",
        )


@live_trading_router.get("/active", response_model=List[Dict[str, Any]])
async def list_active_strategies(
    authorization: Optional[str] = Header(None),
) -> List[Dict[str, Any]]:
    """获取所有活跃策略列表"""
    await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.services.live_trading_manager import LiveTradingManager

        manager = LiveTradingManager()
        strategies = manager.get_active_strategies()

        return strategies
    except Exception as e:
        LOGGER.error(f"获取活跃策略列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取活跃策略列表时发生错误: {str(e)}",
        )


@live_trading_router.post("/run-daily")
async def run_daily_task(
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """手动触发每日任务（生成信号、执行交易）"""
    await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.services.daily_runner import run_daily_task

        result = await run_daily_task()

        return {
            "success": True,
            "message": "每日任务执行完成",
            "result": result,
        }
    except Exception as e:
        LOGGER.error(f"执行每日任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行每日任务时发生错误: {str(e)}",
        )


# ============================================================================
# 新增API: 策略保存、回测、列表查询
# ============================================================================


class SaveStrategyRequest(BaseModel):
    """保存策略请求"""

    strategy_id: str = Field(..., alias="strategyId", description="策略ID")
    name: Optional[str] = Field(None, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    risk_params: Optional[Dict[str, Any]] = Field(
        None, alias="riskParams", description="风险控制参数"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

    class Config:
        allow_population_by_field_name = True


class BacktestRequest(BaseModel):
    """回测请求"""

    strategy_id: str = Field(..., alias="strategyId", description="策略ID")

    class Config:
        allow_population_by_field_name = True


class BacktestStatusResponse(BaseModel):
    """回测状态响应"""

    job_id: str = Field(..., alias="jobId")
    status: str
    progress: float
    message: Optional[str]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class StrategyListItem(BaseModel):
    """策略列表项"""

    strategy_id: str = Field(..., alias="strategyId")
    name: str
    description: Optional[str]
    model_type: Optional[str] = Field(None, alias="modelType")
    stock_symbols: Optional[List[str]] = Field(None, alias="stockSymbols")
    status: str
    total_return: Optional[float] = Field(None, alias="totalReturn")
    sharpe_ratio: Optional[float] = Field(None, alias="sharpeRatio")
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")

    class Config:
        allow_population_by_field_name = True


@router.post("/save", response_model=Dict[str, Any])
async def save_strategy(
    request: SaveStrategyRequest,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """保存策略到数据库

    前端点击"保存策略"按钮后调用此接口，保存策略元数据和配置
    """
    user_id = await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.utils.strategy_database import get_strategy_database

        strategy_db = get_strategy_database()

        # 检查job是否存在
        job = await job_manager.get_job(request.strategy_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略工作流不存在: {request.strategy_id}",
            )

        if job.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略尚未生成完成，当前状态: {job.status}",
            )

        # 准备策略元数据
        strategy_metadata = request.metadata or {}

        # 合并风险参数到元数据
        if request.risk_params:
            strategy_metadata["risk_params"] = request.risk_params
            LOGGER.info(f"📊 保存风险参数: {request.risk_params}")

        # 从job结果中提取策略信息
        result = job.result or {}
        model_info = result.get("model", {})
        universe_info = result.get("universe", {})
        backtest_info = result.get("backtest", {})

        # 添加回测结果到元数据
        if backtest_info:
            strategy_metadata["backtest"] = backtest_info

        # 保存到数据库
        success = strategy_db.save_strategy(
            strategy_id=request.strategy_id,
            user_id=user_id,
            name=request.name or result.get("title", f"策略_{request.strategy_id[:8]}"),
            description=request.description
            or result.get("description", "AI生成的量化交易策略"),
            model_type=model_info.get("type"),
            stock_symbols=universe_info.get("symbols", []),
            user_requirement=result.get("requirement", {}).get("text"),
            strategy_dir=None,  # 策略文件保存在工作流实例中
            status="saved",
            metadata=strategy_metadata,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="保存策略失败"
            )

        # 如果有回测结果，更新回测数据
        if backtest_info:
            strategy_db.update_backtest_result(
                strategy_id=request.strategy_id,
                backtest_id=f"bt_{request.strategy_id}",
                total_return=backtest_info.get("totalReturn", 0),
                annual_return=backtest_info.get("annualReturn", 0),
                sharpe_ratio=backtest_info.get("sharpeRatio", 0),
                max_drawdown=backtest_info.get("maxDrawdown", 0),
                win_rate=backtest_info.get("winRate", 0),
            )
            LOGGER.info("✅ 回测结果已更新到数据库")

        LOGGER.info(f"✅ 策略已保存: {request.strategy_id}, 用户: {user_id}")

        return {
            "success": True,
            "message": "策略已成功保存，可以激活到实盘交易",
            "strategyId": request.strategy_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"保存策略失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存策略时发生错误: {str(e)}",
        )


@backtest_router.post("/backtest/start", response_model=Dict[str, Any])
async def start_backtest(
    request: BacktestRequest,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """启动回测任务

    前端点击"回测"按钮后调用此接口

    当前实现：创建一个新的后台任务来执行回测
    """
    await validate_strategy_permission(authorization)

    try:
        # 从job_manager中获取对应的策略生成任务
        job = await job_manager.get_job(request.strategy_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略工作流不存在: {request.strategy_id}",
            )

        # 检查工作流是否已完成
        if job.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略尚未生成完成，当前状态: {job.status}",
            )

        # 检查是否已有回测结果
        if job.result and "backtest" in job.result and job.result.get("backtest"):
            backtest_data = job.result["backtest"]
            # 检查回测数据是否有效（非空字典）
            if (
                backtest_data
                and isinstance(backtest_data, dict)
                and len(backtest_data) > 0
            ):
                LOGGER.info(f"✅ 返回缓存的回测结果: {request.strategy_id}")
                return {
                    "success": True,
                    "message": "回测已完成",
                    "backtest": backtest_data,
                }

        # 检查是否保存了AI实例
        if not job.ai_instance:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI实例不存在，无法执行回测。请重新生成策略。",
            )

        # 创建后台任务执行回测（不等待完成）
        LOGGER.info(f"🔄 创建回测后台任务: {request.strategy_id}")

        # 定义回测进度回调
        async def backtest_progress_callback(
            current: int, total: int, message: str = ""
        ):
            """回测进度回调函数

            Args:
                current: 当前进度（已完成的交易日数）
                total: 总进度（总交易日数）
                message: 进度消息
            """
            if total > 0:
                progress = current / total
                job.progress = round(progress, 4)
                job.message = (
                    f"回测进度: {current}/{total} ({progress * 100:.1f}%) - {message}"
                )
                job.updated_at = datetime.utcnow()
                LOGGER.debug(f"📊 回测进度更新: {job.progress * 100:.1f}%")

        # 定义后台任务
        async def run_backtest_background():
            """后台执行回测任务"""
            try:
                # 更新任务状态为执行中
                job.status = "running"
                job.progress = 0.0
                job.step_name = "回测执行中"
                job.message = "正在执行策略回测..."
                job.updated_at = datetime.utcnow()

                LOGGER.info(f"📊 后台回测任务开始: {request.strategy_id}")

                # 执行回测
                success = await job.ai_instance.run_backtest(
                    progress_callback=backtest_progress_callback
                )

                if not success or not job.ai_instance.backtest_summary:
                    job.status = "failed"
                    job.progress = 0.0
                    job.error = "回测执行失败"
                    job.updated_at = datetime.utcnow()
                    LOGGER.error(f"❌ 回测执行失败: {request.strategy_id}")
                    return

                # 更新workflow_result
                if job.ai_instance.workflow_result:
                    job.ai_instance.workflow_result.backtest = (
                        job.ai_instance.backtest_summary
                    )

                # 重新序列化结果
                job.result = serialize_workflow_result(job.ai_instance.workflow_result)
                job.status = "completed"
                job.progress = 1.0
                job.step_name = "回测完成"
                job.message = "回测执行成功"
                job.updated_at = datetime.utcnow()

                LOGGER.info(f"✅ 回测完成: {request.strategy_id}")

            except Exception as e:
                job.status = "failed"
                job.progress = 0.0
                job.error = f"回测执行异常: {str(e)}"
                job.updated_at = datetime.utcnow()
                LOGGER.error(f"❌ 回测执行异常: {e}", exc_info=True)

        # 创建后台任务（异步执行，不等待）
        task = asyncio.create_task(run_backtest_background())

        # 将任务保存到job中，以便可以跟踪
        job.backtest_task = task

        # 立即返回，让前端开始轮询
        LOGGER.info(f"✅ 回测任务已创建: {request.strategy_id}")

        return {
            "success": True,
            "message": "回测任务已启动",
            "data": {
                "strategy_id": request.strategy_id,
                "status": "running",
                "progress": 0.0,
                "message": "正在初始化回测...",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"启动回测失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动回测时发生错误: {str(e)}",
        )


@backtest_router.get("/backtest/{strategy_id}/status", response_model=Dict[str, Any])
async def get_backtest_status(
    strategy_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """获取回测任务状态

    前端轮询此接口来获取回测进度和结果
    """
    await validate_strategy_permission(authorization)

    try:
        # 从job_manager中获取对应的策略生成任务
        job = await job_manager.get_job(strategy_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略工作流不存在: {strategy_id}",
            )

        # 返回当前状态
        return {
            "success": True,
            "status": job.status,
            "progress": round(job.progress, 4),
            "message": job.message,
            "backtest": job.result.get("backtest") if job.result else None,
            "error": job.error,
        }

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"获取回测状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取回测状态时发生错误: {str(e)}",
        )


async def _run_backtest_task(
    backtest_job_id: str, strategy_job_id: str, strategy_job: StrategyJob
):
    """后台执行回测任务

    Args:
        backtest_job_id: 回测任务ID
        strategy_job_id: 原策略生成任务ID
        strategy_job: 原策略生成任务对象
    """
    try:
        LOGGER.info(f"🔄 开始执行回测任务: {backtest_job_id}")

        # 从原任务结果中提取必要信息，重新创建AI实例并执行回测
        # 注意：由于IntelligentStrategyAI实例在原任务完成后就销毁了，
        # 这里需要从结果中恢复状态或重新加载策略

        # 简化实现：直接告诉用户当前无法单独执行回测
        LOGGER.warning("回测功能当前需要在策略生成时一并执行")

        # TODO: 实现真正的独立回测功能
        # 需要：
        # 1. 从strategy_job.result中提取策略参数
        # 2. 重新加载特征数据、模型等
        # 3. 调用IntelligentStrategyAI.run_backtest()
        # 4. 更新strategy_job.result中的backtest字段

    except Exception as e:
        LOGGER.error(f"回测任务执行失败: {e}", exc_info=True)


@router.get("/list", response_model=List[StrategyListItem])
async def list_strategies(
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    authorization: Optional[str] = Header(None),
) -> List[StrategyListItem]:
    """获取策略列表

    供前端"策略库"页面使用

    Args:
        status_filter: 状态过滤 (draft, saved, activated)
        limit: 返回数量限制
        offset: 偏移量
    """
    user_id = await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.utils.strategy_database import get_strategy_database

        strategy_db = get_strategy_database()
        strategies = strategy_db.list_strategies(
            user_id=user_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        # 转换为响应模型
        result = []
        for s in strategies:
            result.append(
                StrategyListItem(
                    strategyId=s["strategy_id"],
                    name=s["name"],
                    description=s.get("description"),
                    modelType=s.get("model_type"),
                    stockSymbols=s.get("stock_symbols"),
                    status=s["status"],
                    totalReturn=s.get("total_return"),
                    sharpeRatio=s.get("sharpe_ratio"),
                    createdAt=s["created_at"],
                    updatedAt=s["updated_at"],
                )
            )

        return result

    except Exception as e:
        LOGGER.error(f"获取策略列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表时发生错误: {str(e)}",
        )


@router.get("/{strategy_id}", response_model=Dict[str, Any])
async def get_strategy_detail(
    strategy_id: str,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """获取策略详情

    Args:
        strategy_id: 策略ID
    """
    user_id = await validate_strategy_permission(authorization)

    try:
        from ai_strategy_system.utils.strategy_database import get_strategy_database

        strategy_db = get_strategy_database()
        strategy = strategy_db.get_strategy(strategy_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略不存在: {strategy_id}",
            )

        # 检查权限
        if strategy["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此策略"
            )

        return strategy

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"获取策略详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略详情时发生错误: {str(e)}",
        )
