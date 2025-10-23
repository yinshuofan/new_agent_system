"""
Agent System - 智能体系统
一个支持高并发的模块化智能体框架
"""

from agent_system.core.agent import Agent
from agent_system.core.event_bus import EventBus, Event, EventType
from agent_system.manager.agent_manager import AgentManager, get_global_manager
from agent_system.scheduler.trigger import AgentScheduler, PeriodicTrigger

__version__ = "0.1.0"
__all__ = [
    "Agent",
    "AgentManager",
    "EventBus",
    "Event",
    "EventType",
    "AgentScheduler",
    "PeriodicTrigger",
    "get_global_manager"
]
