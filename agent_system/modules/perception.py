"""
感知模块 - 处理环境输入和感知信息
负责收集和处理来自环境的所有信息
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from agent_system.core.base import PerceptionInterface
from agent_system.core.event_bus import EventBus, EventType


class PerceptionModule(PerceptionInterface):
    """
    感知模块实现
    处理环境刺激、其他智能体消息等所有外部输入
    """

    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, event_bus)
        # 感知缓冲区
        self._perception_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = 100
        # 当前感知状态
        self._current_perception: Dict[str, Any] = {}
        # 感知过滤器（可选）
        self._filters: List = []

    async def initialize(self) -> None:
        """初始化感知模块"""
        self._initialized = True
        self._current_perception = {
            "timestamp": datetime.now(),
            "environment": {},
            "messages": [],
            "events": []
        }
        # 订阅环境变化事件
        self.subscribe_event(EventType.ENVIRONMENT_CHANGED, self._on_environment_changed)

    async def update(self, context: Dict[str, Any]) -> None:
        """
        更新感知状态

        Args:
            context: 上下文信息
        """
        self._mark_updated()
        # 可以在这里实现感知的周期性更新逻辑

    def get_state(self) -> Dict[str, Any]:
        """获取当前感知状态"""
        return {
            "current_perception": self._current_perception,
            "buffer_size": len(self._perception_buffer),
            "last_update": self._last_update.isoformat()
        }

    async def perceive(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理外部刺激

        Args:
            stimulus: 外部刺激数据
                - type: 刺激类型（message/environment/event）
                - content: 刺激内容
                - source: 来源
                - metadata: 元数据

        Returns:
            处理后的感知结果
        """
        # 应用过滤器
        if not self._should_perceive(stimulus):
            return {"filtered": True, "reason": "stimulus filtered out"}

        # 处理不同类型的刺激
        stimulus_type = stimulus.get("type", "unknown")
        perception_result = {
            "timestamp": datetime.now(),
            "type": stimulus_type,
            "content": stimulus.get("content"),
            "source": stimulus.get("source"),
            "processed": True
        }

        # 添加到感知缓冲区
        self._add_to_buffer(perception_result)

        # 更新当前感知
        self._update_current_perception(stimulus_type, perception_result)

        # 发送感知更新事件
        await self.emit_event(
            EventType.PERCEPTION_UPDATED,
            {
                "stimulus_type": stimulus_type,
                "perception": perception_result
            }
        )

        return perception_result

    async def perceive_message(self, sender_id: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        感知来自其他智能体的消息

        Args:
            sender_id: 发送者ID
            message: 消息内容
            metadata: 消息元数据

        Returns:
            感知结果
        """
        stimulus = {
            "type": "message",
            "content": message,
            "source": sender_id,
            "metadata": metadata or {}
        }
        return await self.perceive(stimulus)

    async def perceive_environment(self, environment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        感知环境变化

        Args:
            environment_data: 环境数据

        Returns:
            感知结果
        """
        stimulus = {
            "type": "environment",
            "content": environment_data,
            "source": "environment",
            "metadata": {}
        }
        return await self.perceive(stimulus)

    async def perceive_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        感知特定事件

        Args:
            event_type: 事件类型
            event_data: 事件数据

        Returns:
            感知结果
        """
        stimulus = {
            "type": "event",
            "content": {
                "event_type": event_type,
                "data": event_data
            },
            "source": "system",
            "metadata": {}
        }
        return await self.perceive(stimulus)

    def get_recent_perceptions(self, limit: int = 10, perception_type: str = None) -> List[Dict[str, Any]]:
        """
        获取最近的感知

        Args:
            limit: 返回数量
            perception_type: 感知类型过滤

        Returns:
            感知列表
        """
        if perception_type:
            filtered = [p for p in self._perception_buffer if p.get("type") == perception_type]
            return filtered[-limit:]
        return self._perception_buffer[-limit:]

    def add_filter(self, filter_func) -> None:
        """
        添加感知过滤器

        Args:
            filter_func: 过滤函数，接收stimulus，返回bool
        """
        self._filters.append(filter_func)

    def clear_filters(self) -> None:
        """清空所有过滤器"""
        self._filters.clear()

    # 私有方法

    def _should_perceive(self, stimulus: Dict[str, Any]) -> bool:
        """
        判断是否应该感知该刺激

        Args:
            stimulus: 刺激数据

        Returns:
            是否应该感知
        """
        # 应用所有过滤器
        for filter_func in self._filters:
            if not filter_func(stimulus):
                return False
        return True

    def _add_to_buffer(self, perception: Dict[str, Any]) -> None:
        """
        添加到感知缓冲区

        Args:
            perception: 感知数据
        """
        self._perception_buffer.append(perception)
        # 限制缓冲区大小
        if len(self._perception_buffer) > self._max_buffer_size:
            self._perception_buffer.pop(0)

    def _update_current_perception(self, perception_type: str, perception: Dict[str, Any]) -> None:
        """
        更新当前感知状态

        Args:
            perception_type: 感知类型
            perception: 感知数据
        """
        if perception_type == "message":
            if "messages" not in self._current_perception:
                self._current_perception["messages"] = []
            self._current_perception["messages"].append(perception)
            # 保留最近的消息
            self._current_perception["messages"] = self._current_perception["messages"][-10:]

        elif perception_type == "environment":
            self._current_perception["environment"] = perception.get("content", {})

        elif perception_type == "event":
            if "events" not in self._current_perception:
                self._current_perception["events"] = []
            self._current_perception["events"].append(perception)
            # 保留最近的事件
            self._current_perception["events"] = self._current_perception["events"][-10:]

        self._current_perception["timestamp"] = datetime.now()

    async def _on_environment_changed(self, event) -> None:
        """
        环境变化事件处理器

        Args:
            event: 事件对象
        """
        # 自动感知环境变化
        if event.source != self.__class__.__name__:  # 避免循环
            await self.perceive_environment(event.data.get("environment", {}))
