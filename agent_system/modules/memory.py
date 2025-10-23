"""
记忆模块 - 管理事件记忆和社交记忆
支持记忆的存储、检索和遗忘机制
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from agent_system.core.base import MemoryInterface
from agent_system.core.event_bus import EventBus, EventType
from agent_system.models.memory_models import (
    EventMemory, SocialMemory, MemoryType, MemoryQuery
)


class MemoryModule(MemoryInterface):
    """
    记忆模块实现
    管理事件记忆（个人经历）和社交记忆（与他人的关系）
    """

    def __init__(self, agent_id: str, event_bus: EventBus, max_memories: int = 1000):
        super().__init__(agent_id, event_bus)
        # 事件记忆存储
        self._event_memories: Dict[str, EventMemory] = {}
        # 社交记忆存储
        self._social_memories: Dict[str, SocialMemory] = {}
        # 记忆索引（用于快速检索）
        self._event_index: Dict[str, List[str]] = defaultdict(list)  # tag -> memory_ids
        self._participant_index: Dict[str, List[str]] = defaultdict(list)  # participant -> memory_ids
        self._social_index: Dict[str, str] = {}  # agent_id -> memory_id
        # 配置
        self._max_memories = max_memories
        self._forgetting_enabled = True
        self._forgetting_threshold = 0.1  # 重要性低于此值的记忆会被遗忘

    async def initialize(self) -> None:
        """初始化记忆模块"""
        self._initialized = True
        # 订阅相关事件
        self.subscribe_event(EventType.PERCEPTION_UPDATED, self._on_perception_updated)
        self.subscribe_event(EventType.ACTION_EXECUTED, self._on_action_executed)

    async def update(self, context: Dict[str, Any]) -> None:
        """
        更新记忆模块

        Args:
            context: 上下文信息
        """
        self._mark_updated()
        # 可以在这里实现记忆强化、遗忘等机制
        if self._forgetting_enabled:
            await self._process_forgetting()

    def get_state(self) -> Dict[str, Any]:
        """获取记忆模块状态"""
        return {
            "event_memories_count": len(self._event_memories),
            "social_memories_count": len(self._social_memories),
            "last_update": self._last_update.isoformat(),
            "total_capacity": self._max_memories,
            "usage_percentage": (len(self._event_memories) / self._max_memories) * 100
        }

    async def store(self, memory_type: str, content: Dict[str, Any]) -> str:
        """
        存储记忆

        Args:
            memory_type: 记忆类型（event/social）
            content: 记忆内容

        Returns:
            记忆ID
        """
        if memory_type == MemoryType.EVENT.value or memory_type == "event":
            return await self._store_event_memory(content)
        elif memory_type == MemoryType.SOCIAL.value or memory_type == "social":
            return await self._store_social_memory(content)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

    async def retrieve(self, query: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        检索记忆

        Args:
            query: 查询条件
            limit: 返回数量限制

        Returns:
            记忆列表
        """
        memory_type = query.get("memory_type")

        if memory_type == "event" or memory_type == MemoryType.EVENT.value:
            return await self._retrieve_event_memories(query, limit)
        elif memory_type == "social" or memory_type == MemoryType.SOCIAL.value:
            return await self._retrieve_social_memories(query, limit)
        else:
            # 同时检索两种类型
            event_results = await self._retrieve_event_memories(query, limit // 2)
            social_results = await self._retrieve_social_memories(query, limit // 2)
            return event_results + social_results

    async def get_event_memory(self, memory_id: str) -> Optional[EventMemory]:
        """
        获取特定事件记忆

        Args:
            memory_id: 记忆ID

        Returns:
            事件记忆对象
        """
        return self._event_memories.get(memory_id)

    async def get_social_memory(self, agent_id: str) -> Optional[SocialMemory]:
        """
        获取与特定智能体的社交记忆

        Args:
            agent_id: 目标智能体ID

        Returns:
            社交记忆对象
        """
        memory_id = self._social_index.get(agent_id)
        if memory_id:
            return self._social_memories.get(memory_id)
        return None

    async def update_social_memory(self, agent_id: str, updates: Dict[str, Any]) -> None:
        """
        更新社交记忆

        Args:
            agent_id: 目标智能体ID
            updates: 更新内容
        """
        social_memory = await self.get_social_memory(agent_id)
        if social_memory:
            # 更新现有记忆
            for key, value in updates.items():
                if hasattr(social_memory, key):
                    setattr(social_memory, key, value)
            social_memory.last_interaction = datetime.now()
        else:
            # 创建新的社交记忆
            await self._store_social_memory({
                "target_agent_id": agent_id,
                "target_name": updates.get("target_name", agent_id),
                **updates
            })

    async def record_interaction(self, agent_id: str, interaction_memory_id: str) -> None:
        """
        记录与其他智能体的交互

        Args:
            agent_id: 目标智能体ID
            interaction_memory_id: 交互事件的记忆ID
        """
        social_memory = await self.get_social_memory(agent_id)
        if social_memory:
            social_memory.interaction_count += 1
            social_memory.last_interaction = datetime.now()
            if interaction_memory_id not in social_memory.shared_experiences:
                social_memory.shared_experiences.append(interaction_memory_id)

    # 私有方法

    async def _store_event_memory(self, content: Dict[str, Any]) -> str:
        """存储事件记忆"""
        memory_id = content.get("memory_id", f"mem_{uuid.uuid4().hex[:12]}")

        # 创建事件记忆对象
        event_memory = EventMemory(
            memory_id=memory_id,
            **{k: v for k, v in content.items() if k != "memory_id"}
        )

        self._event_memories[memory_id] = event_memory

        # 更新索引
        for tag in event_memory.tags:
            self._event_index[tag].append(memory_id)
        for participant in event_memory.participants:
            self._participant_index[participant].append(memory_id)

        # 发送事件
        await self.emit_event(
            EventType.MEMORY_CREATED,
            {
                "memory_type": "event",
                "memory_id": memory_id,
                "importance": event_memory.importance
            }
        )

        # 检查容量限制
        await self._manage_capacity()

        return memory_id

    async def _store_social_memory(self, content: Dict[str, Any]) -> str:
        """存储社交记忆"""
        target_agent_id = content.get("target_agent_id")
        if not target_agent_id:
            raise ValueError("target_agent_id is required for social memory")

        memory_id = content.get("memory_id", f"social_{uuid.uuid4().hex[:12]}")

        # 创建社交记忆对象
        social_memory = SocialMemory(
            memory_id=memory_id,
            **{k: v for k, v in content.items() if k != "memory_id"}
        )

        self._social_memories[memory_id] = social_memory
        self._social_index[target_agent_id] = memory_id

        # 发送事件
        await self.emit_event(
            EventType.MEMORY_CREATED,
            {
                "memory_type": "social",
                "memory_id": memory_id,
                "target_agent_id": target_agent_id
            }
        )

        return memory_id

    async def _retrieve_event_memories(self, query: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """检索事件记忆"""
        candidates = list(self._event_memories.values())

        # 应用过滤条件
        keywords = query.get("keywords", [])
        participants = query.get("participants", [])
        tags = query.get("tags", [])
        min_importance = query.get("min_importance")

        filtered = []
        for memory in candidates:
            # 关键词匹配
            if keywords:
                text = f"{memory.event_summary} {memory.event_details}".lower()
                if not any(kw.lower() in text for kw in keywords):
                    continue

            # 参与者匹配
            if participants:
                if not any(p in memory.participants for p in participants):
                    continue

            # 标签匹配
            if tags:
                if not any(t in memory.tags for t in tags):
                    continue

            # 重要性过滤
            if min_importance is not None:
                if memory.importance < min_importance:
                    continue

            filtered.append(memory)

        # 按重要性和时间排序
        filtered.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)

        # 返回结果
        results = []
        for memory in filtered[:limit]:
            results.append(memory.model_dump())

        # 发送检索事件
        await self.emit_event(
            EventType.MEMORY_RETRIEVED,
            {
                "memory_type": "event",
                "count": len(results),
                "query": query
            }
        )

        return results

    async def _retrieve_social_memories(self, query: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """检索社交记忆"""
        candidates = list(self._social_memories.values())

        # 应用过滤条件
        target_name = query.get("target_name")
        min_relationship_strength = query.get("min_relationship_strength")

        filtered = []
        for memory in candidates:
            if target_name:
                if target_name.lower() not in memory.target_name.lower():
                    continue

            if min_relationship_strength is not None:
                if memory.relationship_strength < min_relationship_strength:
                    continue

            filtered.append(memory)

        # 按关系强度排序
        filtered.sort(key=lambda m: m.relationship_strength, reverse=True)

        # 返回结果
        results = []
        for memory in filtered[:limit]:
            results.append(memory.model_dump())

        return results

    async def _manage_capacity(self) -> None:
        """管理记忆容量，超出限制时删除不重要的记忆"""
        if len(self._event_memories) > self._max_memories:
            # 按重要性排序，删除最不重要的记忆
            sorted_memories = sorted(
                self._event_memories.items(),
                key=lambda x: x[1].importance
            )
            # 删除最低10%
            to_delete = sorted_memories[:len(sorted_memories) // 10]
            for memory_id, _ in to_delete:
                del self._event_memories[memory_id]
                # 清理索引
                self._clean_index(memory_id)

    async def _process_forgetting(self) -> None:
        """
        处理记忆遗忘
        重要性低且时间久远的记忆会被遗忘
        """
        current_time = datetime.now()
        to_forget = []

        for memory_id, memory in self._event_memories.items():
            # 计算记忆年龄（天数）
            age_days = (current_time - memory.timestamp).days

            # 遗忘概率 = (1 - importance) * age_factor
            age_factor = min(age_days / 365.0, 1.0)  # 最多1年
            forget_probability = (1 - memory.importance) * age_factor

            if forget_probability > 0.8:  # 80%概率遗忘
                to_forget.append(memory_id)

        # 删除被遗忘的记忆
        for memory_id in to_forget:
            del self._event_memories[memory_id]
            self._clean_index(memory_id)

    def _clean_index(self, memory_id: str) -> None:
        """清理索引中的记忆ID"""
        # 清理标签索引
        for tag_list in self._event_index.values():
            if memory_id in tag_list:
                tag_list.remove(memory_id)

        # 清理参与者索引
        for participant_list in self._participant_index.values():
            if memory_id in participant_list:
                participant_list.remove(memory_id)

    async def _on_perception_updated(self, event) -> None:
        """感知更新事件处理器"""
        # 可以自动创建基于感知的记忆
        pass

    async def _on_action_executed(self, event) -> None:
        """行为执行事件处理器"""
        # 可以自动记录重要行为
        pass
