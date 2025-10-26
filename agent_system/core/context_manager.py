"""
上下文管理器
为认知模块提供统一的完整上下文
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class ContextManager:
    """
    统一的上下文管理器
    收集并整合智能体的所有状态信息
    """

    def __init__(self, agent):
        """
        初始化上下文管理器

        Args:
            agent: 智能体实例
        """
        self.agent = agent

    async def get_full_context(self, trigger: Optional[str] = None) -> Dict[str, Any]:
        """
        获取智能体的完整上下文

        Args:
            trigger: 触发上下文获取的事件描述

        Returns:
            完整的上下文字典
        """
        context = {
            "agent_id": self.agent.agent_id,
            "agent_name": self.agent.name,
            "current_time": datetime.now().isoformat(),
            "trigger": trigger or "none",
        }

        # 1. 角色信息
        context["identity"] = await self._get_identity_context()

        # 2. 当前状态
        context["current_state"] = await self._get_current_state()

        # 3. 日程信息
        context["schedule"] = await self._get_schedule_context()

        # 4. 情感状态
        context["emotion"] = await self._get_emotion_context()

        # 5. 目标信息
        context["goals"] = await self._get_goals_context()

        # 6. 记忆信息
        context["memories"] = await self._get_memory_context()

        # 7. 感知信息
        context["perception"] = await self._get_perception_context()

        # 8. 故事上下文
        context["story"] = await self._get_story_context()

        return context

    async def _get_identity_context(self) -> Dict[str, Any]:
        """获取角色身份信息"""
        return {
            "role": self.agent.config.get("role", "agent"),
            "personality": self.agent.config.get("personality", ""),
            "expertise": self.agent.config.get("expertise", ""),
            "background": self.agent.config.get("background", "")
        }

    async def _get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "running": self.agent.is_running(),
            "created_at": self.agent._created_at.isoformat() if hasattr(self.agent, '_created_at') else None
        }

    async def _get_schedule_context(self) -> Dict[str, Any]:
        """获取日程上下文"""
        schedule_info = {
            "has_schedule": False,
            "current_activity": None,
            "today_summary": [],
            "next_activity": None
        }

        # 检查是否有story_engine
        if hasattr(self.agent, 'story_engine') and self.agent.story_engine:
            schedule = self.agent.story_engine.get_agent_schedule(self.agent.agent_id)
            if schedule:
                schedule_info["has_schedule"] = True

                # 当前活动
                current_item = schedule.get_current_activity(datetime.now())
                if current_item:
                    schedule_info["current_activity"] = {
                        "activity": current_item.activity,
                        "description": current_item.description,
                        "time": f"{current_item.start_time}-{current_item.end_time}",
                        "location": current_item.location
                    }

                # 今日摘要
                for item in schedule.schedule_items[:10]:
                    schedule_info["today_summary"].append({
                        "time": f"{item.start_time}-{item.end_time}",
                        "activity": item.activity,
                        "status": item.status.value,
                        "completed": item.status.value == "completed"
                    })

        return schedule_info

    async def _get_emotion_context(self) -> Dict[str, Any]:
        """获取情感上下文"""
        if not self.agent.emotion:
            return {"available": False}

        emotion_state = self.agent.emotion.get_current_emotion()
        return {
            "available": True,
            "primary_emotion": emotion_state.get("primary_emotion", "neutral"),
            "valence": emotion_state.get("valence", 0),
            "arousal": emotion_state.get("arousal", 0),
            "dominance": emotion_state.get("dominance", 0)
        }

    async def _get_goals_context(self) -> Dict[str, Any]:
        """获取目标上下文"""
        if not self.agent.goal:
            return {"available": False, "goals": []}

        active_goals = self.agent.goal.get_active_goals()
        goals_list = []

        for goal in active_goals[:5]:  # 最多5个目标
            goals_list.append({
                "title": goal.get("title", "Unknown"),
                "description": goal.get("description", ""),
                "priority": goal.get("priority", "MEDIUM"),
                "progress": goal.get("progress", 0)
            })

        return {
            "available": True,
            "count": len(active_goals),
            "goals": goals_list
        }

    async def _get_memory_context(self) -> Dict[str, Any]:
        """获取记忆上下文"""
        if not self.agent.memory:
            return {"available": False, "memories": []}

        # 获取最近的事件记忆
        memories = await self.agent.memory.retrieve(
            {"memory_type": "event"},
            limit=10
        )

        memories_list = []
        for mem in memories:
            content = mem.get("content", {})
            memories_list.append({
                "summary": content.get("event_summary", ""),
                "details": content.get("event_details", ""),
                "timestamp": content.get("timestamp", "")
            })

        return {
            "available": True,
            "count": len(memories),
            "recent": memories_list
        }

    async def _get_perception_context(self) -> Dict[str, Any]:
        """获取感知上下文"""
        if not self.agent.perception:
            return {"available": False}

        # 获取最近的感知
        recent_perceptions = self.agent.perception.get_recent_perceptions(limit=5)

        return {
            "available": True,
            "recent_count": len(recent_perceptions),
            "recent": recent_perceptions
        }

    async def _get_story_context(self) -> Dict[str, Any]:
        """获取故事上下文"""
        story_info = {
            "has_story": False,
            "title": None,
            "theme": None,
            "role": None,
            "goal": None
        }

        if hasattr(self.agent, 'story_engine') and self.agent.story_engine:
            outline = self.agent.story_engine.get_story_outline()
            if outline:
                story_info["has_story"] = True
                story_info["title"] = outline.title
                story_info["theme"] = outline.theme
                story_info["role"] = outline.character_roles.get(self.agent.agent_id, "")
                story_info["goal"] = outline.character_goals.get(self.agent.agent_id, "")

        return story_info

    def format_context_for_llm(self, context: Dict[str, Any], purpose: str = "general") -> str:
        """
        将上下文格式化为LLM友好的文本

        Args:
            context: 上下文字典
            purpose: 目的（chat, decision, reflection等）

        Returns:
            格式化的文本
        """
        lines = []

        # 基本信息
        lines.append(f"# {context['agent_name']} ({context['agent_id']})")
        lines.append(f"时间: {context['current_time']}")
        lines.append("")

        # 身份信息
        identity = context.get("identity", {})
        if identity.get("role"):
            lines.append(f"## 身份")
            lines.append(f"角色: {identity['role']}")
            if identity.get("personality"):
                lines.append(f"性格: {identity['personality']}")
            if identity.get("expertise"):
                lines.append(f"专长: {identity['expertise']}")
            lines.append("")

        # 故事角色
        story = context.get("story", {})
        if story.get("has_story"):
            lines.append(f"## 故事角色")
            lines.append(f"故事: {story['title']}")
            lines.append(f"我的角色: {story['role']}")
            lines.append(f"我的目标: {story['goal']}")
            lines.append("")

        # 当前活动
        schedule = context.get("schedule", {})
        if schedule.get("current_activity"):
            activity = schedule["current_activity"]
            lines.append(f"## 当前活动")
            lines.append(f"正在做: {activity['activity']}")
            lines.append(f"详情: {activity['description']}")
            lines.append(f"时间: {activity['time']}")
            lines.append("")

        # 今日日程
        if schedule.get("today_summary"):
            lines.append(f"## 今日日程")
            for item in schedule["today_summary"][:5]:
                status = "✓" if item["completed"] else "○"
                lines.append(f"  {status} {item['time']}: {item['activity']}")
            lines.append("")

        # 情感状态
        emotion = context.get("emotion", {})
        if emotion.get("available"):
            lines.append(f"## 情感状态")
            lines.append(f"情绪: {emotion['primary_emotion']}")
            lines.append(f"效价: {emotion['valence']:.2f}, 唤醒: {emotion['arousal']:.2f}")
            lines.append("")

        # 目标
        goals = context.get("goals", {})
        if goals.get("available") and goals.get("goals"):
            lines.append(f"## 当前目标")
            for goal in goals["goals"][:3]:
                lines.append(f"  - {goal['title']} (进度: {goal['progress']*100:.0f}%)")
            lines.append("")

        # 记忆
        memories = context.get("memories", {})
        if memories.get("available") and memories.get("recent"):
            lines.append(f"## 最近记忆")
            for mem in memories["recent"][:5]:
                if mem.get("summary"):
                    lines.append(f"  - {mem['summary']}")
            lines.append("")

        return "\n".join(lines)
