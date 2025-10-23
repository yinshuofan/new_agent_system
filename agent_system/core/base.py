"""
基础模块接口和抽象类
定义所有模块的通用接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
from agent_system.core.event_bus import EventBus, Event, EventType


class BaseModule(ABC):
    """
    所有模块的基类
    提供事件总线访问和基础功能
    """

    def __init__(self, agent_id: str, event_bus: EventBus):
        """
        初始化基础模块

        Args:
            agent_id: 智能体ID
            event_bus: 事件总线实例
        """
        self.agent_id = agent_id
        self.event_bus = event_bus
        self._initialized = False
        self._last_update = datetime.now()

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化模块
        子类必须实现此方法来进行模块特定的初始化
        """
        pass

    @abstractmethod
    async def update(self, context: Dict[str, Any]) -> None:
        """
        更新模块状态

        Args:
            context: 上下文信息
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        获取模块当前状态

        Returns:
            状态字典
        """
        pass

    async def emit_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """
        发送事件到事件总线

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        event = Event(
            event_type=event_type,
            source=self.__class__.__name__,
            data=data
        )
        await self.event_bus.publish(event)

    def subscribe_event(self, event_type: EventType, callback) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self.event_bus.subscribe(event_type, callback)

    @property
    def is_initialized(self) -> bool:
        """检查模块是否已初始化"""
        return self._initialized

    @property
    def last_update_time(self) -> datetime:
        """获取最后更新时间"""
        return self._last_update

    def _mark_updated(self) -> None:
        """标记模块已更新"""
        self._last_update = datetime.now()


class PerceptionInterface(BaseModule):
    """感知模块接口"""

    @abstractmethod
    async def perceive(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理外部刺激

        Args:
            stimulus: 外部刺激数据

        Returns:
            感知结果
        """
        pass


class MemoryInterface(BaseModule):
    """记忆模块接口"""

    @abstractmethod
    async def store(self, memory_type: str, content: Dict[str, Any]) -> str:
        """
        存储记忆

        Args:
            memory_type: 记忆类型（event/social）
            content: 记忆内容

        Returns:
            记忆ID
        """
        pass

    @abstractmethod
    async def retrieve(self, query: Dict[str, Any], limit: int = 5) -> list:
        """
        检索记忆

        Args:
            query: 查询条件
            limit: 返回数量限制

        Returns:
            记忆列表
        """
        pass


class EmotionInterface(BaseModule):
    """情感模块接口"""

    @abstractmethod
    async def process_emotion(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理情感变化

        Args:
            trigger: 情感触发因素

        Returns:
            新的情感状态
        """
        pass

    @abstractmethod
    def get_current_emotion(self) -> Dict[str, Any]:
        """
        获取当前情感状态

        Returns:
            情感状态字典
        """
        pass


class GoalInterface(BaseModule):
    """目标与需求模块接口"""

    @abstractmethod
    async def add_goal(self, goal: Dict[str, Any]) -> str:
        """
        添加新目标

        Args:
            goal: 目标信息

        Returns:
            目标ID
        """
        pass

    @abstractmethod
    async def update_goal_progress(self, goal_id: str, progress: float) -> None:
        """
        更新目标进度

        Args:
            goal_id: 目标ID
            progress: 进度（0.0-1.0）
        """
        pass

    @abstractmethod
    def get_active_goals(self) -> list:
        """
        获取活跃目标

        Returns:
            目标列表
        """
        pass


class CognitionInterface(BaseModule):
    """认知模块接口"""

    @abstractmethod
    async def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        做出决策

        Args:
            context: 决策上下文

        Returns:
            决策结果
        """
        pass

    @abstractmethod
    async def reflect(self) -> Dict[str, Any]:
        """
        自我反思

        Returns:
            反思结果
        """
        pass


class BehaviorInterface(BaseModule):
    """行为模块接口"""

    @abstractmethod
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行行为

        Args:
            action: 行为描述

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def register_tool(self, tool_name: str, tool_func) -> None:
        """
        注册工具

        Args:
            tool_name: 工具名称
            tool_func: 工具函数
        """
        pass
