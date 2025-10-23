"""
记忆相关数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    EVENT = "event"  # 事件记忆
    SOCIAL = "social"  # 社交记忆


class EventMemory(BaseModel):
    """事件记忆模型"""
    memory_id: str = Field(description="记忆唯一ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    location: Optional[str] = Field(None, description="地点")
    participants: List[str] = Field(default_factory=list, description="参与者列表")
    event_summary: str = Field(description="事件概括")
    event_details: str = Field(description="事件详细描述")
    emotion_valence: float = Field(0.0, ge=-1.0, le=1.0, description="情绪效价（-1到1）")
    emotion_arousal: float = Field(0.0, ge=0.0, le=1.0, description="情绪唤醒度（0到1）")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="重要性（0到1）")
    tags: List[str] = Field(default_factory=list, description="标签")
    related_goals: List[str] = Field(default_factory=list, description="相关目标ID")

    class Config:
        json_schema_extra = {
            "example": {
                "memory_id": "mem_001",
                "location": "咖啡馆",
                "participants": ["Alice", "Bob"],
                "event_summary": "与朋友讨论项目",
                "event_details": "今天和Alice、Bob在咖啡馆讨论了新项目的具体实施方案",
                "emotion_valence": 0.7,
                "emotion_arousal": 0.6,
                "importance": 0.8,
                "tags": ["工作", "朋友", "讨论"]
            }
        }


class SocialMemory(BaseModel):
    """社交记忆模型"""
    memory_id: str = Field(description="记忆唯一ID")
    target_agent_id: str = Field(description="目标智能体ID")
    target_name: str = Field(description="目标智能体名称")
    relationship_type: str = Field(default="acquaintance", description="关系类型（朋友/同事/陌生人等）")
    relationship_strength: float = Field(0.5, ge=0.0, le=1.0, description="关系强度（0到1）")
    trust_level: float = Field(0.5, ge=0.0, le=1.0, description="信任程度（0到1）")
    impression: str = Field(default="", description="总体印象")
    interaction_count: int = Field(0, description="交互次数")
    last_interaction: Optional[datetime] = Field(None, description="最后交互时间")
    shared_experiences: List[str] = Field(default_factory=list, description="共同经历的事件ID列表")
    notes: str = Field(default="", description="备注")

    class Config:
        json_schema_extra = {
            "example": {
                "memory_id": "social_001",
                "target_agent_id": "agent_alice",
                "target_name": "Alice",
                "relationship_type": "朋友",
                "relationship_strength": 0.8,
                "trust_level": 0.9,
                "impression": "可靠、聪明、幽默",
                "interaction_count": 25,
                "shared_experiences": ["mem_001", "mem_015"]
            }
        }


class MemoryQuery(BaseModel):
    """记忆查询模型"""
    memory_type: Optional[MemoryType] = Field(None, description="记忆类型")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    participants: List[str] = Field(default_factory=list, description="参与者")
    time_range: Optional[tuple] = Field(None, description="时间范围")
    min_importance: Optional[float] = Field(None, description="最小重要性")
    tags: List[str] = Field(default_factory=list, description="标签")
    limit: int = Field(5, description="返回数量限制")
