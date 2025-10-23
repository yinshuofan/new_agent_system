"""
智能体管理器
支持高并发运行多个智能体实例
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict

from agent_system.core.agent import Agent
from agent_system.scheduler.trigger import AgentScheduler


class AgentManager:
    """
    智能体管理器
    在一个服务中管理多个智能体实例，支持高并发
    """

    def __init__(self, max_agents: int = 100):
        """
        初始化管理器

        Args:
            max_agents: 最大智能体数量
        """
        self._agents: Dict[str, Agent] = {}
        self._schedulers: Dict[str, AgentScheduler] = {}
        self._max_agents = max_agents
        self._created_at = datetime.now()

        # 消息路由（智能体间通信）
        self._message_router: Dict[str, List] = defaultdict(list)

        # 统计信息
        self._stats = {
            "total_agents_created": 0,
            "total_messages_routed": 0,
            "total_operations": 0
        }

    async def create_agent(
        self,
        agent_id: str,
        name: str = "",
        config: Optional[Dict[str, Any]] = None,
        start_immediately: bool = True
    ) -> Agent:
        """
        创建并注册新智能体

        Args:
            agent_id: 智能体ID
            name: 智能体名称
            config: 配置参数
            start_immediately: 是否立即启动

        Returns:
            创建的智能体实例

        Raises:
            ValueError: 如果智能体ID已存在或达到最大数量
        """
        if agent_id in self._agents:
            raise ValueError(f"Agent with id '{agent_id}' already exists")

        if len(self._agents) >= self._max_agents:
            raise ValueError(f"Maximum number of agents ({self._max_agents}) reached")

        # 创建智能体
        agent = Agent(agent_id, name, config)

        # 设置消息和环境回调
        agent.set_message_callback(self._create_message_callback(agent_id))
        agent.set_environment_callback(self._create_environment_callback(agent_id))

        # 注册智能体
        self._agents[agent_id] = agent

        # 创建调度器
        scheduler = AgentScheduler(agent)
        self._schedulers[agent_id] = scheduler

        # 启动（如果需要）
        if start_immediately:
            await agent.start()
            await scheduler.start()

        # 更新统计
        self._stats["total_agents_created"] += 1

        return agent

    async def remove_agent(self, agent_id: str) -> bool:
        """
        移除智能体

        Args:
            agent_id: 智能体ID

        Returns:
            是否成功移除
        """
        if agent_id not in self._agents:
            return False

        # 停止智能体和调度器
        agent = self._agents[agent_id]
        scheduler = self._schedulers[agent_id]

        await scheduler.stop()
        await agent.stop()

        # 移除
        del self._agents[agent_id]
        del self._schedulers[agent_id]

        # 清理消息路由
        if agent_id in self._message_router:
            del self._message_router[agent_id]

        return True

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        获取智能体实例

        Args:
            agent_id: 智能体ID

        Returns:
            智能体实例
        """
        return self._agents.get(agent_id)

    def get_all_agents(self) -> List[Agent]:
        """获取所有智能体"""
        return list(self._agents.values())

    def get_agent_count(self) -> int:
        """获取智能体数量"""
        return len(self._agents)

    async def send_message(
        self,
        sender_id: str,
        target_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送消息给指定智能体

        Args:
            sender_id: 发送者ID
            target_id: 目标智能体ID
            message: 消息内容
            metadata: 消息元数据

        Returns:
            响应结果
        """
        if target_id not in self._agents:
            return {"error": f"Target agent '{target_id}' not found"}

        target_agent = self._agents[target_id]

        # 路由消息
        self._stats["total_messages_routed"] += 1
        self._message_router[target_id].append({
            "sender": sender_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

        # 发送给目标智能体
        response = await target_agent.receive_message(sender_id, message, metadata)

        return response

    async def broadcast_message(
        self,
        sender_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        广播消息给所有智能体

        Args:
            sender_id: 发送者ID
            message: 消息内容
            metadata: 消息元数据

        Returns:
            所有响应的字典
        """
        tasks = []
        agent_ids = []

        for agent_id, agent in self._agents.items():
            if agent_id != sender_id:  # 不发送给自己
                tasks.append(agent.receive_message(sender_id, message, metadata))
                agent_ids.append(agent_id)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        results = {}
        for i, agent_id in enumerate(agent_ids):
            if isinstance(responses[i], Exception):
                results[agent_id] = {"error": str(responses[i])}
            else:
                results[agent_id] = responses[i]

        self._stats["total_messages_routed"] += len(agent_ids)

        return results

    async def broadcast_environment_update(
        self,
        environment_data: Dict[str, Any]
    ) -> None:
        """
        向所有智能体广播环境更新

        Args:
            environment_data: 环境数据
        """
        tasks = []
        for agent in self._agents.values():
            tasks.append(agent.perceive_environment(environment_data))

        await asyncio.gather(*tasks, return_exceptions=True)

    def get_status(self) -> Dict[str, Any]:
        """
        获取管理器状态

        Returns:
            状态信息
        """
        agent_statuses = {}
        for agent_id, agent in self._agents.items():
            agent_statuses[agent_id] = {
                "running": agent.is_running(),
                "name": agent.name
            }

        return {
            "created_at": self._created_at.isoformat(),
            "agent_count": len(self._agents),
            "max_agents": self._max_agents,
            "agents": agent_statuses,
            "stats": self._stats
        }

    def get_detailed_status(self) -> Dict[str, Any]:
        """
        获取详细状态（包括所有智能体的详细信息）

        Returns:
            详细状态信息
        """
        agent_details = {}
        for agent_id, agent in self._agents.items():
            agent_details[agent_id] = agent.get_status()

        return {
            "created_at": self._created_at.isoformat(),
            "agent_count": len(self._agents),
            "max_agents": self._max_agents,
            "agents": agent_details,
            "stats": self._stats
        }

    async def start_all(self) -> None:
        """启动所有智能体"""
        tasks = []
        for agent_id in self._agents:
            agent = self._agents[agent_id]
            scheduler = self._schedulers[agent_id]

            if not agent.is_running():
                tasks.append(agent.start())
                tasks.append(scheduler.start())

        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_all(self) -> None:
        """停止所有智能体"""
        tasks = []
        for agent_id in self._agents:
            agent = self._agents[agent_id]
            scheduler = self._schedulers[agent_id]

            tasks.append(scheduler.stop())
            tasks.append(agent.stop())

        await asyncio.gather(*tasks, return_exceptions=True)

    # 私有方法

    def _create_message_callback(self, agent_id: str):
        """
        创建消息回调函数

        Args:
            agent_id: 智能体ID

        Returns:
            回调函数
        """
        async def callback(target_id: str, message: str):
            return await self.send_message(agent_id, target_id, message)

        return callback

    def _create_environment_callback(self, agent_id: str):
        """
        创建环境交互回调函数

        Args:
            agent_id: 智能体ID

        Returns:
            回调函数
        """
        async def callback(action_type: str, parameters: Dict[str, Any]):
            # 这里可以实现环境交互逻辑
            # 例如：更新共享环境状态、触发其他智能体的感知等
            return {
                "agent_id": agent_id,
                "action_type": action_type,
                "result": "success"
            }

        return callback

    def __repr__(self) -> str:
        return f"AgentManager(agent_count={len(self._agents)}, max_agents={self._max_agents})"


# 单例模式（可选）
_global_manager: Optional[AgentManager] = None


def get_global_manager() -> AgentManager:
    """获取全局管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = AgentManager()
    return _global_manager


def set_global_manager(manager: AgentManager) -> None:
    """设置全局管理器实例"""
    global _global_manager
    _global_manager = manager
