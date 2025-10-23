"""
事件总线 - 使用观察者模式实现模块间通信
支持异步事件处理，适合高并发场景
"""

import asyncio
from typing import Callable, Dict, List, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class EventType(Enum):
    """事件类型枚举"""
    # 感知相关事件
    PERCEPTION_UPDATED = "perception_updated"
    ENVIRONMENT_CHANGED = "environment_changed"

    # 记忆相关事件
    MEMORY_CREATED = "memory_created"
    MEMORY_RETRIEVED = "memory_retrieved"

    # 情感相关事件
    EMOTION_CHANGED = "emotion_changed"
    MOOD_SHIFTED = "mood_shifted"

    # 目标相关事件
    GOAL_CREATED = "goal_created"
    GOAL_UPDATED = "goal_updated"
    GOAL_COMPLETED = "goal_completed"

    # 认知相关事件
    DECISION_MADE = "decision_made"
    REFLECTION_COMPLETED = "reflection_completed"

    # 行为相关事件
    ACTION_EXECUTED = "action_executed"
    ACTION_FAILED = "action_failed"

    # 定时触发事件
    PERIODIC_TRIGGER = "periodic_trigger"


@dataclass
class Event:
    """事件数据结构"""
    event_type: EventType
    source: str  # 事件来源模块
    data: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """
    事件总线 - 实现观察者模式
    支持异步事件发布和订阅
    """

    def __init__(self):
        # 存储订阅者: {EventType: [callbacks]}
        self._subscribers: Dict[EventType, List[Callable]] = {}
        # 事件历史（可选，用于调试）
        self._event_history: List[Event] = []
        self._max_history = 1000

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            callback: 回调函数（支持异步函数）
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    async def publish(self, event: Event) -> None:
        """
        发布事件（异步）

        Args:
            event: 事件对象
        """
        # 记录事件历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # 通知所有订阅者
        if event.event_type in self._subscribers:
            tasks = []
            for callback in self._subscribers[event.event_type]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    # 同步函数包装成异步
                    tasks.append(asyncio.to_thread(callback, event))

            # 并发执行所有回调
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    def publish_sync(self, event: Event) -> None:
        """
        同步发布事件（用于非异步上下文）

        Args:
            event: 事件对象
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，创建任务
                asyncio.create_task(self.publish(event))
            else:
                # 如果没有运行的循环，直接运行
                loop.run_until_complete(self.publish(event))
        except RuntimeError:
            # 没有事件循环，创建新的
            asyncio.run(self.publish(event))

    def get_event_history(self, event_type: EventType = None, limit: int = 10) -> List[Event]:
        """
        获取事件历史

        Args:
            event_type: 事件类型（None表示所有类型）
            limit: 返回数量限制

        Returns:
            事件列表
        """
        if event_type is None:
            return self._event_history[-limit:]

        filtered = [e for e in self._event_history if e.event_type == event_type]
        return filtered[-limit:]

    def clear_history(self) -> None:
        """清空事件历史"""
        self._event_history.clear()
