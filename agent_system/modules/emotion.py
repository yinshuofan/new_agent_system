"""
情感模块 - 管理智能体的情感状态
被动更新模块，响应目标进展、环境变化和记忆事件
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent_system.core.base import EmotionInterface
from agent_system.core.event_bus import EventBus, EventType
from agent_system.models.emotion_models import (
    EmotionState, MoodState, BasicEmotion, EmotionDimension
)


class EmotionModule(EmotionInterface):
    """
    情感模块实现
    管理情感状态和心境，响应各种触发因素
    """

    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, event_bus)
        # 当前情感状态
        self._current_emotion: EmotionState = EmotionState()
        # 心境状态（长期情感倾向）
        self._mood: MoodState = MoodState()
        # 情感历史
        self._emotion_history: List[EmotionState] = []
        self._max_history = 50
        # 情感衰减配置
        self._emotion_decay_rate = 0.05  # 情感强度衰减率
        self._mood_update_rate = 0.1  # 心境更新速率

    async def initialize(self) -> None:
        """初始化情感模块"""
        self._initialized = True

        # 订阅触发情感变化的事件
        self.subscribe_event(EventType.GOAL_COMPLETED, self._on_goal_completed)
        self.subscribe_event(EventType.GOAL_UPDATED, self._on_goal_updated)
        self.subscribe_event(EventType.PERCEPTION_UPDATED, self._on_perception_updated)
        self.subscribe_event(EventType.MEMORY_CREATED, self._on_memory_created)
        self.subscribe_event(EventType.ENVIRONMENT_CHANGED, self._on_environment_changed)
        self.subscribe_event(EventType.ACTION_FAILED, self._on_action_failed)

    async def update(self, context: Dict[str, Any]) -> None:
        """
        更新情感模块（周期性调用）

        Args:
            context: 上下文信息
        """
        self._mark_updated()

        # 情感自然衰减（向中性情感回归）
        await self._decay_emotion()

        # 更新心境
        self._mood.update_from_emotion(self._current_emotion, self._mood_update_rate)

    def get_state(self) -> Dict[str, Any]:
        """获取情感模块状态"""
        return {
            "current_emotion": self._current_emotion.to_dict(),
            "mood": {
                "overall_mood": self._mood.overall_mood,
                "stability": self._mood.stability,
                "energy_level": self._mood.energy_level,
                "last_updated": self._mood.last_updated.isoformat()
            },
            "emotion_history_count": len(self._emotion_history),
            "last_update": self._last_update.isoformat()
        }

    async def process_emotion(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理情感触发因素

        Args:
            trigger: 触发因素
                - type: 触发类型
                - valence: 效价变化（-1到1）
                - arousal: 唤醒度变化（0到1）
                - intensity: 强度（0到1）
                - description: 描述

        Returns:
            新的情感状态
        """
        trigger_type = trigger.get("type", "unknown")
        valence_change = trigger.get("valence", 0.0)
        arousal_change = trigger.get("arousal", 0.0)
        intensity = trigger.get("intensity", 0.5)
        description = trigger.get("description", "")

        # 更新情感维度
        new_valence = self._blend_value(
            self._current_emotion.valence,
            valence_change,
            intensity
        )
        new_arousal = self._blend_value(
            self._current_emotion.arousal,
            arousal_change,
            intensity
        )

        # 根据维度推断基本情感
        primary_emotion = self._infer_basic_emotion(new_valence, new_arousal)

        # 创建新的情感状态
        new_emotion = EmotionState(
            valence=new_valence,
            arousal=new_arousal,
            dominance=self._current_emotion.dominance,  # 支配度相对稳定
            primary_emotion=primary_emotion,
            emotion_intensity=intensity,
            trigger_source=trigger_type,
            trigger_description=description
        )

        # 更新当前情感
        self._current_emotion = new_emotion

        # 记录历史
        self._emotion_history.append(new_emotion)
        if len(self._emotion_history) > self._max_history:
            self._emotion_history.pop(0)

        # 发送情感变化事件
        await self.emit_event(
            EventType.EMOTION_CHANGED,
            {
                "emotion": new_emotion.to_dict(),
                "trigger_type": trigger_type
            }
        )

        return new_emotion.to_dict()

    def get_current_emotion(self) -> Dict[str, Any]:
        """获取当前情感状态"""
        return self._current_emotion.to_dict()

    def get_mood(self) -> Dict[str, Any]:
        """获取心境状态"""
        return {
            "overall_mood": self._mood.overall_mood,
            "stability": self._mood.stability,
            "energy_level": self._mood.energy_level
        }

    def get_emotion_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取情感历史

        Args:
            limit: 返回数量限制

        Returns:
            情感历史列表
        """
        return [e.to_dict() for e in self._emotion_history[-limit:]]

    async def set_emotion(self, emotion: BasicEmotion, intensity: float = 0.7) -> None:
        """
        直接设置情感状态

        Args:
            emotion: 基本情感类型
            intensity: 强度
        """
        new_emotion = EmotionState.from_basic_emotion(emotion, intensity)
        self._current_emotion = new_emotion

        await self.emit_event(
            EventType.EMOTION_CHANGED,
            {
                "emotion": new_emotion.to_dict(),
                "trigger_type": "manual_set"
            }
        )

    # 私有方法

    def _blend_value(self, current: float, change: float, intensity: float) -> float:
        """
        混合当前值和变化值

        Args:
            current: 当前值
            change: 变化值
            intensity: 混合强度

        Returns:
            新值
        """
        # 使用加权平均
        new_value = current * (1 - intensity) + change * intensity
        # 限制在合理范围内
        return max(-1.0, min(1.0, new_value))

    def _infer_basic_emotion(self, valence: float, arousal: float) -> BasicEmotion:
        """
        根据维度推断基本情感

        Args:
            valence: 效价
            arousal: 唤醒度

        Returns:
            基本情感类型
        """
        # 基于二维情感空间映射
        if abs(valence) < 0.2 and arousal < 0.4:
            return BasicEmotion.NEUTRAL

        if valence > 0.3:
            if arousal > 0.6:
                return BasicEmotion.JOY
            else:
                return BasicEmotion.JOY  # 平静的快乐

        elif valence < -0.3:
            if arousal > 0.6:
                if arousal > 0.8:
                    return BasicEmotion.FEAR  # 高唤醒负面
                else:
                    return BasicEmotion.ANGER  # 中高唤醒负面
            else:
                return BasicEmotion.SADNESS  # 低唤醒负面

        else:
            if arousal > 0.7:
                return BasicEmotion.SURPRISE
            else:
                return BasicEmotion.NEUTRAL

    async def _decay_emotion(self) -> None:
        """情感自然衰减（向中性回归）"""
        # 效价向0衰减
        if abs(self._current_emotion.valence) > 0.1:
            self._current_emotion.valence *= (1 - self._emotion_decay_rate)

        # 唤醒度向基线（0.3）衰减
        baseline_arousal = 0.3
        if abs(self._current_emotion.arousal - baseline_arousal) > 0.1:
            diff = self._current_emotion.arousal - baseline_arousal
            self._current_emotion.arousal -= diff * self._emotion_decay_rate

        # 强度衰减
        if self._current_emotion.emotion_intensity > 0.1:
            self._current_emotion.emotion_intensity *= (1 - self._emotion_decay_rate)

        # 更新基本情感
        self._current_emotion.primary_emotion = self._infer_basic_emotion(
            self._current_emotion.valence,
            self._current_emotion.arousal
        )

    # 事件处理器

    async def _on_goal_completed(self, event) -> None:
        """目标完成事件处理"""
        await self.process_emotion({
            "type": "goal_completed",
            "valence": 0.7,
            "arousal": 0.6,
            "intensity": 0.8,
            "description": f"目标达成: {event.data.get('goal_id', '')}"
        })

    async def _on_goal_updated(self, event) -> None:
        """目标更新事件处理"""
        progress = event.data.get("progress", 0)
        if progress > 0.5:
            # 进展良好，正面情感
            await self.process_emotion({
                "type": "goal_progress",
                "valence": 0.3,
                "arousal": 0.4,
                "intensity": 0.4,
                "description": "目标进展顺利"
            })

    async def _on_perception_updated(self, event) -> None:
        """感知更新事件处理"""
        # 根据感知内容触发情感
        perception = event.data.get("perception", {})
        content = perception.get("content", {})

        # 检查事件类型
        event_type = content.get("event_type", "")

        # 用户消息 - 正面交互
        if event_type == "user_message":
            await self.process_emotion({
                "type": "social_interaction",
                "valence": 0.3,  # 轻微正面
                "arousal": 0.4,
                "intensity": 0.3,
                "description": "与用户交流"
            })

        # 其他感知类型
        stimulus_type = perception.get("type", "")
        if stimulus_type == "message":
            # 消息类感知，小幅正面情感
            await self.process_emotion({
                "type": "communication",
                "valence": 0.2,
                "arousal": 0.3,
                "intensity": 0.2,
                "description": "收到消息"
            })
        elif stimulus_type == "environment":
            # 环境感知，根据内容判断
            description = content.get("description", "")
            if "危险" in description or "danger" in description.lower():
                await self.process_emotion({
                    "type": "environment_threat",
                    "valence": -0.6,
                    "arousal": 0.8,
                    "intensity": 0.7,
                    "description": "感知到威胁"
                })

    async def _on_environment_changed(self, event) -> None:
        """环境变化事件处理"""
        # 环境变化可能影响情感
        change_type = event.data.get("change_type", "")
        environment_data = event.data.get("environment_data", {})

        if change_type == "danger":
            await self.process_emotion({
                "type": "environment_danger",
                "valence": -0.6,
                "arousal": 0.8,
                "intensity": 0.7,
                "description": "环境出现危险"
            })
        elif change_type == "positive":
            await self.process_emotion({
                "type": "environment_positive",
                "valence": 0.5,
                "arousal": 0.4,
                "intensity": 0.5,
                "description": "环境改善"
            })
        else:
            # 默认中性环境变化，小幅情感波动
            await self.process_emotion({
                "type": "environment_change",
                "valence": 0.1,
                "arousal": 0.2,
                "intensity": 0.1,
                "description": "环境变化"
            })

    async def _on_action_failed(self, event) -> None:
        """行为失败事件处理"""
        await self.process_emotion({
            "type": "action_failed",
            "valence": -0.5,
            "arousal": 0.5,
            "intensity": 0.6,
            "description": f"行为执行失败: {event.data.get('action', '')}"
        })

    async def _on_memory_created(self, event) -> None:
        """记忆创建事件处理"""
        # 可以根据记忆的重要性触发情感
        # 目前作为占位符，未来可以实现
        pass
