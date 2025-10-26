"""
剧情加载器
从YAML配置文件加载剧情
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class StoryConfig:
    """剧情配置数据类"""

    def __init__(self, config_data: Dict[str, Any]):
        self.data = config_data
        self.metadata = config_data.get("metadata", {})
        self.characters = config_data.get("characters", {})
        self.timeline = config_data.get("timeline", [])
        self.settings = config_data.get("story_settings", {})
        self.interaction_rules = config_data.get("interaction_rules", {})
        self.memory_settings = config_data.get("memory_settings", {})

    @property
    def title(self) -> str:
        return self.metadata.get("title", "Untitled Story")

    @property
    def theme(self) -> str:
        return self.metadata.get("theme", "")

    @property
    def date(self) -> str:
        return self.metadata.get("date", datetime.now().strftime("%Y-%m-%d"))

    def get_character_config(self, char_id: str) -> Dict[str, Any]:
        """获取角色配置"""
        return self.characters.get(char_id, {})

    def get_timeline_events(self) -> List[Dict[str, Any]]:
        """获取时间线事件"""
        return self.timeline

    def get_chapter_events(self, chapter: int) -> List[Dict[str, Any]]:
        """获取指定章节的事件"""
        return [event for event in self.timeline if event.get("chapter") == chapter]

    def get_event_by_time(self, time_str: str) -> Optional[Dict[str, Any]]:
        """根据时间获取事件"""
        for event in self.timeline:
            if event.get("time") == time_str:
                return event
        return None

    def get_current_event(self, current_time: datetime) -> Optional[Dict[str, Any]]:
        """获取当前应该发生的事件"""
        current_time_str = current_time.strftime("%H:%M")

        for i, event in enumerate(self.timeline):
            event_time = event.get("time", "")

            # 检查是否是当前事件
            if event_time == current_time_str:
                return event

            # 检查是否在事件时间范围内
            if i < len(self.timeline) - 1:
                next_event_time = self.timeline[i + 1].get("time", "")
                if event_time <= current_time_str < next_event_time:
                    return event

        return None

    def get_next_event(self, current_time: datetime) -> Optional[Dict[str, Any]]:
        """获取下一个事件"""
        current_time_str = current_time.strftime("%H:%M")

        for event in self.timeline:
            if event.get("time", "") > current_time_str:
                return event

        return None

    @property
    def auto_progression(self) -> bool:
        """是否自动推进"""
        return self.settings.get("auto_progression", False)

    @property
    def check_interval_minutes(self) -> int:
        """检查间隔（分钟）"""
        return self.settings.get("check_interval_minutes", 5)

    @property
    def allow_deviation(self) -> bool:
        """是否允许偏离"""
        return self.settings.get("allow_deviation", True)

    @property
    def deviation_threshold(self) -> float:
        """偏离阈值"""
        return self.settings.get("deviation_threshold", 0.6)


class StoryLoader:
    """
    剧情加载器
    从YAML文件加载剧情配置
    """

    @staticmethod
    def load_from_file(file_path: str) -> StoryConfig:
        """
        从文件加载剧情配置

        Args:
            file_path: YAML配置文件路径

        Returns:
            StoryConfig实例

        Raises:
            FileNotFoundError: 文件不存在
            yaml.YAMLError: YAML格式错误
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Story config file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        return StoryConfig(config_data)

    @staticmethod
    def load_from_dict(config_data: Dict[str, Any]) -> StoryConfig:
        """
        从字典加载剧情配置

        Args:
            config_data: 配置数据字典

        Returns:
            StoryConfig实例
        """
        return StoryConfig(config_data)

    @staticmethod
    def create_story_outline_from_config(story_config: StoryConfig):
        """
        从配置创建StoryOutline

        Args:
            story_config: StoryConfig实例

        Returns:
            StoryOutline对象
        """
        from agent_system.models.schedule_models import StoryOutline

        # 提取角色角色和目标
        character_roles = {}
        character_goals = {}

        for char_id, char_data in story_config.characters.items():
            character_roles[char_id] = char_data.get("role", "")
            character_goals[char_id] = char_data.get("story_goal", "")

        # 提取主要剧情点
        main_plot_points = []
        for event in story_config.timeline:
            time = event.get("time", "")
            title = event.get("title", "")
            description = event.get("description", "").strip()
            # 只取第一行作为剧情点
            first_line = description.split('\n')[0] if description else title
            main_plot_points.append(f"{time} {title}: {first_line}")

        # 提取关键事件
        key_events = []
        for event in story_config.timeline:
            key_events.append({
                "time": event.get("time", ""),
                "event": event.get("title", ""),
                "participants": event.get("participants", []),
                "description": event.get("description", "").split('\n')[0]
            })

        # 创建StoryOutline
        outline = StoryOutline(
            story_id=f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=story_config.title,
            theme=story_config.theme,
            story_date=story_config.date,
            setting=f"{story_config.title}的背景设定",
            time_period="一天",
            main_plot_points=main_plot_points,
            character_roles=character_roles,
            character_goals=character_goals,
            key_events=key_events,
            narrative_constraints=[]
        )

        return outline

    @staticmethod
    def generate_schedule_from_config(
        story_config: StoryConfig,
        agent_id: str
    ):
        """
        从配置生成角色日程

        Args:
            story_config: StoryConfig实例
            agent_id: 角色ID

        Returns:
            DailySchedule对象
        """
        from agent_system.models.schedule_models import DailySchedule, ScheduleItem, ScheduleStatus
        import uuid

        schedule_items = []

        # 遍历时间线，为该角色生成日程
        for event in story_config.timeline:
            participants = event.get("participants", [])

            # 如果该角色参与此事件
            if agent_id in participants:
                time_str = event.get("time", "09:00")
                title = event.get("title", "未命名活动")
                description = event.get("description", "").strip()
                location = event.get("location", "未知地点")

                # 估算时长（默认1小时，最后一个事件30分钟）
                event_index = story_config.timeline.index(event)
                if event_index < len(story_config.timeline) - 1:
                    next_time_str = story_config.timeline[event_index + 1].get("time", "")
                    duration = calculate_duration(time_str, next_time_str)
                else:
                    duration = 30  # 最后一个事件30分钟

                end_time_str = calculate_end_time(time_str, duration)

                # 其他参与者
                other_agents = [p for p in participants if p != agent_id]

                schedule_item = ScheduleItem(
                    schedule_id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    date=story_config.date,
                    start_time=time_str,
                    end_time=end_time_str,
                    duration_minutes=duration,
                    activity=title,
                    description=description.split('\n')[0] if description else title,
                    location=location,
                    related_agents=other_agents,
                    related_plot_point=title,
                    story_alignment_score=1.0,
                    status=ScheduleStatus.PLANNED,
                    is_narrative=True
                )

                schedule_items.append(schedule_item)

        # 创建DailySchedule
        daily_schedule = DailySchedule(
            agent_id=agent_id,
            date=story_config.date,
            story_id=story_config.title,
            schedule_items=schedule_items,
            overall_alignment=1.0,
            deviation_warnings=[]
        )

        return daily_schedule


def calculate_duration(start_time: str, end_time: str) -> int:
    """
    计算时长（分钟）

    Args:
        start_time: 开始时间 "HH:MM"
        end_time: 结束时间 "HH:MM"

    Returns:
        时长（分钟）
    """
    try:
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))

        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m

        if end_minutes > start_minutes:
            return end_minutes - start_minutes
        else:
            # 跨天
            return (24 * 60 - start_minutes) + end_minutes
    except:
        return 60  # 默认1小时


def calculate_end_time(start_time: str, duration_minutes: int) -> str:
    """
    计算结束时间

    Args:
        start_time: 开始时间 "HH:MM"
        duration_minutes: 时长（分钟）

    Returns:
        结束时间 "HH:MM"
    """
    try:
        h, m = map(int, start_time.split(':'))
        total_minutes = h * 60 + m + duration_minutes

        end_h = (total_minutes // 60) % 24
        end_m = total_minutes % 60

        return f"{end_h:02d}:{end_m:02d}"
    except:
        return "18:00"
