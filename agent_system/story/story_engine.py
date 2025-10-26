"""
剧情演绎引擎
管理剧情设定和智能体的剧情演绎
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from agent_system.llm import get_llm_client, ModelType
from agent_system.llm.prompt_manager import get_prompt_manager


class StoryMode(Enum):
    """剧情模式"""
    STRICT = "strict"  # 严格模式 - 紧密遵循剧情
    GUIDED = "guided"  # 引导模式 - 引导回到剧情但允许偏离
    FREE = "free"  # 自由模式 - 仅作参考


@dataclass
class Story:
    """剧情数据结构"""
    story_id: str
    title: str
    setting: str  # 时间地点背景
    background: str  # 背景故事
    plot_points: List[str]  # 关键剧情点
    current_plot_index: int = 0
    initial_goals: Dict[str, str] = None  # agent_id -> 初始目标

    def __post_init__(self):
        if self.initial_goals is None:
            self.initial_goals = {}


class StoryEngine:
    """
    剧情演绎引擎
    负责剧情生成、跟踪和纠偏
    """

    def __init__(
        self,
        story_mode: StoryMode = StoryMode.GUIDED,
        use_llm: bool = True
    ):
        """
        初始化剧情引擎

        Args:
            story_mode: 剧情模式
            use_llm: 是否使用LLM生成剧情
        """
        self.story_mode = story_mode
        self.use_llm = use_llm

        # LLM客户端
        self._llm_client = None
        self._prompt_manager = None

        # 当前剧情
        self._current_story: Optional[Story] = None
        self._story_history: List[Dict[str, Any]] = []

        # 智能体状态追踪
        self._agent_actions: Dict[str, List[Dict]] = {}  # agent_id -> actions

    async def initialize(self) -> None:
        """初始化引擎"""
        if self.use_llm:
            self._llm_client = get_llm_client()
            self._prompt_manager = get_prompt_manager()

    async def generate_story(
        self,
        theme: str,
        agent_characters: List[Dict[str, str]],
        custom_plot: Optional[List[str]] = None
    ) -> Story:
        """
        生成剧情

        Args:
            theme: 剧情主题
            agent_characters: 智能体角色列表 [{"agent_id": "xxx", "name": "xxx", "role": "xxx"}]
            custom_plot: 自定义剧情点（如果提供则使用，否则由LLM生成）

        Returns:
            剧情对象
        """
        story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 如果提供了自定义剧情
        if custom_plot:
            story = Story(
                story_id=story_id,
                title=f"Custom Story: {theme}",
                setting="Custom setting",
                background=theme,
                plot_points=custom_plot,
                initial_goals={
                    char["agent_id"]: f"Participate in {theme}"
                    for char in agent_characters
                }
            )
            self._current_story = story
            return story

        # 使用LLM生成剧情
        if self.use_llm and self._llm_client:
            story = await self._generate_story_with_llm(theme, agent_characters)
        else:
            # 默认简单剧情
            story = self._generate_default_story(theme, agent_characters)

        self._current_story = story
        return story

    async def check_action_alignment(
        self,
        agent_id: str,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        检查行为是否符合剧情

        Args:
            agent_id: 智能体ID
            action: 行为描述

        Returns:
            对齐检查结果
        """
        if not self._current_story:
            return {"aligned": True, "deviation_level": 0.0, "suggestion": ""}

        # 记录行为
        if agent_id not in self._agent_actions:
            self._agent_actions[agent_id] = []
        self._agent_actions[agent_id].append({
            "action": action,
            "timestamp": datetime.now().isoformat()
        })

        # 严格模式下检查
        if self.story_mode == StoryMode.FREE:
            return {"aligned": True, "deviation_level": 0.0, "suggestion": ""}

        # 使用LLM检查
        if self.use_llm and self._llm_client:
            return await self._check_alignment_with_llm(agent_id, action)

        # 默认检查
        return self._check_alignment_simple(agent_id, action)

    async def generate_next_event(
        self,
        current_situation: str,
        agent_states: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        生成下一个剧情事件

        Args:
            current_situation: 当前情况描述
            agent_states: 智能体状态字典

        Returns:
            事件数据
        """
        if not self._current_story:
            return {"event_type": "none", "description": "No active story"}

        # 使用LLM生成事件
        if self.use_llm and self._llm_client:
            return await self._generate_event_with_llm(current_situation, agent_states)

        # 默认事件生成
        return self._generate_default_event(current_situation)

    def get_current_story(self) -> Optional[Story]:
        """获取当前剧情"""
        return self._current_story

    def advance_plot(self) -> bool:
        """
        推进剧情点

        Returns:
            是否成功推进
        """
        if not self._current_story:
            return False

        if self._current_story.current_plot_index < len(self._current_story.plot_points) - 1:
            self._current_story.current_plot_index += 1
            return True

        return False

    def get_current_plot_point(self) -> Optional[str]:
        """获取当前剧情点"""
        if not self._current_story:
            return None

        if self._current_story.current_plot_index < len(self._current_story.plot_points):
            return self._current_story.plot_points[self._current_story.current_plot_index]

        return None

    # 私有方法

    async def _generate_story_with_llm(
        self,
        theme: str,
        agent_characters: List[Dict[str, str]]
    ) -> Story:
        """使用LLM生成剧情"""
        try:
            system_prompt = self._prompt_manager.get_prompt("story", "system")

            characters_str = ", ".join([
                f"{char['name']} ({char.get('role', 'character')})"
                for char in agent_characters
            ])

            user_prompt = self._prompt_manager.get_prompt(
                "story",
                "generate_story",
                theme=theme,
                characters=characters_str
            )

            response = await self._llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_type=ModelType.ACCURATE,
                temperature=0.8
            )

            if "parse_error" not in response:
                story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                return Story(
                    story_id=story_id,
                    title=response.get("title", theme),
                    setting=response.get("setting", ""),
                    background=response.get("background", ""),
                    plot_points=response.get("plot_points", []),
                    initial_goals=response.get("initial_goals", {})
                )

        except Exception as e:
            print(f"LLM story generation error: {e}")

        return self._generate_default_story(theme, agent_characters)

    def _generate_default_story(
        self,
        theme: str,
        agent_characters: List[Dict[str, str]]
    ) -> Story:
        """生成默认剧情"""
        story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return Story(
            story_id=story_id,
            title=f"Story: {theme}",
            setting="A generic setting",
            background=f"A story about {theme}",
            plot_points=[
                f"Introduction to {theme}",
                f"Development of {theme}",
                f"Climax of {theme}",
                f"Resolution of {theme}"
            ],
            initial_goals={
                char["agent_id"]: f"Engage with {theme}"
                for char in agent_characters
            }
        )

    async def _check_alignment_with_llm(
        self,
        agent_id: str,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用LLM检查对齐"""
        try:
            system_prompt = self._prompt_manager.get_prompt("story", "system")

            story_context = {
                "title": self._current_story.title,
                "current_plot": self.get_current_plot_point(),
                "all_plots": self._current_story.plot_points
            }

            user_prompt = self._prompt_manager.get_prompt(
                "story",
                "check_deviation",
                story=str(story_context),
                action=str(action)
            )

            response = await self._llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_type=ModelType.FAST,
                temperature=0.3
            )

            if "parse_error" not in response:
                return {
                    "aligned": response.get("aligned", True),
                    "deviation_level": float(response.get("deviation_level", 0.0)),
                    "suggestion": response.get("suggestion", "")
                }

        except Exception as e:
            print(f"LLM alignment check error: {e}")

        return self._check_alignment_simple(agent_id, action)

    def _check_alignment_simple(
        self,
        agent_id: str,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """简单对齐检查"""
        # 简化的检查逻辑
        return {
            "aligned": True,
            "deviation_level": 0.2,
            "suggestion": "Continue with current storyline"
        }

    async def _generate_event_with_llm(
        self,
        current_situation: str,
        agent_states: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """使用LLM生成事件"""
        try:
            system_prompt = self._prompt_manager.get_prompt("story", "system")

            story_info = {
                "title": self._current_story.title,
                "current_plot": self.get_current_plot_point()
            }

            user_prompt = self._prompt_manager.get_prompt(
                "story",
                "generate_event",
                story=str(story_info),
                situation=current_situation,
                agents=str(agent_states)[:500]
            )

            response = await self._llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_type=ModelType.FAST,
                temperature=0.8
            )

            if "parse_error" not in response:
                return {
                    "event_type": response.get("event_type", "environment"),
                    "description": response.get("description", ""),
                    "affected_agents": response.get("affected_agents", []),
                    "impact": response.get("impact", "")
                }

        except Exception as e:
            print(f"LLM event generation error: {e}")

        return self._generate_default_event(current_situation)

    def _generate_default_event(self, current_situation: str) -> Dict[str, Any]:
        """生成默认事件"""
        return {
            "event_type": "environment",
            "description": f"The story continues: {self.get_current_plot_point()}",
            "affected_agents": [],
            "impact": "Story progression"
        }
