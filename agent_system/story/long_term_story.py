"""
长期剧情系统 - 混合式方案
支持几百天甚至几千天的剧情配置

核心思想：
1. 日常模板 - 定义重复活动模式
2. 剧情阶段 - 定义故事弧线
3. 关键事件 - 手动配置重要节点
4. 动态生成 - LLM按需生成细节
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
from pathlib import Path
import yaml

from agent_system.models.schedule_models import ScheduleItem, ScheduleStatus


class DayType(Enum):
    """日期类型"""
    WEEKDAY = "weekday"  # 工作日
    WEEKEND = "weekend"  # 周末
    HOLIDAY = "holiday"  # 假日
    SPECIAL = "special"  # 特殊日


@dataclass
class DailyTemplate:
    """日常活动模板"""
    template_id: str
    name: str
    applicable_days: List[int]  # [1-7] 表示周一到周日，或 [1-365] 表示一年中的天数
    activities: List[Dict[str, Any]]  # 活动列表
    priority: int = 1  # 优先级（数字越大越优先）


@dataclass
class StoryPhase:
    """故事阶段"""
    phase_id: str
    title: str
    day_range: tuple  # (start_day, end_day)
    theme: str
    description: str = ""
    key_events: List[Dict[str, Any]] = field(default_factory=list)
    character_goals: Dict[str, List[str]] = field(default_factory=dict)  # {character_id: [goals]}
    override_templates: bool = False  # 是否覆盖日常模板


@dataclass
class EventRule:
    """事件生成规则"""
    rule_id: str
    event_type: str
    frequency: str  # "daily", "weekly", "monthly", "random"
    probability: float = 1.0  # 0-1，用于随机事件
    applicable_phases: List[str] = field(default_factory=list)  # 适用的剧情阶段
    templates: List[Dict[str, Any]] = field(default_factory=list)  # 事件模板


class LongTermStoryEngine:
    """
    长期剧情引擎
    支持几百天甚至几千天的剧情生成
    """

    def __init__(
        self,
        start_date: datetime,
        total_days: int = 365,
        use_llm: bool = True
    ):
        """
        初始化长期剧情引擎

        Args:
            start_date: 起始日期
            total_days: 总天数
            use_llm: 是否使用LLM动态生成
        """
        self.start_date = start_date
        self.total_days = total_days
        self.use_llm = use_llm

        # 存储配置
        self.daily_templates: Dict[str, DailyTemplate] = {}
        self.story_phases: Dict[str, StoryPhase] = {}
        self.event_rules: Dict[str, EventRule] = {}
        self.key_events: Dict[int, List[Dict]] = {}  # {day_number: [events]}

        # 缓存
        self._generated_days: Dict[int, List[ScheduleItem]] = {}
        self._cache_size = 30  # 缓存30天

    def add_daily_template(self, template: DailyTemplate) -> None:
        """添加日常活动模板"""
        self.daily_templates[template.template_id] = template

    def add_story_phase(self, phase: StoryPhase) -> None:
        """添加故事阶段"""
        self.story_phases[phase.phase_id] = phase

    def add_event_rule(self, rule: EventRule) -> None:
        """添加事件生成规则"""
        self.event_rules[rule.rule_id] = rule

    def add_key_event(self, day_number: int, event: Dict[str, Any]) -> None:
        """添加关键事件"""
        if day_number not in self.key_events:
            self.key_events[day_number] = []
        self.key_events[day_number].append(event)

    def get_day_schedule(
        self,
        day_number: int,
        character_id: str = None
    ) -> List[ScheduleItem]:
        """
        获取指定天数的日程

        Args:
            day_number: 第几天（从1开始）
            character_id: 角色ID（用于角色特定的日程）

        Returns:
            该天的日程项列表
        """
        # 检查缓存
        cache_key = f"{day_number}_{character_id}"
        if cache_key in self._generated_days:
            return self._generated_days[cache_key]

        # 计算日期
        current_date = self.start_date + timedelta(days=day_number - 1)
        weekday = current_date.weekday() + 1  # 1-7

        # 1. 获取适用的剧情阶段
        current_phase = self._get_current_phase(day_number)

        # 2. 生成基础日程（从模板）
        schedule_items = []

        # 如果阶段不覆盖模板，使用日常模板
        if not current_phase or not current_phase.override_templates:
            schedule_items.extend(
                self._generate_from_templates(day_number, weekday, current_date, character_id)
            )

        # 3. 添加关键事件
        if day_number in self.key_events:
            schedule_items.extend(
                self._create_items_from_events(self.key_events[day_number], current_date, character_id)
            )

        # 4. 添加阶段事件
        if current_phase:
            phase_events = self._get_phase_events(current_phase, day_number)
            schedule_items.extend(
                self._create_items_from_events(phase_events, current_date, character_id)
            )

        # 5. 应用事件规则
        rule_events = self._generate_from_rules(day_number, weekday, current_phase)
        schedule_items.extend(
            self._create_items_from_events(rule_events, current_date, character_id)
        )

        # 6. LLM动态生成（如果启用）
        if self.use_llm and self._should_generate_dynamic_content(day_number):
            dynamic_items = self._generate_dynamic_content(
                day_number,
                current_date,
                current_phase,
                schedule_items,
                character_id
            )
            schedule_items.extend(dynamic_items)

        # 7. 排序和去重
        schedule_items = self._sort_and_deduplicate(schedule_items)

        # 8. 缓存
        self._cache_schedule(cache_key, schedule_items)

        return schedule_items

    def _get_current_phase(self, day_number: int) -> Optional[StoryPhase]:
        """获取当前剧情阶段"""
        for phase in self.story_phases.values():
            start, end = phase.day_range
            if start <= day_number <= end:
                return phase
        return None

    def _generate_from_templates(
        self,
        day_number: int,
        weekday: int,
        current_date: datetime,
        agent_id: str = "unknown"
    ) -> List[ScheduleItem]:
        """从模板生成日程"""
        items = []

        # 按优先级排序模板
        sorted_templates = sorted(
            self.daily_templates.values(),
            key=lambda t: t.priority,
            reverse=True
        )

        for template in sorted_templates:
            # 检查是否适用于当天
            if weekday in template.applicable_days or day_number in template.applicable_days:
                for activity in template.activities:
                    item = self._create_schedule_item(activity, current_date, template.name, agent_id)
                    items.append(item)

        return items

    def _get_phase_events(self, phase: StoryPhase, day_number: int) -> List[Dict]:
        """获取阶段内的事件"""
        events = []
        for key_event in phase.key_events:
            trigger_day = key_event.get("trigger_day")
            if trigger_day == day_number:
                events.append(key_event)
        return events

    def _generate_from_rules(
        self,
        day_number: int,
        weekday: int,
        current_phase: Optional[StoryPhase]
    ) -> List[Dict]:
        """根据规则生成事件"""
        events = []

        for rule in self.event_rules.values():
            # 检查是否适用于当前阶段
            if rule.applicable_phases and current_phase:
                if current_phase.phase_id not in rule.applicable_phases:
                    continue

            # 根据频率决定是否触发
            should_trigger = False

            if rule.frequency == "daily":
                should_trigger = True
            elif rule.frequency == "weekly":
                should_trigger = (weekday == 1)  # 每周一
            elif rule.frequency == "monthly":
                should_trigger = (day_number % 30 == 1)  # 每30天
            elif rule.frequency == "random":
                should_trigger = (random.random() < rule.probability)

            if should_trigger and rule.templates:
                # 随机选择一个模板
                template = random.choice(rule.templates)
                events.append(template)

        return events

    def _should_generate_dynamic_content(self, day_number: int) -> bool:
        """判断是否需要LLM动态生成内容"""
        # 简单策略：每10天生成一次
        return (day_number % 10 == 0)

    def _generate_dynamic_content(
        self,
        day_number: int,
        current_date: datetime,
        current_phase: Optional[StoryPhase],
        existing_items: List[ScheduleItem],
        character_id: str
    ) -> List[ScheduleItem]:
        """LLM动态生成内容（占位符，实际需要调用LLM）"""
        # TODO: 实现LLM调用
        # 这里返回空列表，实际应该调用LLM生成
        return []

    def _create_schedule_item(
        self,
        event: Dict[str, Any],
        date: datetime,
        source: str = "",
        agent_id: str = "unknown"
    ) -> ScheduleItem:
        """创建日程项"""
        import uuid

        start_time_str = event.get("time", "09:00")
        end_time_str = event.get("end_time", "10:00")

        # 计算持续时间（分钟）
        start_h, start_m = map(int, start_time_str.split(':'))
        end_h, end_m = map(int, end_time_str.split(':'))
        duration = (end_h * 60 + end_m) - (start_h * 60 + start_m)
        if duration <= 0:
            duration = 60  # 默认1小时

        return ScheduleItem(
            schedule_id=f"sched_{uuid.uuid4().hex[:12]}",
            agent_id=agent_id,
            date=date.strftime("%Y-%m-%d"),
            start_time=start_time_str,
            end_time=end_time_str,
            duration_minutes=duration,
            activity=event.get("activity", event.get("title", "活动")),
            description=event.get("description", ""),
            location=event.get("location", "未知"),
            related_agents=event.get("participants", []),
            status=ScheduleStatus.PLANNED
        )

    def _create_items_from_events(
        self,
        events: List[Dict],
        date: datetime,
        agent_id: str = "unknown"
    ) -> List[ScheduleItem]:
        """从事件列表创建日程项"""
        items = []
        for event in events:
            item = self._create_schedule_item(event, date, event.get("source", ""), agent_id)
            items.append(item)
        return items

    def _sort_and_deduplicate(self, items: List[ScheduleItem]) -> List[ScheduleItem]:
        """排序和去重"""
        # 按时间排序
        items.sort(key=lambda x: x.start_time)

        # 简单去重：相同时间和活动的只保留一个
        seen = set()
        unique_items = []
        for item in items:
            key = (item.start_time, item.activity)
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        return unique_items

    def _cache_schedule(self, key: str, items: List[ScheduleItem]) -> None:
        """缓存日程"""
        self._generated_days[key] = items

        # 限制缓存大小
        if len(self._generated_days) > self._cache_size:
            # 删除最旧的
            oldest_key = list(self._generated_days.keys())[0]
            del self._generated_days[oldest_key]

    def get_phase_summary(self) -> Dict[str, Any]:
        """获取剧情阶段摘要"""
        return {
            "total_days": self.total_days,
            "phases_count": len(self.story_phases),
            "phases": [
                {
                    "phase_id": phase.phase_id,
                    "title": phase.title,
                    "day_range": phase.day_range,
                    "theme": phase.theme
                }
                for phase in self.story_phases.values()
            ]
        }

    @classmethod
    def load_from_yaml(cls, config_path: str) -> 'LongTermStoryEngine':
        """从YAML配置文件加载"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 解析元数据
        metadata = config.get("metadata", {})
        start_date_str = metadata.get("start_date", "2025-01-01")
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        total_days = metadata.get("duration_days", 365)
        use_llm = metadata.get("use_llm", True)

        engine = cls(start_date, total_days, use_llm)

        # 加载日常模板
        for template_id, template_data in config.get("daily_templates", {}).items():
            template = DailyTemplate(
                template_id=template_id,
                name=template_data.get("name", template_id),
                applicable_days=template_data.get("applicable_days", []),
                activities=template_data.get("activities", []),
                priority=template_data.get("priority", 1)
            )
            engine.add_daily_template(template)

        # 加载故事阶段
        for phase_id, phase_data in config.get("story_phases", {}).items():
            phase = StoryPhase(
                phase_id=phase_id,
                title=phase_data.get("title", phase_id),
                day_range=tuple(phase_data.get("day_range", [1, total_days])),
                theme=phase_data.get("theme", ""),
                description=phase_data.get("description", ""),
                key_events=phase_data.get("key_events", []),
                character_goals=phase_data.get("character_goals", {}),
                override_templates=phase_data.get("override_templates", False)
            )
            engine.add_story_phase(phase)

        # 加载事件规则
        for rule_id, rule_data in config.get("event_rules", {}).items():
            rule = EventRule(
                rule_id=rule_id,
                event_type=rule_data.get("event_type", ""),
                frequency=rule_data.get("frequency", "daily"),
                probability=rule_data.get("probability", 1.0),
                applicable_phases=rule_data.get("applicable_phases", []),
                templates=rule_data.get("templates", [])
            )
            engine.add_event_rule(rule)

        return engine
