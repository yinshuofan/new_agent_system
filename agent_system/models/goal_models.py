"""
目标与需求数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class GoalStatus(Enum):
    """目标状态"""
    PENDING = "pending"  # 待开始
    ACTIVE = "active"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    SUSPENDED = "suspended"  # 暂停


class GoalPriority(Enum):
    """目标优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class NeedType(Enum):
    """需求类型（基于马斯洛需求层次）"""
    PHYSIOLOGICAL = "physiological"  # 生理需求
    SAFETY = "safety"  # 安全需求
    SOCIAL = "social"  # 社交需求
    ESTEEM = "esteem"  # 尊重需求
    SELF_ACTUALIZATION = "self_actualization"  # 自我实现需求


class Goal(BaseModel):
    """目标模型"""
    goal_id: str = Field(description="目标唯一ID")
    title: str = Field(description="目标标题")
    description: str = Field(description="目标描述")
    goal_type: str = Field(default="general", description="目标类型")
    priority: GoalPriority = Field(GoalPriority.MEDIUM, description="优先级")
    status: GoalStatus = Field(GoalStatus.PENDING, description="状态")

    # 进度相关
    progress: float = Field(0.0, ge=0.0, le=1.0, description="进度（0-1）")
    sub_goals: List[str] = Field(default_factory=list, description="子目标ID列表")
    parent_goal: Optional[str] = Field(None, description="父目标ID")

    # 时间相关
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    deadline: Optional[datetime] = Field(None, description="截止时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    # 关联信息
    related_needs: List[NeedType] = Field(default_factory=list, description="关联的需求类型")
    required_resources: List[str] = Field(default_factory=list, description="所需资源")
    dependencies: List[str] = Field(default_factory=list, description="依赖的其他目标")

    # 反馈
    success_criteria: str = Field(default="", description="成功标准")
    feedback: str = Field(default="", description="反馈信息")

    def is_active(self) -> bool:
        """检查目标是否活跃"""
        return self.status == GoalStatus.ACTIVE

    def is_completed(self) -> bool:
        """检查目标是否完成"""
        return self.status == GoalStatus.COMPLETED

    def update_progress(self, new_progress: float) -> None:
        """
        更新进度

        Args:
            new_progress: 新的进度值
        """
        self.progress = max(0.0, min(1.0, new_progress))
        if self.progress >= 1.0:
            self.status = GoalStatus.COMPLETED
            self.completed_at = datetime.now()

    class Config:
        json_schema_extra = {
            "example": {
                "goal_id": "goal_001",
                "title": "完成项目报告",
                "description": "在本周五前完成项目进度报告并提交",
                "priority": "HIGH",
                "status": "ACTIVE",
                "progress": 0.6,
                "deadline": "2025-10-25T17:00:00",
                "related_needs": ["esteem", "self_actualization"],
                "success_criteria": "报告完整、数据准确、按时提交"
            }
        }


class Need(BaseModel):
    """需求模型"""
    need_type: NeedType = Field(description="需求类型")
    satisfaction_level: float = Field(0.5, ge=0.0, le=1.0, description="满足程度（0-1）")
    urgency: float = Field(0.5, ge=0.0, le=1.0, description="紧急程度（0-1）")
    last_satisfied: Optional[datetime] = Field(None, description="最后满足时间")
    decay_rate: float = Field(0.01, description="需求衰减速率")

    def decay(self, time_delta_hours: float) -> None:
        """
        需求随时间衰减

        Args:
            time_delta_hours: 时间间隔（小时）
        """
        decay_amount = self.decay_rate * time_delta_hours
        self.satisfaction_level = max(0.0, self.satisfaction_level - decay_amount)
        # 满足度降低时，紧急程度增加
        self.urgency = min(1.0, 1.0 - self.satisfaction_level)

    def satisfy(self, amount: float) -> None:
        """
        满足需求

        Args:
            amount: 满足量（0-1）
        """
        self.satisfaction_level = min(1.0, self.satisfaction_level + amount)
        self.urgency = max(0.0, 1.0 - self.satisfaction_level)
        self.last_satisfied = datetime.now()


class GoalPlan(BaseModel):
    """目标计划"""
    plan_id: str = Field(description="计划ID")
    goal_id: str = Field(description="关联的目标ID")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="执行步骤")
    current_step: int = Field(0, description="当前步骤索引")
    estimated_duration: Optional[float] = Field(None, description="预计耗时（小时）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    def next_step(self) -> Optional[Dict[str, Any]]:
        """获取下一步"""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def advance(self) -> bool:
        """前进到下一步"""
        if self.current_step < len(self.steps):
            self.current_step += 1
            return True
        return False

    def get_progress(self) -> float:
        """获取计划进度"""
        if not self.steps:
            return 0.0
        return self.current_step / len(self.steps)
