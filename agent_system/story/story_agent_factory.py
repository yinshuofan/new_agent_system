"""
故事智能体工厂
简化故事智能体的创建流程
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from agent_system import AgentManager
from agent_system.story import StoryLoader, StoryConfig
from agent_system.llm.prompt_manager import initialize_prompts


class StoryAgentFactory:
    """
    故事智能体工厂
    简化创建和配置故事智能体的过程
    """

    def __init__(
        self,
        story_config_path: str,
        prompts_path: str = "/home/user/new_agent_system/config/prompts.yaml",
        max_agents: int = 10
    ):
        """
        初始化工厂

        Args:
            story_config_path: 故事配置文件路径
            prompts_path: 提示词配置路径
            max_agents: 最大智能体数量
        """
        self.story_config_path = story_config_path
        self.prompts_path = prompts_path
        self.max_agents = max_agents

        # 加载配置
        self.story_config: Optional[StoryConfig] = None
        self.manager: Optional[AgentManager] = None
        self.agents: Dict[str, Any] = {}

    async def initialize(self, use_llm: bool = True) -> None:
        """
        初始化工厂

        Args:
            use_llm: 是否使用LLM
        """
        # 初始化提示词
        initialize_prompts(self.prompts_path)

        # 加载故事配置
        self.story_config = StoryLoader.load_from_file(self.story_config_path)

        # 创建智能体管理器
        self.manager = AgentManager(max_agents=self.max_agents)

        # 创建所有角色
        for char_id in self.story_config.characters.keys():
            agent = await self.create_character(char_id, use_llm=use_llm)
            self.agents[char_id] = agent

    async def create_character(self, character_id: str, use_llm: bool = True):
        """
        创建单个角色智能体

        Args:
            character_id: 角色ID
            use_llm: 是否使用LLM

        Returns:
            创建的智能体
        """
        if not self.story_config or not self.manager:
            raise RuntimeError("Factory not initialized. Call initialize() first.")

        # 获取角色配置
        char_config = self.story_config.get_character_config(character_id)
        if not char_config:
            raise ValueError(f"Character '{character_id}' not found in story config")

        # 创建智能体
        agent = await self.manager.create_agent(
            agent_id=character_id,
            name=char_config.get("name", character_id),
            config=char_config,
            use_llm=use_llm
        )

        # 注意：日程和故事大纲由StoryEngine管理，不在Agent上
        # 如果需要使用剧情引擎功能，请使用StoryEngine类

        return agent

    def get_agent(self, character_id: str):
        """
        获取已创建的智能体

        Args:
            character_id: 角色ID

        Returns:
            智能体实例
        """
        return self.agents.get(character_id)

    def get_all_agents(self) -> Dict[str, Any]:
        """获取所有智能体"""
        return self.agents

    async def cleanup(self) -> None:
        """清理资源"""
        if self.manager:
            await self.manager.stop_all()

    @property
    def story_title(self) -> str:
        """故事标题"""
        return self.story_config.title if self.story_config else ""

    @property
    def story_theme(self) -> str:
        """故事主题"""
        return self.story_config.theme if self.story_config else ""

    @property
    def character_ids(self) -> List[str]:
        """所有角色ID"""
        return list(self.story_config.characters.keys()) if self.story_config else []


async def create_story_agents(
    story_config_path: str,
    character_ids: Optional[List[str]] = None,
    use_llm: bool = True,
    prompts_path: str = "/home/user/new_agent_system/config/prompts.yaml"
) -> Dict[str, Any]:
    """
    快速创建故事智能体的辅助函数

    Args:
        story_config_path: 故事配置文件路径
        character_ids: 要创建的角色ID列表（None表示创建所有角色）
        use_llm: 是否使用LLM
        prompts_path: 提示词配置路径

    Returns:
        {character_id: agent} 字典

    Example:
        >>> agents = await create_story_agents("config/holmes_story.yaml")
        >>> holmes = agents["holmes"]
        >>> await holmes.chat("你好，福尔摩斯！")
    """
    factory = StoryAgentFactory(story_config_path, prompts_path)
    await factory.initialize(use_llm=use_llm)

    if character_ids:
        # 只返回指定的角色
        return {char_id: factory.get_agent(char_id) for char_id in character_ids}
    else:
        # 返回所有角色
        return factory.get_all_agents()
