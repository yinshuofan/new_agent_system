"""
日程相关数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum


class ScheduleStatus(Enum):
    """日程状态"""
    PLANNED = "planned"  # 已计划
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    MODIFIED = "modified"  # 已修改


class ScheduleItem(BaseModel):
    """单个日程项"""
    schedule_id: str = Field(description="日程唯一ID")
    agent_id: str = Field(description="智能体ID")

    # 时间信息
    date: str = Field(description="日期（YYYY-MM-DD）")
    start_time: str = Field(description="开始时间（HH:MM）")
    end_time: str = Field(description="结束时间（HH:MM）")
    duration_minutes: int = Field(description="持续时间（分钟）")

    # 活动信息
    activity: str = Field(description="活动名称")
    description: str = Field(description="活动详细描述")
    location: Optional[str] = Field(None, description="地点")

    # 关联信息
    related_agents: List[str] = Field(default_factory=list, description="相关智能体ID列表")
    related_plot_point: Optional[str] = Field(None, description="关联的剧情点")
    story_alignment_score: float = Field(1.0, ge=0.0, le=1.0, description="与剧情的对齐度")

    # 状态
    status: ScheduleStatus = Field(ScheduleStatus.PLANNED, description="日程状态")
    completed: bool = Field(False, description="是否完成")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    modified_at: Optional[datetime] = Field(None, description="最后修改时间")
    modification_reason: Optional[str] = Field(None, description="修改原因")

    # 演绎标记
    is_narrative: bool = Field(True, description="是否为剧情演绎（非真实执行）")

    def is_current(self, current_time: datetime) -> bool:
        """
        检查是否为当前时间段的活动

        Args:
            current_time: 当前时间

        Returns:
            是否为当前活动
        """
        # 解析时间
        start_hour, start_minute = map(int, self.start_time.split(':'))
        end_hour, end_minute = map(int, self.end_time.split(':'))

        current_hour = current_time.hour
        current_minute = current_time.minute

        # 转换为分钟数便于比较
        current_minutes = current_hour * 60 + current_minute
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute

        return start_minutes <= current_minutes < end_minutes

    def mark_completed(self) -> None:
        """标记为已完成"""
        self.status = ScheduleStatus.COMPLETED
        self.completed = True

    def modify(self, updates: Dict[str, Any], reason: str = "") -> None:
        """
        修改日程

        Args:
            updates: 更新的字段
            reason: 修改原因
        """
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.status = ScheduleStatus.MODIFIED
        self.modified_at = datetime.now()
        self.modification_reason = reason

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "schedule_001",
                "agent_id": "alice",
                "date": "2025-10-26",
                "start_time": "09:00",
                "end_time": "10:00",
                "duration_minutes": 60,
                "activity": "晨间会议",
                "description": "与团队讨论今日计划",
                "location": "会议室A",
                "related_agents": ["bob", "charlie"],
                "related_plot_point": "项目启动",
                "status": "planned",
                "is_narrative": True
            }
        }


class DailySchedule(BaseModel):
    """每日日程"""
    agent_id: str = Field(description="智能体ID")
    date: str = Field(description="日期（YYYY-MM-DD）")
    story_id: Optional[str] = Field(None, description="关联的剧情ID")

    # 日程列表（按时间排序）
    schedule_items: List[ScheduleItem] = Field(default_factory=list, description="日程项列表")

    # 统计信息
    total_activities: int = Field(0, description="总活动数")
    completed_activities: int = Field(0, description="已完成活动数")

    # 剧情对齐
    overall_alignment: float = Field(1.0, ge=0.0, le=1.0, description="整体剧情对齐度")
    deviation_warnings: List[str] = Field(default_factory=list, description="偏离警告")

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    def add_item(self, item: ScheduleItem) -> None:
        """添加日程项"""
        self.schedule_items.append(item)
        self.schedule_items.sort(key=lambda x: x.start_time)
        self.total_activities = len(self.schedule_items)
        self.last_updated = datetime.now()
        self._update_alignment()

    def remove_item(self, schedule_id: str) -> bool:
        """
        移除日程项

        Args:
            schedule_id: 日程ID

        Returns:
            是否成功移除
        """
        original_length = len(self.schedule_items)
        self.schedule_items = [item for item in self.schedule_items if item.schedule_id != schedule_id]

        if len(self.schedule_items) < original_length:
            self.total_activities = len(self.schedule_items)
            self.last_updated = datetime.now()
            self._update_alignment()
            return True
        return False

    def get_current_activity(self, current_time: datetime) -> Optional[ScheduleItem]:
        """
        获取当前时间段的活动

        Args:
            current_time: 当前时间

        Returns:
            当前活动，如果没有则返回None
        """
        for item in self.schedule_items:
            if item.is_current(current_time):
                return item
        return None

    def get_next_activity(self, current_time: datetime) -> Optional[ScheduleItem]:
        """
        获取下一个活动

        Args:
            current_time: 当前时间

        Returns:
            下一个活动
        """
        current_minutes = current_time.hour * 60 + current_time.minute

        for item in self.schedule_items:
            hour, minute = map(int, item.start_time.split(':'))
            item_minutes = hour * 60 + minute

            if item_minutes > current_minutes and not item.completed:
                return item

        return None

    def update_item(self, schedule_id: str, updates: Dict[str, Any], reason: str = "") -> bool:
        """
        更新日程项

        Args:
            schedule_id: 日程ID
            updates: 更新内容
            reason: 修改原因

        Returns:
            是否成功更新
        """
        for item in self.schedule_items:
            if item.schedule_id == schedule_id:
                item.modify(updates, reason)
                self.last_updated = datetime.now()
                self._update_alignment()
                return True
        return False

    def mark_completed(self, schedule_id: str) -> bool:
        """
        标记日程项为已完成

        Args:
            schedule_id: 日程ID

        Returns:
            是否成功标记
        """
        for item in self.schedule_items:
            if item.schedule_id == schedule_id:
                item.mark_completed()
                self.completed_activities = sum(1 for i in self.schedule_items if i.completed)
                self.last_updated = datetime.now()
                return True
        return False

    def _update_alignment(self) -> None:
        """更新整体对齐度"""
        if not self.schedule_items:
            self.overall_alignment = 1.0
            return

        total_score = sum(item.story_alignment_score for item in self.schedule_items)
        self.overall_alignment = total_score / len(self.schedule_items)

        # 检查偏离
        self.deviation_warnings.clear()
        for item in self.schedule_items:
            if item.story_alignment_score < 0.5:
                self.deviation_warnings.append(
                    f"{item.start_time} {item.activity}: 严重偏离剧情"
                )

    def get_summary(self) -> str:
        """
        获取日程摘要

        Returns:
            日程摘要字符串
        """
        if not self.schedule_items:
            return "今天没有安排活动"

        summary = f"今天共有{self.total_activities}个活动:\n"
        for item in self.schedule_items:
            status_emoji = "✓" if item.completed else "○"
            summary += f"{status_emoji} {item.start_time}-{item.end_time}: {item.activity}\n"

        return summary.strip()


class StoryOutline(BaseModel):
    """剧情大纲"""
    story_id: str = Field(description="剧情ID")
    title: str = Field(description="剧情标题")
    theme: str = Field(description="主题")

    # 时间设定
    story_date: str = Field(description="剧情日期")
    time_period: str = Field(description="时间段（如：一天、一周）")

    # 剧情结构
    setting: str = Field(description="背景设定")
    main_plot_points: List[str] = Field(description="主要剧情点")

    # 角色设定
    character_roles: Dict[str, str] = Field(description="角色定位 {agent_id: role_description}")
    character_goals: Dict[str, str] = Field(description="角色目标 {agent_id: goal}")

    # 关键时间点
    key_events: List[Dict[str, Any]] = Field(default_factory=list, description="关键事件列表")

    # 剧情要求
    narrative_constraints: List[str] = Field(default_factory=list, description="剧情约束条件")

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_schema_extra = {
            "example": {
                "story_id": "story_001",
                "title": "侦探的一天",
                "theme": "推理悬疑",
                "story_date": "2025-10-26",
                "time_period": "一天",
                "setting": "伦敦，阴雨天",
                "main_plot_points": [
                    "早晨接到案件",
                    "现场调查",
                    "询问证人",
                    "发现线索",
                    "推理破案"
                ],
                "character_roles": {
                    "detective": "主角侦探",
                    "assistant": "助手"
                },
                "character_goals": {
                    "detective": "破解盗窃案",
                    "assistant": "协助侦探"
                }
            }
        }
