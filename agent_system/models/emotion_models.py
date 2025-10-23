"""
情感状态数据模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime
from enum import Enum


class EmotionDimension(Enum):
    """情感维度（基于情感心理学的多维度模型）"""
    VALENCE = "valence"  # 效价（愉快-不愉快）
    AROUSAL = "arousal"  # 唤醒度（激动-平静）
    DOMINANCE = "dominance"  # 支配度（控制-被控制）


class BasicEmotion(Enum):
    """基本情感类型（基于Ekman的基本情感理论）"""
    JOY = "joy"  # 快乐
    SADNESS = "sadness"  # 悲伤
    ANGER = "anger"  # 愤怒
    FEAR = "fear"  # 恐惧
    SURPRISE = "surprise"  # 惊讶
    DISGUST = "disgust"  # 厌恶
    NEUTRAL = "neutral"  # 中性


class EmotionState(BaseModel):
    """
    情感状态模型
    使用维度模型和离散情感混合表示
    """
    # 维度表示（连续值）
    valence: float = Field(0.0, ge=-1.0, le=1.0, description="效价（-1不愉快到1愉快）")
    arousal: float = Field(0.0, ge=0.0, le=1.0, description="唤醒度（0平静到1激动）")
    dominance: float = Field(0.5, ge=0.0, le=1.0, description="支配度（0被控制到1控制）")

    # 离散情感（带强度）
    primary_emotion: BasicEmotion = Field(BasicEmotion.NEUTRAL, description="主要情感")
    emotion_intensity: float = Field(0.0, ge=0.0, le=1.0, description="情感强度")

    # 元数据
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    trigger_source: Optional[str] = Field(None, description="触发来源")
    trigger_description: Optional[str] = Field(None, description="触发描述")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "primary_emotion": self.primary_emotion.value,
            "emotion_intensity": self.emotion_intensity,
            "timestamp": self.timestamp.isoformat(),
            "trigger_source": self.trigger_source,
            "trigger_description": self.trigger_description
        }

    @classmethod
    def from_basic_emotion(cls, emotion: BasicEmotion, intensity: float = 0.7):
        """
        从基本情感创建情感状态

        Args:
            emotion: 基本情感类型
            intensity: 强度

        Returns:
            EmotionState实例
        """
        # 预定义的基本情感到维度的映射
        emotion_mapping = {
            BasicEmotion.JOY: {"valence": 0.8, "arousal": 0.6, "dominance": 0.7},
            BasicEmotion.SADNESS: {"valence": -0.7, "arousal": 0.3, "dominance": 0.3},
            BasicEmotion.ANGER: {"valence": -0.6, "arousal": 0.8, "dominance": 0.7},
            BasicEmotion.FEAR: {"valence": -0.8, "arousal": 0.7, "dominance": 0.2},
            BasicEmotion.SURPRISE: {"valence": 0.0, "arousal": 0.8, "dominance": 0.5},
            BasicEmotion.DISGUST: {"valence": -0.6, "arousal": 0.5, "dominance": 0.6},
            BasicEmotion.NEUTRAL: {"valence": 0.0, "arousal": 0.3, "dominance": 0.5}
        }

        dims = emotion_mapping.get(emotion, emotion_mapping[BasicEmotion.NEUTRAL])
        return cls(
            valence=dims["valence"],
            arousal=dims["arousal"],
            dominance=dims["dominance"],
            primary_emotion=emotion,
            emotion_intensity=intensity
        )

    class Config:
        json_schema_extra = {
            "example": {
                "valence": 0.7,
                "arousal": 0.6,
                "dominance": 0.7,
                "primary_emotion": "joy",
                "emotion_intensity": 0.8,
                "trigger_source": "GoalModule",
                "trigger_description": "目标达成"
            }
        }


class MoodState(BaseModel):
    """
    心境状态（长期情感倾向）
    相比情感，心境更持久且不那么强烈
    """
    overall_mood: float = Field(0.0, ge=-1.0, le=1.0, description="总体心境（-1消极到1积极）")
    stability: float = Field(0.5, ge=0.0, le=1.0, description="稳定性（0波动到1稳定）")
    energy_level: float = Field(0.5, ge=0.0, le=1.0, description="能量水平")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    def update_from_emotion(self, emotion: EmotionState, decay_rate: float = 0.1):
        """
        根据情感更新心境（使用指数衰减）

        Args:
            emotion: 情感状态
            decay_rate: 衰减率（0-1，值越大心境变化越快）
        """
        # 心境随情感缓慢变化
        self.overall_mood = (1 - decay_rate) * self.overall_mood + decay_rate * emotion.valence
        self.energy_level = (1 - decay_rate) * self.energy_level + decay_rate * emotion.arousal
        self.last_updated = datetime.now()
