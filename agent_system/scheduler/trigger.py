"""
定时触发器
支持智能体定期自动更新和触发事件
"""

import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum


class TriggerType(Enum):
    """触发器类型"""
    INTERVAL = "interval"  # 固定间隔
    CRON = "cron"  # Cron表达式（简化版）
    CONDITIONAL = "conditional"  # 条件触发


class PeriodicTrigger:
    """
    周期性触发器
    支持定时触发智能体更新
    """

    def __init__(
        self,
        trigger_id: str,
        interval_seconds: float,
        callback: Callable,
        enabled: bool = True
    ):
        """
        初始化触发器

        Args:
            trigger_id: 触发器ID
            interval_seconds: 触发间隔（秒）
            callback: 触发时调用的回调函数
            enabled: 是否启用
        """
        self.trigger_id = trigger_id
        self.interval_seconds = interval_seconds
        self.callback = callback
        self.enabled = enabled

        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._trigger_count = 0
        self._last_trigger_time: Optional[datetime] = None

    async def start(self) -> None:
        """启动触发器"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """停止触发器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def is_running(self) -> bool:
        """检查触发器是否运行中"""
        return self._running

    def get_stats(self) -> Dict[str, Any]:
        """获取触发器统计信息"""
        return {
            "trigger_id": self.trigger_id,
            "running": self._running,
            "enabled": self.enabled,
            "trigger_count": self._trigger_count,
            "last_trigger_time": self._last_trigger_time.isoformat() if self._last_trigger_time else None,
            "interval_seconds": self.interval_seconds
        }

    async def _run_loop(self) -> None:
        """触发循环"""
        while self._running:
            try:
                # 等待指定间隔
                await asyncio.sleep(self.interval_seconds)

                if not self.enabled:
                    continue

                # 触发回调
                self._last_trigger_time = datetime.now()
                self._trigger_count += 1

                # 执行回调
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback()
                else:
                    await asyncio.to_thread(self.callback)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # 记录错误但继续运行
                print(f"Error in trigger {self.trigger_id}: {e}")
                await asyncio.sleep(1)  # 短暂延迟后继续


class AgentScheduler:
    """
    智能体调度器
    管理智能体的定时任务和自动更新
    """

    def __init__(self, agent):
        """
        初始化调度器

        Args:
            agent: 智能体实例
        """
        self.agent = agent
        self._triggers: Dict[str, PeriodicTrigger] = {}
        self._running = False

        # 默认触发间隔（分钟）
        self._default_update_interval = 5.0 * 60  # 5分钟
        self._default_environment_check_interval = 2.0 * 60  # 2分钟

    async def start(self) -> None:
        """启动调度器"""
        if self._running:
            return

        self._running = True

        # 创建默认触发器
        await self._create_default_triggers()

        # 启动所有触发器
        for trigger in self._triggers.values():
            await trigger.start()

    async def stop(self) -> None:
        """停止调度器"""
        self._running = False

        # 停止所有触发器
        for trigger in self._triggers.values():
            await trigger.stop()

    def add_trigger(
        self,
        trigger_id: str,
        interval_seconds: float,
        callback: Callable,
        enabled: bool = True
    ) -> None:
        """
        添加自定义触发器

        Args:
            trigger_id: 触发器ID
            interval_seconds: 触发间隔（秒）
            callback: 回调函数
            enabled: 是否启用
        """
        trigger = PeriodicTrigger(trigger_id, interval_seconds, callback, enabled)
        self._triggers[trigger_id] = trigger

        # 如果调度器已运行，立即启动触发器
        if self._running:
            asyncio.create_task(trigger.start())

    def remove_trigger(self, trigger_id: str) -> bool:
        """
        移除触发器

        Args:
            trigger_id: 触发器ID

        Returns:
            是否成功移除
        """
        if trigger_id in self._triggers:
            trigger = self._triggers[trigger_id]
            asyncio.create_task(trigger.stop())
            del self._triggers[trigger_id]
            return True
        return False

    def get_trigger_stats(self) -> List[Dict[str, Any]]:
        """获取所有触发器统计信息"""
        return [trigger.get_stats() for trigger in self._triggers.values()]

    async def _create_default_triggers(self) -> None:
        """创建默认触发器"""
        # 1. 定期更新触发器（更新所有模块）
        self.add_trigger(
            "agent_update",
            self._default_update_interval,
            self._on_periodic_update,
            enabled=True
        )

        # 2. 环境检查触发器
        self.add_trigger(
            "environment_check",
            self._default_environment_check_interval,
            self._on_environment_check,
            enabled=True
        )

        # 3. 目标评估触发器
        self.add_trigger(
            "goal_evaluation",
            10.0 * 60,  # 10分钟
            self._on_goal_evaluation,
            enabled=True
        )

        # 4. 剧情演绎检查触发器
        self.add_trigger(
            "story_narrative_check",
            5.0 * 60,  # 5分钟
            self._on_story_narrative_check,
            enabled=True
        )

    async def _on_periodic_update(self) -> None:
        """定期更新回调"""
        if not self.agent.is_running():
            return

        # 触发智能体tick
        await self.agent.process_tick()

        # 发送定期触发事件
        event_bus = self.agent.get_event_bus()
        from agent_system.core.event_bus import Event, EventType
        await event_bus.publish(Event(
            event_type=EventType.PERIODIC_TRIGGER,
            source="AgentScheduler",
            data={"trigger_type": "periodic_update"}
        ))

    async def _on_environment_check(self) -> None:
        """环境检查回调"""
        if not self.agent.is_running():
            return

        # 这里可以主动检查环境变化
        # 例如：根据剧情设定生成环境事件
        environment_update = await self._generate_environment_update()

        if environment_update:
            await self.agent.perceive_environment(environment_update)

    async def _on_goal_evaluation(self) -> None:
        """目标评估回调"""
        if not self.agent.is_running():
            return

        # 评估当前目标进展
        active_goals = self.agent.goal.get_active_goals()

        # 可以根据智能体状态自动调整目标
        # 或者生成新的目标
        if len(active_goals) == 0:
            # 如果没有活跃目标，考虑生成新目标
            await self._maybe_generate_goal()

    async def _on_story_narrative_check(self) -> None:
        """
        剧情演绎检查回调
        检查智能体日程是否偏离剧情，触发修正事件，并记录到记忆
        """
        if not self.agent.is_running():
            return

        # 检查是否有story_engine
        story_engine = getattr(self.agent, 'story_engine', None)
        if not story_engine:
            return

        try:
            # 1. 检查并修正偏离
            deviation_events = await story_engine.check_and_correct_deviation()

            if deviation_events:
                print(f"[StoryNarrative] 检测到{len(deviation_events)}个偏离，已触发修正事件")

            # 2. 记录已完成的日程到记忆
            await story_engine.record_to_memory(self.agent.agent_id)

        except Exception as e:
            print(f"[StoryNarrative] 剧情演绎检查失败: {e}")

    async def _generate_environment_update(self) -> Optional[Dict[str, Any]]:
        """
        生成环境更新
        根据剧情设定和智能体状态生成合理的环境变化

        Returns:
            环境更新数据
        """
        # 这里是简化版本，实际可以集成更复杂的环境生成逻辑
        # 例如：使用LLM根据剧情和智能体历史生成环境事件

        # 获取智能体当前状态
        emotion_state = self.agent.emotion.get_current_emotion()
        active_goals = self.agent.goal.get_active_goals()

        # 简单示例：基于情感状态生成环境事件
        valence = emotion_state.get("valence", 0)

        if valence < -0.5:
            # 负面情绪时，可能发生安慰性事件
            return {
                "event_type": "social_interaction",
                "description": "A friend approaches to offer support",
                "impact": "positive"
            }

        # 大部分时候不生成事件
        return None

    async def _maybe_generate_goal(self) -> None:
        """
        可能生成新目标
        根据需求状态生成合适的目标
        """
        # 获取需求状态
        needs = self.agent.goal.get_needs()

        # 找到最紧急的需求
        most_urgent_need = None
        max_urgency = 0

        for need_type, need_data in needs.items():
            urgency = need_data.get("urgency", 0)
            if urgency > max_urgency:
                max_urgency = urgency
                most_urgent_need = need_type

        # 如果有紧急需求，生成相应目标
        if most_urgent_need and max_urgency > 0.7:
            from agent_system.models.goal_models import NeedType, GoalPriority

            goal_data = {
                "title": f"满足 {most_urgent_need} 需求",
                "description": f"当前 {most_urgent_need} 需求紧急程度较高，需要采取行动",
                "priority": GoalPriority.HIGH.value,
                "related_needs": [most_urgent_need]
            }

            await self.agent.add_goal(goal_data)
