"""
智能体核心类
整合所有模块，实现完整的智能体系统
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from agent_system.core.event_bus import EventBus, Event, EventType
from agent_system.modules.perception import PerceptionModule
from agent_system.modules.memory import MemoryModule
from agent_system.modules.emotion import EmotionModule
from agent_system.modules.goal import GoalModule
from agent_system.modules.cognition import CognitionModule
from agent_system.modules.behavior import BehaviorModule
from agent_system.tools.base_tools import (
    SendMessageTool, UpdateGoalTool, InteractEnvironmentTool, RetrieveMemoryTool
)


class Agent:
    """
    智能体核心类
    整合感知、记忆、情感、目标、认知、行为六大模块
    """

    def __init__(
        self,
        agent_id: str,
        name: str = "",
        config: Optional[Dict[str, Any]] = None,
        use_llm: bool = True
    ):
        """
        初始化智能体

        Args:
            agent_id: 智能体唯一ID
            name: 智能体名称
            config: 配置参数
            use_llm: 是否使用LLM
        """
        self.agent_id = agent_id
        self.name = name or agent_id
        self.config = config or {}
        self.use_llm = use_llm

        # 创建事件总线
        self._event_bus = EventBus()

        # 初始化各模块（暂不初始化，等待start调用）
        self.perception: Optional[PerceptionModule] = None
        self.memory: Optional[MemoryModule] = None
        self.emotion: Optional[EmotionModule] = None
        self.goal: Optional[GoalModule] = None
        self.cognition: Optional[CognitionModule] = None
        self.behavior: Optional[BehaviorModule] = None

        # 状态
        self._running = False
        self._initialized = False
        self._created_at = datetime.now()

        # 回调函数（用于与外部环境交互）
        self._message_callback: Optional[Callable] = None
        self._environment_callback: Optional[Callable] = None

    async def start(self) -> None:
        """启动智能体"""
        if self._running:
            return

        # 创建模块实例
        self.perception = PerceptionModule(self.agent_id, self._event_bus)
        self.memory = MemoryModule(
            self.agent_id,
            self._event_bus,
            max_memories=self.config.get("max_memories", 1000)
        )
        self.emotion = EmotionModule(self.agent_id, self._event_bus)
        self.goal = GoalModule(self.agent_id, self._event_bus)
        self.cognition = CognitionModule(
            self.agent_id,
            self._event_bus,
            decision_strategy=self.config.get("decision_strategy"),
            use_llm=self.use_llm
        )
        self.behavior = BehaviorModule(self.agent_id, self._event_bus)

        # 初始化所有模块
        await self.perception.initialize()
        await self.memory.initialize()
        await self.emotion.initialize()
        await self.goal.initialize()
        await self.cognition.initialize()
        await self.behavior.initialize()

        # 注册默认工具
        await self._register_default_tools()

        self._initialized = True
        self._running = True

    async def stop(self) -> None:
        """停止智能体"""
        self._running = False

    def is_running(self) -> bool:
        """检查智能体是否运行中"""
        return self._running

    def is_initialized(self) -> bool:
        """检查智能体是否已初始化"""
        return self._initialized

    # 对外接口

    async def receive_message(self, sender_id: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        接收来自其他智能体或用户的消息

        Args:
            sender_id: 发送者ID
            message: 消息内容
            metadata: 消息元数据

        Returns:
            响应结果
        """
        if not self._running:
            return {"error": "Agent not running"}

        # 感知消息
        perception_result = await self.perception.perceive_message(sender_id, message, metadata)

        # 检索相关记忆
        memories = await self.memory.retrieve({
            "keywords": [sender_id],
            "memory_type": "social"
        }, limit=3)

        # 做出决策
        decision_context = {
            "situation": f"Received message from {sender_id}: {message}",
            "options": [
                {"type": "send_message", "target_id": sender_id},
                {"type": "ignore"},
                {"type": "store_memory"}
            ]
        }
        decision = await self.cognition.make_decision(decision_context)

        # 执行决策
        action = decision.get("action", {})
        if action.get("type") == "send_message":
            # 这里应该生成回复内容（可以通过LLM）
            response_message = f"Response: {decision}"
            await self.behavior.execute_action({
                "tool_name": "send_message",
                "parameters": {
                    "target_id": sender_id,
                    "message": response_message
                }
            })
            return {"response": response_message}

        return {"acknowledged": True}

    async def perceive_environment(self, environment_data: Dict[str, Any]) -> None:
        """
        感知环境变化

        Args:
            environment_data: 环境数据
        """
        if not self._running:
            return

        await self.perception.perceive_environment(environment_data)

    async def add_goal(self, goal_data: Dict[str, Any]) -> str:
        """
        添加目标

        Args:
            goal_data: 目标数据

        Returns:
            目标ID
        """
        if not self._running:
            raise RuntimeError("Agent not running")

        return await self.goal.add_goal(goal_data)

    async def process_tick(self) -> None:
        """
        处理一次tick（周期性调用）
        更新所有模块
        """
        if not self._running:
            return

        # 构建通用上下文
        context = await self._build_context()

        # 更新所有模块
        await asyncio.gather(
            self.perception.update(context),
            self.memory.update(context),
            self.emotion.update(context),
            self.goal.update(context),
            self.cognition.update(context),
            self.behavior.update(context)
        )

    def get_status(self) -> Dict[str, Any]:
        """
        获取智能体状态

        Returns:
            状态信息
        """
        if not self._initialized:
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "running": False,
                "initialized": False
            }

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "running": self._running,
            "initialized": self._initialized,
            "created_at": self._created_at.isoformat(),
            "modules": {
                "perception": self.perception.get_state(),
                "memory": self.memory.get_state(),
                "emotion": self.emotion.get_state(),
                "goal": self.goal.get_state(),
                "cognition": self.cognition.get_state(),
                "behavior": self.behavior.get_state()
            }
        }

    def set_message_callback(self, callback: Callable) -> None:
        """
        设置消息回调函数

        Args:
            callback: 回调函数
        """
        self._message_callback = callback

    def set_environment_callback(self, callback: Callable) -> None:
        """
        设置环境交互回调函数

        Args:
            callback: 回调函数
        """
        self._environment_callback = callback

    def get_event_bus(self) -> EventBus:
        """获取事件总线（用于外部监听）"""
        return self._event_bus

    # 私有方法

    async def _register_default_tools(self) -> None:
        """注册默认工具"""
        # 发送消息工具
        send_message_tool = SendMessageTool(self._message_callback)
        self.behavior.register_tool("send_message", send_message_tool)

        # 更新目标工具
        update_goal_tool = UpdateGoalTool(self.goal)
        self.behavior.register_tool("update_goal", update_goal_tool)

        # 环境交互工具
        interact_env_tool = InteractEnvironmentTool(self._environment_callback)
        self.behavior.register_tool("interact_environment", interact_env_tool)

        # 检索记忆工具
        retrieve_memory_tool = RetrieveMemoryTool(self.memory)
        self.behavior.register_tool("retrieve_memory", retrieve_memory_tool)

    async def _build_context(self) -> Dict[str, Any]:
        """构建通用上下文"""
        return {
            "perception": self.perception.get_state() if self.perception else {},
            "emotion": self.emotion.get_current_emotion() if self.emotion else {},
            "goals": self.goal.get_active_goals() if self.goal else [],
            "timestamp": datetime.now().isoformat()
        }

    def __repr__(self) -> str:
        return f"Agent(id={self.agent_id}, name={self.name}, running={self._running})"
