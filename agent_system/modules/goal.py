"""
目标与需求模块 - 管理智能体的目标和需求
支持目标创建、更新、优先级管理和需求满足
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from agent_system.core.base import GoalInterface
from agent_system.core.event_bus import EventBus, EventType
from agent_system.models.goal_models import (
    Goal, Need, GoalPlan, GoalStatus, GoalPriority, NeedType
)


class GoalModule(GoalInterface):
    """
    目标与需求模块实现
    管理目标层级、计划执行和需求满足
    """

    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, event_bus)
        # 目标存储
        self._goals: Dict[str, Goal] = {}
        # 计划存储
        self._plans: Dict[str, GoalPlan] = {}
        # 需求管理
        self._needs: Dict[NeedType, Need] = {}
        # 初始化基础需求
        self._initialize_needs()

    def _initialize_needs(self) -> None:
        """初始化基础需求"""
        for need_type in NeedType:
            self._needs[need_type] = Need(
                need_type=need_type,
                satisfaction_level=0.5,
                urgency=0.5,
                decay_rate=0.01  # 每小时衰减1%
            )

    async def initialize(self) -> None:
        """初始化目标模块"""
        self._initialized = True

        # 订阅相关事件
        self.subscribe_event(EventType.ACTION_EXECUTED, self._on_action_executed)
        self.subscribe_event(EventType.MEMORY_CREATED, self._on_memory_created)

    async def update(self, context: Dict[str, Any]) -> None:
        """
        更新目标模块

        Args:
            context: 上下文信息
        """
        self._mark_updated()

        # 更新需求衰减
        await self._update_needs()

        # 检查目标截止时间
        await self._check_deadlines()

        # 更新目标优先级
        await self._update_priorities()

    def get_state(self) -> Dict[str, Any]:
        """获取目标模块状态"""
        active_goals = self.get_active_goals()
        return {
            "total_goals": len(self._goals),
            "active_goals": len(active_goals),
            "needs": {
                need_type.value: {
                    "satisfaction": need.satisfaction_level,
                    "urgency": need.urgency
                }
                for need_type, need in self._needs.items()
            },
            "most_urgent_need": self._get_most_urgent_need(),
            "last_update": self._last_update.isoformat()
        }

    async def add_goal(self, goal: Dict[str, Any]) -> str:
        """
        添加新目标

        Args:
            goal: 目标信息

        Returns:
            目标ID
        """
        goal_id = goal.get("goal_id", f"goal_{uuid.uuid4().hex[:12]}")

        # 创建目标对象
        new_goal = Goal(
            goal_id=goal_id,
            **{k: v for k, v in goal.items() if k != "goal_id"}
        )

        self._goals[goal_id] = new_goal

        # 发送事件
        await self.emit_event(
            EventType.GOAL_CREATED,
            {
                "goal_id": goal_id,
                "title": new_goal.title,
                "priority": new_goal.priority.value
            }
        )

        return goal_id

    async def update_goal_progress(self, goal_id: str, progress: float) -> None:
        """
        更新目标进度

        Args:
            goal_id: 目标ID
            progress: 进度（0.0-1.0）
        """
        if goal_id not in self._goals:
            raise ValueError(f"Goal {goal_id} not found")

        goal = self._goals[goal_id]
        old_progress = goal.progress
        goal.update_progress(progress)

        # 如果目标完成
        if goal.is_completed() and old_progress < 1.0:
            await self._on_goal_completed(goal)

        # 发送更新事件
        await self.emit_event(
            EventType.GOAL_UPDATED,
            {
                "goal_id": goal_id,
                "progress": progress,
                "completed": goal.is_completed()
            }
        )

    def get_active_goals(self) -> List[Dict[str, Any]]:
        """
        获取活跃目标

        Returns:
            目标列表（按优先级排序）
        """
        active = [
            goal for goal in self._goals.values()
            if goal.status == GoalStatus.ACTIVE
        ]

        # 按优先级和紧急程度排序
        active.sort(
            key=lambda g: (g.priority.value, self._calculate_urgency(g)),
            reverse=True
        )

        return [goal.model_dump() for goal in active]

    async def get_goal(self, goal_id: str) -> Optional[Goal]:
        """
        获取特定目标

        Args:
            goal_id: 目标ID

        Returns:
            目标对象
        """
        return self._goals.get(goal_id)

    async def activate_goal(self, goal_id: str) -> None:
        """
        激活目标

        Args:
            goal_id: 目标ID
        """
        if goal_id in self._goals:
            self._goals[goal_id].status = GoalStatus.ACTIVE
            self._goals[goal_id].started_at = datetime.now()

            await self.emit_event(
                EventType.GOAL_UPDATED,
                {"goal_id": goal_id, "status": "ACTIVE"}
            )

    async def suspend_goal(self, goal_id: str) -> None:
        """
        暂停目标

        Args:
            goal_id: 目标ID
        """
        if goal_id in self._goals:
            self._goals[goal_id].status = GoalStatus.SUSPENDED

            await self.emit_event(
                EventType.GOAL_UPDATED,
                {"goal_id": goal_id, "status": "SUSPENDED"}
            )

    async def create_plan(self, goal_id: str, steps: List[Dict[str, Any]]) -> str:
        """
        为目标创建计划

        Args:
            goal_id: 目标ID
            steps: 执行步骤列表

        Returns:
            计划ID
        """
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"

        plan = GoalPlan(
            plan_id=plan_id,
            goal_id=goal_id,
            steps=steps
        )

        self._plans[plan_id] = plan
        return plan_id

    async def get_plan(self, plan_id: str) -> Optional[GoalPlan]:
        """
        获取计划

        Args:
            plan_id: 计划ID

        Returns:
            计划对象
        """
        return self._plans.get(plan_id)

    def get_needs(self) -> Dict[str, Dict[str, float]]:
        """
        获取所有需求状态

        Returns:
            需求字典
        """
        return {
            need_type.value: {
                "satisfaction": need.satisfaction_level,
                "urgency": need.urgency
            }
            for need_type, need in self._needs.items()
        }

    async def satisfy_need(self, need_type: NeedType, amount: float) -> None:
        """
        满足需求

        Args:
            need_type: 需求类型
            amount: 满足量（0-1）
        """
        if need_type in self._needs:
            self._needs[need_type].satisfy(amount)

    def get_top_priority_goals(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        获取最高优先级的目标

        Args:
            limit: 返回数量

        Returns:
            目标列表
        """
        active_goals = self.get_active_goals()
        return active_goals[:limit]

    # 私有方法

    def _calculate_urgency(self, goal: Goal) -> float:
        """
        计算目标紧急程度

        Args:
            goal: 目标对象

        Returns:
            紧急程度（0-1）
        """
        if not goal.deadline:
            return 0.5

        # 基于截止时间计算紧急程度
        now = datetime.now()
        time_left = (goal.deadline - now).total_seconds()
        total_time = (goal.deadline - goal.created_at).total_seconds()

        if time_left <= 0:
            return 1.0  # 已过期，最紧急

        urgency = 1.0 - (time_left / total_time)
        return max(0.0, min(1.0, urgency))

    def _get_most_urgent_need(self) -> Optional[str]:
        """获取最紧急的需求"""
        if not self._needs:
            return None

        most_urgent = max(self._needs.items(), key=lambda x: x[1].urgency)
        return most_urgent[0].value

    async def _update_needs(self) -> None:
        """更新需求衰减"""
        # 计算时间间隔
        if not hasattr(self, '_last_need_update'):
            self._last_need_update = datetime.now()
            return

        now = datetime.now()
        time_delta = (now - self._last_need_update).total_seconds() / 3600.0  # 转换为小时
        self._last_need_update = now

        # 应用衰减
        for need in self._needs.values():
            need.decay(time_delta)

    async def _check_deadlines(self) -> None:
        """检查目标截止时间"""
        now = datetime.now()
        for goal in self._goals.values():
            if goal.deadline and goal.status == GoalStatus.ACTIVE:
                if now > goal.deadline and goal.progress < 1.0:
                    # 目标过期但未完成
                    goal.status = GoalStatus.FAILED
                    goal.feedback = "超过截止时间"

                    await self.emit_event(
                        EventType.GOAL_UPDATED,
                        {
                            "goal_id": goal.goal_id,
                            "status": "FAILED",
                            "reason": "deadline_exceeded"
                        }
                    )

    async def _update_priorities(self) -> None:
        """动态更新目标优先级"""
        # 可以根据需求紧急程度、目标依赖等因素动态调整优先级
        for goal in self._goals.values():
            if goal.status != GoalStatus.ACTIVE:
                continue

            # 如果目标关联紧急需求，提高优先级
            for need_type in goal.related_needs:
                if need_type in self._needs:
                    need = self._needs[need_type]
                    if need.urgency > 0.8 and goal.priority.value < GoalPriority.HIGH.value:
                        # 可以考虑动态提升优先级
                        pass

    async def _on_goal_completed(self, goal: Goal) -> None:
        """
        目标完成处理

        Args:
            goal: 完成的目标
        """
        # 满足相关需求
        for need_type in goal.related_needs:
            await self.satisfy_need(need_type, 0.3)

        # 更新子目标的父目标进度
        if goal.parent_goal:
            await self._update_parent_goal_progress(goal.parent_goal)

        # 发送完成事件
        await self.emit_event(
            EventType.GOAL_COMPLETED,
            {
                "goal_id": goal.goal_id,
                "title": goal.title,
                "completion_time": goal.completed_at.isoformat() if goal.completed_at else None
            }
        )

    async def _update_parent_goal_progress(self, parent_goal_id: str) -> None:
        """
        更新父目标进度

        Args:
            parent_goal_id: 父目标ID
        """
        parent_goal = self._goals.get(parent_goal_id)
        if not parent_goal or not parent_goal.sub_goals:
            return

        # 计算子目标平均进度
        total_progress = 0.0
        for sub_goal_id in parent_goal.sub_goals:
            sub_goal = self._goals.get(sub_goal_id)
            if sub_goal:
                total_progress += sub_goal.progress

        avg_progress = total_progress / len(parent_goal.sub_goals)
        await self.update_goal_progress(parent_goal_id, avg_progress)

    async def _on_action_executed(self, event) -> None:
        """行为执行事件处理"""
        # 可以根据行为结果更新相关目标进度
        pass

    async def _on_memory_created(self, event) -> None:
        """记忆创建事件处理"""
        # 可以根据记忆创建新目标或更新现有目标
        pass
