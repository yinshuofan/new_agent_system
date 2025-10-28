"""
提示词管理器
负责加载和管理各模块的提示词模板
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class PromptManager:
    """
    提示词管理器
    从配置文件加载提示词模板
    """

    def __init__(self, prompt_config_path: Optional[str] = None):
        """
        初始化提示词管理器

        Args:
            prompt_config_path: 提示词配置文件路径
        """
        self._prompts: Dict[str, Dict[str, str]] = {}
        self._loaded = False

        if prompt_config_path:
            self.load_prompts(prompt_config_path)

    def load_prompts(self, config_path: str) -> None:
        """
        加载提示词配置

        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Prompt config file not found: {config_path}")

        with open(path, 'r', encoding='utf-8') as f:
            self._prompts = yaml.safe_load(f)

        self._loaded = True

    def get_prompt(self, module: str, prompt_name: str, **kwargs) -> str:
        """
        获取提示词并进行格式化

        Args:
            module: 模块名称（如cognition, emotion等）
            prompt_name: 提示词名称
            **kwargs: 格式化参数

        Returns:
            格式化后的提示词
        """
        if not self._loaded:
            return self._get_default_prompt(module, prompt_name, **kwargs)

        if module not in self._prompts:
            return self._get_default_prompt(module, prompt_name, **kwargs)

        if prompt_name not in self._prompts[module]:
            return self._get_default_prompt(module, prompt_name, **kwargs)

        template = self._prompts[module][prompt_name]

        # 格式化模板
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # 如果缺少参数，返回原模板
            return template

    def _get_default_prompt(self, module: str, prompt_name: str, **kwargs) -> str:
        """
        获取默认提示词（当配置文件不存在或没有配置时使用）

        Args:
            module: 模块名称
            prompt_name: 提示词名称
            **kwargs: 格式化参数

        Returns:
            默认提示词
        """
        # 最简化的默认提示词
        default_prompts = {
            "cognition": {
                "make_decision": "Based on the current situation, make a decision.\n\nSituation: {situation}\n\nProvide your decision in JSON format with 'action', 'reasoning', and 'confidence' fields.'action'参数中必须包含'type'参数，用于表明你要执行的操作类型，例如'send_message'、'think'等。",
                "reflect": "Reflect on recent decisions and experiences.\n\nRecent decisions: {recent_decisions}\n\nProvide insights and adjustments in JSON format.",
                "system": "You are an intelligent agent making decisions based on perception, memory, emotion, and goals."
            },
            "emotion": {
                "process_emotion": "Analyze the emotional impact of this event.\n\nEvent: {trigger}\nCurrent emotion: {current_emotion}\n\nProvide emotion changes in JSON format with 'valence', 'arousal', and 'primary_emotion' fields.",
                "system": "You are processing emotional responses to events."
            },
            "goal": {
                "generate_goal": "Generate a new goal based on current needs.\n\nNeeds: {needs}\nContext: {context}\n\nProvide goal in JSON format with 'title', 'description', and 'priority' fields.",
                "evaluate_progress": "Evaluate progress towards this goal.\n\nGoal: {goal}\nRecent actions: {actions}\n\nProvide progress evaluation.",
                "system": "You are managing goals and needs."
            },
            "perception": {
                "analyze_perception": "Analyze this perception and extract key information.\n\nPerception: {perception}\n\nProvide analysis in JSON format.",
                "system": "You are processing sensory input."
            },
            "memory": {
                "summarize_memory": "Summarize this event for storage.\n\nEvent details: {event}\n\nProvide a concise summary.",
                "retrieve_relevant": "Find the most relevant memories.\n\nQuery: {query}\nAvailable memories: {memories}\n\nList relevant memory IDs.",
                "system": "You are managing memory storage and retrieval."
            },
            "story": {
                "generate_story": "Generate a story scenario.\n\nTheme: {theme}\nCharacters: {characters}\n\nProvide story in JSON format with 'setting', 'plot_points', and 'goals' fields.",
                "check_deviation": "Check if agent actions deviate from the story.\n\nStory: {story}\nAgent action: {action}\n\nProvide analysis in JSON format.",
                "system": "You are managing story narrative."
            }
        }

        if module in default_prompts and prompt_name in default_prompts[module]:
            template = default_prompts[module][prompt_name]
            try:
                return template.format(**kwargs)
            except KeyError:
                return template

        return f"[Default prompt for {module}.{prompt_name}]"

    def set_prompt(self, module: str, prompt_name: str, prompt_template: str) -> None:
        """
        动态设置提示词

        Args:
            module: 模块名称
            prompt_name: 提示词名称
            prompt_template: 提示词模板
        """
        if module not in self._prompts:
            self._prompts[module] = {}

        self._prompts[module][prompt_name] = prompt_template

    def get_all_prompts(self) -> Dict[str, Dict[str, str]]:
        """获取所有提示词"""
        return self._prompts.copy()


# 全局提示词管理器
_global_prompt_manager: Optional[PromptManager] = None


def initialize_prompts(config_path: Optional[str] = None) -> PromptManager:
    """
    初始化全局提示词管理器

    Args:
        config_path: 配置文件路径

    Returns:
        提示词管理器实例
    """
    global _global_prompt_manager
    _global_prompt_manager = PromptManager(config_path)
    return _global_prompt_manager


def get_prompt_manager() -> PromptManager:
    """获取全局提示词管理器"""
    global _global_prompt_manager
    if _global_prompt_manager is None:
        _global_prompt_manager = PromptManager()
    return _global_prompt_manager
