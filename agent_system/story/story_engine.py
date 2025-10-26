"""
剧情演绎引擎 - 增强版
支持剧情大纲生成、角色日程管理、偏离检测和自动纠正
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from enum import Enum

from agent_system.llm import get_llm_client, ModelType
from agent_system.llm.prompt_manager import get_prompt_manager
from agent_system.models.schedule_models import (
    StoryOutline, DailySchedule, ScheduleItem, ScheduleStatus
)

if TYPE_CHECKING:
    from agent_system.core.agent import Agent


class StoryMode(Enum):
    """剧情模式"""
    STRICT = "strict"  # 严格模式 - 紧密遵循剧情
    GUIDED = "guided"  # 引导模式 - 引导回到剧情但允许偏离
    FREE = "free"  # 自由模式 - 仅作参考


class StoryEngine:
    """
    剧情演绎引擎
    管理剧情大纲生成、角色日程、偏离检测和纠正
    """

    def __init__(
        self,
        story_mode: StoryMode = StoryMode.GUIDED,
        use_llm: bool = True,
        deviation_threshold: float = 0.5  # 偏离阈值
    ):
        """
        初始化剧情引擎

        Args:
            story_mode: 剧情模式
            use_llm: 是否使用LLM
            deviation_threshold: 偏离阈值（低于此值触发纠正）
        """
        self.story_mode = story_mode
        self.use_llm = use_llm
        self.deviation_threshold = deviation_threshold

        # LLM客户端
        self._llm_client = None
        self._prompt_manager = None

        # 当前剧情大纲
        self._current_outline: Optional[StoryOutline] = None

        # 角色日程管理 {agent_id: DailySchedule}
        self._agent_schedules: Dict[str, DailySchedule] = {}

        # 智能体引用 {agent_id: Agent}
        self._agents: Dict[str, 'Agent'] = {}

        # 偏离记录
        self._deviation_history: List[Dict[str, Any]] = []

        # 自动运行标志
        self._auto_running = False
        self._last_update = datetime.now()

    async def initialize(self) -> None:
        """初始化引擎"""
        if self.use_llm:
            self._llm_client = get_llm_client()
            self._prompt_manager = get_prompt_manager()

    def register_agent(self, agent: 'Agent') -> None:
        """
        注册智能体

        Args:
            agent: 智能体实例
        """
        self._agents[agent.agent_id] = agent

    async def generate_story_outline(
        self,
        theme: str,
        agent_characters: List[Dict[str, str]],
        story_date: Optional[str] = None,
        custom_plot_points: Optional[List[str]] = None
    ) -> StoryOutline:
        """
        生成剧情大纲

        Args:
            theme: 剧情主题
            agent_characters: 角色列表 [{"agent_id": "xxx", "name": "xxx", "role": "xxx"}]
            story_date: 剧情日期，默认为今天
            custom_plot_points: 自定义剧情点

        Returns:
            剧情大纲
        """
        if story_date is None:
            story_date = datetime.now().strftime("%Y-%m-%d")

        story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 如果提供了自定义剧情点，使用它们
        if custom_plot_points:
            outline = StoryOutline(
                story_id=story_id,
                title=f"{theme}的故事",
                theme=theme,
                story_date=story_date,
                time_period="一天",
                setting=f"{theme}的背景设定",
                main_plot_points=custom_plot_points,
                character_roles={char["agent_id"]: char.get("role", "角色") for char in agent_characters},
                character_goals={char["agent_id"]: f"参与{theme}" for char in agent_characters}
            )
        elif self.use_llm and self._llm_client:
            # 使用LLM生成剧情大纲
            outline = await self._generate_outline_with_llm(theme, agent_characters, story_date)
        else:
            # 默认简单大纲
            outline = self._generate_default_outline(theme, agent_characters, story_date)

        self._current_outline = outline
        return outline

    async def generate_agent_schedule(
        self,
        agent_id: str,
        agent: Optional['Agent'] = None
    ) -> DailySchedule:
        """
        为智能体生成日程

        Args:
            agent_id: 智能体ID
            agent: 智能体实例（可选）

        Returns:
            每日日程
        """
        if not self._current_outline:
            raise ValueError("请先生成剧情大纲")

        if agent not in self._agents and agent:
            self._agents[agent_id] = agent

        # 使用LLM生成日程
        if self.use_llm and self._llm_client and agent_id in self._agents:
            schedule = await self._generate_schedule_with_llm(agent_id)
        else:
            # 默认日程生成
            schedule = self._generate_default_schedule(agent_id)

        self._agent_schedules[agent_id] = schedule
        return schedule

    async def modify_schedule(
        self,
        agent_id: str,
        schedule_id: str,
        updates: Dict[str, Any],
        reason: str = "用户修改"
    ) -> bool:
        """
        修改日程

        Args:
            agent_id: 智能体ID
            schedule_id: 日程ID
            updates: 更新内容
            reason: 修改原因

        Returns:
            是否成功修改
        """
        if agent_id not in self._agent_schedules:
            return False

        schedule = self._agent_schedules[agent_id]
        success = schedule.update_item(schedule_id, updates, reason)

        if success:
            # 重新检查对齐度
            await self._check_schedule_alignment(agent_id)

        return success

    async def check_and_correct_deviation(self) -> List[Dict[str, Any]]:
        """
        检查所有智能体的日程偏离并触发纠正事件

        Returns:
            触发的纠正事件列表
        """
        correction_events = []

        for agent_id, schedule in self._agent_schedules.items():
            # 检查整体对齐度
            if schedule.overall_alignment < self.deviation_threshold:
                # 生成纠正事件
                event = await self._generate_correction_event(agent_id, schedule)

                if event and agent_id in self._agents:
                    # 触发环境事件
                    agent = self._agents[agent_id]
                    await agent.perceive_environment(event)

                    correction_events.append({
                        "agent_id": agent_id,
                        "alignment": schedule.overall_alignment,
                        "event": event,
                        "timestamp": datetime.now().isoformat()
                    })

                    # 记录偏离
                    self._deviation_history.append({
                        "agent_id": agent_id,
                        "alignment": schedule.overall_alignment,
                        "corrected": True,
                        "timestamp": datetime.now().isoformat()
                    })

        return correction_events

    def get_current_activity(self, agent_id: str) -> Optional[str]:
        """
        获取智能体当前正在做什么

        Args:
            agent_id: 智能体ID

        Returns:
            当前活动描述
        """
        if agent_id not in self._agent_schedules:
            return None

        schedule = self._agent_schedules[agent_id]
        current_item = schedule.get_current_activity(datetime.now())

        if current_item:
            return f"{current_item.activity}: {current_item.description}"

        return "当前没有特定活动"

    def get_schedule(self, agent_id: str) -> Optional[DailySchedule]:
        """
        获取智能体的日程

        Args:
            agent_id: 智能体ID

        Returns:
            每日日程
        """
        return self._agent_schedules.get(agent_id)

    def get_story_outline(self) -> Optional[StoryOutline]:
        """获取当前剧情大纲"""
        return self._current_outline

    def get_agent_schedule(self, agent_id: str) -> Optional[DailySchedule]:
        """
        获取智能体的日程（get_schedule的别名）

        Args:
            agent_id: 智能体ID

        Returns:
            每日日程
        """
        return self.get_schedule(agent_id)

    def mark_schedule_completed(self, agent_id: str, schedule_id: str) -> bool:
        """
        标记日程项为已完成

        Args:
            agent_id: 智能体ID
            schedule_id: 日程ID

        Returns:
            是否成功标记
        """
        if agent_id not in self._agent_schedules:
            return False

        schedule = self._agent_schedules[agent_id]
        return schedule.mark_completed(schedule_id)

    async def record_to_memory(self, agent_id: str) -> None:
        """
        将日程记录到智能体记忆

        Args:
            agent_id: 智能体ID
        """
        if agent_id not in self._agents or agent_id not in self._agent_schedules:
            return

        agent = self._agents[agent_id]
        schedule = self._agent_schedules[agent_id]

        # 记录每个已完成的活动为事件记忆
        for item in schedule.schedule_items:
            if item.completed and item.is_narrative:
                # 存储为事件记忆
                await agent.memory.store("event", {
                    "event_summary": f"{item.start_time} {item.activity}",
                    "event_details": item.description,
                    "participants": [agent_id] + item.related_agents,
                    "location": item.location,
                    "emotion_valence": 0.5,  # 中性
                    "emotion_arousal": 0.3,
                    "importance": item.story_alignment_score,
                    "tags": ["日程", "剧情演绎", item.activity],
                    "related_goals": []
                })

    # 私有方法

    async def _generate_outline_with_llm(
        self,
        theme: str,
        agent_characters: List[Dict[str, str]],
        story_date: str
    ) -> StoryOutline:
        """使用LLM生成剧情大纲"""
        try:
            system_prompt = self._prompt_manager.get_prompt("story", "system")

            characters_str = "\n".join([
                f"- {char['name']} (ID: {char['agent_id']}, 角色: {char.get('role', '未指定')})"
                for char in agent_characters
            ])

            user_prompt = self._prompt_manager.get_prompt(
                "story",
                "generate_outline",
                theme=theme,
                characters=characters_str,
                date=story_date
            )

            response = await self._llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_type=ModelType.ACCURATE,
                temperature=0.8
            )

            if "parse_error" not in response:
                story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                return StoryOutline(
                    story_id=story_id,
                    title=response.get("title", theme),
                    theme=theme,
                    story_date=story_date,
                    time_period=response.get("time_period", "一天"),
                    setting=response.get("setting", ""),
                    main_plot_points=response.get("main_plot_points", []),
                    character_roles=response.get("character_roles", {}),
                    character_goals=response.get("character_goals", {}),
                    key_events=response.get("key_events", []),
                    narrative_constraints=response.get("narrative_constraints", [])
                )

        except Exception as e:
            print(f"LLM大纲生成错误: {e}")

        return self._generate_default_outline(theme, agent_characters, story_date)

    def _generate_default_outline(
        self,
        theme: str,
        agent_characters: List[Dict[str, str]],
        story_date: str
    ) -> StoryOutline:
        """生成默认剧情大纲"""
        story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return StoryOutline(
            story_id=story_id,
            title=f"{theme}的一天",
            theme=theme,
            story_date=story_date,
            time_period="一天",
            setting=f"关于{theme}的故事背景",
            main_plot_points=[
                f"开始：引入{theme}",
                f"发展：深入{theme}",
                f"高潮：{theme}的关键时刻",
                f"结束：{theme}的结局"
            ],
            character_roles={char["agent_id"]: char.get("role", "参与者") for char in agent_characters},
            character_goals={char["agent_id"]: f"完成与{theme}相关的任务" for char in agent_characters}
        )

    async def _generate_schedule_with_llm(self, agent_id: str) -> DailySchedule:
        """使用LLM生成日程"""
        try:
            agent = self._agents[agent_id]
            outline = self._current_outline

            system_prompt = self._prompt_manager.get_prompt("story", "system")

            # 构建角色信息
            character_role = outline.character_roles.get(agent_id, "参与者")
            character_goal = outline.character_goals.get(agent_id, "参与剧情")

            user_prompt = self._prompt_manager.get_prompt(
                "story",
                "generate_schedule",
                agent_id=agent_id,
                character_name=agent.name,
                character_role=character_role,
                character_goal=character_goal,
                story_title=outline.title,
                plot_points="\n".join([f"{i+1}. {p}" for i, p in enumerate(outline.main_plot_points)]),
                date=outline.story_date
            )

            # 使用cognition模块的决策能力
            decision_context = {
                "situation": f"作为{character_role}，需要为今天制定符合剧情的行动计划",
                "story_outline": {
                    "title": outline.title,
                    "goal": character_goal,
                    "plot_points": outline.main_plot_points
                }
            }

            # 通过LLM直接生成
            response = await self._llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_type=ModelType.FAST,
                temperature=0.7
            )

            if "parse_error" not in response and "schedule_items" in response:
                # 构建日程
                schedule = DailySchedule(
                    agent_id=agent_id,
                    date=outline.story_date,
                    story_id=outline.story_id
                )

                for item_data in response["schedule_items"]:
                    schedule_id = f"sched_{agent_id}_{uuid.uuid4().hex[:8]}"
                    item = ScheduleItem(
                        schedule_id=schedule_id,
                        agent_id=agent_id,
                        date=outline.story_date,
                        start_time=item_data.get("start_time", "09:00"),
                        end_time=item_data.get("end_time", "10:00"),
                        duration_minutes=item_data.get("duration_minutes", 60),
                        activity=item_data.get("activity", "活动"),
                        description=item_data.get("description", ""),
                        location=item_data.get("location"),
                        related_agents=item_data.get("related_agents", []),
                        related_plot_point=item_data.get("related_plot_point"),
                        story_alignment_score=1.0,
                        status=ScheduleStatus.PLANNED,
                        is_narrative=True
                    )
                    schedule.add_item(item)

                return schedule

        except Exception as e:
            print(f"LLM日程生成错误: {e}")

        return self._generate_default_schedule(agent_id)

    def _generate_default_schedule(self, agent_id: str) -> DailySchedule:
        """生成默认日程"""
        outline = self._current_outline

        schedule = DailySchedule(
            agent_id=agent_id,
            date=outline.story_date,
            story_id=outline.story_id
        )

        # 为每个剧情点创建一个活动
        start_hour = 9
        for i, plot_point in enumerate(outline.main_plot_points):
            schedule_id = f"sched_{agent_id}_{i}"
            start_time = f"{start_hour + i*2:02d}:00"
            end_time = f"{start_hour + i*2 + 1:02d}:00"

            item = ScheduleItem(
                schedule_id=schedule_id,
                agent_id=agent_id,
                date=outline.story_date,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=60,
                activity=plot_point,
                description=f"执行剧情: {plot_point}",
                related_plot_point=plot_point,
                story_alignment_score=1.0,
                is_narrative=True
            )
            schedule.add_item(item)

        return schedule

    async def _check_schedule_alignment(self, agent_id: str) -> float:
        """
        检查日程与剧情的对齐度

        Args:
            agent_id: 智能体ID

        Returns:
            对齐度分数
        """
        if agent_id not in self._agent_schedules:
            return 1.0

        schedule = self._agent_schedules[agent_id]

        # 使用LLM检查对齐度
        if self.use_llm and self._llm_client:
            try:
                system_prompt = self._prompt_manager.get_prompt("story", "system")

                outline_info = {
                    "plot_points": self._current_outline.main_plot_points,
                    "character_goal": self._current_outline.character_goals.get(agent_id)
                }

                schedule_summary = "\n".join([
                    f"{item.start_time}-{item.end_time}: {item.activity}"
                    for item in schedule.schedule_items
                ])

                user_prompt = self._prompt_manager.get_prompt(
                    "story",
                    "check_schedule_alignment",
                    outline=str(outline_info),
                    schedule=schedule_summary
                )

                response = await self._llm_client.generate_json(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model_type=ModelType.FAST,
                    temperature=0.3
                )

                if "parse_error" not in response:
                    overall_score = float(response.get("alignment_score", 0.8))

                    # 更新每个活动的对齐度
                    item_scores = response.get("item_scores", {})
                    for item in schedule.schedule_items:
                        if item.schedule_id in item_scores:
                            item.story_alignment_score = float(item_scores[item.schedule_id])

                    schedule._update_alignment()
                    return overall_score

            except Exception as e:
                print(f"对齐度检查错误: {e}")

        return schedule.overall_alignment

    async def _generate_correction_event(
        self,
        agent_id: str,
        schedule: DailySchedule
    ) -> Dict[str, Any]:
        """
        生成纠正事件

        Args:
            agent_id: 智能体ID
            schedule: 日程

        Returns:
            环境事件
        """
        if not self.use_llm or not self._llm_client:
            # 默认纠正事件
            return {
                "type": "story_correction",
                "description": "剧情引导：请关注核心剧情发展",
                "guidance": "回到主要剧情线",
                "urgency": "medium"
            }

        try:
            system_prompt = self._prompt_manager.get_prompt("story", "system")

            # 找出偏离的活动
            low_alignment_items = [
                item for item in schedule.schedule_items
                if item.story_alignment_score < self.deviation_threshold
            ]

            deviations_str = "\n".join([
                f"- {item.start_time} {item.activity}: 对齐度 {item.story_alignment_score:.2f}"
                for item in low_alignment_items
            ])

            user_prompt = self._prompt_manager.get_prompt(
                "story",
                "generate_correction_event",
                agent_id=agent_id,
                deviations=deviations_str,
                expected_plot=self._current_outline.main_plot_points[0] if self._current_outline.main_plot_points else "",
                character_goal=self._current_outline.character_goals.get(agent_id, "")
            )

            response = await self._llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_type=ModelType.FAST,
                temperature=0.7
            )

            if "parse_error" not in response:
                return {
                    "type": "story_correction",
                    "description": response.get("event_description", ""),
                    "guidance": response.get("guidance", ""),
                    "urgency": response.get("urgency", "medium"),
                    "suggested_action": response.get("suggested_action", "")
                }

        except Exception as e:
            print(f"纠正事件生成错误: {e}")

        return {
            "type": "story_correction",
            "description": "剧情需要你的注意",
            "guidance": "请关注主要剧情目标",
            "urgency": "medium"
        }
